from django.conf import settings
from django.db import models

class RecentlyViewed(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recently_viewed_movies')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='recently_viewed_by')
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at', '-id']
        constraints = [models.UniqueConstraint(fields=['user','movie'], name='unique_recently_viewed_user_movie')]
        indexes = [models.Index(fields=['user','-viewed_at'])]

class PlaylistUndoAction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlist_undo_actions')
    playlist = models.ForeignKey('playlists.Playlist', on_delete=models.CASCADE, related_name='undo_actions')
    action_type = models.CharField(max_length=32)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['user','-created_at'])]
