#!/usr/bin/env python3
"""
Fixes video seeking (skip back/forward, dragging the scrub bar) by
replacing Django's default media file serving - which has ZERO HTTP
Range support - with a Range-aware version. Without Range support,
browsers cannot seek video at all; this is why skip/scrub silently
did nothing before.

Also (re-)adds gunicorn/whitenoise for production deploys, since this
touches the same settings file.

Usage (run from the project ROOT - the folder containing
'backend' and 'frontend'):

    cd mdm-project-main
    python apply_video_seeking_fix.py

Then reinstall backend deps and restart the Django server:

    cd backend
    venv\\Scripts\\pip install -r requirements.txt   (Windows)
    venv/bin/pip install -r requirements.txt        (macOS/Linux)
    python manage.py runserver
"""

import os
import shutil
import sys

FILES = {}

FILES['backend/requirements.txt'] = 'Django==5.1.3\ndjangorestframework==3.15.2\ndjangorestframework-simplejwt==5.3.1\npsycopg2-binary==2.9.10\npython-decouple==3.8\ndjango-cors-headers==4.6.0\ndjango-filter==24.3\ndrf-spectacular==0.27.2\nPillow==11.0.0\ndj-database-url==2.3.0\ngunicorn==23.0.0\nwhitenoise==6.8.2\ndjango-ranged-response==0.2.0\n'

