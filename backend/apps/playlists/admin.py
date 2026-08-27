from django.contrib import admin

from .models import Playlist, PlaylistMovie


class PlaylistMovieInline(admin.TabularInline):
    model = PlaylistMovie
    extra = 0


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_public', 'updated_at']
    list_filter = ['is_public']
    search_fields = ['name', 'user__username']
    inlines = [PlaylistMovieInline]


@admin.register(PlaylistMovie)
class PlaylistMovieAdmin(admin.ModelAdmin):
    list_display = ['playlist', 'movie', 'position', 'watched']
    list_filter = ['watched']
