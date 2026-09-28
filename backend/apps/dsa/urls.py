from django.urls import path
from .views import MovieAutocompleteView, TopRatedMoviesView, RecentlyViewedView, UndoPlaylistActionView
urlpatterns=[
    path('autocomplete/',MovieAutocompleteView.as_view()),
    path('top-rated/',TopRatedMoviesView.as_view()),
    path('recently-viewed/',RecentlyViewedView.as_view()),
    path('undo/',UndoPlaylistActionView.as_view()),
]
