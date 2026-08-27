'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ListVideo, Plus, Lock, Globe } from 'lucide-react';
import { playlistsApi } from '@/lib/endpoints';
import type { Playlist } from '@/types';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { PlaylistCardSkeleton } from '@/components/ui/Skeleton';
import { CreatePlaylistModal } from '@/components/playlists/CreatePlaylistModal';
import { Pagination } from '@/components/ui/Pagination';
import { formatRelativeDate, getErrorMessage } from '@/lib/utils';

const PAGE_SIZE = 20;

export default function PlaylistsPage() {
  const [playlists, setPlaylists] = useState<Playlist[] | null>(null);
  const [count, setCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  function load() {
    setError(null);
    playlistsApi
      .list(page)
      .then((res) => {
        setPlaylists(res.results);
        setCount(res.count);
        setHasNext(Boolean(res.next));
        setHasPrevious(Boolean(res.previous));
      })
      .catch((err) => setError(getErrorMessage(err)));
  }

  useEffect(() => {
    queueMicrotask(load);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">My Playlists</h1>
          <p className="mt-1 text-sm text-foreground-muted">Every playlist you&apos;ve created.</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus size={16} /> Create playlist
        </Button>
      </div>

      {error && (
        <p role="alert" className="mt-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </p>
      )}

      <div className="mt-6" aria-busy={playlists === null}>
        {playlists === null ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <PlaylistCardSkeleton key={i} />
            ))}
          </div>
        ) : playlists.length === 0 ? (
          <EmptyState
            icon={<ListVideo size={32} />}
            title="No playlists yet"
            description="Create your first playlist to start organizing movies you love."
            actionLabel="Create playlist"
            onAction={() => setCreateOpen(true)}
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {playlists.map((playlist) => (
              <Link
                key={playlist.id}
                href={`/playlists/${playlist.id}`}
                className="flex flex-col rounded-xl border border-border bg-surface p-4 transition-colors hover:border-accent/40"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-medium text-foreground line-clamp-1">{playlist.name}</h3>
                  {playlist.is_public ? (
                    <Globe size={14} className="mt-1 shrink-0 text-foreground-muted" />
                  ) : (
                    <Lock size={14} className="mt-1 shrink-0 text-foreground-muted" />
                  )}
                </div>
                {playlist.description && (
                  <p className="mt-1 line-clamp-2 text-xs text-foreground-muted">{playlist.description}</p>
                )}
                <div className="mt-auto flex items-center gap-2 pt-3 font-mono text-xs text-foreground-muted">
                  <span>{playlist.movie_count} movies</span>
                  <span>•</span>
                  <span>Updated {formatRelativeDate(playlist.updated_at)}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {playlists !== null && playlists.length > 0 && (
        <Pagination page={page} hasNext={hasNext} hasPrevious={hasPrevious} onChange={setPage} totalCount={count} pageSize={PAGE_SIZE} />
      )}

      <CreatePlaylistModal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(playlist) => setPlaylists((prev) => (prev ? [playlist, ...prev] : [playlist]))}
      />
    </div>
  );
}
