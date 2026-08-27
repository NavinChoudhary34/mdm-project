from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.playlists import urls as playlists_urls

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('apps.accounts.urls')),
    path('api/movies/', include('apps.movies.urls')),
    path('api/playlists/', include('apps.playlists.urls')),
    path('api/public/playlists/', include((playlists_urls.public_urlpatterns, 'playlists'), namespace='public-playlists')),
    path('api/', include('apps.library.urls')),

    # OpenAPI schema + Swagger UI (see section 37 of the spec).
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
