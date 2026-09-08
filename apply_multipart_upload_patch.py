#!/usr/bin/env python3
"""
Apply the Backblaze B2 multipart-upload fix to the Movie Playlist Manager.

Usage:
    python apply_multipart_upload_patch.py

Run this script from the ROOT of your project, i.e. the directory that
contains both "backend" and "frontend".

The script:
  - backs up every file it changes as *.bak.multipart
  - adds B2/S3 multipart endpoints to Django
  - adds the frontend multipart uploader
  - makes large videos (>20 MiB) use multipart upload
  - exposes the ETag header through B2 CORS
  - adds FRONTEND_URL to production settings

It is safe to run more than once; already-applied changes are skipped.
"""

from pathlib import Path
import shutil
import sys

ROOT = Path.cwd()
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

if not (BACKEND / "manage.py").exists() or not (FRONTEND / "package.json").exists():
    print("ERROR: Run this script from the project root.")
    print("Expected:")
    print("  ./backend/manage.py")
    print("  ./frontend/package.json")
    sys.exit(1)


def backup(path: Path):
    backup_path = Path(str(path) + ".bak.multipart")
    if not backup_path.exists():
        shutil.copy2(path, backup_path)
        print(f"  backup: {backup_path}")


def write_if_changed(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        print(f"  unchanged: {path}")
        return
    if path.exists():
        backup(path)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"  updated: {path}")


def replace_once(path: Path, old: str, new: str, label: str):
    if not path.exists():
        print(f"ERROR: Missing file: {path}")
        sys.exit(1)

    text = path.read_text(encoding="utf-8")

    if new in text:
        print(f"  already applied: {label}")
        return

    if old not in text:
        print(f"ERROR: Could not find expected text for: {label}")
        print(f"File: {path}")
        print("The file may have changed since this patch was created.")
        sys.exit(1)

    backup(path)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"  applied: {label}")


# 1. Replace backend/apps/movies/presign.py
presign_path = BACKEND / "apps" / "movies" / "presign.py"
presign_content = '''"""Direct and multipart upload helpers for Backblaze B2's S3 API.

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
'''
write_if_changed(presign_path, presign_content)


# 2. Add multipart routes
urls_path = BACKEND / "apps" / "movies" / "urls.py"
replace_once(
    urls_path,
    "from .presign import PresignVideoUploadView",
    """from .presign import (
    AbortMultipartVideoUploadView,
    CompleteMultipartVideoUploadView,
    InitiateMultipartVideoUploadView,
    PresignMultipartPartView,
    PresignVideoUploadView,
)""",
    "multipart imports in movies/urls.py",
)
replace_once(
    urls_path,
    "    path('presign-video-upload/', PresignVideoUploadView.as_view(), name='presign-video-upload'),",
    """    path('presign-video-upload/', PresignVideoUploadView.as_view(), name='presign-video-upload'),
    path('multipart/initiate/', InitiateMultipartVideoUploadView.as_view(), name='multipart-initiate'),
    path('multipart/presign-part/', PresignMultipartPartView.as_view(), name='multipart-presign-part'),
    path('multipart/complete/', CompleteMultipartVideoUploadView.as_view(), name='multipart-complete'),
    path('multipart/abort/', AbortMultipartVideoUploadView.as_view(), name='multipart-abort'),""",
    "multipart routes in movies/urls.py",
)


# 3. Add frontend API methods
endpoints_path = FRONTEND / "lib" / "endpoints.ts"
replace_once(
    endpoints_path,
    """  presignVideoUpload: (filename: string, contentType: string) =>
    api.post<{ upload_url: string; key: string }>(
      '/movies/presign-video-upload/',
      { filename, content_type: contentType }
    ),""",
    """  presignVideoUpload: (filename: string, contentType: string) =>
    api.post<{ upload_url: string; key: string }>(
      '/movies/presign-video-upload/',
      { filename, content_type: contentType }
    ),

  initiateMultipartVideoUpload: (filename: string, contentType: string) =>
    api.post<{ upload_id: string; key: string }>(
      '/movies/multipart/initiate/',
      { filename, content_type: contentType }
    ),

  presignMultipartPart: (key: string, uploadId: string, partNumber: number) =>
    api.post<{ upload_url: string }>(
      '/movies/multipart/presign-part/',
      {
        key,
        upload_id: uploadId,
        part_number: partNumber,
      }
    ),

  completeMultipartVideoUpload: (
    key: string,
    uploadId: string,
    parts: Array<{ part_number: number; etag: string }>,
  ) =>
    api.post<{ key: string }>(
      '/movies/multipart/complete/',
      { key, upload_id: uploadId, parts }
    ),

  abortMultipartVideoUpload: (key: string, uploadId: string) =>
    api.post<void>(
      '/movies/multipart/abort/',
      { key, upload_id: uploadId }
    ),""",
    "multipart API methods in endpoints.ts",
)


