"""
One-off setup command: configures CORS on the B2 bucket so browsers are
allowed to upload directly to it (see apps/movies/presign.py for why the
browser talks to B2 directly at all).

Without this, B2 silently rejects the browser's direct PUT upload -
which is why a presigned-upload attempt can look like it "just hangs"
in the browser with no clear error, rather than failing obviously.

Run this once after setting up the bucket (or again any time the
frontend's URL changes):

    python manage.py configure_b2_cors
"""

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Configures CORS on the B2 bucket so the browser can upload directly to it.'

    def handle(self, *args, **options):
        connection = getattr(default_storage, 'connection', None)

        if connection is None:
            raise CommandError(
                'No S3-compatible storage is configured (default_storage has '
                'no .connection). This command only does something useful '
                'against B2/S3 storage - e.g. run it on Render, not locally.'
            )

        client = connection.meta.client
        bucket = default_storage.bucket_name

        frontend_url = getattr(settings, 'FRONTEND_URL', None)

        if not frontend_url:
            raise CommandError(
                'FRONTEND_URL is not set - cannot determine which origin to '
                'allow. Set it in your environment variables first.'
            )

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

        client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_configuration)

        self.stdout.write(self.style.SUCCESS(
            f'CORS configured on bucket {bucket!r} - '
            f'browser uploads from {frontend_url!r} are now allowed.'
        ))
