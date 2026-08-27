from django.db.models import Prefetch
from rest_framework import generics, permissions

from apps.library.models import Favorite, WatchedEntry, WatchlistEntry

from .filters import MovieFilter
from .models import Movie
from .permissions import IsStaffOrReadOnly
from .serializers import MovieDetailSerializer, MovieListSerializer, MovieWriteSerializer


class MovieListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/movies/  — paginated, searchable, filterable list of movies. Public (anyone can browse).
    POST /api/movies/  — create a movie. Staff only.
    """
    permission_classes = [IsStaffOrReadOnly]
    filterset_class = MovieFilter
    search_fields = ['title', 'description', 'director__name', 'cast__name']
    ordering_fields = ['title', 'release_date', 'rating', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Movie.objects.select_related('director').prefetch_related('genres').distinct()
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MovieWriteSerializer
        return MovieListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            # One query per relation instead of one query per movie per relation (avoids N+1).
            context['favorited_movie_ids'] = set(
                Favorite.objects.filter(user=user).values_list('movie_id', flat=True)
            )
            context['watchlisted_movie_ids'] = set(
                WatchlistEntry.objects.filter(user=user).values_list('movie_id', flat=True)
            )
            context['watched_movie_ids'] = set(
                WatchedEntry.objects.filter(user=user).values_list('movie_id', flat=True)
            )
        return context

    def create(self, request, *args, **kwargs):
        # Return the richer detail representation after a successful staff create.
        response = super().create(request, *args, **kwargs)
        movie = Movie.objects.get(pk=response.data['id'])
        response.data = MovieDetailSerializer(movie, context=self.get_serializer_context()).data
        return response


class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/movies/:id/ — full movie detail. Public.
    PATCH  /api/movies/:id/ — update. Staff only.
    DELETE /api/movies/:id/ — delete. Staff only.
    """
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        return Movie.objects.select_related('director').prefetch_related(
            'genres', Prefetch('cast_members')
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return MovieWriteSerializer
        return MovieDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['favorited_movie_ids'] = set(
                Favorite.objects.filter(user=user).values_list('movie_id', flat=True)
            )
            context['watchlisted_movie_ids'] = set(
                WatchlistEntry.objects.filter(user=user).values_list('movie_id', flat=True)
            )
            context['watched_movie_ids'] = set(
                WatchedEntry.objects.filter(user=user).values_list('movie_id', flat=True)
            )
        return context

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        movie = self.get_object()
        response.data = MovieDetailSerializer(movie, context=self.get_serializer_context()).data
        return response


class GenreListView(generics.ListAPIView):
    """GET /api/movies/genres/ — used to populate the genre filter dropdown."""
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        from .models import Genre
        return Genre.objects.all()

    def get_serializer_class(self):
        from .serializers import GenreSerializer
        return GenreSerializer
