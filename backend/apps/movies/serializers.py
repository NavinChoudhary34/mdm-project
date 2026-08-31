from rest_framework import serializers

from .models import Genre, Movie, MovieCastMember, Person


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['id', 'name', 'photo_url']


class CastMemberSerializer(serializers.ModelSerializer):
    """
    Cast entry as seen from a movie.
    """

    id = serializers.IntegerField(
        source='person.id',
        read_only=True
    )

    name = serializers.CharField(
        source='person.name',
        read_only=True
    )

    photo_url = serializers.URLField(
        source='person.photo_url',
        read_only=True
    )

    class Meta:
        model = MovieCastMember
        fields = [
            'id',
            'name',
            'photo_url',
            'character_name',
            'billing_order',
        ]


class MovieListSerializer(serializers.ModelSerializer):
    """
    Lightweight representation used by movie list/grid pages.
    """

    genres = GenreSerializer(
        many=True,
        read_only=True
    )

    director = PersonSerializer(
        read_only=True
    )

    release_year = serializers.IntegerField(
        read_only=True
    )

    # Information about the user who uploaded the movie.
    owner_id = serializers.IntegerField(
        source='owner.id',
        read_only=True
    )

    owner_username = serializers.CharField(
        source='owner.username',
        read_only=True,
        allow_null=True
    )

    # Actual uploaded video file.
    video_file = serializers.FileField(
        read_only=True
    )

    # private / public
    visibility = serializers.CharField(
        read_only=True
    )

    # User-specific library information.
    is_favorited = serializers.SerializerMethodField()
    is_in_watchlist = serializers.SerializerMethodField()
    is_watched = serializers.SerializerMethodField()

    class Meta:
        model = Movie

        fields = [
            'id',
            'title',
            'description',
            'poster_url',
            'backdrop_url',
            'release_date',
            'release_year',
            'runtime_minutes',
            'rating',
            'genres',
            'director',

            # Uploaded movie information
            'owner_id',
            'owner_username',
            'video_file',
            'visibility',

            # User library information
            'is_favorited',
            'is_in_watchlist',
            'is_watched',
        ]

    def _user(self):
        request = self.context.get('request')

        user = getattr(
            request,
            'user',
            None
        )

        return (
            user
            if user and user.is_authenticated
            else None
        )

    def get_is_favorited(self, obj):
        user = self._user()

        if user is None:
            return False

        ids = self.context.get(
            'favorited_movie_ids'
        )

        if ids is not None:
            return obj.id in ids

        return obj.favorited_by.filter(
            user=user
        ).exists()

    def get_is_in_watchlist(self, obj):
        user = self._user()

        if user is None:
            return False

        ids = self.context.get(
            'watchlisted_movie_ids'
        )

        if ids is not None:
            return obj.id in ids

        return obj.on_watchlists.filter(
            user=user
        ).exists()

    def get_is_watched(self, obj):
        user = self._user()

        if user is None:
            return False

        ids = self.context.get(
            'watched_movie_ids'
        )

        if ids is not None:
            return obj.id in ids

        return obj.watched_by.filter(
            user=user
        ).exists()


class MovieDetailSerializer(MovieListSerializer):
    """
    Full representation used by the movie detail page.
    """

    cast_members = CastMemberSerializer(
        many=True,
        read_only=True
    )

    my_rating = serializers.SerializerMethodField()

    class Meta(MovieListSerializer.Meta):
        fields = MovieListSerializer.Meta.fields + [
            'cast_members',
            'created_at',
            'updated_at',
            'my_rating',
        ]

    def get_my_rating(self, obj):
        user = self._user()

        if user is None:
            return None

        rating = obj.ratings.filter(
            user=user
        ).first()

        if rating is None:
            return None

        return {
            'score': rating.score,
            'review': rating.review,
        }


class MovieWriteSerializer(serializers.ModelSerializer):
    """
    Serializer used by authenticated users to create and update
    their own uploaded movies.

    The owner is NOT supplied by the frontend.
    The view will automatically assign request.user as the owner.
    """

    genre_ids = serializers.PrimaryKeyRelatedField(
        source='genres',
        queryset=Genre.objects.all(),
        many=True,
        required=False
    )

    director_id = serializers.PrimaryKeyRelatedField(
        source='director',
        queryset=Person.objects.all(),
        required=False,
        allow_null=True
    )

    video_file = serializers.FileField(
        required=False,
        allow_null=True
    )

    visibility = serializers.ChoiceField(
        choices=Movie.VISIBILITY_CHOICES,
        required=False,
        default=Movie.VISIBILITY_PRIVATE
    )

    class Meta:
        model = Movie

        fields = [
            'id',
            'title',
            'description',
            'release_date',
            'poster_url',
            'backdrop_url',
            'runtime_minutes',
            'rating',

            # Uploaded video
            'video_file',

            # Private/public
            'visibility',

            # Relationships
            'genre_ids',
            'director_id',
        ]

        read_only_fields = [
            'id',
        ]