# 4. Create frontend/lib/multipartUpload.ts
multipart_path = FRONTEND / "lib" / "multipartUpload.ts"
multipart_content = '''import { moviesApi } from '@/lib/endpoints';

const PART_SIZE = 20 * 1024 * 1024; // 20 MiB
const MAX_CONCURRENCY = 3;
const MAX_RETRIES = 3;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function uploadPart(
  url: string,
  blob: Blob,
  onProgress: (loaded: number) => void,
): Promise<string> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', url);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(event.loaded);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const etag = xhr.getResponseHeader('ETag');
        if (!etag) {
          reject(new Error('Storage did not return an ETag for the uploaded part.'));
          return;
        }
        resolve(etag.replace(/^"|"$/g, ''));
        return;
      }
      reject(new Error(`Multipart part upload failed with HTTP ${xhr.status}.`));
    };

    xhr.onerror = () => reject(new Error('Network error while uploading a video part.'));
    xhr.onabort = () => reject(new Error('Video part upload was aborted.'));
    xhr.ontimeout = () => reject(new Error('Video part upload timed out.'));
    xhr.send(blob);
  });
}

async function uploadPartWithRetry(
  url: string,
  blob: Blob,
  partNumber: number,
  onProgress: (loaded: number) => void,
): Promise<string> {
  let lastError: unknown;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt += 1) {
    try {
      console.log(`[VideoUpload] multipart part ${partNumber}: attempt ${attempt}`);
      return await uploadPart(url, blob, onProgress);
    } catch (error) {
      lastError = error;
      console.warn(
        `[VideoUpload] multipart part ${partNumber}: attempt ${attempt} failed`,
        error,
      );
      if (attempt < MAX_RETRIES) {
        await sleep(1000 * 2 ** (attempt - 1));
      }
    }
  }

  throw lastError instanceof Error
    ? lastError
    : new Error(`Multipart part ${partNumber} failed.`);
}

export async function uploadVideoMultipart(
  file: File,
  onProgress: (percent: number) => void,
): Promise<string> {
  const { upload_id: uploadId, key } =
    await moviesApi.initiateMultipartVideoUpload(
      file.name,
      file.type || 'application/octet-stream',
    );

  const partCount = Math.ceil(file.size / PART_SIZE);

  if (partCount > 10_000) {
    throw new Error('Video is too large for the multipart upload configuration.');
  }

  console.log(
    `[VideoUpload] multipart upload started: ${file.size} bytes, ${partCount} parts`,
  );

  const uploadedBytes = new Array<number>(partCount).fill(0);
  const completedParts: Array<{ part_number: number; etag: string }> = [];

  const updateProgress = () => {
    const loaded = uploadedBytes.reduce((sum, value) => sum + value, 0);
    onProgress(Math.min(100, Math.round((loaded / file.size) * 100)));
  };

  try {
    let nextPart = 1;

    async function worker() {
      while (nextPart <= partCount) {
        const partNumber = nextPart;
        nextPart += 1;

        const start = (partNumber - 1) * PART_SIZE;
        const end = Math.min(start + PART_SIZE, file.size);
        const blob = file.slice(start, end);

        const { upload_url: uploadUrl } =
          await moviesApi.presignMultipartPart(key, uploadId, partNumber);

        const etag = await uploadPartWithRetry(
          uploadUrl,
          blob,
          partNumber,
          (loaded) => {
            uploadedBytes[partNumber - 1] = loaded;
            updateProgress();
          },
        );

        uploadedBytes[partNumber - 1] = blob.size;
        completedParts.push({ part_number: partNumber, etag });
        updateProgress();
      }
    }

    const workerCount = Math.min(MAX_CONCURRENCY, partCount);
    await Promise.all(Array.from({ length: workerCount }, () => worker()));

    completedParts.sort((a, b) => a.part_number - b.part_number);

    await moviesApi.completeMultipartVideoUpload(
      key,
      uploadId,
      completedParts,
    );

    onProgress(100);
    console.log(`[VideoUpload] multipart upload completed: ${key}`);
    return key;
  } catch (error) {
    console.error(
      `[VideoUpload] multipart upload failed; aborting upload ${uploadId}`,
      error,
    );

    try {
      await moviesApi.abortMultipartVideoUpload(key, uploadId);
    } catch (abortError) {
      console.warn(
        '[VideoUpload] failed to abort unfinished multipart upload',
        abortError,
      );
    }

    throw error;
  }
}
'''
write_if_changed(multipart_path, multipart_content)