FILES['backend/config/settings/base.py'] = '"""\nBase settings shared by all environments.\nEnvironment-specific settings live in development.py / production.py.\n"""\nfrom pathlib import Path\nfrom datetime import timedelta\nfrom decouple import config, Csv\n\n# BASE_DIR points at backend/ (three levels up from this file: settings -> config -> backend)\nBASE_DIR = Path(__file__).resolve().parent.parent.parent\n\n# --- Core ---\nSECRET_KEY = config(\'SECRET_KEY\')  # must be set in .env, no fallback for safety\nDEBUG = config(\'DEBUG\', default=False, cast=bool)\nALLOWED_HOSTS = config(\'ALLOWED_HOSTS\', default=\'localhost,127.0.0.1\', cast=Csv())\n\n# --- Applications ---\nDJANGO_APPS = [\n    \'django.contrib.admin\',\n    \'django.contrib.auth\',\n    \'django.contrib.contenttypes\',\n    \'django.contrib.sessions\',\n    \'django.contrib.messages\',\n    \'django.contrib.staticfiles\',\n]\n\nTHIRD_PARTY_APPS = [\n    \'rest_framework\',\n    \'rest_framework_simplejwt\',\n    \'rest_framework_simplejwt.token_blacklist\',\n    \'corsheaders\',\n    \'django_filters\',\n    \'drf_spectacular\',\n]\n\nLOCAL_APPS = [\n    \'apps.accounts\',\n    \'apps.movies\',\n    \'apps.playlists\',\n    \'apps.library\',\n]\n\nINSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS\n\n# --- Custom user model (email-capable, used for auth) ---\nAUTH_USER_MODEL = \'accounts.User\'\n\nAUTHENTICATION_BACKENDS = [\n    \'apps.accounts.backends.EmailOrUsernameBackend\',\n    \'django.contrib.auth.backends.ModelBackend\',\n]\n\nMIDDLEWARE = [\n    \'django.middleware.security.SecurityMiddleware\',\n    \'whitenoise.middleware.WhiteNoiseMiddleware\',  # serves static files in production\n    \'corsheaders.middleware.CorsMiddleware\',  # must sit above CommonMiddleware\n    \'django.contrib.sessions.middleware.SessionMiddleware\',\n    \'django.middleware.common.CommonMiddleware\',\n    \'django.middleware.csrf.CsrfViewMiddleware\',\n    \'django.contrib.auth.middleware.AuthenticationMiddleware\',\n    \'django.contrib.messages.middleware.MessageMiddleware\',\n    \'django.middleware.clickjacking.XFrameOptionsMiddleware\',\n]\n\nROOT_URLCONF = \'config.urls\'\n\nTEMPLATES = [\n    {\n        \'BACKEND\': \'django.template.backends.django.DjangoTemplates\',\n        \'DIRS\': [BASE_DIR / \'templates\'],\n        \'APP_DIRS\': True,\n        \'OPTIONS\': {\n            \'context_processors\': [\n                \'django.template.context_processors.debug\',\n                \'django.template.context_processors.request\',\n                \'django.contrib.auth.context_processors.auth\',\n                \'django.contrib.messages.context_processors.messages\',\n            ],\n        },\n    },\n]\n\nWSGI_APPLICATION = \'config.wsgi.application\'\nASGI_APPLICATION = \'config.asgi.application\'\n\n# --- Database (PostgreSQL, always driven by env vars — never hardcoded) ---\nDATABASES = {\n    \'default\': {\n        \'ENGINE\': \'django.db.backends.postgresql\',\n        \'NAME\': config(\'DATABASE_NAME\'),\n        \'USER\': config(\'DATABASE_USER\'),\n        \'PASSWORD\': config(\'DATABASE_PASSWORD\'),\n        \'HOST\': config(\'DATABASE_HOST\', default=\'localhost\'),\n        \'PORT\': config(\'DATABASE_PORT\', default=\'5432\'),\n        \'CONN_MAX_AGE\': 60,\n    }\n}\n\n# --- Password validation ---\nAUTH_PASSWORD_VALIDATORS = [\n    {\'NAME\': \'django.contrib.auth.password_validation.UserAttributeSimilarityValidator\'},\n    {\'NAME\': \'django.contrib.auth.password_validation.MinimumLengthValidator\', \'OPTIONS\': {\'min_length\': 8}},\n    {\'NAME\': \'django.contrib.auth.password_validation.CommonPasswordValidator\'},\n    {\'NAME\': \'django.contrib.auth.password_validation.NumericPasswordValidator\'},\n]\n\n# --- I18N ---\nLANGUAGE_CODE = \'en-us\'\nTIME_ZONE = \'UTC\'\nUSE_I18N = True\nUSE_TZ = True\n\n# --- Static / media ---\nSTATIC_URL = \'static/\'\nSTATIC_ROOT = BASE_DIR / \'staticfiles\'\nSTORAGES = {\n    \'default\': {\n        \'BACKEND\': \'django.core.files.storage.FileSystemStorage\',\n    },\n    \'staticfiles\': {\n        \'BACKEND\': \'whitenoise.storage.CompressedManifestStaticFilesStorage\',\n    },\n}\nMEDIA_URL = \'media/\'\nMEDIA_ROOT = BASE_DIR / \'media\'\n\nDEFAULT_AUTO_FIELD = \'django.db.models.BigAutoField\'\n\n# --- Django REST Framework ---\nREST_FRAMEWORK = {\n    \'DEFAULT_AUTHENTICATION_CLASSES\': (\n        \'rest_framework_simplejwt.authentication.JWTAuthentication\',\n    ),\n    \'DEFAULT_PERMISSION_CLASSES\': (\n        \'rest_framework.permissions.IsAuthenticated\',\n    ),\n    \'DEFAULT_FILTER_BACKENDS\': (\n        \'django_filters.rest_framework.DjangoFilterBackend\',\n        \'rest_framework.filters.SearchFilter\',\n        \'rest_framework.filters.OrderingFilter\',\n    ),\n    \'DEFAULT_PAGINATION_CLASS\': \'rest_framework.pagination.PageNumberPagination\',\n    \'PAGE_SIZE\': 20,\n    \'DEFAULT_SCHEMA_CLASS\': \'drf_spectacular.openapi.AutoSchema\',\n    \'DEFAULT_THROTTLE_CLASSES\': [\n        \'rest_framework.throttling.ScopedRateThrottle\',\n    ],\n    \'DEFAULT_THROTTLE_RATES\': {\n        # Applied explicitly to auth views via throttle_scope; keeps brute-forcing login/register slow.\n        \'auth\': \'10/min\',\n    },\n}\n\n# --- Simple JWT ---\nSIMPLE_JWT = {\n    \'ACCESS_TOKEN_LIFETIME\': timedelta(minutes=30),\n    \'REFRESH_TOKEN_LIFETIME\': timedelta(days=7),\n    \'ROTATE_REFRESH_TOKENS\': True,\n    \'BLACKLIST_AFTER_ROTATION\': True,\n    \'UPDATE_LAST_LOGIN\': True,\n    \'AUTH_HEADER_TYPES\': (\'Bearer\',),\n    \'USER_ID_FIELD\': \'id\',\n    \'USER_ID_CLAIM\': \'user_id\',\n}\n\n# --- CORS ---\nCORS_ALLOWED_ORIGINS = config(\'CORS_ALLOWED_ORIGINS\', default=\'http://localhost:3000\', cast=Csv())\nCORS_ALLOW_CREDENTIALS = True\n\n# --- drf-spectacular (OpenAPI/Swagger docs) ---\nSPECTACULAR_SETTINGS = {\n    \'TITLE\': \'Movie Playlist Manager API\',\n    \'DESCRIPTION\': \'REST API for browsing movies, managing playlists, watchlists, favorites, and reviews.\',\n    \'VERSION\': \'1.0.0\',\n    \'SERVE_INCLUDE_SCHEMA\': False,\n}\n\n'

