'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { moviesApi } from '@/lib/endpoints';
import { ApiRequestError } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function AddMoviePage() {
  const router = useRouter();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [releaseDate, setReleaseDate] = useState('');
  const [runtime, setRuntime] = useState('');
  const [rating, setRating] = useState('');
  const [posterUrl, setPosterUrl] = useState('');
  const [backdropUrl, setBackdropUrl] = useState('');
  const [visibility, setVisibility] = useState<'public' | 'private'>('private');
  const [videoFile, setVideoFile] = useState<File | null>(null);

  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    setError('');

    if (!videoFile) {
      setError('Please select a video file.');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a movie title.');
      return;
    }

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

    if (posterUrl) {
      formData.append('poster_url', posterUrl);
    }

    if (backdropUrl) {
      formData.append('backdrop_url', backdropUrl);
    }

    formData.append('video_file', videoFile);

    setIsSubmitting(true);

    try {
      await moviesApi.create(formData);

      router.push('/movies/my');
      router.refresh();
    } catch (err) {
      if (err instanceof ApiRequestError) {
        const body = err.body;

        if (body.detail) {
          setError(body.detail);
        } else {
          const firstError = Object.values(body)[0];

          if (Array.isArray(firstError)) {
            setError(String(firstError[0]));
          } else {
            setError(String(firstError ?? 'Failed to upload movie.'));
          }
        }
      } else {
        setError('Failed to upload movie.');
      }
    } finally {
      setIsSubmitting(false);
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

          <Input
            label="Poster URL"
            type="url"
            value={posterUrl}
            onChange={(e) => setPosterUrl(e.target.value)}
            placeholder="https://..."
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