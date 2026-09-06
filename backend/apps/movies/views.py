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

        Public/catalog movies are visible to everyone.
        Public user-uploaded movies are visible to everyone.
        Private user-uploaded movies are visible only to their owner.

    POST /api/movies/
        Authenticated users can upload/create their own movies.
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
        user = self.request.user

        qs = Movie.objects.select_related(
            'owner',
            'director',
        ).prefetch_related(
            'genres',
        )

        from django.db.models import Q

        # Anonymous users can only see:
        # 1. Catalog/TMDB movies (owner is NULL)
        # 2. Public user-uploaded movies
        #
        # .distinct() matters here just like in the authenticated branch
        # below: a movie could in principle match both conditions (e.g. a
        # catalog movie whose visibility is set to 'public'), and without it
        # such a movie would be returned twice by the OR'd filter.
        if not user.is_authenticated:
            return qs.filter(
                Q(owner__isnull=True)
                | Q(visibility=Movie.VISIBILITY_PUBLIC)
            ).distinct()

        # Authenticated users can see:
        # 1. Catalog/TMDB movies
        # 2. Their own movies, including private
        # 3. Other users' public movies
        return qs.filter(
            Q(owner__isnull=True)
            | Q(owner=user)
            | Q(visibility=Movie.VISIBILITY_PUBLIC)
        ).distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MovieWriteSerializer

        return MovieListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        user = self.request.user

        if user.is_authenticated:

            context['favorited_movie_ids'] = set(
                Favorite.objects.filter(
                    user=user
                ).values_list(
                    'movie_id',
                    flat=True
                )
            )

            context['watchlisted_movie_ids'] = set(
                WatchlistEntry.objects.filter(
                    user=user
                ).values_list(
                    'movie_id',
                    flat=True
                )
            )

            context['watched_movie_ids'] = set(
                WatchedEntry.objects.filter(
                    user=user
                ).values_list(
                    'movie_id',
                    flat=True
                )
            )

        return context

    def perform_create(self, serializer):
        """
        Automatically assign the logged-in user as the owner.

        The frontend does NOT get to choose the owner.
        """

        serializer.save(
            owner=self.request.user
        )

    def create(self, request, *args, **kwargs):
        """
        Return the richer movie representation after creation.
        """

        response = super().create(
            request,
            *args,
            **kwargs
        )

        movie = Movie.objects.select_related(
            'owner',
            'director',
        ).prefetch_related(
            'genres'
        ).get(
            pk=response.data['id']
        )

        response.data = MovieDetailSerializer(
            movie,
            context=self.get_serializer_context()
        ).data

        return response


class MyMoviesView(generics.ListAPIView):
    """
    GET /api/movies/my/

    Returns only movies uploaded by the currently authenticated user.
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = MovieListSerializer

    def get_queryset(self):
        return Movie.objects.filter(
            owner=self.request.user
        ).select_related(
            'owner',
            'director',
        ).prefetch_related(
            'genres'
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()

        user = self.request.user

        context['favorited_movie_ids'] = set(
            Favorite.objects.filter(
                user=user
            ).values_list(
                'movie_id',
                flat=True
            )
        )

        context['watchlisted_movie_ids'] = set(
            WatchlistEntry.objects.filter(
                user=user
            ).values_list(
                'movie_id',
                flat=True
            )
        )

        context['watched_movie_ids'] = set(
            WatchedEntry.objects.filter(
                user=user
            ).values_list(
                'movie_id',
                flat=True
            )
        )

        return context


class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/movies/<id>/

        Public/catalog movies can be viewed by everyone.
        Public uploaded movies can be viewed by everyone.
        Private uploaded movies can only be viewed by their owner.

    PATCH /api/movies/<id>/

        Only the owner can update their uploaded movie.

    DELETE /api/movies/<id>/

        Only the owner can delete their uploaded movie.
    """

    permission_classes = [
        MoviePermission
    ]

    def get_queryset(self):
        return Movie.objects.select_related(
            'owner',
            'director',
        ).prefetch_related(
            'genres',
            Prefetch('cast_members')
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
                ).values_list(
                    'movie_id',
                    flat=True
                )
            )

            context['watchlisted_movie_ids'] = set(
                WatchlistEntry.objects.filter(
                    user=user
                ).values_list(
                    'movie_id',
                    flat=True
                )
            )

            context['watched_movie_ids'] = set(
                WatchedEntry.objects.filter(
                    user=user
                ).values_list(
                    'movie_id',
                    flat=True
                )
            )

        return context

    def update(self, request, *args, **kwargs):
        response = super().update(
            request,
            *args,
            **kwargs
        )

        movie = self.get_object()

        response.data = MovieDetailSerializer(
            movie,
            context=self.get_serializer_context()
        ).data

        return response


class GenreListView(generics.ListAPIView):
    """
    GET /api/movies/genres/

    Returns all available genres.
    """

    permission_classes = [
        permissions.AllowAny
    ]

    pagination_class = None

    def get_queryset(self):
        from .models import Genre

        return Genre.objects.all()

    def get_serializer_class(self):
        from .serializers import GenreSerializer

        return GenreSerializer