'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Film, Plus } from 'lucide-react';

import { moviesApi } from '@/lib/endpoints';
import type { Movie } from '@/types';
import { MovieFilters, type MovieFilterState } from '@/components/movies/MovieFilters';
import { MovieGrid } from '@/components/movies/MovieGrid';
import { MovieGridSkeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { getErrorMessage } from '@/lib/utils';

const PAGE_SIZE = 20;

const DEFAULT_FILTERS: MovieFilterState = {
  search: '',
  genre: '',
  year: '',
  min_rating: '',
  watched: '',
  ordering: '-created_at',
};

export default function MoviesPage() {
  const [filters, setFilters] = useState<MovieFilterState>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);

  const [movies, setMovies] = useState<Movie[] | null>(null);
  const [count, setCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Any filter change should reset back to page 1.
  function handleFiltersChange(next: MovieFilterState) {
    setFilters(next);
    setPage(1);
  }

  useEffect(() => {
    let cancelled = false;

    setError(null);
    setMovies(null);

    moviesApi
      .list({
        search: filters.search || undefined,
        genre: filters.genre || undefined,
        year: filters.year ? Number(filters.year) : undefined,
        min_rating: filters.min_rating ? Number(filters.min_rating) : undefined,
        watched: filters.watched ? filters.watched === 'true' : undefined,
        ordering: filters.ordering || undefined,
        page,
      })
      .then((res) => {
        if (cancelled) return;
        setMovies(res.results);
        setCount(res.count);
        setHasNext(Boolean(res.next));
        setHasPrevious(Boolean(res.previous));
      })
      .catch((err) => {
        if (cancelled) return;
        setError(getErrorMessage(err));
      });

    return () => {
      cancelled = true;
    };
  }, [filters, page]);

  return (
    <div className="mx-auto max-w-7xl">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">Movies</h1>
          <p className="mt-1 text-sm text-foreground-muted">Browse the catalog and everyone&apos;s public uploads.</p>
        </div>

        <Link href="/movies/add">
          <Button className="gap-1.5">
            <Plus size={16} /> Add movie
          </Button>
        </Link>
      </div>

      <div className="mt-6">
        <MovieFilters filters={filters} onChange={handleFiltersChange} />
      </div>

      {error && (
        <p role="alert" className="mt-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </p>
      )}

      <div className="mt-6" aria-busy={movies === null}>
        {movies === null ? (
          <MovieGridSkeleton />
        ) : movies.length === 0 ? (
          <EmptyState
            icon={<Film size={32} />}
            title="No movies found"
            description="Try adjusting your search or filters."
          />
        ) : (
          <MovieGrid movies={movies} />
        )}
      </div>

      {movies !== null && movies.length > 0 && (
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
