"""Direct and multipart upload helpers for Backblaze B2's S3 API.

The browser never sends large movie bytes through Django. Django only creates
short-lived presigned URLs and records the final object key. Large videos use
S3 multipart upload so a dropped connection only loses the current part rather
than the entire movie upload.
"""

import logging
import os
import uuid

from django.core.files.storage import default_storage
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

PRESIGNED_URL_EXPIRES = 3600
MAX_PARTS = 10_000


def get_s3_client_and_bucket():
    connection = getattr(default_storage, 'connection', None)
    if connection is None:
        return None, None

    meta = getattr(connection, 'meta', None)
    client = getattr(meta, 'client', None)
    bucket = getattr(default_storage, 'bucket_name', None)

    if client is None or not bucket:
        return None, None

    return client, bucket


def make_video_key(filename):
    ext = os.path.splitext(filename or 'video')[1]
    return f'movies/videos/{uuid.uuid4().hex}{ext}'


class PresignVideoUploadView(APIView):
    """Backward-compatible single PUT endpoint for smaller files."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        client, bucket = get_s3_client_and_bucket()
        if client is None:
            return Response(
                {'detail': 'Direct upload is not available in this environment.'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        filename = request.data.get('filename') or 'video'
        content_type = request.data.get('content_type') or 'application/octet-stream'
        key = make_video_key(filename)

        try:
            upload_url = client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket,
                    'Key': key,
                    'ContentType': content_type,
                },
                ExpiresIn=PRESIGNED_URL_EXPIRES,
                HttpMethod='PUT',
            )
        except Exception:
            logger.exception('Failed to create single-upload URL for key=%r', key)
            return Response(
                {'detail': 'Could not prepare a direct upload URL.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'upload_url': upload_url, 'key': key})


class InitiateMultipartVideoUploadView(APIView):
    """Create a B2/S3 multipart upload and return its upload ID and object key."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        client, bucket = get_s3_client_and_bucket()
        if client is None:
            return Response(
                {'detail': 'Multipart upload is not available in this environment.'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        filename = request.data.get('filename') or 'video'
        content_type = request.data.get('content_type') or 'application/octet-stream'
        key = make_video_key(filename)

        try:
            result = client.create_multipart_upload(
                Bucket=bucket,
                Key=key,
                ContentType=content_type,
            )
        except Exception:
            logger.exception('Failed to initiate multipart upload for key=%r', key)
            return Response(
                {'detail': 'Could not start the video upload.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        upload_id = result.get('UploadId')
        if not upload_id:
            logger.error('B2 returned no UploadId for key=%r: %r', key, result)
            return Response(
                {'detail': 'Storage did not return an upload ID.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        logger.info(
            'Started multipart video upload user=%s key=%r upload_id=%r',
            request.user.id,
            key,
            upload_id,
        )

        return Response({'upload_id': upload_id, 'key': key})


class PresignMultipartPartView(APIView):
    """Return a short-lived presigned PUT URL for one multipart part."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        client, bucket = get_s3_client_and_bucket()
        if client is None:
            return Response(
                {'detail': 'Multipart upload is not available in this environment.'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        key = str(request.data.get('key') or '')
        upload_id = str(request.data.get('upload_id') or '')

        try:
            part_number = int(request.data.get('part_number'))
        except (TypeError, ValueError):
            part_number = 0

        if not key.startswith('movies/videos/') or not upload_id:
            return Response(
                {'detail': 'Invalid multipart upload.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if part_number < 1 or part_number > MAX_PARTS:
            return Response(
                {'detail': f'part_number must be between 1 and {MAX_PARTS}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            upload_url = client.generate_presigned_url(
                'upload_part',
                Params={
                    'Bucket': bucket,
                    'Key': key,
                    'UploadId': upload_id,
                    'PartNumber': part_number,
                },
                ExpiresIn=PRESIGNED_URL_EXPIRES,
                HttpMethod='PUT',
            )
        except Exception:
            logger.exception(
                'Failed to sign multipart part user=%s key=%r part=%s',
                request.user.id,
                key,
                part_number,
            )
            return Response(
                {'detail': 'Could not prepare this upload part.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'upload_url': upload_url})


class CompleteMultipartVideoUploadView(APIView):
    """Tell B2 to assemble all successfully uploaded parts into one object."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        client, bucket = get_s3_client_and_bucket()
        if client is None:
            return Response(
                {'detail': 'Multipart upload is not available in this environment.'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        key = str(request.data.get('key') or '')
        upload_id = str(request.data.get('upload_id') or '')
        raw_parts = request.data.get('parts')

        if not key.startswith('movies/videos/') or not upload_id:
            return Response(
                {'detail': 'Invalid multipart upload.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(raw_parts, list) or not raw_parts:
            return Response(
                {'detail': 'At least one uploaded part is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parts = []
        seen = set()

        try:
            for item in raw_parts:
                part_number = int(item['part_number'])
                etag = str(item['etag']).strip().strip('"')

                if part_number < 1 or part_number > MAX_PARTS or not etag:
                    raise ValueError

                if part_number in seen:
                    raise ValueError

                seen.add(part_number)
                parts.append({'PartNumber': part_number, 'ETag': etag})

        except (KeyError, TypeError, ValueError):
            return Response(
                {'detail': 'Invalid multipart parts list.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parts.sort(key=lambda item: item['PartNumber'])
        expected = list(range(1, len(parts) + 1))

        if [part['PartNumber'] for part in parts] != expected:
            return Response(
                {'detail': 'Multipart parts must be consecutive starting at part 1.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts},
            )
        except Exception:
            logger.exception(
                'Failed to complete multipart upload user=%s key=%r upload_id=%r',
                request.user.id,
                key,
                upload_id,
            )
            return Response(
                {'detail': 'Storage could not assemble the uploaded video.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        logger.info(
            'Completed multipart video upload user=%s key=%r upload_id=%r parts=%s',
            request.user.id,
            key,
            upload_id,
            len(parts),
        )
        return Response({'key': key})


class AbortMultipartVideoUploadView(APIView):
    """Clean up an unfinished multipart upload after a failed browser upload."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        client, bucket = get_s3_client_and_bucket()
        if client is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        key = str(request.data.get('key') or '')
        upload_id = str(request.data.get('upload_id') or '')

        if not key.startswith('movies/videos/') or not upload_id:
            return Response(
                {'detail': 'Invalid multipart upload.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            client.abort_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
            )
        except Exception:
            # Cleanup is best effort. Do not hide the original upload error.
            logger.exception(
                'Failed to abort multipart upload user=%s key=%r upload_id=%r',
                request.user.id,
                key,
                upload_id,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
