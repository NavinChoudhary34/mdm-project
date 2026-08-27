from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.movies.models import Movie
from apps.movies.serializers import MovieListSerializer
from apps.playlists.models import Playlist

from .models import Favorite, Rating, WatchedEntry, WatchlistEntry
from .serializers import (
    FavoriteSerializer,
    MovieIdSerializer,
    RatingSerializer,
    RatingWriteSerializer,
    WatchedEntrySerializer,
    WatchlistEntrySerializer,
)


class _ToggleRelationMixin:
    """
    Shared logic for the favorite / watchlist / watched endpoints, which are all
    "a user either has this movie in the list or doesn't" relationships:
      GET    /api/<thing>/          — list the current user's entries (paginated)
      POST   /api/<thing>/          — add a movie (body: {"movie_id": <id>})
      DELETE /api/<thing>/<movie_id>/ — remove a movie
    """
    model = None
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user).select_related('movie')


class FavoriteListCreateView(_ToggleRelationMixin, generics.ListCreateAPIView):
    model = Favorite
    serializer_class = FavoriteSerializer

    def post(self, request, *args, **kwargs):
        serializer = MovieIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movie = get_object_or_404(Movie, pk=serializer.validated_data['movie_id'])
        favorite, created = Favorite.objects.get_or_create(user=request.user, movie=movie)
        return Response(
            FavoriteSerializer(favorite).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class FavoriteDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, movie_id):
        deleted, _ = Favorite.objects.filter(user=request.user, movie_id=movie_id).delete()
        if not deleted:
            return Response({'detail': 'Not favorited.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WatchlistListCreateView(_ToggleRelationMixin, generics.ListCreateAPIView):
    model = WatchlistEntry
    serializer_class = WatchlistEntrySerializer

    def post(self, request, *args, **kwargs):
        serializer = MovieIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movie = get_object_or_404(Movie, pk=serializer.validated_data['movie_id'])
        entry, created = WatchlistEntry.objects.get_or_create(user=request.user, movie=movie)
        return Response(
            WatchlistEntrySerializer(entry).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WatchlistDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, movie_id):
        deleted, _ = WatchlistEntry.objects.filter(user=request.user, movie_id=movie_id).delete()
        if not deleted:
            return Response({'detail': 'Not on watchlist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WatchedListCreateView(_ToggleRelationMixin, generics.ListCreateAPIView):
    model = WatchedEntry
    serializer_class = WatchedEntrySerializer

    def post(self, request, *args, **kwargs):
        serializer = MovieIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movie = get_object_or_404(Movie, pk=serializer.validated_data['movie_id'])
        entry, created = WatchedEntry.objects.get_or_create(user=request.user, movie=movie)
        return Response(
            WatchedEntrySerializer(entry).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WatchedDeleteView(APIView):
    """DELETE /api/watched/<movie_id>/ — mark a movie unwatched."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, movie_id):
        deleted, _ = WatchedEntry.objects.filter(user=request.user, movie_id=movie_id).delete()
        if not deleted:
            return Response({'detail': 'Not marked watched.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RatingListView(generics.ListAPIView):
    """GET /api/ratings/ — the current user's own ratings/reviews."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RatingSerializer

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user).select_related('movie')


class RatingDetailView(APIView):
    """
    PUT    /api/ratings/<movie_id>/ — create or overwrite the current user's rating/review.
    DELETE /api/ratings/<movie_id>/ — remove it.
    A user gets exactly one rating per movie — PUT upserts rather than duplicating.
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, movie_id):
        movie = get_object_or_404(Movie, pk=movie_id)
        serializer = RatingWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating, _created = Rating.objects.update_or_create(
            user=request.user, movie=movie, defaults=serializer.validated_data
        )
        return Response(RatingSerializer(rating).data)

    def delete(self, request, movie_id):
        deleted, _ = Rating.objects.filter(user=request.user, movie_id=movie_id).delete()
        if not deleted:
            return Response({'detail': 'No rating found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardView(APIView):
    """GET /api/dashboard/ — the stats + recent-activity data the dashboard page needs."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        playlists_qs = Playlist.objects.filter(user=user)
        watched_count = WatchedEntry.objects.filter(user=user).count()
        favorites_qs = Favorite.objects.filter(user=user).select_related('movie')
        watchlist_qs = WatchlistEntry.objects.filter(user=user).select_related('movie')

        # "Total movies" = distinct movies the user has touched in any way (playlists,
        # watched, watchlist, or favorites) — matches the dashboard's intent of a
        # personal library size, not the whole catalog.
        movie_ids = set()
        movie_ids.update(
            Movie.objects.filter(playlist_entries__playlist__user=user).values_list('id', flat=True)
        )
        movie_ids.update(watchlist_qs.values_list('movie_id', flat=True))
        movie_ids.update(favorites_qs.values_list('movie_id', flat=True))
        movie_ids.update(WatchedEntry.objects.filter(user=user).values_list('movie_id', flat=True))
        total_movies = len(movie_ids)

        recent_favorites = favorites_qs.order_by('-created_at')[:5]
        recent_watched = WatchedEntry.objects.filter(user=user).select_related('movie').order_by('-watched_at')[:5]
        recently_updated_playlists = playlists_qs.order_by('-updated_at')[:5]

        return Response({
            'stats': {
                'total_playlists': playlists_qs.count(),
                'total_movies': total_movies,
                'movies_watched': watched_count,
                'movies_unwatched': max(total_movies - watched_count, 0),
                'favorite_count': favorites_qs.count(),
                'watchlist_count': watchlist_qs.count(),
            },
            'recent_favorites': MovieListSerializer(
                [f.movie for f in recent_favorites], many=True, context={'request': request}
            ).data,
            'recently_watched': MovieListSerializer(
                [w.movie for w in recent_watched], many=True, context={'request': request}
            ).data,
            'recently_updated_playlists': [
                {'id': p.id, 'name': p.name, 'updated_at': p.updated_at} for p in recently_updated_playlists
            ],
        })
