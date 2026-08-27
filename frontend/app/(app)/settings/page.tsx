'use client';

import { useState, type FormEvent } from 'react';
import { authApi } from '@/lib/endpoints';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/useToast';
import { Input, Textarea } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { getErrorMessage } from '@/lib/utils';
import { ApiRequestError } from '@/lib/api';
import type { ApiError } from '@/types';

export default function SettingsPage() {
  const { user, refetchUser, logout } = useAuth();
  const { showToast } = useToast();

  const [username, setUsername] = useState(user?.username ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [bio, setBio] = useState(user?.bio ?? '');
  const [profileErrors, setProfileErrors] = useState<ApiError>({});
  const [savingProfile, setSavingProfile] = useState(false);

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [savingPassword, setSavingPassword] = useState(false);

  function fieldError(errors: ApiError, field: string): string | undefined {
    const value = errors[field];
    if (Array.isArray(value)) return value[0] as string;
    return typeof value === 'string' ? value : undefined;
  }

  async function handleProfileSubmit(e: FormEvent) {
    e.preventDefault();
    setProfileErrors({});
    setSavingProfile(true);
    try {
      await authApi.updateProfile({ username, email, bio });
      await refetchUser();
      showToast('Profile updated.', 'success');
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setProfileErrors(err.body);
      } else {
        showToast(getErrorMessage(err), 'error');
      }
    } finally {
      setSavingProfile(false);
    }
  }

  async function handlePasswordSubmit(e: FormEvent) {
    e.preventDefault();
    setPasswordError(null);
    setSavingPassword(true);
    try {
      await authApi.changePassword({ old_password: oldPassword, new_password: newPassword });
      setOldPassword('');
      setNewPassword('');
      showToast('Password changed.', 'success');
    } catch (err) {
      setPasswordError(getErrorMessage(err));
    } finally {
      setSavingPassword(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl pb-16">
      <h1 className="font-display text-2xl font-medium text-foreground sm:text-3xl">Settings</h1>
      <p className="mt-1 text-sm text-foreground-muted">Manage your profile and account.</p>

      <form onSubmit={handleProfileSubmit} className="mt-8 flex flex-col gap-4 rounded-xl border border-border bg-surface p-5">
        <h2 className="font-display text-lg font-medium text-foreground">Profile</h2>
        <Input
          label="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          error={fieldError(profileErrors, 'username')}
        />
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={fieldError(profileErrors, 'email')}
        />
        <Textarea
          label="Bio"
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          rows={3}
          placeholder="A little about you and what you like to watch."
        />
        <div>
          <Button type="submit" isLoading={savingProfile}>
            Save profile
          </Button>
        </div>
      </form>

      <form onSubmit={handlePasswordSubmit} className="mt-6 flex flex-col gap-4 rounded-xl border border-border bg-surface p-5">
        <h2 className="font-display text-lg font-medium text-foreground">Change password</h2>
        <Input
          label="Current password"
          type="password"
          autoComplete="current-password"
          value={oldPassword}
          onChange={(e) => setOldPassword(e.target.value)}
          required
        />
        <Input
          label="New password"
          type="password"
          autoComplete="new-password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
        />
        {passwordError && (
          <p className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">{passwordError}</p>
        )}
        <div>
          <Button type="submit" isLoading={savingPassword}>
            Change password
          </Button>
        </div>
      </form>

      <div className="mt-6 flex justify-end">
        <Button variant="ghost" onClick={logout}>
          Log out
        </Button>
      </div>
    </div>
  );
}
