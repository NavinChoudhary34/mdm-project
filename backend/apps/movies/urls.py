from django.urls import path

from .presign import (
    AbortMultipartVideoUploadView,
    CompleteMultipartVideoUploadView,
    InitiateMultipartVideoUploadView,
    PresignMultipartPartView,
    PresignVideoUploadView,
)
from .views import GenreListView, MovieDetailView, MovieListCreateView, MyMoviesView

app_name = 'movies'

urlpatterns = [
    path('', MovieListCreateView.as_view(), name='movie-list'),
    path('genres/', GenreListView.as_view(), name='genre-list'),
    path('my/', MyMoviesView.as_view(), name='my-movies'),
    path('presign-video-upload/', PresignVideoUploadView.as_view(), name='presign-video-upload'),
    path('multipart/initiate/', InitiateMultipartVideoUploadView.as_view(), name='multipart-initiate'),
    path('multipart/presign-part/', PresignMultipartPartView.as_view(), name='multipart-presign-part'),
    path('multipart/complete/', CompleteMultipartVideoUploadView.as_view(), name='multipart-complete'),
    path('multipart/abort/', AbortMultipartVideoUploadView.as_view(), name='multipart-abort'),
    path('<int:pk>/', MovieDetailView.as_view(), name='movie-detail'),
]
