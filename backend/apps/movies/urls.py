from django.urls import path

from .views import GenreListView, MovieDetailView, MovieListCreateView

app_name = 'movies'

urlpatterns = [
    path('', MovieListCreateView.as_view(), name='movie-list'),
    path('genres/', GenreListView.as_view(), name='genre-list'),
    path('<int:pk>/', MovieDetailView.as_view(), name='movie-detail'),
]
