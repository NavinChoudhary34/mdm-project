from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.movies.models import Movie

from .models import Playlist, PlaylistMovie

User = get_user_model()


class PlaylistTestBase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', email='owner@example.com', password='pass12345')
        self.other_user = User.objects.create_user(username='intruder', email='intruder@example.com', password='pass12345')
        self.movie = Movie.objects.create(title='Some Movie')
        self.movie2 = Movie.objects.create(title='Another Movie')
        self.client.force_authenticate(self.user)


class PlaylistCrudTests(PlaylistTestBase):
    def test_create_playlist(self):
        resp = self.client.post('/api/playlists/', {'name': 'My List', 'description': 'x', 'is_public': False})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Playlist.objects.get().user, self.user)

    def test_create_playlist_requires_name(self):
        resp = self.client.post('/api/playlists/', {'name': '  ', 'is_public': False})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_playlist(self):
        playlist = Playlist.objects.create(user=self.user, name='Old Name')
        resp = self.client.patch(f'/api/playlists/{playlist.id}/', {'name': 'New Name'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        playlist.refresh_from_db()
        self.assertEqual(playlist.name, 'New Name')

    def test_delete_playlist(self):
        playlist = Playlist.objects.create(user=self.user, name='Delete Me')
        resp = self.client.delete(f'/api/playlists/{playlist.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Playlist.objects.filter(id=playlist.id).exists())

    def test_unauthorized_access_returns_404_not_403(self):
        playlist = Playlist.objects.create(user=self.other_user, name='Private')
        resp = self.client.get(f'/api/playlists/{playlist.id}/')
        # 404 rather than 403 so existence of another user's private playlist is never revealed.
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_update_blocked(self):
        playlist = Playlist.objects.create(user=self.other_user, name='Private')
        resp = self.client.patch(f'/api/playlists/{playlist.id}/', {'name': 'Hacked'})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        playlist.refresh_from_db()
        self.assertEqual(playlist.name, 'Private')

    def test_unauthorized_delete_blocked(self):
        playlist = Playlist.objects.create(user=self.other_user, name='Private')
        resp = self.client.delete(f'/api/playlists/{playlist.id}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Playlist.objects.filter(id=playlist.id).exists())

    def test_public_playlist_readable_without_auth(self):
        self.client.force_authenticate(None)
        playlist = Playlist.objects.create(user=self.other_user, name='Public List', is_public=True)
        resp = self.client.get(f'/api/public/playlists/{playlist.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_private_playlist_not_reachable_via_public_endpoint(self):
        self.client.force_authenticate(None)
        playlist = Playlist.objects.create(user=self.other_user, name='Still Private', is_public=False)
        resp = self.client.get(f'/api/public/playlists/{playlist.id}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class PlaylistMovieTests(PlaylistTestBase):
    def setUp(self):
        super().setUp()
        self.playlist = Playlist.objects.create(user=self.user, name='My List')

    def test_add_movie(self):
        resp = self.client.post(f'/api/playlists/{self.playlist.id}/movies/', {'movie_id': self.movie.id})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlaylistMovie.objects.filter(playlist=self.playlist).count(), 1)

    def test_add_duplicate_movie_rejected(self):
        self.client.post(f'/api/playlists/{self.playlist.id}/movies/', {'movie_id': self.movie.id})
        resp = self.client.post(f'/api/playlists/{self.playlist.id}/movies/', {'movie_id': self.movie.id})
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(PlaylistMovie.objects.filter(playlist=self.playlist).count(), 1)

    def test_remove_movie(self):
        self.client.post(f'/api/playlists/{self.playlist.id}/movies/', {'movie_id': self.movie.id})
        resp = self.client.delete(f'/api/playlists/{self.playlist.id}/movies/{self.movie.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PlaylistMovie.objects.filter(playlist=self.playlist).count(), 0)

    def test_other_user_cannot_add_to_playlist(self):
        self.client.force_authenticate(self.other_user)
        resp = self.client.post(f'/api/playlists/{self.playlist.id}/movies/', {'movie_id': self.movie.id})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_reorder(self):
        self.client.post(f'/api/playlists/{self.playlist.id}/movies/', {'movie_id': self.movie.id})
        self.client.post(f'/api/playlists/{self.playlist.id}/movies/', {'movie_id': self.movie2.id})
        resp = self.client.patch(
            f'/api/playlists/{self.playlist.id}/reorder/',
            {'movie_ids': [self.movie2.id, self.movie.id]},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [m['movie']['title'] for m in resp.data['movies']]
        self.assertEqual(titles, ['Another Movie', 'Some Movie'])
