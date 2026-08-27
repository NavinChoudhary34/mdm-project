from datetime import date

from django.core.management.base import BaseCommand

from apps.movies.models import Genre, Movie, MovieCastMember, Person

# Realistic sample data — enough variety across genres/decades/directors to make
# search, filtering, and sorting meaningful during local development.
SAMPLE_MOVIES = [
    {
        'title': 'Inception',
        'description': 'A thief who steals corporate secrets through dream-sharing technology '
                        'is given the inverse task of planting an idea into a target\'s subconscious.',
        'release_date': date(2010, 7, 16),
        'runtime_minutes': 148,
        'rating': 8.8,
        'poster_url': 'https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/s3TBrRGB1iav7gFOCNx3H31MoES.jpg',
        'genres': ['Sci-Fi', 'Thriller', 'Action'],
        'director': 'Christopher Nolan',
        'cast': ['Leonardo DiCaprio', 'Joseph Gordon-Levitt', 'Elliot Page'],
    },
    {
        'title': 'Interstellar',
        'description': 'A team of explorers travel through a wormhole in space in an attempt '
                        'to ensure humanity\'s survival.',
        'release_date': date(2014, 11, 7),
        'runtime_minutes': 169,
        'rating': 8.7,
        'poster_url': 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/pbrkL804c8yAv3zBZR4QPWZAAn8.jpg',
        'genres': ['Sci-Fi', 'Drama', 'Adventure'],
        'director': 'Christopher Nolan',
        'cast': ['Matthew McConaughey', 'Anne Hathaway', 'Jessica Chastain'],
    },
    {
        'title': 'The Dark Knight',
        'description': 'When the menace known as the Joker wreaks havoc on Gotham, Batman must '
                        'accept one of the greatest psychological tests of his ability to fight injustice.',
        'release_date': date(2008, 7, 18),
        'runtime_minutes': 152,
        'rating': 9.0,
        'poster_url': 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/hqkIcbrOHL86UncnHIsHVcVmzue.jpg',
        'genres': ['Action', 'Crime', 'Drama'],
        'director': 'Christopher Nolan',
        'cast': ['Christian Bale', 'Heath Ledger', 'Aaron Eckhart'],
    },
    {
        'title': 'Tenet',
        'description': 'Armed with only one word, Tenet, and fighting for the survival of the '
                        'entire world, a Protagonist journeys through a twilight world of espionage.',
        'release_date': date(2020, 8, 26),
        'runtime_minutes': 150,
        'rating': 7.3,
        'poster_url': 'https://image.tmdb.org/t/p/w500/k68nPLbIST6NP96JmTxmZijEvCA.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/ec242top649GaBaHF9G30rArlq2.jpg',
        'genres': ['Sci-Fi', 'Thriller', 'Action'],
        'director': 'Christopher Nolan',
        'cast': ['John David Washington', 'Robert Pattinson', 'Elizabeth Debicki'],
    },
    {
        'title': 'The Grand Budapest Hotel',
        'description': 'A writer encounters the owner of an aging high-class hotel, who tells him '
                        'of his early years serving as a lobby boy in the hotel\'s glorious years.',
        'release_date': date(2014, 3, 28),
        'runtime_minutes': 99,
        'rating': 8.1,
        'poster_url': 'https://image.tmdb.org/t/p/w500/eWdyYQreja6JGCzqHWXpWHDrrPo.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/nX5XoGaCwSRgqfKUlj0O1hR5xDl.jpg',
        'genres': ['Comedy', 'Drama'],
        'director': 'Wes Anderson',
        'cast': ['Ralph Fiennes', 'Tony Revolori', 'Saoirse Ronan'],
    },
    {
        'title': 'Parasite',
        'description': 'Greed and class discrimination threaten the newly formed symbiotic '
                        'relationship between the wealthy Park family and the destitute Kim clan.',
        'release_date': date(2019, 5, 30),
        'runtime_minutes': 132,
        'rating': 8.5,
        'poster_url': 'https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/TU9NIjwzjoKPwQHoHshkFcQUCG.jpg',
        'genres': ['Thriller', 'Drama', 'Comedy'],
        'director': 'Bong Joon-ho',
        'cast': ['Song Kang-ho', 'Lee Sun-kyun', 'Cho Yeo-jeong'],
    },
    {
        'title': 'Spider-Man: Into the Spider-Verse',
        'description': 'Teen Miles Morales becomes the Spider-Man of his universe and must join '
                        'with five spider-powered individuals from other dimensions.',
        'release_date': date(2018, 12, 14),
        'runtime_minutes': 117,
        'rating': 8.4,
        'poster_url': 'https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/2rmK7mnchw9Xr3XdMXeuwWlLBLc.jpg',
        'genres': ['Animation', 'Action', 'Sci-Fi'],
        'director': 'Bob Persichetti',
        'cast': ['Shameik Moore', 'Jake Johnson', 'Hailee Steinfeld'],
    },
    {
        'title': 'Everything Everywhere All at Once',
        'description': 'A middle-aged Chinese immigrant is swept up into an insane adventure in '
                        'which she alone can save existence by exploring other universes.',
        'release_date': date(2022, 3, 25),
        'runtime_minutes': 139,
        'rating': 7.8,
        'poster_url': 'https://image.tmdb.org/t/p/w500/w3LxiVYdWWRvEVdn5RYq6jIqkb1.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/r0FLYcTF6i88pbaQuXbEDcqnleG.jpg',
        'genres': ['Sci-Fi', 'Comedy', 'Action'],
        'director': 'Daniel Kwan',
        'cast': ['Michelle Yeoh', 'Stephanie Hsu', 'Ke Huy Quan'],
    },
    {
        'title': 'Dune',
        'description': 'Feature adaptation of Frank Herbert\'s science fiction novel about the son '
                        'of a noble family entrusted with the protection of the most valuable asset '
                        'in the galaxy.',
        'release_date': date(2021, 10, 22),
        'runtime_minutes': 155,
        'rating': 8.0,
        'poster_url': 'https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/jYEW5xZkZk2WTrdbMGAPFuBqbDc.jpg',
        'genres': ['Sci-Fi', 'Adventure', 'Drama'],
        'director': 'Denis Villeneuve',
        'cast': ['Timothée Chalamet', 'Rebecca Ferguson', 'Zendaya'],
    },
    {
        'title': 'La La Land',
        'description': 'While navigating their careers in Los Angeles, a pianist and an actress '
                        'fall in love while attempting to reconcile their aspirations for the future.',
        'release_date': date(2016, 12, 9),
        'runtime_minutes': 128,
        'rating': 8.0,
        'poster_url': 'https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/nlPmDbXOblUFhTV6h6bLUJj4rMw.jpg',
        'genres': ['Comedy', 'Drama', 'Romance'],
        'director': 'Damien Chazelle',
        'cast': ['Ryan Gosling', 'Emma Stone', 'John Legend'],
    },
    {
        'title': 'Mad Max: Fury Road',
        'description': 'In a post-apocalyptic wasteland, Max teams up with a mysterious woman, '
                        'Furiosa, to flee from a tyrannical ruler.',
        'release_date': date(2015, 5, 15),
        'runtime_minutes': 120,
        'rating': 8.1,
        'poster_url': 'https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/tbhdm8UJAb4ViCTsulYFL3lxMCd.jpg',
        'genres': ['Action', 'Adventure', 'Sci-Fi'],
        'director': 'George Miller',
        'cast': ['Tom Hardy', 'Charlize Theron', 'Nicholas Hoult'],
    },
    {
        'title': 'Coco',
        'description': 'Aspiring musician Miguel enters the Land of the Dead to find his '
                        'great-great-grandfather, a legendary singer.',
        'release_date': date(2017, 11, 22),
        'runtime_minutes': 105,
        'rating': 8.4,
        'poster_url': 'https://image.tmdb.org/t/p/w500/gGEsBPAijhVUFoiNpgZXqRVWJt2.jpg',
        'backdrop_url': 'https://image.tmdb.org/t/p/original/askg3SMvhqEl4OL52YuvdtY40Yb.jpg',
        'genres': ['Animation', 'Family', 'Comedy'],
        'director': 'Lee Unkrich',
        'cast': ['Anthony Gonzalez', 'Gael García Bernal', 'Benjamin Bratt'],
    },
]


