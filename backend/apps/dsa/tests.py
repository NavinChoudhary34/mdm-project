"""Regression tests for bugs found in the code audit (and the first tests for the dsa app)."""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase

from apps.movies.models import Movie
from apps.playlists.models import PlaylistMovie

User = get_user_model()


class DsaAndVisibilityRegressionTests(APITestCase):
    def setUp(self):
        cache.clear()  # the auth throttle (10/min) is stored in the cache; reset it per test
        self.alice = User.objects.create_user('alice', 'a@x.com', 'pw-12345-xyz')
        self.bob = User.objects.create_user('bob', 'b@x.com', 'pw-12345-xyz')
        self.secret = Movie.objects.create(
            title='Alice Secret', owner=self.alice, visibility='private',
            video_file='movies/videos/1/secret.mp4')

    # --- autocomplete used to crash with FieldError (.only() + select_related()) ---
    def test_autocomplete_returns_prefix_matches(self):
        Movie.objects.create(title='Inception')
        Movie.objects.create(title='Interstellar')
        r = self.client.get('/api/dsa/autocomplete/?q=in')
        self.assertEqual(r.status_code, 200)
        self.assertEqual({m['title'] for m in r.data}, {'Inception', 'Interstellar'})
        r = self.client.get('/api/dsa/autocomplete/?q=inc')
        self.assertEqual([m['title'] for m in r.data], ['Inception'])

    def test_autocomplete_hides_other_users_private_titles(self):
        self.client.force_authenticate(self.bob)
        r = self.client.get('/api/dsa/autocomplete/?q=al')
        self.assertEqual(r.data, [])

    # --- private movies were readable by anyone through the detail endpoint ---
    def test_private_movie_detail_is_404_for_others_and_anonymous(self):
        self.assertEqual(self.client.get(f'/api/movies/{self.secret.id}/').status_code, 404)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(f'/api/movies/{self.secret.id}/').status_code, 404)

    def test_owner_can_still_open_private_movie(self):
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.get(f'/api/movies/{self.secret.id}/').status_code, 200)

    def test_cannot_favorite_playlist_or_rate_someone_elses_private_movie(self):
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.post('/api/favorites/', {'movie_id': self.secret.id}, format='json').status_code, 404)
        self.assertEqual(self.client.post('/api/watchlist/', {'movie_id': self.secret.id}, format='json').status_code, 404)
        self.assertEqual(self.client.put(f'/api/ratings/{self.secret.id}/', {'score': 5}, format='json').status_code, 404)
        pl = self.client.post('/api/playlists/', {'name': 'p'}, format='json').data['id']
        self.assertEqual(self.client.post(f'/api/playlists/{pl}/movies/', {'movie_id': self.secret.id}, format='json').status_code, 404)

    # --- video_file_key accepted any storage key ---
    def test_video_file_key_must_be_the_users_own_upload_key(self):
        self.client.force_authenticate(self.bob)
        bad_keys = ['movies/videos/1/secret.mp4', '../../anything.txt', 'movies/videos/%d/../1/x' % self.bob.id]
        for key in bad_keys:
            r = self.client.post('/api/movies/', {'title': 't', 'video_file_key': key}, format='json')
            self.assertEqual(r.status_code, 400, key)
        good = f'movies/videos/{self.bob.id}/' + 'a' * 32 + '.mp4'
        r = self.client.post('/api/movies/', {'title': 't', 'video_file_key': good}, format='json')
        self.assertEqual(r.status_code, 201)

    # --- rating had no 0-10 bounds, so 99.9 topped the Top Rated list ---
    def test_rating_is_bounded(self):
        self.client.force_authenticate(self.bob)
        r = self.client.post('/api/movies/', {'title': 'Fake', 'rating': '99.9'}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.client.post('/api/movies/', {'title': 'Ok', 'rating': '8.5'}, format='json')
        self.assertEqual(r.status_code, 201)

    # --- recently viewed order was scrambled (auto_now ignored the timestamps) ---
    def test_recently_viewed_is_most_recent_first(self):
        movies = [Movie.objects.create(title=t) for t in 'ABCD']
        self.client.force_authenticate(self.bob)
        for m in movies:
            self.client.get(f'/api/movies/{m.id}/')
        self.client.get(f'/api/movies/{movies[0].id}/')  # re-view A: should jump to the front
        r = self.client.get('/api/dsa/recently-viewed/')
        self.assertEqual([m['title'] for m in r.data], ['A', 'D', 'C', 'B'])

    def test_recently_viewed_keeps_only_ten(self):
        self.client.force_authenticate(self.bob)
        for i in range(12):
            m = Movie.objects.create(title=f'M{i}')
            self.client.get(f'/api/movies/{m.id}/')
        r = self.client.get('/api/dsa/recently-viewed/')
        self.assertEqual(len(r.data), 10)
        self.assertEqual(r.data[0]['title'], 'M11')

    # --- new playlist entries landed mid-list after removals ---
    def test_added_movie_goes_to_the_end_after_removals(self):
        movies = [Movie.objects.create(title=f'M{i}') for i in range(4)]
        self.client.force_authenticate(self.bob)
        pl = self.client.post('/api/playlists/', {'name': 'p'}, format='json').data['id']
        for m in movies:
            self.client.post(f'/api/playlists/{pl}/movies/', {'movie_id': m.id}, format='json')
        self.client.delete(f'/api/playlists/{pl}/movies/{movies[0].id}/')
        self.client.delete(f'/api/playlists/{pl}/movies/{movies[1].id}/')
        new = Movie.objects.create(title='NEW')
        self.client.post(f'/api/playlists/{pl}/movies/', {'movie_id': new.id}, format='json')
        order = [e.movie.title for e in PlaylistMovie.objects.filter(playlist_id=pl)]
        self.assertEqual(order, ['M2', 'M3', 'NEW'])

    # --- undo ignored which playlist the user was looking at ---
    def test_undo_can_be_scoped_to_one_playlist(self):
        ms = [Movie.objects.create(title=f'M{i}') for i in range(2)]
        self.client.force_authenticate(self.bob)
        p1 = self.client.post('/api/playlists/', {'name': 'one'}, format='json').data['id']
        p2 = self.client.post('/api/playlists/', {'name': 'two'}, format='json').data['id']
        self.client.post(f'/api/playlists/{p1}/movies/', {'movie_id': ms[0].id}, format='json')
        self.client.post(f'/api/playlists/{p2}/movies/', {'movie_id': ms[1].id}, format='json')
        r = self.client.post('/api/dsa/undo/', {'playlist_id': p1}, format='json')
        self.assertEqual(r.data['playlist_id'], p1)
        self.assertTrue(PlaylistMovie.objects.filter(playlist_id=p2).exists())  # untouched
        self.assertFalse(PlaylistMovie.objects.filter(playlist_id=p1).exists())

    # --- username containing '@' could collide with an e-mail and block e-mail login ---
    def test_username_with_at_sign_rejected(self):
        r = self.client.post('/api/auth/register/', {'username': 'x@y.com', 'email': 'n@y.com',
                             'password': 'Str0ng-pass-123', 'password_confirm': 'Str0ng-pass-123'}, format='json')
        self.assertEqual(r.status_code, 400)

    # --- old refresh tokens survived a password reset ---
    def test_password_reset_revokes_refresh_tokens(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        t = self.client.post('/api/auth/login/', {'username': 'bob', 'password': 'pw-12345-xyz'}, format='json').data
        uid = urlsafe_base64_encode(force_bytes(self.bob.pk))
        token = default_token_generator.make_token(self.bob)
        r = self.client.post('/api/auth/password-reset/confirm/',
                             {'uid': uid, 'token': token, 'new_password': 'Brand-new-pass-77'}, format='json')
        self.assertEqual(r.status_code, 204)
        r = self.client.post('/api/auth/refresh/', {'refresh': t['refresh']}, format='json')
        self.assertEqual(r.status_code, 401)


class SecondRoundRegressionTests(APITestCase):
    """Bugs found in the second (frontend-focused) pass."""

    def setUp(self):
        cache.clear()
        self.bob = User.objects.create_user('bob', 'b@x.com', 'pw-12345-xyz')

    # Settings page could rename a user to something that looks like another user's e-mail
    def test_profile_update_rejects_new_username_with_at_sign(self):
        self.client.force_authenticate(self.bob)
        r = self.client.patch('/api/auth/me/', {'username': 'someone@else.com'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_profile_update_keeps_existing_at_sign_username_working(self):
        legacy = User.objects.create_user('old@name.com', 'legacy@x.com', 'pw-12345-xyz')
        self.client.force_authenticate(legacy)
        r = self.client.patch('/api/auth/me/', {'username': 'old@name.com', 'bio': 'hi'}, format='json')
        self.assertEqual(r.status_code, 200)

    # Unrated movies must never lead "Highest rated" (PostgreSQL sorts NULL first on DESC)
    def test_ordering_puts_unrated_movies_last_and_is_stable(self):
        Movie.objects.create(title='No rating A')
        for i, rating in enumerate(['6.0', '9.0', '9.0', '7.5']):
            Movie.objects.create(title=f'R{i}', rating=rating)
        Movie.objects.create(title='No rating B')
        r = self.client.get('/api/movies/?ordering=-rating')
        ratings = [m['rating'] for m in r.data['results']]
        self.assertEqual(ratings[-2:], [None, None])
        self.assertEqual(ratings[:4], ['9.0', '9.0', '7.5', '6.0'])
        r = self.client.get('/api/movies/?ordering=rating')
        ratings = [m['rating'] for m in r.data['results']]
        self.assertEqual(ratings[-2:], [None, None])  # nulls last ascending too