FILES['backend/config/urls.py'] = "from django.contrib import admin\nfrom django.conf import settings\nfrom django.urls import include, path, re_path\nfrom drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView\n\nfrom apps.playlists import urls as playlists_urls\nfrom config.media_serving import serve_media\n\nurlpatterns = [\n    path('admin/', admin.site.urls),\n\n    path('api/auth/', include('apps.accounts.urls')),\n    path('api/movies/', include('apps.movies.urls')),\n    path('api/playlists/', include('apps.playlists.urls')),\n    path('api/public/playlists/', include((playlists_urls.public_urlpatterns, 'playlists'), namespace='public-playlists')),\n    path('api/', include('apps.library.urls')),\n\n    # OpenAPI schema + Swagger UI (see section 37 of the spec).\n    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),\n    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),\n]\n\nif settings.DEBUG:\n    # Range-aware media serving (not Django's default static.serve, which\n    # ignores Range headers entirely and breaks video seeking) - see\n    # config/media_serving.py for why.\n    urlpatterns += [\n        re_path(\n            r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),\n            serve_media,\n            {'document_root': settings.MEDIA_ROOT},\n        ),\n    ]\n"

FILES['backend/config/media_serving.py'] = '"""\nServes files under MEDIA_ROOT (uploaded posters/videos) during development,\nthe same way Django\'s own django.views.static.serve() does - except this\none actually honors HTTP Range requests.\n\nWhy this exists: browsers seek within a <video> by requesting a specific\nbyte range (an HTTP "Range" header) rather than re-downloading the whole\nfile. Django\'s built-in static.serve() has no Range support at all - it\nalways returns the full file with a 200, no matter what the browser asked\nfor - so seeking (skip back/forward, dragging the scrub bar) silently does\nnothing. This view uses RangedFileResponse (django-ranged-response) to\nreturn a proper 206 Partial Content response with Content-Range headers,\nwhich is what makes video seeking actually work.\n\nOnly used when DEBUG=True (see config/urls.py). In production, whatever\nserves your media (e.g. S3/Cloudflare R2, or nginx) should already handle\nRange requests natively.\n"""\n\nimport mimetypes\nimport posixpath\nfrom pathlib import Path\n\nfrom django.http import Http404\nfrom django.utils._os import safe_join\nfrom ranged_response import RangedFileResponse\n\n\ndef serve_media(request, path, document_root=None):\n    path = posixpath.normpath(path).lstrip(\'/\')\n    fullpath = Path(safe_join(document_root, path))\n\n    if fullpath.is_dir() or not fullpath.exists():\n        raise Http404(\'"%s" does not exist\' % fullpath)\n\n    content_type, encoding = mimetypes.guess_type(str(fullpath))\n    content_type = content_type or \'application/octet-stream\'\n\n    response = RangedFileResponse(request, fullpath.open(\'rb\'), content_type=content_type)\n    response[\'Content-Disposition\'] = f\'inline; filename="{fullpath.name}"\'\n    if encoding:\n        response[\'Content-Encoding\'] = encoding\n    return response\n'

def main():
    root = os.getcwd()
    if not os.path.isdir(os.path.join(root, 'backend')) or not os.path.isdir(os.path.join(root, 'frontend')):
        print('Error: run this script from the project root (must contain backend/ and frontend/ folders).')
        sys.exit(1)

    print('Backing up files that will be changed (.bak)...')
    for rel_path in FILES:
        full_path = os.path.join(root, rel_path)
        if os.path.exists(full_path):
            shutil.copyfile(full_path, full_path + '.bak')

    for rel_path, content in FILES.items():
        full_path = os.path.join(root, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        print(f'Writing {rel_path}...')
        with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

    print()
    print('Done. Now install the new dependency and restart Django:')
    print()
    print('  cd backend')
    if os.name == 'nt':
        print('  venv\\Scripts\\pip install -r requirements.txt')
    else:
        print('  venv/bin/pip install -r requirements.txt')
    print('  python manage.py runserver')
    print()
    print('Backups of the original files were saved alongside them as *.bak')

if __name__ == '__main__':
    main()
