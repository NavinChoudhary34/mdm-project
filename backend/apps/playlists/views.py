from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.movies.models import Movie

from .models import Playlist, PlaylistMovie
from .permissions import IsPlaylistOwner
from .serializers import (
    AddMovieToPlaylistSerializer,
    PlaylistDetailSerializer,
    PlaylistListSerializer,
    PlaylistMovieSerializer,
    PlaylistMovieUpdateSerializer,
    PlaylistWriteSerializer,
    ReorderSerializer,
)


class PlaylistListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/playlists/ — the current user's own playlists only (private by default).
    POST /api/playlists/ — create a new playlist owned by the current user.
    """
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        # Always scoped to the logged-in user — never trust a user id from the client.
        return Playlist.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return PlaylistWriteSerializer if self.request.method == 'POST' else PlaylistListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        playlist = Playlist.objects.get(pk=response.data['id'])
        response.data = PlaylistDetailSerializer(playlist, context=self.get_serializer_context()).data
        return response


class PlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/playlists/:id/ — full detail (owner only).
    PATCH  /api/playlists/:id/ — rename / edit description / change privacy.
    DELETE /api/playlists/:id/ — delete the playlist.
    """
    permission_classes = [permissions.IsAuthenticated, IsPlaylistOwner]
    queryset = Playlist.objects.all()

    def get_queryset(self):
        # Belt-and-suspenders: object permission already checks ownership, but scoping
        # the queryset too means a non-owner gets a clean 404 instead of leaking existence via 403.
        return Playlist.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        return PlaylistWriteSerializer if self.request.method in ('PUT', 'PATCH') else PlaylistDetailSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        playlist = self.get_object()
        response.data = PlaylistDetailSerializer(playlist, context=self.get_serializer_context()).data
        return response


class PublicPlaylistDetailView(generics.RetrieveAPIView):
    """GET /api/public/playlists/:id/ — read-only, no auth required, only for playlists
    the owner has explicitly marked public. Never exposes private playlists."""
    permission_classes = [permissions.AllowAny]
    serializer_class = PlaylistDetailSerializer
    queryset = Playlist.objects.filter(is_public=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Tells PlaylistDetailSerializer.get_movies() to hide any private
        # movies that happen to be inside this otherwise-public playlist.
        context['public_view'] = True
        return context


class PlaylistMoviesView(APIView):
    """
    GET  /api/playlists/:id/movies/ — list movies in the playlist (owner only).
    POST /api/playlists/:id/movies/ — add a movie (body: {"movie_id": <id>}).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_playlist(self, request, pk):
        # 404s for playlists you don't own rather than 403s, so existence of other
        # users' private playlists is never revealed.
        return get_object_or_404(Playlist, pk=pk, user=request.user)

    def get(self, request, pk):
        playlist = self.get_playlist(request, pk)
        entries = playlist.playlist_movies.select_related('movie').order_by('position', 'added_at')
        return Response(PlaylistMovieSerializer(entries, many=True, context={'request': request}).data)

    def post(self, request, pk):
        playlist = self.get_playlist(request, pk)
        serializer = AddMovieToPlaylistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movie = get_object_or_404(Movie, pk=serializer.validated_data['movie_id'])

        try:
            with transaction.atomic():
                # Lock the playlist row so two concurrent "add movie" requests
                # can't both read the same count and collide on position.
                Playlist.objects.select_for_update().get(pk=playlist.pk)
                next_position = playlist.playlist_movies.count()
                entry = PlaylistMovie.objects.create(playlist=playlist, movie=movie, position=next_position)
        except IntegrityError:
            return Response(
                {'detail': 'This movie is already in the playlist.'},
                status=status.HTTP_409_CONFLICT,
            )
        # NOTE: update_fields=[] is a no-op in Django (an empty-but-not-None
        # list makes save() return immediately without touching the DB), so
        # this must NOT pass update_fields at all in order to bump updated_at
        # via auto_now.
        playlist.save()
        return Response(
            PlaylistMovieSerializer(entry, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class PlaylistMovieDetailView(APIView):
    """
    PATCH  /api/playlists/:id/movies/:movie_id/ — update watched flag / notes for that entry.
    DELETE /api/playlists/:id/movies/:movie_id/ — remove the movie from the playlist.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_entry(self, request, pk, movie_id):
        return get_object_or_404(
            PlaylistMovie, playlist_id=pk, movie_id=movie_id, playlist__user=request.user
        )

    def patch(self, request, pk, movie_id):
        entry = self.get_entry(request, pk, movie_id)
        serializer = PlaylistMovieUpdateSerializer(entry, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PlaylistMovieSerializer(entry, context={'request': request}).data)

    def delete(self, request, pk, movie_id):
        entry = self.get_entry(request, pk, movie_id)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlaylistReorderView(APIView):
    """PATCH /api/playlists/:id/reorder/ — body: {"movie_ids": [3, 1, 2]} sets the new order."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        playlist = get_object_or_404(Playlist, pk=pk, user=request.user)
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movie_ids = serializer.validated_data['movie_ids']

        entries = {e.movie_id: e for e in playlist.playlist_movies.all()}
        if set(movie_ids) != set(entries.keys()):
            raise ValidationError('movie_ids must exactly match the movies currently in this playlist.')

        with transaction.atomic():
            for position, movie_id in enumerate(movie_ids):
                entries[movie_id].position = position
            PlaylistMovie.objects.bulk_update(entries.values(), ['position'])

        return Response(PlaylistDetailSerializer(playlist, context={'request': request}).data)
