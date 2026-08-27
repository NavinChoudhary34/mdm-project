from django.contrib import admin

from .models import Favorite, Rating, WatchedEntry, WatchlistEntry


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'created_at']
    search_fields = ['user__username', 'movie__title']


@admin.register(WatchlistEntry)
class WatchlistEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'added_at']
    search_fields = ['user__username', 'movie__title']


@admin.register(WatchedEntry)
class WatchedEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'watched_at']
    search_fields = ['user__username', 'movie__title']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'score', 'updated_at']
    list_filter = ['score']
    search_fields = ['user__username', 'movie__title', 'review']
