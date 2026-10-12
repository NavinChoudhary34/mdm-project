"""Local development settings. Import everything from base and loosen a few things."""
from .base import *  # noqa: F401,F403

DEBUG = True

# Password-reset links print in the runserver terminal (the view's comment assumed this).
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Show DRF's browsable API + full error pages locally.
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

SPECTACULAR_SETTINGS['SERVE_INCLUDE_SCHEMA'] = True  # noqa: F405
