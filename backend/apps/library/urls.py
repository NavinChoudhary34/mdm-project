from django.urls import path

from .views import (
    DashboardView,
    FavoriteDeleteView,
    FavoriteListCreateView,
    RatingDetailView,
    RatingListView,
    WatchedDeleteView,
    WatchedListCreateView,
    WatchlistDeleteView,
    WatchlistListCreateView,
)

app_name = 'library'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('favorites/', FavoriteListCreateView.as_view(), name='favorite-list'),
    path('favorites/<int:movie_id>/', FavoriteDeleteView.as_view(), name='favorite-delete'),

    path('watchlist/', WatchlistListCreateView.as_view(), name='watchlist-list'),
    path('watchlist/<int:movie_id>/', WatchlistDeleteView.as_view(), name='watchlist-delete'),

    path('watched/', WatchedListCreateView.as_view(), name='watched-list'),
    path('watched/<int:movie_id>/', WatchedDeleteView.as_view(), name='watched-delete'),

    path('ratings/', RatingListView.as_view(), name='rating-list'),
    path('ratings/<int:movie_id>/', RatingDetailView.as_view(), name='rating-detail'),
]
