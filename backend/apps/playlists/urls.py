from django.urls import path

from .views import (
    PlaylistDetailView,
    PlaylistListCreateView,
    PlaylistMovieDetailView,
    PlaylistMoviesView,
    PlaylistReorderView,
    PublicPlaylistDetailView,
)

app_name = 'playlists'

urlpatterns = [
    path('', PlaylistListCreateView.as_view(), name='playlist-list'),
    path('<int:pk>/', PlaylistDetailView.as_view(), name='playlist-detail'),
    path('<int:pk>/movies/', PlaylistMoviesView.as_view(), name='playlist-movies'),
    path('<int:pk>/movies/<int:movie_id>/', PlaylistMovieDetailView.as_view(), name='playlist-movie-detail'),
    path('<int:pk>/reorder/', PlaylistReorderView.as_view(), name='playlist-reorder'),
]

# Public, read-only, unauthenticated playlist viewing lives at a separate top-level
# path (see config/urls.py: /api/public/playlists/:id/) so it's never accidentally
# reachable through the authenticated /api/playlists/ namespace.
public_urlpatterns = [
    path('<int:pk>/', PublicPlaylistDetailView.as_view(), name='public-playlist-detail'),
]
