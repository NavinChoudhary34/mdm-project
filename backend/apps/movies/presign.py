"""
Lets the browser upload a movie's video file directly to Backblaze B2,
bypassing Django for the actual file transfer.

Why this exists: uploading a full movie file through Django itself means
Django receives the whole file, then re-uploads that same file to B2,
all within one HTTP request - and Gunicorn's default 30s worker timeout
kills that request long before a multi-gigabyte file finishes moving
through Render's free-tier 0.1 CPU instance twice. A presigned URL lets
the browser skip Django entirely for the bytes: it PUTs the file straight
to B2, which has no such timeout, and only tells Django "here's where I
put it" once that's done - a JSON call that takes milliseconds.

Only meaningful when cloud (S3-compatible) storage is configured - see
config.settings.production. In local dev (plain filesystem storage),
this returns 501 so the frontend falls back to uploading through
Django's normal multipart endpoint instead, which is fine locally since
there's no network hop or timeout to worry about.
"""

import logging
import os
import uuid

from django.core.files.storage import default_storage
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class PresignVideoUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logger.info(
            'presign-video-upload requested by user=%s filename=%r',
            request.user.id,
            request.data.get('filename'),
        )

        s3_client = getattr(
            getattr(default_storage, 'connection', None), 'meta', None
        )

        if s3_client is None:
            logger.info(
                'presign-video-upload: no S3-compatible storage configured '
                '(default_storage has no .connection) - returning 501'
            )
            return Response(
                {'detail': 'Direct upload is not available in this environment.'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        filename = request.data.get('filename') or 'video'
        content_type = request.data.get('content_type') or 'application/octet-stream'

        # Random key, not the original filename - avoids collisions and
        # avoids exposing the uploader's original filename/path in the URL.
        ext = os.path.splitext(filename)[1]
        key = f'movies/videos/{uuid.uuid4().hex}{ext}'

        try:
            client = default_storage.connection.meta.client
            upload_url = client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': default_storage.bucket_name,
                    'Key': key,
                    'ContentType': content_type,
                },
                ExpiresIn=3600,
            )
        except Exception:
            # Don't let a boto3/credentials/network problem surface as an
            # opaque 500 with no context - log the real cause server-side
            # and give the frontend a clear, specific reason to show.
            logger.exception(
                'presign-video-upload: failed to generate a presigned URL '
                'for key=%r',
                key,
            )
            return Response(
                {'detail': 'Could not prepare a direct upload URL. Check the server logs for the underlying storage error.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        logger.info('presign-video-upload: issued upload URL for key=%r', key)

        return Response({'upload_url': upload_url, 'key': key})
