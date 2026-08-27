'use client';

import { useEffect, useState } from 'react';
import { Heart } from 'lucide-react';
import { libraryApi } from '@/lib/endpoints';
import type { Favorite } from '@/types';
import { MovieGrid } from '@/components/movies/MovieGrid';
import { MovieGridSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Pagination } from '@/components/ui/Pagination';
import { getErrorMessage } from '@/lib/utils';

const PAGE_SIZE = 20;

export default function FavoritesPage() {
  const [entries, setEntries] = useState<Favorite[] | null>(null);
  const [count, setCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      setError(null);
      libraryApi
        .favorites(page)
        .then((res) => {
          if (cancelled) return;
          setEntries(res.results);
          setCount(res.count);
          setHasNext(Boolean(res.next));
          setHasPrevious(Boolean(res.previous));
        })
        .catch((err) => !cancelled && setError(getErrorMessage(err)));
    });
    return () => {
      cancelled = true;
    };
  }, [page]);

  return (
    <div className="mx-auto max-w-7xl">
      <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">Favorites</h1>
      <p className="mt-1 text-sm text-foreground-muted">The movies you&apos;ve marked as favorites.</p>

      {error && (
        <p role="alert" className="mt-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </p>
      )}

      <div className="mt-6" aria-busy={entries === null}>
        {entries === null ? (
          <MovieGridSkeleton />
        ) : entries.length === 0 ? (
          <EmptyState
            icon={<Heart size={32} />}
            title="No favorites yet"
            description="Tap the heart on any movie to add it here."
          />
        ) : (
          <MovieGrid movies={entries.map((e) => e.movie)} />
        )}
      </div>

      {entries !== null && entries.length > 0 && (
        <Pagination page={page} hasNext={hasNext} hasPrevious={hasPrevious} onChange={setPage} totalCount={count} pageSize={PAGE_SIZE} />
      )}
    </div>
  );
}
