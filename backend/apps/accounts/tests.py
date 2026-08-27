from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    def test_register_success(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'alice', 'email': 'alice@example.com',
            'password': 'StrongPass123!', 'password_confirm': 'StrongPass123!',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertTrue(User.objects.filter(username='alice').exists())

    def test_register_password_mismatch(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'bob', 'email': 'bob@example.com',
            'password': 'StrongPass123!', 'password_confirm': 'Different123!',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_username(self):
        User.objects.create_user(username='carl', email='carl1@example.com', password='x')
        resp = self.client.post('/api/auth/register/', {
            'username': 'carl', 'email': 'carl2@example.com',
            'password': 'StrongPass123!', 'password_confirm': 'StrongPass123!',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email(self):
        User.objects.create_user(username='dana1', email='dana@example.com', password='x')
        resp = self.client.post('/api/auth/register/', {
            'username': 'dana2', 'email': 'dana@example.com',
            'password': 'StrongPass123!', 'password_confirm': 'StrongPass123!',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_is_hashed_not_plaintext(self):
        self.client.post('/api/auth/register/', {
            'username': 'erin', 'email': 'erin@example.com',
            'password': 'StrongPass123!', 'password_confirm': 'StrongPass123!',
        })
        user = User.objects.get(username='erin')
        self.assertNotEqual(user.password, 'StrongPass123!')
        self.assertTrue(user.password.startswith('pbkdf2_') or user.password.startswith('argon2'))


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='frank', email='frank@example.com', password='CorrectPass123!')

    def test_login_with_username(self):
        resp = self.client.post('/api/auth/login/', {'username': 'frank', 'password': 'CorrectPass123!'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_login_with_email(self):
        resp = self.client.post('/api/auth/login/', {'username': 'frank@example.com', 'password': 'CorrectPass123!'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_invalid_credentials(self):
        resp = self.client.post('/api/auth/login/', {'username': 'frank', 'password': 'WrongPass'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_auth(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        login = self.client.post('/api/auth/login/', {'username': 'frank', 'password': 'CorrectPass123!'})
        access = login.data['access']
        resp = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'frank')

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post('/api/auth/login/', {'username': 'frank', 'password': 'CorrectPass123!'})
        access, refresh = login.data['access'], login.data['refresh']

        logout = self.client.post(
            '/api/auth/logout/', {'refresh': refresh},
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)

        reuse = self.client.post('/api/auth/refresh/', {'refresh': refresh})
        self.assertEqual(reuse.status_code, status.HTTP_401_UNAUTHORIZED)
