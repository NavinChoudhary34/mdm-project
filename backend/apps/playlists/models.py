from django.conf import settings
from django.db import models


class Playlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='playlists', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    is_public = models.BooleanField(default=False)

    movies = models.ManyToManyField(
        'movies.Movie', through='PlaylistMovie', related_name='playlists', blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return f'{self.name} ({self.user})'


class PlaylistMovie(models.Model):
    """Through-model: lets a movie sit in a playlist with its own order/status/notes."""
    playlist = models.ForeignKey(Playlist, related_name='playlist_movies', on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', related_name='playlist_entries', on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)
    watched = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'added_at']
        # A movie can only appear once inside the same playlist.
        unique_together = ['playlist', 'movie']
        indexes = [
            models.Index(fields=['playlist', 'position']),
        ]

    def __str__(self):
        return f'{self.movie} in {self.playlist}'
