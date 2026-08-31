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
    """Cast entry as seen from a movie: the person's name flattened in, plus the role."""
    id = serializers.IntegerField(source='person.id', read_only=True)
    name = serializers.CharField(source='person.name', read_only=True)
    photo_url = serializers.URLField(source='person.photo_url', read_only=True)

    class Meta:
        model = MovieCastMember
        fields = ['id', 'name', 'photo_url', 'character_name', 'billing_order']


class MovieListSerializer(serializers.ModelSerializer):
    """Lightweight representation used for grid/list views — no full cast list."""
    genres = GenreSerializer(many=True, read_only=True)
    director = PersonSerializer(read_only=True)
    release_year = serializers.IntegerField(read_only=True)

    video_url = serializers.SerializerMethodField()
    # Per-request-user convenience flags, populated via SerializerMethodField so the
    # frontend can render favorite/watchlist/watched state without extra API calls.
    is_favorited = serializers.SerializerMethodField()
    is_in_watchlist = serializers.SerializerMethodField()
    is_watched = serializers.SerializerMethodField()

    owner = serializers.IntegerField(
    source='owner_id',
    read_only=True,
    allow_null=True,
    )

    video_file = serializers.FileField(
    read_only=True
    )

    visibility = serializers.CharField(
    read_only=True
    )
    class Meta:
        model = Movie
        fields = [
    'id',
    'owner',
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
    'video_file',
    'visibility',
    'is_favorited',
    'is_in_watchlist',
    'is_watched',
]

    def _user(self):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return user if user and user.is_authenticated else None

    def get_is_favorited(self, obj):
        user = self._user()
        # Prefetched sets (see MovieViewSet.get_queryset) avoid N+1 queries here.
        if user is None:
            return False
        ids = self.context.get('favorited_movie_ids')
        return obj.id in ids if ids is not None else obj.favorited_by.filter(user=user).exists()

    def get_is_in_watchlist(self, obj):
        user = self._user()
        if user is None:
            return False
        ids = self.context.get('watchlisted_movie_ids')
        return obj.id in ids if ids is not None else obj.on_watchlists.filter(user=user).exists()

    def get_is_watched(self, obj):
        user = self._user()
        if user is None:
            return False
        ids = self.context.get('watched_movie_ids')
        return obj.id in ids if ids is not None else obj.watched_by.filter(user=user).exists()

    def get_video_url(self, obj):
        request = self.context.get('request')

        if not obj.video_file:
            return None

        url = obj.video_file.url

        if request:
            return request.build_absolute_uri(url)

        return url

class MovieDetailSerializer(MovieListSerializer):
    """Full representation for the movie detail page — includes description, cast, and the
    requesting user's own rating/review if one exists."""
    cast_members = CastMemberSerializer(many=True, read_only=True)
    my_rating = serializers.SerializerMethodField()

    class Meta(MovieListSerializer.Meta):
        fields = MovieListSerializer.Meta.fields + [
            'description', 'cast_members', 'created_at', 'updated_at', 'my_rating',
        ]

    def get_my_rating(self, obj):
        user = self._user()
        if user is None:
            return None
        rating = obj.ratings.filter(user=user).first()
        if rating is None:
            return None
        return {'score': rating.score, 'review': rating.review}


class MovieWriteSerializer(serializers.ModelSerializer):
    """
    Used by authenticated users to create/update their own movies.
    The owner is assigned automatically by the view.
    """

    genre_ids = serializers.PrimaryKeyRelatedField(
        source='genres',
        queryset=Genre.objects.all(),
        many=True,
        required=False,
    )

    director_id = serializers.PrimaryKeyRelatedField(
        source='director',
        queryset=Person.objects.all(),
        required=False,
        allow_null=True,
    )

    owner = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    video_file = serializers.FileField(
        required=False,
        allow_null=True,
    )

    visibility = serializers.ChoiceField(
        choices=Movie.VISIBILITY_CHOICES,
        required=False,
        default=Movie.VISIBILITY_PRIVATE,
    )

    class Meta:
        model = Movie
        fields = [
            'id',
            'owner',
            'title',
            'description',
            'release_date',
            'poster_url',
            'backdrop_url',
            'runtime_minutes',
            'rating',
            'genre_ids',
            'director_id',
            'video_file',
            'visibility',
        ]
        read_only_fields = ['id', 'owner']