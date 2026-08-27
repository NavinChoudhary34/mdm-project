import django_filters as filters

from .models import Movie


class MovieFilter(filters.FilterSet):
    genre = filters.CharFilter(field_name='genres__name', lookup_expr='iexact')
    director = filters.CharFilter(field_name='director__name', lookup_expr='icontains')
    actor = filters.CharFilter(field_name='cast__name', lookup_expr='icontains')
    year = filters.NumberFilter(field_name='release_date__year')
    min_rating = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = filters.NumberFilter(field_name='rating', lookup_expr='lte')
    # Per-user, so it can't be a plain field filter — resolved against whoever's
    # making the request. Silently has no effect for anonymous users (there's no
    # "watched" concept without an account), which is fine for the public catalog.
    watched = filters.BooleanFilter(method='filter_watched')

    class Meta:
        model = Movie
        fields = ['genre', 'director', 'actor', 'year', 'min_rating', 'max_rating', 'watched']

    def filter_watched(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return queryset
        from apps.library.models import WatchedEntry
        watched_ids = WatchedEntry.objects.filter(user=user).values_list('movie_id', flat=True)
        return queryset.filter(id__in=watched_ids) if value else queryset.exclude(id__in=watched_ids)
