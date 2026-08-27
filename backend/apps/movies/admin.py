from django.contrib import admin

from .models import Genre, Movie, MovieCastMember, Person


class MovieCastMemberInline(admin.TabularInline):
    model = MovieCastMember
    extra = 1


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_date', 'runtime_minutes', 'rating', 'director']
    list_filter = ['genres', 'release_date']
    search_fields = ['title', 'description', 'director__name']
    filter_horizontal = ['genres']
    inlines = [MovieCastMemberInline]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
