'use client';

import { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input, Textarea } from '../ui/Input';
import { playlistsApi } from '@/lib/endpoints';
import { useToast } from '@/hooks/useToast';
import { getErrorMessage } from '@/lib/utils';
import type { Playlist } from '@/types';

interface CreatePlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (playlist: Playlist) => void;
}

export function CreatePlaylistModal({ isOpen, onClose, onCreated }: CreatePlaylistModalProps) {
  const { showToast } = useToast();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  function reset() {
    setName('');
    setDescription('');
    setIsPublic(false);
    setError('');
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError('Playlist name is required.');
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      const playlist = await playlistsApi.create({ name: name.trim(), description, is_public: isPublic });
      showToast(`Playlist "${playlist.name}" created.`, 'success');
      onCreated(playlist);
      reset();
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        reset();
        onClose();
      }}
      title="Create playlist"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Playlist name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Weekend Watchlist"
          maxLength={150}
          error={error}
          autoFocus
        />
        <Textarea
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What's this playlist about?"
          rows={3}
        />
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="h-4 w-4 rounded border-border accent-accent"
          />
          Make this playlist public
        </label>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            Create playlist
          </Button>
        </div>
      </form>
    </Modal>
  );
}
