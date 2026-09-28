from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial=True
    dependencies=[
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('movies','0004_movie_poster_image'),
        ('playlists','0001_initial'),
    ]
    operations=[
        migrations.CreateModel(name='RecentlyViewed',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('viewed_at',models.DateTimeField(auto_now=True)),
            ('movie',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='recently_viewed_by',to='movies.movie')),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='recently_viewed_movies',to=settings.AUTH_USER_MODEL)),
        ],options={'ordering':['-viewed_at','-id'],'indexes':[models.Index(fields=['user','-viewed_at'],name='dsa_recent_user_viewed_idx')],'constraints':[models.UniqueConstraint(fields=('user','movie'),name='unique_recently_viewed_user_movie')]}),
        migrations.CreateModel(name='PlaylistUndoAction',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('action_type',models.CharField(max_length=32)),
            ('payload',models.JSONField()),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('playlist',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='undo_actions',to='playlists.playlist')),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='playlist_undo_actions',to=settings.AUTH_USER_MODEL)),
        ],options={'ordering':['-created_at','-id'],'indexes':[models.Index(fields=['user','-created_at'],name='dsa_undo_user_created_idx')]}),
    ]
