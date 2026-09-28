from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.playlists import urls as playlists_urls
from config.media_serving import serve_media

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('apps.accounts.urls')),
    path('api/movies/', include('apps.movies.urls')),
    path('api/playlists/', include('apps.playlists.urls')),
    path('api/public/playlists/', include((playlists_urls.public_urlpatterns, 'playlists'), namespace='public-playlists')),
    path('api/', include('apps.library.urls')),
    path('api/dsa/', include('apps.dsa.urls')),

    # OpenAPI schema + Swagger UI (see section 37 of the spec).
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    # Range-aware media serving (not Django's default static.serve, which
    # ignores Range headers entirely and breaks video seeking) - see
    # config/media_serving.py for why.
    urlpatterns += [
        re_path(
            r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            serve_media,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
