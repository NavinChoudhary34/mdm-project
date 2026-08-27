from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Person(models.Model):
    """A real person who can appear as a director and/or as cast on many movies."""
    name = models.CharField(max_length=200, db_index=True)
    photo_url = models.URLField(blank=True, default='')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'people'

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, default='')
    release_date = models.DateField(db_index=True, null=True, blank=True)

    # Movie artwork
    poster_url = models.URLField(blank=True, default='')
    backdrop_url = models.URLField(blank=True, default='')

    # Actual movie/video file
    video_file = models.FileField(
        upload_to='movies/',
        blank=True,
        null=True
    )

    runtime_minutes = models.PositiveIntegerField(null=True, blank=True)

    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)

    # genres = models.ManyToManyField(Genre, related_name='movies', blank=True)
    director = models.ForeignKey(
        Person, related_name='directed_movies', on_delete=models.SET_NULL, null=True, blank=True
    )
    cast = models.ManyToManyField(Person, through='MovieCastMember', related_name='acted_in_movies', blank=True)

    # Aggregate/critical rating (e.g. imported from an external source), distinct
    # from any individual user's personal rating stored in apps.library.Rating.
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
        ]

    def __str__(self):
        return self.title

    @property
    def release_year(self):
        return self.release_date.year if self.release_date else None


class MovieCastMember(models.Model):
    """Through-model so we can keep cast ordering / character names per movie."""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='cast_members')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='cast_credits')
    character_name = models.CharField(max_length=200, blank=True, default='')
    billing_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['billing_order']
        unique_together = ['movie', 'person']

    def __str__(self):
        return f'{self.person} in {self.movie}'
