'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Plus, Play, Trash2 } from 'lucide-react';

import { moviesApi } from '@/lib/endpoints';
import { ApiRequestError } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { getErrorMessage } from '@/lib/utils';

import type { Movie, Paginated } from '@/types';

export default function MyMoviesPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function loadMovies() {
    setLoading(true);
    setError(null);

    try {
      const data = await moviesApi.myMovies();

      setMovies(data.results);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMovies();
  }, []);

  async function deleteMovie(id: number) {
    const confirmed = window.confirm(
      'Are you sure you want to delete this movie?'
    );

    if (!confirmed) return;

    setDeletingId(id);

    try {
      await moviesApi.remove(id);

      setMovies((current) =>
        current.filter((movie) => movie.id !== id)
      );
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <main className="mx-auto max-w-6xl pb-16">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-display text-3xl font-medium text-foreground">
            My Movies
          </h1>

          <p className="mt-2 text-sm text-foreground-muted">
            Movies you have uploaded to your personal library.
          </p>
        </div>

        <Link href="/movies/add">
          <Button>
            <Plus size={16} />
            Add Movie
          </Button>
        </Link>
      </div>

      {error && (
        <div className="mt-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {loading ? (
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index}>
              <Skeleton className="aspect-[2/3] w-full rounded-xl" />
              <Skeleton className="mt-3 h-5 w-3/4" />
              <Skeleton className="mt-2 h-4 w-1/2" />
            </div>
          ))}
        </div>
      ) : movies.length === 0 ? (
        <div className="mt-10 rounded-xl border border-border bg-surface px-6 py-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-background">
            <Plus size={22} className="text-foreground-muted" />
          </div>

          <h2 className="mt-4 font-display text-xl font-medium text-foreground">
            No movies yet
          </h2>

          <p className="mx-auto mt-2 max-w-md text-sm text-foreground-muted">
            You haven't uploaded any movies yet. Add your first movie to
            start building your personal library.
          </p>

          <Link href="/movies/add" className="mt-5 inline-block">
            <Button>
              <Plus size={16} />
              Add your first movie
            </Button>
          </Link>
        </div>
      ) : (
        <div className="mt-8 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4">
          {movies.map((movie) => (
            <article key={movie.id} className="group">
              <Link href={`/movies/${movie.id}`}>
                <div className="relative aspect-[2/3] overflow-hidden rounded-xl border border-border bg-surface">
                  {movie.poster_url ? (
                    <Image
                      src={movie.poster_url}
                      alt={movie.title}
                      fill
                      sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
                      className="object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-sm text-foreground-muted">
                      No poster
                    </div>
                  )}

                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 pt-10">
                    <div className="flex items-center gap-1.5 text-xs text-white">
                      <Play size={12} fill="currentColor" />
                      Uploaded movie
                    </div>
                  </div>
                </div>
              </Link>

              <div className="mt-3">
                <div className="flex items-start justify-between gap-2">
                  <Link
                    href={`/movies/${movie.id}`}
                    className="min-w-0"
                  >
                    <h2 className="truncate font-medium text-foreground hover:text-accent">
                      {movie.title}
                    </h2>
                  </Link>

                  <button
                    type="button"
                    onClick={() => deleteMovie(movie.id)}
                    disabled={deletingId === movie.id}
                    className="shrink-0 rounded-md p-1.5 text-foreground-muted hover:bg-danger/10 hover:text-danger disabled:opacity-50"
                    title="Delete movie"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>

                <div className="mt-1 flex items-center gap-2 text-xs text-foreground-muted">
                  {movie.visibility && (
                    <span className="capitalize">
                      {movie.visibility}
                    </span>
                  )}

                  {movie.release_year && (
                    <>
                      <span>•</span>
                      <span>{movie.release_year}</span>
                    </>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}