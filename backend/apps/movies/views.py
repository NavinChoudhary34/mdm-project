from django.db.models import Prefetch
from rest_framework import generics, permissions

from apps.library.models import Favorite, WatchedEntry, WatchlistEntry

from .filters import MovieFilter
from .models import Movie
from .permissions import MoviePermission
from .serializers import (
    MovieDetailSerializer,
    MovieListSerializer,
    MovieWriteSerializer,
)


class MovieListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/movies/
        Browse movies.

    POST /api/movies/
        Create a movie for the currently authenticated user.
    """

    permission_classes = [MoviePermission]

    filterset_class = MovieFilter
    search_fields = [
        'title',
        'description',
        'director__name',
        'cast__name',
    ]
    ordering_fields = [
        'title',
        'release_date',
        'rating',
        'created_at',
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Movie.objects.select_related('director', 'owner').prefetch_related(
            'genres'
        ).distinct()

        user = self.request.user

        # Anonymous users can only see public movies.
        if not user.is_authenticated:
            return qs.filter(
                visibility=Movie.VISIBILITY_PUBLIC
            )

        # Logged-in users can see:
        # 1. Their own movies
        # 2. Public movies uploaded by other users
        #
        # This will also include catalog/TMDB movies where owner is NULL.
        from django.db.models import Q

        return qs.filter(
            Q(owner=user)
            | Q(owner__isnull=True)
            | Q(visibility=Movie.VISIBILITY_PUBLIC)
        )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MovieWriteSerializer
        return MovieListSerializer

    def perform_create(self, serializer):
        # Automatically make the logged-in user the owner.
        serializer.save(owner=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()

        user = self.request.user

        if user.is_authenticated:
            context['favorited_movie_ids'] = set(
                Favorite.objects.filter(
                    user=user
                ).values_list('movie_id', flat=True)
            )

            context['watchlisted_movie_ids'] = set(
                WatchlistEntry.objects.filter(
                    user=user
                ).values_list('movie_id', flat=True)
            )

            context['watched_movie_ids'] = set(
                WatchedEntry.objects.filter(
                    user=user
                ).values_list('movie_id', flat=True)
            )

        return context

    def create(self, request, *args, **kwargs):
        # Create the movie using MovieWriteSerializer.
        response = super().create(request, *args, **kwargs)

        # Return the richer movie representation.
        movie = Movie.objects.select_related(
            'director',
            'owner'
        ).prefetch_related(
            'genres',
            'cast_members',
        ).get(pk=response.data['id'])

        response.data = MovieDetailSerializer(
            movie,
            context=self.get_serializer_context()
        ).data

        return response


class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/movies/:id/
        View a movie.

    PATCH  /api/movies/:id/
        Update your own movie.

    DELETE /api/movies/:id/
        Delete your own movie.
    """

    permission_classes = [MoviePermission]

    def get_queryset(self):
        from django.db.models import Q

        qs = Movie.objects.select_related(
            'director',
            'owner'
        ).prefetch_related(
            'genres',
            Prefetch('cast_members')
        )

        user = self.request.user

        if not user.is_authenticated:
            return qs.filter(
                visibility=Movie.VISIBILITY_PUBLIC
            )

        return qs.filter(
            Q(owner=user)
            | Q(owner__isnull=True)
            | Q(visibility=Movie.VISIBILITY_PUBLIC)
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
                Favorite.objects.filter(
                    user=user
                ).values_list('movie_id', flat=True)
            )

            context['watchlisted_movie_ids'] = set(
                WatchlistEntry.objects.filter(
                    user=user
                ).values_list('movie_id', flat=True)
            )

            context['watched_movie_ids'] = set(
                WatchedEntry.objects.filter(
                    user=user
                ).values_list('movie_id', flat=True)
            )

        return context

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        movie = self.get_object()

        response.data = MovieDetailSerializer(
            movie,
            context=self.get_serializer_context()
        ).data

        return response


class GenreListView(generics.ListAPIView):
    """
    GET /api/movies/genres/

    Used to populate the genre filter dropdown.
    """

    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        from .models import Genre

        return Genre.objects.all()

    def get_serializer_class(self):
        from .serializers import GenreSerializer

        return GenreSerializer