# 5. Make the Add Movie page use multipart upload for large videos
page_path = FRONTEND / "app" / "(app)" / "movies" / "add" / "page.tsx"
replace_once(
    page_path,
    "import { Input } from '@/components/ui/Input';",
    """import { Input } from '@/components/ui/Input';
import { uploadVideoMultipart } from '@/lib/multipartUpload';""",
    "multipart uploader import in add movie page",
)
replace_once(
    page_path,
    "const PRESIGN_TIMEOUT_MS = 15_000;",
    """const PRESIGN_TIMEOUT_MS = 15_000;
const MULTIPART_THRESHOLD_BYTES = 20 * 1024 * 1024;""",
    "multipart threshold in add movie page",
)

old_upload_block = """      try {
        setStatusText('Requesting upload URL...');
        log('requesting presigned upload URL...');

        const { upload_url, key } = await withTimeout(
          moviesApi.presignVideoUpload(videoFile.name, videoFile.type),
          PRESIGN_TIMEOUT_MS,
          'Requesting an upload URL'
        );

        log('got presigned URL, key:', key);
        setStatusText('Uploading video directly to storage...');
        setUploadProgress(0);

        await uploadFileDirect(upload_url, videoFile, setUploadProgress);
        videoFileKey = key;
        log('direct upload to storage complete');
      } catch (presignErr) {
        if (presignErr instanceof ApiRequestError && presignErr.status === 501) {
          // Expected in local dev - storage backend doesn't support direct
          // upload here, so fall through to the normal path below.
          log('direct upload not supported in this environment (501) - falling back to upload-through-server');
        } else {
          log('direct upload path failed:', presignErr);
          throw presignErr;
        }
      } finally {
        setUploadProgress(null);
      }"""

new_upload_block = """      try {
        setUploadProgress(0);

        if (videoFile.size > MULTIPART_THRESHOLD_BYTES) {
          // Large movies use B2/S3 multipart upload. Each part is a separate
          // direct browser->B2 request, so a network interruption only forces
          // the failed part to retry instead of restarting the entire movie.
          setStatusText('Starting multipart video upload...');
          log('using multipart upload for', videoFile.size, 'bytes');

          videoFileKey = await uploadVideoMultipart(
            videoFile,
            (percent) => setUploadProgress(percent)
          );

          log('multipart upload to storage complete, key:', videoFileKey);
        } else {
          // Small files can use the simpler single PUT path.
          setStatusText('Requesting upload URL...');
          log('requesting presigned upload URL...');

          const { upload_url, key } = await withTimeout(
            moviesApi.presignVideoUpload(videoFile.name, videoFile.type),
            PRESIGN_TIMEOUT_MS,
            'Requesting an upload URL'
          );

          log('got presigned URL, key:', key);
          setStatusText('Uploading video directly to storage...');

          await uploadFileDirect(upload_url, videoFile, setUploadProgress);
          videoFileKey = key;
          log('direct upload to storage complete');
        }
      } catch (uploadErr) {
        if (uploadErr instanceof ApiRequestError && uploadErr.status === 501) {
          // Expected in local dev - storage backend doesn't support direct
          // upload here, so fall through to Django's normal multipart path.
          log('direct/multipart upload not supported in this environment (501) - falling back to upload-through-server');
        } else {
          log('direct/multipart upload path failed:', uploadErr);
          throw uploadErr;
        }
      } finally {
        setUploadProgress(null);
      }"""

replace_once(page_path, old_upload_block, new_upload_block, "large-file multipart logic in add movie page")


# 6. Add FRONTEND_URL to production settings
production_path = BACKEND / "config" / "settings" / "production.py"
replace_once(
    production_path,
    "DEBUG = False\n",
    """DEBUG = False

# Frontend origin used by the B2 bucket CORS management command.
FRONTEND_URL = config('FRONTEND_URL', default='')
""",
    "FRONTEND_URL in production settings",
)


# 7. Expose ETag from B2 through CORS
cors_path = BACKEND / "apps" / "movies" / "management" / "commands" / "configure_b2_cors.py"
replace_once(
    cors_path,
    "                    'AllowedHeaders': ['*'],\n                    'MaxAgeSeconds': 3600,",
    """                    'AllowedHeaders': ['*'],
                    # Multipart completion needs the browser to read the
                    # ETag returned by each uploaded part.
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3600,""",
    "ETag exposure in B2 CORS configuration",
)

print()
print("=" * 72)
print("Multipart upload patch applied successfully.")
print("=" * 72)
print()
print("Next steps:")
print("1. Set FRONTEND_URL on your production Django/Render environment.")
print("2. Redeploy the backend.")
print("3. Run: python manage.py configure_b2_cors")
print("4. Redeploy the frontend.")
print("5. Test an 800 MB+ movie.")
print()
print("Large files use 20 MiB multipart parts, 3 concurrent uploads, and")
print("up to 3 attempts per part.")