class Command(BaseCommand):
    """
    python manage.py seed_movies

    Populates the database with a small set of realistic sample movies so the
    app has something to browse in local development. Safe to re-run —
    get_or_create is used everywhere, so it won't duplicate data.
    """
    help = 'Seed the database with sample movies for local development.'

    def handle(self, *args, **options):
        created_count = 0

        for entry in SAMPLE_MOVIES:
            director, _ = Person.objects.get_or_create(name=entry['director'])

            movie, created = Movie.objects.get_or_create(
                title=entry['title'],
                defaults={
                    'description': entry['description'],
                    'release_date': entry['release_date'],
                    'runtime_minutes': entry['runtime_minutes'],
                    'rating': entry['rating'],
                    'poster_url': entry['poster_url'],
                    'backdrop_url': entry['backdrop_url'],
                    'director': director,
                },
            )
            if created:
                created_count += 1

            genre_objs = []
            for genre_name in entry['genres']:
                genre, _ = Genre.objects.get_or_create(name=genre_name)
                genre_objs.append(genre)
            movie.genres.set(genre_objs)

            for billing_order, actor_name in enumerate(entry['cast']):
                actor, _ = Person.objects.get_or_create(name=actor_name)
                MovieCastMember.objects.get_or_create(
                    movie=movie, person=actor, defaults={'billing_order': billing_order}
                )

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(SAMPLE_MOVIES)} movies ({created_count} newly created, '
            f'{len(SAMPLE_MOVIES) - created_count} already existed).'
        ))
