#!/usr/bin/env python3
"""
Makes configure_b2_cors never fail the build - it now warns and exits
successfully instead of raising CommandError when FRONTEND_URL isn't
set yet or storage isn't configured, so chaining it into your Render
build command can't take down an otherwise-working deploy.

Usage (run from the project ROOT):
    cd mdm-project-main
    python apply_forgiving_cors_command.py
"""

import os
import shutil
import sys

FILES = {}

FILES['backend/apps/movies/management/commands/configure_b2_cors.py'] = '"""\nOne-off setup command: configures CORS on the B2 bucket so browsers are\nallowed to upload directly to it (see apps/movies/presign.py for why the\nbrowser talks to B2 directly at all).\n\nWithout this, B2 silently rejects the browser\'s direct PUT upload -\nwhich is why a presigned-upload attempt can look like it "just hangs"\nin the browser with no clear error, rather than failing obviously.\n\nSafe to run repeatedly and safe to leave permanently in your deploy\'s\nbuild command - it never fails the build. If storage isn\'t configured\n(local dev) or FRONTEND_URL isn\'t set yet, it prints a warning and exits\nsuccessfully instead of blocking the whole deploy over what is, at\nworst, a missed CORS update.\n\n    python manage.py configure_b2_cors\n"""\n\nfrom django.conf import settings\nfrom django.core.files.storage import default_storage\nfrom django.core.management.base import BaseCommand\n\n\nclass Command(BaseCommand):\n    help = \'Configures CORS on the B2 bucket so the browser can upload directly to it.\'\n\n    def handle(self, *args, **options):\n        connection = getattr(default_storage, \'connection\', None)\n\n        if connection is None:\n            # Expected in local dev (plain filesystem storage) - not an\n            # error, just nothing to do here.\n            self.stdout.write(\n                \'No S3-compatible storage is configured - skipping B2 CORS setup.\'\n            )\n            return\n\n        frontend_url = getattr(settings, \'FRONTEND_URL\', None)\n\n        if not frontend_url:\n            # Don\'t fail the whole deploy over a missing CORS update - warn\n            # loudly instead, so it\'s visible in the build log but doesn\'t\n            # block everything else from shipping.\n            self.stderr.write(self.style.WARNING(\n                \'FRONTEND_URL is not set - skipping B2 CORS configuration. \'\n                \'Direct video uploads from the browser will not work until \'\n                \'FRONTEND_URL is set and this command runs again (it is safe \'\n                \'to leave in your build command permanently).\'\n            ))\n            return\n\n        client = connection.meta.client\n        bucket = default_storage.bucket_name\n\n        cors_configuration = {\n            \'CORSRules\': [\n                {\n                    \'AllowedOrigins\': [frontend_url],\n                    \'AllowedMethods\': [\'PUT\', \'GET\', \'HEAD\'],\n                    \'AllowedHeaders\': [\'*\'],\n                    \'MaxAgeSeconds\': 3600,\n                },\n            ],\n        }\n\n        try:\n            client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_configuration)\n        except Exception as exc:\n            # Same reasoning: a storage-side hiccup here shouldn\'t take the\n            # whole deploy down with it.\n            self.stderr.write(self.style.WARNING(\n                f\'Could not configure B2 CORS (deploy will continue): {exc}\'\n            ))\n            return\n\n        self.stdout.write(self.style.SUCCESS(\n            f\'CORS configured on bucket {bucket!r} - \'\n            f\'browser uploads from {frontend_url!r} are now allowed.\'\n        ))\n'

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
    print('Done. Next: git add -A && git commit -m "Make configure_b2_cors never fail the build" && git push')
    print()
    print('IMPORTANT: also set FRONTEND_URL on your BACKEND service Environment tab')
    print('  FRONTEND_URL = https://mdm-project-frontend.onrender.com')
    print('otherwise CORS still wont get configured - it will just no longer break the build.')
    print()
    print('Backups of the original files were saved alongside them as *.bak')

if __name__ == '__main__':
    main()
