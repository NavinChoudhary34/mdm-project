"""Local development settings. Import everything from base and loosen a few things."""
from .base import *  # noqa: F401,F403

DEBUG = True

# Show DRF's browsable API + full error pages locally.
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

SPECTACULAR_SETTINGS['SERVE_INCLUDE_SCHEMA'] = True  # noqa: F405
