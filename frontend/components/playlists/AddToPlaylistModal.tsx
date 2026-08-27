'use client';

import { useEffect, useState } from 'react';
import { Plus, Check } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { playlistsApi } from '@/lib/endpoints';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/lib/utils';
import type { Playlist } from '@/types';
import { CreatePlaylistModal } from './CreatePlaylistModal';

interface AddToPlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  movieId: number;
  movieTitle: string;
}

export function AddToPlaylistModal({ isOpen, onClose, movieId, movieTitle }: AddToPlaylistModalProps) {
  const { showToast } = useToast();
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [addedIds, setAddedIds] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    // See useAuth.tsx for why this is deferred via queueMicrotask.
    queueMicrotask(() => {
      setIsLoading(true);
      playlistsApi
        .list()
        .then((res) => setPlaylists(res.results))
        .catch((err) => showToast(getErrorMessage(err), 'error'))
        .finally(() => setIsLoading(false));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  async function handleToggle(playlist: Playlist) {
    if (addedIds.has(playlist.id) || pendingId) return;
    setPendingId(playlist.id);
    try {
      await playlistsApi.addMovie(playlist.id, movieId);
      setAddedIds((prev) => new Set(prev).add(playlist.id));
      showToast(`Added to "${playlist.name}".`, 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setPendingId(null);
    }
  }

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} title={`Add "${movieTitle}" to...`}>
        <div className="flex flex-col gap-1">
          {isLoading ? (
            <p className="py-4 text-center text-sm text-foreground-muted">Loading playlists…</p>
          ) : playlists.length === 0 ? (
            <p className="py-4 text-center text-sm text-foreground-muted">You don&apos;t have any playlists yet.</p>
          ) : (
            playlists.map((playlist) => {
              const added = addedIds.has(playlist.id);
              return (
                <button
                  key={playlist.id}
                  onClick={() => handleToggle(playlist)}
                  disabled={pendingId === playlist.id}
                  className="flex items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm hover:bg-surface transition-colors disabled:opacity-60"
                >
                  <span>
                    <span className="font-medium text-foreground">{playlist.name}</span>{' '}
                    <span className="text-xs text-foreground-muted">({playlist.movie_count} movies)</span>
                  </span>
                  <span
                    className={`flex h-5 w-5 items-center justify-center rounded border ${
                      added ? 'border-accent bg-accent' : 'border-border'
                    }`}
                  >
                    {added && <Check size={12} className="text-white" />}
                  </span>
                </button>
              );
            })
          )}
        </div>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-border py-2.5 text-sm text-foreground-muted hover:border-accent/40 hover:text-foreground transition-colors"
        >
          <Plus size={14} /> Create new playlist
        </button>
        <div className="mt-4 flex justify-end">
          <Button variant="secondary" onClick={onClose}>
            Done
          </Button>
        </div>
      </Modal>
      <CreatePlaylistModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreated={(playlist) => setPlaylists((prev) => [playlist, ...prev])}
      />
    </>
  );
}
