'use client';

import { memo, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Heart, ListPlus, CheckCircle2, Star } from 'lucide-react';
import type { Movie } from '@/types';
import { libraryApi } from '@/lib/endpoints';
import { useToast } from '@/hooks/useToast';
import { cn, formatYear, getErrorMessage } from '@/lib/utils';
import { AddToPlaylistModal } from '../playlists/AddToPlaylistModal';

interface MovieCardProps {
  movie: Movie;
}

function MovieCardComponent({ movie }: MovieCardProps) {
  const { showToast } = useToast();
  const [isFavorited, setIsFavorited] = useState(movie.is_favorited);
  const [isWatched, setIsWatched] = useState(movie.is_watched);
  const [busy, setBusy] = useState(false);
  const [playlistModalOpen, setPlaylistModalOpen] = useState(false);

  async function toggleFavorite(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (busy) return;
    setBusy(true);
    const next = !isFavorited;
    setIsFavorited(next); // optimistic
    try {
      if (next) {
        await libraryApi.addFavorite(movie.id);
      } else {
        await libraryApi.removeFavorite(movie.id);
      }
    } catch (err) {
      setIsFavorited(!next); // revert
      showToast(getErrorMessage(err), 'error');
    } finally {
      setBusy(false);
    }
  }

  async function toggleWatched(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (busy) return;
    setBusy(true);
    const next = !isWatched;
    setIsWatched(next);
    try {
      if (next) {
        await libraryApi.markWatched(movie.id);
      } else {
        await libraryApi.markUnwatched(movie.id);
      }
    } catch (err) {
      setIsWatched(!next);
      showToast(getErrorMessage(err), 'error');
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Link
        href={`/movies/${movie.id}`}
        className="group flex flex-col overflow-hidden rounded-xl border border-border bg-surface transition-colors hover:border-accent/40"
      >
        <div className="relative aspect-[2/3] w-full overflow-hidden bg-surface-raised">
          {movie.poster_url ? (
            <Image
              src={movie.poster_url}
              alt={movie.title}
              fill
              sizes="(max-width: 768px) 45vw, 200px"
              className="object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-foreground-muted">
              No poster
            </div>
          )}
          {isWatched && (
            <div className="absolute right-2 top-2 rounded-full bg-success/90 p-1">
              <CheckCircle2 size={14} className="text-white" />
            </div>
          )}
        </div>
        <div className="flex flex-1 flex-col gap-1 p-3">
          <h3 className="line-clamp-1 text-sm font-semibold text-foreground">{movie.title}</h3>
          <div className="flex items-center gap-2 text-xs text-foreground-muted">
            <span>{formatYear(movie.release_date)}</span>
            {movie.rating && (
              <span className="flex items-center gap-0.5">
                <Star size={11} className="fill-warning text-warning" />
                {movie.rating}
              </span>
            )}
          </div>
          {movie.genres.length > 0 && (
            <p className="line-clamp-1 text-xs text-foreground-muted">
              {movie.genres.map((g) => g.name).join(' • ')}
            </p>
          )}
          <div className="mt-auto flex items-center gap-1 pt-2">
            <button
              onClick={toggleFavorite}
              className={cn(
                'icon-btn-focus rounded-md p-1.5 transition-colors hover:bg-surface-raised',
                isFavorited ? 'text-accent' : 'text-foreground-muted'
              )}
              aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
            >
              <Heart size={16} className={isFavorited ? 'fill-accent' : ''} />
            </button>
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setPlaylistModalOpen(true);
              }}
              className="icon-btn-focus rounded-md p-1.5 text-foreground-muted transition-colors hover:bg-surface-raised hover:text-foreground"
              aria-label="Add to playlist"
            >
              <ListPlus size={16} />
            </button>
            <button
              onClick={toggleWatched}
              className={cn(
                'icon-btn-focus ml-auto rounded-md p-1.5 transition-colors hover:bg-surface-raised',
                isWatched ? 'text-success' : 'text-foreground-muted'
              )}
              aria-label={isWatched ? 'Mark unwatched' : 'Mark watched'}
            >
              <CheckCircle2 size={16} className={isWatched ? 'fill-success/20' : ''} />
            </button>
          </div>
        </div>
      </Link>
      <AddToPlaylistModal
        isOpen={playlistModalOpen}
        onClose={() => setPlaylistModalOpen(false)}
        movieId={movie.id}
        movieTitle={movie.title}
      />
    </>
  );
}

export const MovieCard = memo(MovieCardComponent);
