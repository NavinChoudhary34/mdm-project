from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0003_movie_owner_movie_visibility_alter_movie_video_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='poster_image',
            field=models.ImageField(blank=True, null=True, upload_to='movies/posters/'),
        ),
    ]
