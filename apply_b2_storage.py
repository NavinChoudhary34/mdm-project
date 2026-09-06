#!/usr/bin/env python3
"""
Wires up Backblaze B2 as the production file storage for movie/poster
uploads, so they persist across Render deploys instead of living on
Render's ephemeral local disk. Local dev is untouched - this only
changes config/settings/production.py.

Usage (run from the project ROOT):
    cd mdm-project-main
    python apply_b2_storage.py

After running, set these on Render (Environment tab), not locally:
    B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME,
    B2_ENDPOINT_URL, B2_REGION_NAME
"""

import os
import shutil
import sys

FILES = {}

FILES['backend/requirements.txt'] = 'Django==5.1.3\ndjangorestframework==3.15.2\ndjangorestframework-simplejwt==5.3.1\npsycopg2-binary==2.9.10\npython-decouple==3.8\ndjango-cors-headers==4.6.0\ndjango-filter==24.3\ndrf-spectacular==0.27.2\nPillow==11.0.0\ndj-database-url==2.3.0\ngunicorn==23.0.0\nwhitenoise==6.8.2\ndjango-ranged-response==0.2.0\ndjango-storages==1.14.4\nboto3==1.35.99\n'

FILES['backend/config/settings/production.py'] = '"""Production settings. Import everything from base and harden it."""\nfrom decouple import config\nfrom .base import *  # noqa: F401,F403\n\nDEBUG = False\n\n# --- HTTPS / cookie hardening ---\nSECURE_SSL_REDIRECT = config(\'SECURE_SSL_REDIRECT\', default=True, cast=bool)\nSESSION_COOKIE_SECURE = True\nCSRF_COOKIE_SECURE = True\nSECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days\nSECURE_HSTS_INCLUDE_SUBDOMAINS = True\nSECURE_HSTS_PRELOAD = True\nSECURE_CONTENT_TYPE_NOSNIFF = True\nSECURE_BROWSER_XSS_FILTER = True\nX_FRAME_OPTIONS = \'DENY\'\n\n# Only the JSON renderer in production — no browsable API exposing DB internals.\nREST_FRAMEWORK[\'DEFAULT_RENDERER_CLASSES\'] = (  # noqa: F405\n    \'rest_framework.renderers.JSONRenderer\',\n)\n\n# --- Movie/poster file storage: Backblaze B2 (S3-compatible) ---\n# Render\'s disk doesn\'t persist across deploys/restarts, so uploaded videos\n# and posters can\'t live in the local filesystem here the way they do in\n# dev. django-storages\' S3-compatible backend works with B2 directly — B2\n# just needs its own endpoint/region instead of AWS\'s.\nSTORAGES[\'default\'] = {  # noqa: F405\n    \'BACKEND\': \'storages.backends.s3.S3Storage\',\n}\n\nAWS_ACCESS_KEY_ID = config(\'B2_KEY_ID\')\nAWS_SECRET_ACCESS_KEY = config(\'B2_APPLICATION_KEY\')\nAWS_STORAGE_BUCKET_NAME = config(\'B2_BUCKET_NAME\')\nAWS_S3_ENDPOINT_URL = config(\'B2_ENDPOINT_URL\')  # e.g. https://s3.us-west-004.backblazeb2.com\nAWS_S3_REGION_NAME = config(\'B2_REGION_NAME\')  # e.g. us-west-004\nAWS_S3_ADDRESSING_STYLE = \'virtual\'\nAWS_S3_FILE_OVERWRITE = False  # don\'t clobber a file if two uploads share a name\n\n# The bucket stays private — the app already has a "private" vs "public"\n# visibility concept for uploaded movies, so files shouldn\'t be publicly\n# readable by anyone who has (or guesses) the URL. Instead every file URL\n# is signed and expires, so a link only works briefly and only via a URL\n# this app itself generated.\nAWS_DEFAULT_ACL = None\nAWS_QUERYSTRING_AUTH = True\nAWS_QUERYSTRING_EXPIRE = 3600  # signed URLs expire after 1 hour\n'

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
    print('Done. Next:')
    print('  1. cd backend && venv\\Scripts\\pip install -r requirements.txt   (Windows)')
    print('     or venv/bin/pip install -r requirements.txt                    (macOS/Linux)')
    print('  2. Create a B2 bucket (private) and application key at backblaze.com')
    print('  3. Add B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME, B2_ENDPOINT_URL,')
    print('     B2_REGION_NAME as environment variables on Render (not locally)')
    print()
    print('Backups of the original files were saved alongside them as *.bak')

if __name__ == '__main__':
    main()
