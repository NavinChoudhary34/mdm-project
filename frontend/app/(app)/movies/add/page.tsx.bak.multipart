'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { moviesApi } from '@/lib/endpoints';
import { ApiRequestError } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

const PRESIGN_TIMEOUT_MS = 15_000;
// If no upload progress event has fired within this long after the PUT
// starts, something is stuck (a hung connection, a CORS block that never
// resolved, etc.) - fail loudly instead of spinning forever.
const NO_PROGRESS_TIMEOUT_MS = 20_000;

function log(...args: unknown[]) {
  console.log('[VideoUpload]', ...args);
}

/**
 * PUTs a file straight to a presigned storage URL (bypassing Django
 * entirely for the bytes), reporting progress along the way. Uses XHR
 * rather than fetch because fetch has no upload-progress event.
 *
 * Guards against silently hanging forever: if no progress event fires
 * within NO_PROGRESS_TIMEOUT_MS of starting, aborts and reports a clear
 * error rather than leaving the UI spinning with no explanation.
 */
function uploadFileDirect(
  url: string,
  file: File,
  onProgress: (percent: number) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    let sawProgress = false;

    const watchdog = setTimeout(() => {
      if (!sawProgress) {
        log('direct upload: no progress event within', NO_PROGRESS_TIMEOUT_MS, 'ms - aborting');
        xhr.abort();
        reject(new Error(
          `Upload to storage stalled - no data was sent within ${NO_PROGRESS_TIMEOUT_MS / 1000}s. ` +
          'This usually means the storage bucket is blocking the request (check its CORS settings) ' +
          'or the network connection dropped.'
        ));
      }
    }, NO_PROGRESS_TIMEOUT_MS);

    xhr.open('PUT', url);
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');

    xhr.upload.onprogress = (e) => {
      sawProgress = true;
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        onProgress(percent);
        if (percent % 10 === 0) log('direct upload progress:', percent + '%');
      }
    };

    xhr.onload = () => {
      clearTimeout(watchdog);
      log('direct upload finished, status:', xhr.status);
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(
          `Upload to storage failed (HTTP ${xhr.status}). ` +
          (xhr.responseText ? `Response: ${xhr.responseText.slice(0, 300)}` : '')
        ));
      }
    };

    xhr.onerror = () => {
      clearTimeout(watchdog);
      log('direct upload: network error (xhr.onerror fired)');
      reject(new Error(
        'Upload to storage failed due to a network error - this often means the storage ' +
        "bucket's CORS configuration is blocking uploads from this site's origin."
      ));
    };

    xhr.onabort = () => {
      clearTimeout(watchdog);
    };

    log('direct upload: starting PUT to storage, file size:', file.size, 'bytes');
    xhr.send(file);
  });
}

/** Wraps a promise with a hard timeout so a hung request fails loudly instead of forever. */
function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`${label} timed out after ${ms / 1000}s - the request never got a response.`));
    }, ms);

    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (err) => {
        clearTimeout(timer);
        reject(err);
      }
    );
  });
}

