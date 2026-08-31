'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { libraryApi } from '@/lib/endpoints';
import { ApiRequestError } from '@/lib/api';
import type { DashboardData } from '@/types';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const dashboard = await libraryApi.dashboard();
        setData(dashboard);
      } catch (err) {
        if (err instanceof ApiRequestError) {
          setError(err.message);
        } else {
          setError('Unable to load dashboard.');
        }
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <div className="mb-8">
          <h1 className="font-display text-3xl font-medium text-foreground">
            Dashboard
          </h1>
          <p className="mt-2 text-sm text-foreground-muted">
            Loading your movie library...
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-28 animate-pulse rounded-xl border border-border bg-surface"
            />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="font-display text-3xl font-medium text-foreground">
          Dashboard
        </h1>

        <div className="mt-6 rounded-xl border border-danger/30 bg-danger/10 p-4">
          <p className="text-sm text-danger">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const { stats } = data;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-3xl font-medium text-foreground">
          Dashboard
        </h1>

        <p className="mt-2 text-sm text-foreground-muted">
          Manage your movies, playlists, watchlist and favorites.
        </p>
      </div>

      {/* Quick actions */}
      <div className="mb-8 flex flex-wrap gap-3">
        <Link
          href="/movies"
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
        >
          Browse Movies
        </Link>

        <Link
          href="/movies/add"
          className="rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-hover"
        >
          Add Movie
        </Link>

        <Link
          href="/playlists"
          className="rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-hover"
        >
          My Playlists
        </Link>
      </div>

      {/* Statistics */}
      <section>
        <h2 className="mb-4 font-display text-xl font-medium text-foreground">
          Your Library
        </h2>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Movies"
            value={stats.total_movies}
            href="/movies"
          />

          <StatCard
            label="Playlists"
            value={stats.total_playlists}
            href="/playlists"
          />

          <StatCard
            label="Watched"
            value={stats.movies_watched}
            href="/watched"
          />

          <StatCard
            label="Favorites"
            value={stats.favorite_count}
            href="/favorites"
          />
        </div>
      </section>

      {/* Watchlist */}
      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-display text-xl font-medium text-foreground">
              Watchlist
            </h2>

            <p className="mt-1 text-sm text-foreground-muted">
              Movies you want to watch.
            </p>
          </div>

          <Link
            href="/watchlist"
            className="text-sm text-accent hover:underline"
          >
            View all
          </Link>
        </div>

        <div className="rounded-xl border border-border bg-surface p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-foreground-muted">
                Movies in your watchlist
              </p>

              <p className="mt-1 text-2xl font-semibold text-foreground">
                {stats.watchlist_count}
              </p>
            </div>

            <Link
              href="/watchlist"
              className="rounded-lg border border-border px-4 py-2 text-sm text-foreground hover:bg-surface-hover"
            >
              Open Watchlist
            </Link>
          </div>
        </div>
      </section>

      {/* Recent favorites */}
      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-display text-xl font-medium text-foreground">
              Recent Favorites
            </h2>

            <p className="mt-1 text-sm text-foreground-muted">
              Movies you recently added to favorites.
            </p>
          </div>

          <Link
            href="/favorites"
            className="text-sm text-accent hover:underline"
          >
            View all
          </Link>
        </div>

        {data.recent_favorites.length === 0 ? (
          <div className="rounded-xl border border-border bg-surface p-6 text-center">
            <p className="text-sm text-foreground-muted">
              You haven't added any favorites yet.
            </p>

            <Link
              href="/movies"
              className="mt-3 inline-block text-sm text-accent hover:underline"
            >
              Browse movies
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {data.recent_favorites.slice(0, 4).map((movie) => (
              <MovieCard
                key={movie.id}
                id={movie.id}
                title={movie.title}
                posterUrl={movie.poster_url}
              />
            ))}
          </div>
        )}
      </section>

      {/* Recently watched */}
      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-display text-xl font-medium text-foreground">
              Recently Watched
            </h2>

            <p className="mt-1 text-sm text-foreground-muted">
              Movies you've recently watched.
            </p>
          </div>

          <Link
            href="/watched"
            className="text-sm text-accent hover:underline"
          >
            View all
          </Link>
        </div>

        {data.recently_watched.length === 0 ? (
          <div className="rounded-xl border border-border bg-surface p-6 text-center">
            <p className="text-sm text-foreground-muted">
              You haven't watched any movies yet.
            </p>

            <Link
              href="/movies"
              className="mt-3 inline-block text-sm text-accent hover:underline"
            >
              Browse movies
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {data.recently_watched.slice(0, 4).map((movie) => (
              <MovieCard
                key={movie.id}
                id={movie.id}
                title={movie.title}
                posterUrl={movie.poster_url}
              />
            ))}
          </div>
        )}
      </section>

      {/* Recently updated playlists */}
      <section className="mt-10 pb-10">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-display text-xl font-medium text-foreground">
              Recently Updated Playlists
            </h2>

            <p className="mt-1 text-sm text-foreground-muted">
              Your latest playlist activity.
            </p>
          </div>

          <Link
            href="/playlists"
            className="text-sm text-accent hover:underline"
          >
            View all
          </Link>
        </div>

        {data.recently_updated_playlists.length === 0 ? (
          <div className="rounded-xl border border-border bg-surface p-6 text-center">
            <p className="text-sm text-foreground-muted">
              You haven't created any playlists yet.
            </p>

            <Link
              href="/playlists"
              className="mt-3 inline-block text-sm text-accent hover:underline"
            >
              Create a playlist
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data.recently_updated_playlists.slice(0, 6).map((playlist) => (
              <Link
                key={playlist.id}
                href={`/playlists/${playlist.id}`}
                className="rounded-xl border border-border bg-surface p-5 transition-colors hover:bg-surface-hover"
              >
                <h3 className="font-medium text-foreground">
                  {playlist.name}
                </h3>

                <p className="mt-2 text-xs text-foreground-muted">
                  Updated{' '}
                  {new Date(playlist.updated_at).toLocaleDateString()}
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({
  label,
  value,
  href,
}: {
  label: string;
  value: number;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="rounded-xl border border-border bg-surface p-5 transition-colors hover:bg-surface-hover"
    >
      <p className="text-sm text-foreground-muted">{label}</p>

      <p className="mt-2 text-3xl font-semibold text-foreground">
        {value}
      </p>
    </Link>
  );
}

function MovieCard({
  id,
  title,
  posterUrl,
}: {
  id: number;
  title: string;
  posterUrl: string;
}) {
  return (
    <Link
      href={`/movies/${id}`}
      className="overflow-hidden rounded-xl border border-border bg-surface transition-transform hover:-translate-y-1"
    >
      <div className="aspect-[2/3] bg-background">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center px-4 text-center">
            <span className="text-sm text-foreground-muted">
              No poster
            </span>
          </div>
        )}
      </div>

      <div className="p-4">
        <h3 className="line-clamp-2 text-sm font-medium text-foreground">
          {title}
        </h3>
      </div>
    </Link>
  );
}