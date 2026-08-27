from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.movies.models import Movie

from .models import Favorite, Rating, WatchedEntry, WatchlistEntry

User = get_user_model()


class LibraryTestBase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reader', email='reader@example.com', password='pass12345')
        self.movie = Movie.objects.create(title='Some Movie')
        self.client.force_authenticate(self.user)


class FavoriteTests(LibraryTestBase):
    def test_favorite_movie(self):
        resp = self.client.post('/api/favorites/', {'movie_id': self.movie.id})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Favorite.objects.count(), 1)

    def test_favorite_same_movie_twice_stays_single_row(self):
        self.client.post('/api/favorites/', {'movie_id': self.movie.id})
        resp = self.client.post('/api/favorites/', {'movie_id': self.movie.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Favorite.objects.count(), 1)

    def test_unfavorite(self):
        self.client.post('/api/favorites/', {'movie_id': self.movie.id})
        resp = self.client.delete(f'/api/favorites/{self.movie.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_favorites_require_auth(self):
        self.client.force_authenticate(None)
        resp = self.client.get('/api/favorites/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class WatchlistTests(LibraryTestBase):
    def test_add_and_remove_watchlist(self):
        add = self.client.post('/api/watchlist/', {'movie_id': self.movie.id})
        self.assertEqual(add.status_code, status.HTTP_201_CREATED)
        remove = self.client.delete(f'/api/watchlist/{self.movie.id}/')
        self.assertEqual(remove.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(WatchlistEntry.objects.count(), 0)


class WatchedTests(LibraryTestBase):
    def test_mark_watched_and_unwatched(self):
        mark = self.client.post('/api/watched/', {'movie_id': self.movie.id})
        self.assertEqual(mark.status_code, status.HTTP_201_CREATED)
        unmark = self.client.delete(f'/api/watched/{self.movie.id}/')
        self.assertEqual(unmark.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(WatchedEntry.objects.count(), 0)


class RatingTests(LibraryTestBase):
    def test_create_rating(self):
        resp = self.client.put(f'/api/ratings/{self.movie.id}/', {'score': 8, 'review': 'Great'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Rating.objects.get().score, 8)

    def test_rating_upsert_keeps_single_row(self):
        self.client.put(f'/api/ratings/{self.movie.id}/', {'score': 8}, format='json')
        self.client.put(f'/api/ratings/{self.movie.id}/', {'score': 5, 'review': 'Changed my mind'}, format='json')
        self.assertEqual(Rating.objects.count(), 1)
        rating = Rating.objects.get()
        self.assertEqual(rating.score, 5)
        self.assertEqual(rating.review, 'Changed my mind')

    def test_rating_out_of_range_rejected(self):
        resp = self.client.put(f'/api/ratings/{self.movie.id}/', {'score': 11}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_rating(self):
        self.client.put(f'/api/ratings/{self.movie.id}/', {'score': 8}, format='json')
        resp = self.client.delete(f'/api/ratings/{self.movie.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Rating.objects.count(), 0)


class DashboardTests(LibraryTestBase):
    def test_dashboard_reflects_activity(self):
        self.client.post('/api/watched/', {'movie_id': self.movie.id})
        resp = self.client.get('/api/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['stats']['movies_watched'], 1)
