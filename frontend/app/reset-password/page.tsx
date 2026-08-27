'use client';

import { Suspense, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { authApi } from '@/lib/endpoints';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { getErrorMessage } from '@/lib/utils';

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const uid = searchParams.get('uid') ?? '';
  const token = searchParams.get('token') ?? '';

  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await authApi.confirmPasswordReset({ uid, token, new_password: newPassword });
      router.push('/login');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!uid || !token) {
    return (
      <p className="mt-8 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-center text-sm text-danger">
        This reset link is missing information. Please request a new one.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
      <Input
        label="New password"
        name="new_password"
        type="password"
        autoComplete="new-password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        required
      />
      {error && (
        <p className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>
      )}
      <Button type="submit" isLoading={isSubmitting} className="w-full justify-center">
        Set new password
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <h1 className="font-display text-center text-2xl font-medium text-foreground">Choose a new password</h1>
        <Suspense fallback={<p className="mt-8 text-center text-sm text-foreground-muted">Loading…</p>}>
          <ResetPasswordForm />
        </Suspense>
        <p className="mt-6 text-center text-sm text-foreground-muted">
          <Link href="/login" className="text-accent hover:underline">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
