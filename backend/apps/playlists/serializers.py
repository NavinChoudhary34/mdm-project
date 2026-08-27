from rest_framework import serializers

from apps.movies.serializers import MovieListSerializer

from .models import Playlist, PlaylistMovie


class PlaylistListSerializer(serializers.ModelSerializer):
    """Lightweight representation for the playlists index page — counts, not full movie list."""
    movie_count = serializers.IntegerField(source='playlist_movies.count', read_only=True)
    owner_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id', 'name', 'description', 'is_public', 'movie_count',
            'owner_username', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlaylistMovieSerializer(serializers.ModelSerializer):
    """A single movie entry inside a playlist, with the playlist-specific metadata."""
    movie = MovieListSerializer(read_only=True)

    class Meta:
        model = PlaylistMovie
        fields = ['id', 'movie', 'position', 'watched', 'notes', 'added_at']
        read_only_fields = ['id', 'added_at']


class PlaylistDetailSerializer(PlaylistListSerializer):
    """Full representation including the ordered list of movies in the playlist."""
    movies = serializers.SerializerMethodField()

    class Meta(PlaylistListSerializer.Meta):
        fields = PlaylistListSerializer.Meta.fields + ['movies']

    def get_movies(self, obj):
        entries = obj.playlist_movies.select_related('movie').prefetch_related('movie__genres').order_by(
            'position', 'added_at'
        )
        return PlaylistMovieSerializer(entries, many=True, context=self.context).data


class PlaylistWriteSerializer(serializers.ModelSerializer):
    """Used for create/update — name/description/is_public only, owner is set server-side."""

    class Meta:
        model = Playlist
        fields = ['id', 'name', 'description', 'is_public']
        read_only_fields = ['id']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Playlist name is required.')
        return value


class AddMovieToPlaylistSerializer(serializers.Serializer):
    movie_id = serializers.IntegerField()

    def validate_movie_id(self, value):
        from apps.movies.models import Movie
        if not Movie.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Movie not found.')
        return value


class PlaylistMovieUpdateSerializer(serializers.ModelSerializer):
    """PATCH body for updating a single playlist entry (watched flag / notes)."""

    class Meta:
        model = PlaylistMovie
        fields = ['watched', 'notes']


class ReorderSerializer(serializers.Serializer):
    # Ordered list of movie ids representing the new playlist order, front to back.
    movie_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
