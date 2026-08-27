'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Film, Lock } from 'lucide-react';
import { playlistsApi } from '@/lib/endpoints';
import type { Playlist } from '@/types';
import { Skeleton } from '@/components/ui/Skeleton';
import { formatYear, getErrorMessage } from '@/lib/utils';

/**
 * Read-only, unauthenticated view of a playlist its owner has marked public.
 * Deliberately has no favorite/watchlist/rating actions — those all require
 * an account, and this route is reachable by anyone with the link.
 */
export default function PublicPlaylistPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const playlistId = Number(id);

  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    playlistsApi
      .publicDetail(playlistId)
      .then((data) => !cancelled && setPlaylist(data))
      .catch((err) => !cancelled && setError(getErrorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [playlistId]);

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
        <Lock size={32} className="text-foreground-muted" />
        <h1 className="mt-4 font-display text-xl font-medium text-foreground">This playlist isn&apos;t available</h1>
        <p className="mt-2 max-w-sm text-sm text-foreground-muted">
          It may be private, or the link may be incorrect.
        </p>
        <Link href="/login" className="mt-6 text-sm text-accent hover:underline">
          Go to Movie Manager
        </Link>
      </div>
    );
  }

  if (!playlist) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="mt-3 h-4 w-1/2" />
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[2/3]" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-4xl px-4 py-10">
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-accent">
          <Film size={14} /> Shared playlist
        </div>
        <h1 className="mt-2 font-display text-2xl font-medium text-foreground sm:text-3xl">{playlist.name}</h1>
        {playlist.description && <p className="mt-2 max-w-xl text-sm text-foreground-muted">{playlist.description}</p>}
        <p className="mt-2 font-mono text-xs text-foreground-muted">
          By {playlist.owner_username} • {playlist.movie_count} movies
        </p>

        {!playlist.movies || playlist.movies.length === 0 ? (
          <p className="mt-10 text-sm text-foreground-muted">This playlist doesn&apos;t have any movies yet.</p>
        ) : (
          <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
            {playlist.movies.map((entry) => (
              <div key={entry.movie.id} className="flex flex-col">
                <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-surface">
                  {entry.movie.poster_url ? (
                    <Image
                      src={entry.movie.poster_url}
                      alt={entry.movie.title}
                      fill
                      sizes="(min-width: 768px) 25vw, (min-width: 640px) 33vw, 50vw"
                      className="object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-xs text-foreground-muted">No poster</div>
                  )}
                </div>
                <p className="mt-2 truncate text-sm font-medium text-foreground">{entry.movie.title}</p>
                <p className="font-mono text-xs text-foreground-muted">{formatYear(entry.movie.release_date)}</p>
              </div>
            ))}
          </div>
        )}

        <div className="mt-12 border-t border-border pt-6 text-center">
          <p className="text-sm text-foreground-muted">
            Want to build your own playlists?{' '}
            <Link href="/register" className="text-accent hover:underline">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
