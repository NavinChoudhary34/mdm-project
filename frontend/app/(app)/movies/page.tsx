'use client';

import { useEffect, useState } from 'react';
import { moviesApi, type MovieFilters } from '@/lib/endpoints';
import { MovieFilters as MovieFiltersBar, type MovieFilterState } from '@/components/movies/MovieFilters';
import { MovieGrid } from '@/components/movies/MovieGrid';
import { MovieGridSkeleton } from '@/components/ui/Skeleton';
import { Pagination } from '@/components/ui/Pagination';
import type { Movie } from '@/types';
import { getErrorMessage } from '@/lib/utils';

const DEFAULT_FILTERS: MovieFilterState = {
  search: '',
  genre: '',
  year: '',
  min_rating: '',
  watched: '',
  ordering: '-created_at',
};

const PAGE_SIZE = 20;

export default function MoviesPage() {
  const [filters, setFilters] = useState<MovieFilterState>(DEFAULT_FILTERS);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [count, setCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters changing means the result set changed shape — always jump back to page 1.
  useEffect(() => {
    queueMicrotask(() => setPage(1));
  }, [filters]);

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      if (cancelled) return;
      setIsLoading(true);
      setError(null);

      const apiFilters: MovieFilters = {
        search: filters.search || undefined,
        genre: filters.genre || undefined,
        year: filters.year ? Number(filters.year) : undefined,
        min_rating: filters.min_rating ? Number(filters.min_rating) : undefined,
        watched: filters.watched ? filters.watched === 'true' : undefined,
        ordering: filters.ordering,
        page,
      };

      moviesApi
        .list(apiFilters)
        .then((res) => {
          if (cancelled) return;
          setMovies(res.results);
          setCount(res.count);
          setHasNext(Boolean(res.next));
          setHasPrevious(Boolean(res.previous));
        })
        .catch((err) => {
          if (!cancelled) setError(getErrorMessage(err));
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    });

    return () => {
      cancelled = true;
    };
  }, [filters, page]);

  return (
    <div className="mx-auto max-w-7xl">
      <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">Movies</h1>
      <p className="mt-1 text-sm text-foreground-muted">Browse the full catalog and find something to watch.</p>

      <div className="mt-6">
        <MovieFiltersBar filters={filters} onChange={setFilters} />
      </div>

      {error && (
        <p role="alert" className="mt-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </p>
      )}

      <div className="mt-6" aria-busy={isLoading}>
        {isLoading ? <MovieGridSkeleton /> : <MovieGrid movies={movies} />}
      </div>

      {!isLoading && (
        <Pagination
          page={page}
          hasNext={hasNext}
          hasPrevious={hasPrevious}
          onChange={setPage}
          totalCount={count}
          pageSize={PAGE_SIZE}
        />
      )}
    </div>
  );
}
