from django.urls import path

from .views import GenreListView, MovieDetailView, MovieListCreateView, MyMoviesView

app_name = 'movies'

urlpatterns = [
    path('', MovieListCreateView.as_view(), name='movie-list'),
    path('genres/', GenreListView.as_view(), name='genre-list'),
    path('my/', MyMoviesView.as_view(), name='my-movies'),
    path('<int:pk>/', MovieDetailView.as_view(), name='movie-detail'),
]
