'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, ArrowUp, ArrowDown, CheckCircle2, GripVertical, Lock, Globe, Pencil, Trash2, X, Check,
} from 'lucide-react';
import { playlistsApi } from '@/lib/endpoints';
import type { Playlist, PlaylistMovieEntry } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { useToast } from '@/hooks/useToast';
import { cn, formatRelativeDate, formatYear, getErrorMessage } from '@/lib/utils';

export default function PlaylistDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const playlistId = Number(id);
  const router = useRouter();
  const { showToast } = useToast();

  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [dragMovieId, setDragMovieId] = useState<number | null>(null);

  function load() {
    setError(null);
    playlistsApi
      .detail(playlistId)
      .then((data) => {
        setPlaylist(data);
        setEditName(data.name);
        setEditDescription(data.description);
      })
      .catch((err) => setError(getErrorMessage(err)));
  }

  useEffect(() => {
    queueMicrotask(load);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playlistId]);

  async function saveEdit() {
    if (!editName.trim()) {
      showToast('Playlist name is required.', 'error');
      return;
    }
    setSavingEdit(true);
    try {
      const updated = await playlistsApi.update(playlistId, {
        name: editName.trim(),
        description: editDescription,
      });
      setPlaylist(updated);
      setIsEditing(false);
      showToast('Playlist updated.', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setSavingEdit(false);
    }
  }

  async function togglePrivacy() {
    if (!playlist) return;
    const next = !playlist.is_public;
    setPlaylist({ ...playlist, is_public: next });
    try {
      await playlistsApi.update(playlistId, { is_public: next });
      showToast(next ? 'Playlist is now public.' : 'Playlist is now private.', 'success');
    } catch (err) {
      setPlaylist({ ...playlist, is_public: !next });
      showToast(getErrorMessage(err), 'error');
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await playlistsApi.remove(playlistId);
      showToast('Playlist deleted.', 'success');
      router.push('/playlists');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
      setDeleting(false);
    }
  }

  async function removeMovie(movieId: number) {
    if (!playlist?.movies) return;
    const prev = playlist.movies;
    setPlaylist({ ...playlist, movies: prev.filter((m) => m.movie.id !== movieId) });
    try {
      await playlistsApi.removeMovie(playlistId, movieId);
    } catch (err) {
      setPlaylist({ ...playlist, movies: prev });
      showToast(getErrorMessage(err), 'error');
    }
  }

  async function toggleEntryWatched(entry: PlaylistMovieEntry) {
    if (!playlist?.movies) return;
    const prev = playlist.movies;
    const next = prev.map((m) => (m.movie.id === entry.movie.id ? { ...m, watched: !m.watched } : m));
    setPlaylist({ ...playlist, movies: next });
    try {
      await playlistsApi.updateMovieEntry(playlistId, entry.movie.id, { watched: !entry.watched });
    } catch (err) {
      setPlaylist({ ...playlist, movies: prev });
      showToast(getErrorMessage(err), 'error');
    }
  }

  async function persistOrder(movies: PlaylistMovieEntry[]) {
    try {
      await playlistsApi.reorder(playlistId, movies.map((m) => m.movie.id));
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
      load();
    }
  }

  function handleDrop(targetMovieId: number) {
    if (!playlist?.movies || dragMovieId === null || dragMovieId === targetMovieId) return;
    const movies = [...playlist.movies];
    const fromIndex = movies.findIndex((m) => m.movie.id === dragMovieId);
    const toIndex = movies.findIndex((m) => m.movie.id === targetMovieId);
    if (fromIndex === -1 || toIndex === -1) return;
    const [moved] = movies.splice(fromIndex, 1);
    movies.splice(toIndex, 0, moved);
    setPlaylist({ ...playlist, movies });
    setDragMovieId(null);
    persistOrder(movies);
  }

  // Up/down buttons: the accessible, touch-friendly alternative to the drag
  // handle above. HTML5 drag-and-drop doesn't fire on touch devices without
  // extra polyfilling, and dragging alone is also unusable for keyboard/
  // screen-reader users — these buttons cover both cases.
  function moveEntry(movieId: number, direction: -1 | 1) {
    if (!playlist?.movies) return;
    const movies = [...playlist.movies];
    const index = movies.findIndex((m) => m.movie.id === movieId);
    const targetIndex = index + direction;
    if (index === -1 || targetIndex < 0 || targetIndex >= movies.length) return;
    [movies[index], movies[targetIndex]] = [movies[targetIndex], movies[index]];
    setPlaylist({ ...playlist, movies });
    persistOrder(movies);
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl">
        <p className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>
      </div>
    );
  }

  if (!playlist) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl pb-16">
      <Link href="/playlists" className="inline-flex items-center gap-1.5 text-sm text-foreground-muted hover:text-foreground">
        <ArrowLeft size={15} /> Back to playlists
      </Link>

      <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        {isEditing ? (
          <div className="flex-1 space-y-3">
            <Input value={editName} onChange={(e) => setEditName(e.target.value)} maxLength={150} />
            <Textarea value={editDescription} onChange={(e) => setEditDescription(e.target.value)} rows={2} />
            <div className="flex gap-2">
              <Button size="sm" onClick={saveEdit} isLoading={savingEdit}>
                <Check size={14} /> Save
              </Button>
              <Button size="sm" variant="secondary" onClick={() => setIsEditing(false)}>
                <X size={14} /> Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">{playlist.name}</h1>
              <button onClick={() => setIsEditing(true)} className="text-foreground-muted hover:text-foreground" aria-label="Edit playlist">
                <Pencil size={16} />
              </button>
            </div>
            {playlist.description && <p className="mt-1 max-w-xl text-sm text-foreground-muted">{playlist.description}</p>}
            <p className="mt-2 font-mono text-xs text-foreground-muted">
              {playlist.movie_count} movies • Updated {formatRelativeDate(playlist.updated_at)}
            </p>
          </div>
        )}

        <div className="flex shrink-0 gap-2">
          <Button variant="secondary" size="sm" onClick={togglePrivacy}>
            {playlist.is_public ? <Globe size={14} /> : <Lock size={14} />}
            {playlist.is_public ? 'Public' : 'Private'}
          </Button>
          <Button variant="danger" size="sm" onClick={() => setConfirmDeleteOpen(true)}>
            <Trash2 size={14} /> Delete
          </Button>
        </div>
      </div>

      <div className="mt-8">
        {!playlist.movies || playlist.movies.length === 0 ? (
          <EmptyState
            title="No movies in this playlist yet"
            description="Browse movies and use “Add to playlist” to start filling this one up."
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {playlist.movies.map((entry, index) => (
              <li
                key={entry.movie.id}
                draggable
                onDragStart={() => setDragMovieId(entry.movie.id)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => handleDrop(entry.movie.id)}
                className={cn(
                  'flex items-center gap-3 rounded-lg border border-border bg-surface p-2.5 transition-opacity',
                  dragMovieId === entry.movie.id && 'opacity-50'
                )}
              >
                <span className="hidden shrink-0 cursor-grab text-foreground-muted active:cursor-grabbing sm:inline-flex" aria-hidden="true">
                  <GripVertical size={16} />
                </span>

                {/* Up/down buttons: visible on all sizes since drag doesn't work on
                    touch, and these also make reordering usable via keyboard. */}
                <div className="flex shrink-0 flex-col">
                  <button
                    onClick={() => moveEntry(entry.movie.id, -1)}
                    disabled={index === 0}
                    className="rounded p-0.5 text-foreground-muted hover:bg-surface-raised hover:text-foreground disabled:pointer-events-none disabled:opacity-30"
                    aria-label={`Move ${entry.movie.title} up`}
                  >
                    <ArrowUp size={14} />
                  </button>
                  <button
                    onClick={() => moveEntry(entry.movie.id, 1)}
                    disabled={index === (playlist.movies?.length ?? 0) - 1}
                    className="rounded p-0.5 text-foreground-muted hover:bg-surface-raised hover:text-foreground disabled:pointer-events-none disabled:opacity-30"
                    aria-label={`Move ${entry.movie.title} down`}
                  >
                    <ArrowDown size={14} />
                  </button>
                </div>

                <Link href={`/movies/${entry.movie.id}`} className="relative h-16 w-11 shrink-0 overflow-hidden rounded bg-surface-raised">
                  {entry.movie.poster_url && (
                    <Image src={entry.movie.poster_url} alt={entry.movie.title} fill sizes="44px" className="object-cover" />
                  )}
                </Link>

                <Link href={`/movies/${entry.movie.id}`} className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-foreground">{entry.movie.title}</p>
                  <p className="font-mono text-xs text-foreground-muted">{formatYear(entry.movie.release_date)}</p>
                </Link>

                <button
                  onClick={() => toggleEntryWatched(entry)}
                  className={cn(
                    'icon-btn-focus shrink-0 rounded-md p-1.5 transition-colors hover:bg-surface-raised',
                    entry.watched ? 'text-success' : 'text-foreground-muted'
                  )}
                  aria-label={entry.watched ? 'Mark unwatched' : 'Mark watched'}
                >
                  <CheckCircle2 size={18} className={entry.watched ? 'fill-success/20' : ''} />
                </button>

                <button
                  onClick={() => removeMovie(entry.movie.id)}
                  className="icon-btn-focus shrink-0 rounded-md p-1.5 text-foreground-muted transition-colors hover:bg-danger/10 hover:text-danger"
                  aria-label="Remove from playlist"
                >
                  <X size={18} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <ConfirmDialog
        isOpen={confirmDeleteOpen}
        onClose={() => setConfirmDeleteOpen(false)}
        onConfirm={handleDelete}
        title="Delete playlist"
        message={`Are you sure you want to delete "${playlist.name}"? This can't be undone.`}
        confirmLabel="Delete"
        isLoading={deleting}
      />
    </div>
  );
}
