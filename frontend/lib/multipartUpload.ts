import { moviesApi } from '@/lib/endpoints';

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
