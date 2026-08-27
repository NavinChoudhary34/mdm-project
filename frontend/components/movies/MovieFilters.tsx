'use client';

import { useEffect, useState } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import type { Genre } from '@/types';
import { moviesApi } from '@/lib/endpoints';
import { cn } from '@/lib/utils';

export interface MovieFilterState {
  search: string;
  genre: string;
  year: string;
  min_rating: string;
  watched: string;
  ordering: string;
}

interface MovieFiltersProps {
  filters: MovieFilterState;
  onChange: (filters: MovieFilterState) => void;
}

const SORT_OPTIONS = [
  { value: '-created_at', label: 'Recently added' },
  { value: 'title', label: 'Title (A–Z)' },
  { value: '-release_date', label: 'Newest first' },
  { value: 'release_date', label: 'Oldest first' },
  { value: '-rating', label: 'Highest rated' },
];

export function MovieFilters({ filters, onChange }: MovieFiltersProps) {
  const [genres, setGenres] = useState<Genre[]>([]);
  const [showMore, setShowMore] = useState(false);
  const [searchInput, setSearchInput] = useState(filters.search);

  useEffect(() => {
    moviesApi.genres().then(setGenres).catch(() => {});
  }, []);

  // Debounce the free-text search so we don't hit the API on every keystroke.
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (searchInput !== filters.search) {
        onChange({ ...filters, search: searchInput });
      }
    }, 350);
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput]);

  function update(patch: Partial<MovieFilterState>) {
    onChange({ ...filters, ...patch });
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-muted" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search movies, directors, actors…"
            className="w-full rounded-lg border border-border bg-surface py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-accent/40"
          />
        </div>
        <select
          value={filters.ordering}
          onChange={(e) => update({ ordering: e.target.value })}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/40"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              Sort: {opt.label}
            </option>
          ))}
        </select>
        <button
          onClick={() => setShowMore((v) => !v)}
          className={cn(
            'flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-2 text-sm transition-colors hover:bg-surface-raised',
            showMore ? 'text-accent border-accent/40' : 'text-foreground-muted'
          )}
        >
          <SlidersHorizontal size={14} /> Filters
        </button>
      </div>

      {showMore && (
        <div className="flex flex-wrap gap-2 rounded-lg border border-border bg-surface p-3">
          <select
            value={filters.genre}
            onChange={(e) => update({ genre: e.target.value })}
            className="rounded-md border border-border bg-background px-2.5 py-1.5 text-sm text-foreground"
          >
            <option value="">All genres</option>
            {genres.map((g) => (
              <option key={g.id} value={g.name}>
                {g.name}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="Year"
            value={filters.year}
            onChange={(e) => update({ year: e.target.value })}
            className="w-24 rounded-md border border-border bg-background px-2.5 py-1.5 text-sm text-foreground placeholder:text-foreground-muted"
          />
          <select
            value={filters.min_rating}
            onChange={(e) => update({ min_rating: e.target.value })}
            className="rounded-md border border-border bg-background px-2.5 py-1.5 text-sm text-foreground"
          >
            <option value="">Any rating</option>
            <option value="9">9+ rating</option>
            <option value="8">8+ rating</option>
            <option value="7">7+ rating</option>
            <option value="6">6+ rating</option>
          </select>
          <select
            value={filters.watched}
            onChange={(e) => update({ watched: e.target.value })}
            className="rounded-md border border-border bg-background px-2.5 py-1.5 text-sm text-foreground"
          >
            <option value="">Watched or not</option>
            <option value="true">Watched</option>
            <option value="false">Unwatched</option>
          </select>
          {(filters.genre || filters.year || filters.min_rating || filters.watched) && (
            <button
              onClick={() => update({ genre: '', year: '', min_rating: '', watched: '' })}
              className="text-sm text-foreground-muted underline hover:text-foreground"
            >
              Clear
            </button>
          )}
        </div>
      )}
    </div>
  );
}
