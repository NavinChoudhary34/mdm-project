from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.movies.models import Movie
from apps.movies.serializers import MovieListSerializer
from .doubly_linked_list import DoublyLinkedList
from .max_heap import MaxHeap
from .models import RecentlyViewed
from .services import undo_last_playlist_action, visible_movies_for_user
from .trie import MovieTitleTrie

class MovieAutocompleteView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        query = request.query_params.get('q','').strip()
        if len(query) < 2:
            return Response([])
        movies = visible_movies_for_user(request.user).only('id','title').order_by('title')[:1000]
        trie = MovieTitleTrie(); by_id = {}
        for movie in movies:
            trie.insert(movie.title, movie.id); by_id[movie.id] = movie
        return Response([{'id':i,'title':by_id[i].title} for i in trie.autocomplete(query,8)])

class TopRatedMoviesView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        try:
            limit = max(1,min(int(request.query_params.get('limit',10)),20))
        except ValueError:
            limit = 10
        heap = MaxHeap()
        for movie in visible_movies_for_user(request.user).filter(rating__isnull=False):
            heap.push((movie.rating, movie.id), movie)
        movies=[]
        while len(heap) and len(movies)<limit:
            movies.append(heap.pop()[1])
        return Response(MovieListSerializer(movies,many=True,context={'request':request}).data)

class RecentlyViewedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        ids=list(RecentlyViewed.objects.filter(user=request.user).order_by('-viewed_at','-id').values_list('movie_id',flat=True))
        movie_map={m.id:m for m in Movie.objects.filter(id__in=ids).select_related('owner','director').prefetch_related('genres')}
        dll=DoublyLinkedList()
        for movie_id in reversed(ids):
            if movie_id in movie_map: dll.add_front(movie_id)
        movies=[movie_map[i] for i in dll.values()]
        return Response(MovieListSerializer(movies,many=True,context={'request':request}).data)

class UndoPlaylistActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        action=undo_last_playlist_action(request.user)
        if action is None:
            return Response({'detail':'There is no playlist change to undo.'},status=status.HTTP_404_NOT_FOUND)
        return Response({'detail':'Last playlist change undone.','playlist_id':action.playlist_id,'action_type':action.action_type})