export default function AddMoviePage() {
  const router = useRouter();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [releaseDate, setReleaseDate] = useState('');
  const [runtime, setRuntime] = useState('');
  const [rating, setRating] = useState('');
  const [posterUrl, setPosterUrl] = useState('');
  const [posterImage, setPosterImage] = useState<File | null>(null);
  const [backdropUrl, setBackdropUrl] = useState('');
  const [visibility, setVisibility] = useState<'public' | 'private'>('private');
  const [videoFile, setVideoFile] = useState<File | null>(null);

  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [statusText, setStatusText] = useState('');

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    setError('');
    setStatusText('');

    if (!videoFile) {
      setError('Please select a video file.');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a movie title.');
      return;
    }

    setIsSubmitting(true);
    log('submit started. file:', videoFile.name, videoFile.size, 'bytes, type:', videoFile.type || '(none)');

    try {
      // For a movie-length file, sending it through Django (which would
      // then re-upload it to storage itself) reliably exceeds server
      // request timeouts. So: ask for a direct upload URL first, and if
      // storage supports it, upload straight there instead - the file
      // never touches our own server. Local dev has no such storage
      // backend (presign returns 501), so it falls back to the old
      // all-in-one-request path, which is fine for small local files.
      let videoFileKey: string | null = null;

      try {
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
      }

      setStatusText(videoFileKey ? 'Saving movie details...' : 'Uploading movie (this may take a while for large files)...');

      const formData = new FormData();

      formData.append('title', title);
      formData.append('description', description);
      formData.append('visibility', visibility);

      if (releaseDate) {
        formData.append('release_date', releaseDate);
      }

      if (runtime) {
        formData.append('runtime_minutes', runtime);
      }

      if (rating) {
        formData.append('rating', rating);
      }

      // An uploaded poster image takes priority over a pasted URL
      // (enforced on the backend too), so only send the URL when
      // there's no file.
      if (posterImage) {
        formData.append('poster_image', posterImage);
      } else if (posterUrl) {
        formData.append('poster_url', posterUrl);
      }

      if (backdropUrl) {
        formData.append('backdrop_url', backdropUrl);
      }

      if (videoFileKey) {
        formData.append('video_file_key', videoFileKey);
      } else {
        formData.append('video_file', videoFile);
      }

      log('submitting movie record, using', videoFileKey ? 'video_file_key (already in storage)' : 'video_file (uploading through server)');
      await moviesApi.create(formData);
      log('movie created successfully');

      router.push('/movies/my');
      router.refresh();
    } catch (err) {
      log('submit failed:', err);

      if (err instanceof Error && !(err instanceof ApiRequestError)) {
        // Our own descriptive errors from withTimeout/uploadFileDirect.
        setError(err.message);
      } else if (err instanceof ApiRequestError) {
        const body = err.body;

        if (body?.detail) {
          setError(String(body.detail));
        } else if (body) {
          const firstError = Object.values(body)[0];

          if (Array.isArray(firstError)) {
            setError(String(firstError[0]));
          } else {
            setError(String(firstError ?? 'Failed to upload movie.'));
          }
        } else {
          setError(`Failed to upload movie (HTTP ${err.status}).`);
        }
      } else {
        setError('Failed to upload movie - see the browser console for details.');
      }
    } finally {
      setIsSubmitting(false);
      setStatusText('');
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <div className="mb-8">
          <Link
            href="/movies/my"
            className="text-sm text-foreground-muted hover:text-foreground"
          >
            ← Back to My Movies
          </Link>

          <h1 className="mt-4 font-display text-3xl font-medium text-foreground">
            Add Movie
          </h1>

          <p className="mt-2 text-sm text-foreground-muted">
            Upload a movie to your personal library.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-5 rounded-xl border border-border bg-card p-6"
        >
          <Input
            label="Movie title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">
              Description
            </label>

            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
              placeholder="Enter a description..."
            />
          </div>

          <Input
            label="Release date"
            type="date"
            value={releaseDate}
            onChange={(e) => setReleaseDate(e.target.value)}
          />

          <Input
            label="Runtime (minutes)"
            type="number"
            min="1"
            value={runtime}
            onChange={(e) => setRuntime(e.target.value)}
          />

          <Input
            label="Rating"
            type="number"
            min="0"
            max="10"
            step="0.1"
            value={rating}
            onChange={(e) => setRating(e.target.value)}
          />

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">
              Poster image
            </label>

            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                setPosterImage(e.target.files?.[0] ?? null);
              }}
              className="block w-full rounded-lg border border-border bg-background p-3 text-sm text-foreground"
            />

            {posterImage && (
              <p className="mt-2 text-xs text-foreground-muted">
                Selected: {posterImage.name}
              </p>
            )}
          </div>

          <Input
            label="Poster URL"
            type="url"
            value={posterUrl}
            onChange={(e) => setPosterUrl(e.target.value)}
            placeholder="https://... (ignored if you upload an image above)"
            disabled={!!posterImage}
          />

          <Input
            label="Backdrop URL"
            type="url"
            value={backdropUrl}
            onChange={(e) => setBackdropUrl(e.target.value)}
            placeholder="https://..."
          />

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">
              Video file
            </label>

            <input
              type="file"
              accept="video/*"
              onChange={(e) => {
                setVideoFile(e.target.files?.[0] ?? null);
              }}
              className="block w-full rounded-lg border border-border bg-background p-3 text-sm text-foreground"
              required
            />

            {videoFile && (
              <p className="mt-2 text-xs text-foreground-muted">
                Selected: {videoFile.name}
              </p>
            )}
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">
              Visibility
            </label>

            <select
              value={visibility}
              onChange={(e) =>
                setVisibility(e.target.value as 'public' | 'private')
              }
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground"
            >
              <option value="private">
                Private — only I can see it
              </option>

              <option value="public">
                Public — other users can see it
              </option>
            </select>
          </div>

          {isSubmitting && statusText && uploadProgress === null && (
            <p className="text-xs text-foreground-muted">{statusText}</p>
          )}

          {uploadProgress !== null && (
            <div>
              <div className="mb-1 flex justify-between text-xs text-foreground-muted">
                <span>{statusText || 'Uploading video...'}</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-surface-raised">
                <div
                  className="h-full rounded-full bg-accent transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
              {error}
            </div>
          )}

          <Button
            type="submit"
            isLoading={isSubmitting}
            className="w-full justify-center"
          >
            Upload Movie
          </Button>
        </form>
      </div>
    </main>
  );
}
