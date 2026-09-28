from django.db import transaction
from django.utils import timezone
from apps.movies.models import Movie
from apps.playlists.models import PlaylistMovie
from .doubly_linked_list import DoublyLinkedList
from .models import PlaylistUndoAction, RecentlyViewed
from .stack import Stack

RECENT_VIEW_LIMIT = 10
UNDO_STACK_LIMIT = 30

def record_recent_view(user, movie):
    ids = list(RecentlyViewed.objects.filter(user=user).order_by('-viewed_at','-id').values_list('movie_id', flat=True)[:RECENT_VIEW_LIMIT])
    dll = DoublyLinkedList()
    for movie_id in reversed(ids):
        dll.add_front(movie_id)
    dll.remove(movie.id)
    dll.add_front(movie.id)
    while dll.size > RECENT_VIEW_LIMIT:
        dll.remove_tail()
    ordered = dll.values()
    now = timezone.now()
    with transaction.atomic():
        RecentlyViewed.objects.filter(user=user).delete()
        RecentlyViewed.objects.bulk_create([
            RecentlyViewed(user=user, movie_id=movie_id, viewed_at=now-timezone.timedelta(seconds=i))
            for i, movie_id in enumerate(ordered)
        ])

def push_undo_action(user, playlist, action_type, payload):
    PlaylistUndoAction.objects.create(user=user, playlist=playlist, action_type=action_type, payload=payload)
    old = list(PlaylistUndoAction.objects.filter(user=user).order_by('-created_at','-id').values_list('id', flat=True)[UNDO_STACK_LIMIT:])
    if old:
        PlaylistUndoAction.objects.filter(id__in=old).delete()

def undo_last_playlist_action(user):
    actions = list(PlaylistUndoAction.objects.filter(user=user).select_related('playlist').order_by('-created_at','-id')[:UNDO_STACK_LIMIT])
    stack = Stack()
    for action in reversed(actions):
        stack.push(action)
    action = stack.pop()
    if action is None:
        return None
    playlist = action.playlist
    payload = action.payload
    with transaction.atomic():
        if action.action_type == 'add':
            PlaylistMovie.objects.filter(playlist=playlist, movie_id=payload['movie_id']).delete()
        elif action.action_type == 'remove':
            if not PlaylistMovie.objects.filter(playlist=playlist, movie_id=payload['movie_id']).exists():
                PlaylistMovie.objects.create(playlist=playlist, movie_id=payload['movie_id'], position=payload['position'], watched=payload.get('watched',False), notes=payload.get('notes',''))
        elif action.action_type == 'reorder':
            entries = {e.movie_id:e for e in playlist.playlist_movies.all()}
            for position, movie_id in enumerate(payload['movie_ids']):
                if movie_id in entries:
                    entries[movie_id].position = position
            PlaylistMovie.objects.bulk_update(entries.values(), ['position'])
        elif action.action_type == 'update_entry':
            entry = PlaylistMovie.objects.filter(playlist=playlist, movie_id=payload['movie_id']).first()
            if entry:
                entry.watched = payload.get('watched', entry.watched)
                entry.notes = payload.get('notes', entry.notes)
                entry.save(update_fields=['watched','notes'])
        else:
            return None
        playlist.save()
        action.delete()
    return action

def visible_movies_for_user(user):
    from django.db.models import Q
    qs = Movie.objects.select_related('owner','director').prefetch_related('genres')
    if user.is_authenticated:
        return qs.filter(Q(owner__isnull=True)|Q(owner=user)|Q(visibility=Movie.VISIBILITY_PUBLIC)).distinct()
    return qs.filter(Q(owner__isnull=True)|Q(visibility=Movie.VISIBILITY_PUBLIC)).distinct()
