from rest_framework import serializers

from apps.movies.serializers import MovieListSerializer

from .models import Favorite, Rating, WatchedEntry, WatchlistEntry


class FavoriteSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'movie', 'created_at']


class WatchlistEntrySerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)

    class Meta:
        model = WatchlistEntry
        fields = ['id', 'movie', 'added_at']


class WatchedEntrySerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)

    class Meta:
        model = WatchedEntry
        fields = ['id', 'movie', 'watched_at']


class MovieIdSerializer(serializers.Serializer):
    """Shared input shape for the favorite/watchlist/watched 'add' endpoints."""
    movie_id = serializers.IntegerField()

    def validate_movie_id(self, value):
        from apps.movies.models import Movie
        if not Movie.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Movie not found.')
        return value


class RatingSerializer(serializers.ModelSerializer):
    movie = MovieListSerializer(read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'movie', 'score', 'review', 'created_at', 'updated_at']


class RatingWriteSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=1, max_value=10)
    review = serializers.CharField(required=False, allow_blank=True, default='')
