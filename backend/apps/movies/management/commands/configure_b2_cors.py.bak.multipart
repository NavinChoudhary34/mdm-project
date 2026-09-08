"""
One-off setup command: configures CORS on the B2 bucket so browsers are
allowed to upload directly to it (see apps/movies/presign.py for why the
browser talks to B2 directly at all).

Without this, B2 silently rejects the browser's direct PUT upload -
which is why a presigned-upload attempt can look like it "just hangs"
in the browser with no clear error, rather than failing obviously.

Safe to run repeatedly and safe to leave permanently in your deploy's
build command - it never fails the build. If storage isn't configured
(local dev) or FRONTEND_URL isn't set yet, it prints a warning and exits
successfully instead of blocking the whole deploy over what is, at
worst, a missed CORS update.

    python manage.py configure_b2_cors
"""

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Configures CORS on the B2 bucket so the browser can upload directly to it.'

    def handle(self, *args, **options):
        connection = getattr(default_storage, 'connection', None)

        if connection is None:
            # Expected in local dev (plain filesystem storage) - not an
            # error, just nothing to do here.
            self.stdout.write(
                'No S3-compatible storage is configured - skipping B2 CORS setup.'
            )
            return

        frontend_url = getattr(settings, 'FRONTEND_URL', None)

        if not frontend_url:
            # Don't fail the whole deploy over a missing CORS update - warn
            # loudly instead, so it's visible in the build log but doesn't
            # block everything else from shipping.
            self.stderr.write(self.style.WARNING(
                'FRONTEND_URL is not set - skipping B2 CORS configuration. '
                'Direct video uploads from the browser will not work until '
                'FRONTEND_URL is set and this command runs again (it is safe '
                'to leave in your build command permanently).'
            ))
            return

        client = connection.meta.client
        bucket = default_storage.bucket_name

        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedOrigins': [frontend_url],
                    'AllowedMethods': ['PUT', 'GET', 'HEAD'],
                    'AllowedHeaders': ['*'],
                    'MaxAgeSeconds': 3600,
                },
            ],
        }

        try:
            client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_configuration)
        except Exception as exc:
            # Same reasoning: a storage-side hiccup here shouldn't take the
            # whole deploy down with it.
            self.stderr.write(self.style.WARNING(
                f'Could not configure B2 CORS (deploy will continue): {exc}'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f'CORS configured on bucket {bucket!r} - '
            f'browser uploads from {frontend_url!r} are now allowed.'
        ))
