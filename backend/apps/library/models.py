from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Favorite(models.Model):
    """A user/movie relationship — a user can favorite a given movie only once."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favorites', on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', related_name='favorited_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'movie']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f'{self.user} ♥ {self.movie}'


class WatchlistEntry(models.Model):
    """The global 'want to watch later' list, separate from any playlist."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='watchlist_entries', on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', related_name='on_watchlists', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'movie']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f'{self.movie} on {self.user}\'s watchlist'


class WatchedEntry(models.Model):
    """Tracks that a user has watched a movie, independent of any single playlist."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='watched_entries', on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', related_name='watched_by', on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'movie']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f'{self.user} watched {self.movie}'


class Rating(models.Model):
    """A user's personal 1-10 rating plus an optional written review of a movie.
    One row per (user, movie) — re-saving overwrites the previous rating/review."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='ratings', on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', related_name='ratings', on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    review = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'movie']
        indexes = [models.Index(fields=['user'])]

    def __str__(self):
        return f'{self.user} rated {self.movie}: {self.score}/10'
