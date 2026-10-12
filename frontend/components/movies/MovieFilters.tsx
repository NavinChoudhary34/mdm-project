'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Search, SlidersHorizontal } from 'lucide-react';
import type { DsaAutocompleteItem, Genre } from '@/types';
import { dsaApi, moviesApi } from '@/lib/endpoints';
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
  const router = useRouter();

  // --- Title autocomplete (served by the backend trie) ---
  // Suggestions are stored together with the text they were fetched for. While the next request is
  // loading we keep showing the previous results (so the list doesn't flicker on every keystroke),
  // but only when the typed text is a refinement of what was fetched ("in" -> "inc" or back).
  // Unrelated text hides them, and no state has to be reset inside an effect.
  const [suggestionState, setSuggestionState] = useState<{ query: string; items: DsaAutocompleteItem[] }>({
    query: '',
    items: [],
  });
  const [isSuggestOpen, setIsSuggestOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const trimmedInput = searchInput.trim();
  const typed = trimmedInput.toLowerCase();
  const fetched = suggestionState.query.toLowerCase();
  const isRelated = fetched !== '' && (typed.startsWith(fetched) || fetched.startsWith(typed));
  const suggestions = isRelated ? suggestionState.items : [];
  const showSuggestions = isSuggestOpen && trimmedInput.length >= 2 && suggestions.length > 0;
  // The list can change length while an item is highlighted, so never point past its end.
  const highlighted = activeIndex < suggestions.length ? activeIndex : -1;

  // Always holds the newest filters, so the debounced search below never applies stale ones.
  const latestFilters = useRef(filters);
  useEffect(() => {
    latestFilters.current = filters;
  }, [filters]);

  useEffect(() => {
    moviesApi.genres().then(setGenres).catch(() => {});
  }, []);

  // Debounce the free-text search so we don't hit the API on every keystroke.
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (searchInput !== latestFilters.current.search) {
        onChange({ ...latestFilters.current, search: searchInput });
      }
    }, 350);
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput]);

  // Fetch suggestions shortly after typing stops (needs at least 2 characters).
  useEffect(() => {
    if (trimmedInput.length < 2) return;
    let stale = false;
    const timeout = setTimeout(() => {
      dsaApi
        .autocomplete(trimmedInput)
        .then((items) => {
          if (!stale) setSuggestionState({ query: trimmedInput, items });
        })
        .catch(() => {
          // Suggestions are a convenience: if they fail, normal search still works.
        });
    }, 150);
    return () => {
      stale = true;
      clearTimeout(timeout);
    };
  }, [trimmedInput]);

  // Keyboard support: arrows move through the suggestions, Enter opens the highlighted movie,
  // Escape closes the list. Enter with nothing highlighted just continues the normal search.
  function handleSearchKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!showSuggestions) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => (i + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => (i <= 0 ? suggestions.length - 1 : i - 1));
    } else if (e.key === 'Enter' && highlighted >= 0) {
      e.preventDefault();
      router.push(`/movies/${suggestions[highlighted].id}`);
    } else if (e.key === 'Escape') {
      setIsSuggestOpen(false);
    }
  }

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
            onChange={(e) => {
              setSearchInput(e.target.value);
              setIsSuggestOpen(true);
              setActiveIndex(-1);
            }}
            onFocus={() => setIsSuggestOpen(true)}
            onBlur={() => setIsSuggestOpen(false)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search movies, directors, actors…"
            role="combobox"
            aria-expanded={showSuggestions}
            aria-controls="movie-search-suggestions"
            aria-autocomplete="list"
            aria-activedescendant={highlighted >= 0 ? `movie-suggestion-${suggestions[highlighted].id}` : undefined}
            className="w-full rounded-lg border border-border bg-surface py-2 pl-9 pr-3 text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-accent/40"
          />

          {showSuggestions && (
            // onMouseDown preventDefault keeps focus in the input, otherwise the blur handler
            // would close the list before a click on a suggestion registers.
            <ul
              id="movie-search-suggestions"
              role="listbox"
              onMouseDown={(e) => e.preventDefault()}
              className="absolute left-0 right-0 top-full z-20 mt-1 overflow-hidden rounded-lg border border-border bg-surface shadow-lg"
            >
              {suggestions.map((s, i) => (
                <li key={s.id} id={`movie-suggestion-${s.id}`} role="option" aria-selected={i === highlighted}>
                  <Link
                    href={`/movies/${s.id}`}
                    className={cn(
                      'block px-3 py-2 text-sm text-foreground hover:bg-surface-raised',
                      i === highlighted && 'bg-surface-raised'
                    )}
                  >
                    {s.title}
                  </Link>
                </li>
              ))}
            </ul>
          )}
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
