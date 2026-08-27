from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Genre, Movie, Person

User = get_user_model()


class MovieTestBase(APITestCase):
    def setUp(self):
        nolan = Person.objects.create(name='Christopher Nolan')
        tarantino = Person.objects.create(name='Quentin Tarantino')
        scifi = Genre.objects.create(name='Sci-Fi')
        drama = Genre.objects.create(name='Drama')

        self.inception = Movie.objects.create(
            title='Inception', director=nolan, release_date=date(2010, 7, 16), rating=8.8
        )
        self.inception.genres.add(scifi)

        self.pulp_fiction = Movie.objects.create(
            title='Pulp Fiction', director=tarantino, release_date=date(1994, 10, 14), rating=8.9
        )
        self.pulp_fiction.genres.add(drama)


class MovieListTests(MovieTestBase):
    def test_list_movies_is_public(self):
        resp = self.client.get('/api/movies/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 2)

    def test_search_by_title(self):
        resp = self.client.get('/api/movies/', {'search': 'Inception'})
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['title'], 'Inception')

    def test_filter_by_director(self):
        resp = self.client.get('/api/movies/', {'director': 'Nolan'})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_genre(self):
        resp = self.client.get('/api/movies/', {'genre': 'Drama'})
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['title'], 'Pulp Fiction')

    def test_filter_by_min_rating(self):
        resp = self.client.get('/api/movies/', {'min_rating': 8.85})
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['title'], 'Pulp Fiction')


class MovieDetailTests(MovieTestBase):
    def test_movie_detail(self):
        resp = self.client.get(f'/api/movies/{self.inception.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], 'Inception')
        self.assertEqual(resp.data['director']['name'], 'Christopher Nolan')

    def test_movie_not_found(self):
        resp = self.client.get('/api/movies/99999/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_staff_cannot_create_movie(self):
        user = User.objects.create_user(username='regular', email='r@example.com', password='pass12345')
        self.client.force_authenticate(user)
        resp = self.client.post('/api/movies/', {'title': 'New Movie'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create_movie(self):
        staff = User.objects.create_user(username='admin2', email='a2@example.com', password='pass12345', is_staff=True)
        self.client.force_authenticate(staff)
        resp = self.client.post('/api/movies/', {'title': 'New Movie'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
