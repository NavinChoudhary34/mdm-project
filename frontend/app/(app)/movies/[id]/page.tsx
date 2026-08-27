'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowLeft, Heart, ListPlus, CheckCircle2, Bookmark, Star } from 'lucide-react';
import { moviesApi, libraryApi } from '@/lib/endpoints';
import { useToast } from '@/hooks/useToast';
import { formatRuntime, formatYear, getErrorMessage } from '@/lib/utils';
import type { Movie } from '@/types';
import { Button } from '@/components/ui/Button';
import { StarRating } from '@/components/ui/StarRating';
import { Textarea } from '@/components/ui/Input';
import { AddToPlaylistModal } from '@/components/playlists/AddToPlaylistModal';
import { Skeleton } from '@/components/ui/Skeleton';

export default function MovieDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const movieId = Number(id);
  const { showToast } = useToast();

  const [movie, setMovie] = useState<Movie | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [playlistModalOpen, setPlaylistModalOpen] = useState(false);

  const [isFavorited, setIsFavorited] = useState(false);
  const [isWatched, setIsWatched] = useState(false);
  const [isOnWatchlist, setIsOnWatchlist] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  const [ratingScore, setRatingScore] = useState(0);
  const [review, setReview] = useState('');
  const [savingRating, setSavingRating] = useState(false);

  useEffect(() => {
    let cancelled = false;
    moviesApi
      .detail(movieId)
      .then((data) => {
        if (cancelled) return;
        setMovie(data);
        setIsFavorited(data.is_favorited);
        setIsWatched(data.is_watched);
        setIsOnWatchlist(data.is_in_watchlist);
        if (data.my_rating) {
          setRatingScore(data.my_rating.score);
          setReview(data.my_rating.review);
        }
      })
      .catch((err) => !cancelled && setError(getErrorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [movieId]);

  async function toggleFavorite() {
    if (busy) return;
    setBusy('favorite');
    const next = !isFavorited;
    setIsFavorited(next);
    try {
      if (next) {
        await libraryApi.addFavorite(movieId);
      } else {
        await libraryApi.removeFavorite(movieId);
      }
    } catch (err) {
      setIsFavorited(!next);
      showToast(getErrorMessage(err), 'error');
    } finally {
      setBusy(null);
    }
  }

  async function toggleWatched() {
    if (busy) return;
    setBusy('watched');
    const next = !isWatched;
    setIsWatched(next);
    try {
      if (next) {
        await libraryApi.markWatched(movieId);
      } else {
        await libraryApi.markUnwatched(movieId);
      }
    } catch (err) {
      setIsWatched(!next);
      showToast(getErrorMessage(err), 'error');
    } finally {
      setBusy(null);
    }
  }

  async function toggleWatchlist() {
    if (busy) return;
    setBusy('watchlist');
    const next = !isOnWatchlist;
    setIsOnWatchlist(next);
    try {
      if (next) {
        await libraryApi.addToWatchlist(movieId);
      } else {
        await libraryApi.removeFromWatchlist(movieId);
      }
    } catch (err) {
      setIsOnWatchlist(!next);
      showToast(getErrorMessage(err), 'error');
    } finally {
      setBusy(null);
    }
  }

  async function saveRating() {
    if (ratingScore === 0) {
      showToast('Pick a star rating first.', 'error');
      return;
    }
    setSavingRating(true);
    try {
      await libraryApi.rateMovie(movieId, { score: ratingScore, review });
      showToast('Rating saved.', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setSavingRating(false);
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl">
        <p className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="mx-auto max-w-5xl">
        <Skeleton className="h-64 w-full" />
        <div className="mt-6 flex gap-6">
          <Skeleton className="h-72 w-48 shrink-0" />
          <div className="flex-1 space-y-3">
            <Skeleton className="h-8 w-2/3" />
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-24 w-full" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl pb-16">
      <Link href="/movies" className="inline-flex items-center gap-1.5 text-sm text-foreground-muted hover:text-foreground">
        <ArrowLeft size={15} /> Back to movies
      </Link>

      {/* Backdrop */}
      <div className="relative mt-4 aspect-[21/9] w-full overflow-hidden rounded-xl bg-surface">
        {movie.backdrop_url ? (
          <Image src={movie.backdrop_url} alt="" fill sizes="100vw" className="object-cover" priority />
        ) : null}
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
      </div>

      <div className="-mt-20 flex flex-col gap-6 px-2 sm:flex-row sm:px-4">
        {/* Poster */}
        <div className="relative aspect-[2/3] w-40 shrink-0 overflow-hidden rounded-lg border border-border bg-surface shadow-xl sm:w-52">
          {movie.poster_url ? (
            <Image src={movie.poster_url} alt={movie.title} fill sizes="208px" className="object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center text-xs text-foreground-muted">No poster</div>
          )}
        </div>

        <div className="flex-1 pt-2 sm:pt-16">
          <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">{movie.title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-sm text-foreground-muted">
            <span>{formatYear(movie.release_date)}</span>
            <span>•</span>
            <span>{formatRuntime(movie.runtime_minutes)}</span>
            {movie.genres.length > 0 && (
              <>
                <span>•</span>
                <span>{movie.genres.map((g) => g.name).join(' / ')}</span>
              </>
            )}
            {movie.rating && (
              <>
                <span>•</span>
                <span className="flex items-center gap-1 text-warning">
                  <Star size={13} className="fill-warning" /> {movie.rating}
                </span>
              </>
            )}
          </div>

          {movie.description && <p className="mt-4 max-w-2xl text-sm leading-relaxed text-foreground-muted">{movie.description}</p>}

          {movie.director && <p className="mt-4 text-sm text-foreground">
            <span className="text-foreground-muted">Director: </span>{movie.director.name}
          </p>}

          {movie.cast_members && movie.cast_members.length > 0 && (
            <div className="mt-2 text-sm text-foreground">
              <span className="text-foreground-muted">Cast: </span>
              {movie.cast_members
                .slice()
                .sort((a, b) => a.billing_order - b.billing_order)
                .map((c) => c.name)
                .join(', ')}
            </div>
          )}

          <div className="mt-6 flex flex-wrap gap-2">
            <Button
              variant={isWatched ? 'primary' : 'secondary'}
              onClick={toggleWatched}
              isLoading={busy === 'watched'}
            >
              <CheckCircle2 size={16} /> {isWatched ? 'Watched' : 'Mark watched'}
            </Button>
            <Button
              variant={isOnWatchlist ? 'primary' : 'secondary'}
              onClick={toggleWatchlist}
              isLoading={busy === 'watchlist'}
            >
              <Bookmark size={16} /> {isOnWatchlist ? 'On watchlist' : 'Add to watchlist'}
            </Button>
            <Button variant="secondary" onClick={() => setPlaylistModalOpen(true)}>
              <ListPlus size={16} /> Add to playlist
            </Button>
            <Button
              variant={isFavorited ? 'primary' : 'secondary'}
              onClick={toggleFavorite}
              isLoading={busy === 'favorite'}
            >
              <Heart size={16} className={isFavorited ? 'fill-current' : ''} /> Favorite
            </Button>
          </div>
        </div>
      </div>

      {/* Personal rating + review */}
      <div className="mt-10 max-w-2xl rounded-xl border border-border bg-surface p-5">
        <h2 className="font-display text-lg font-medium text-foreground">Your rating</h2>
        <div className="mt-3">
          <StarRating value={ratingScore} onChange={setRatingScore} />
        </div>
        <Textarea
          label="Your review"
          value={review}
          onChange={(e) => setReview(e.target.value)}
          placeholder="What did you think?"
          rows={3}
          className="mt-4"
        />
        <Button className="mt-3" onClick={saveRating} isLoading={savingRating}>
          Save review
        </Button>
      </div>

      <AddToPlaylistModal
        isOpen={playlistModalOpen}
        onClose={() => setPlaylistModalOpen(false)}
        movieId={movie.id}
        movieTitle={movie.title}
      />
    </div>
  );
}
