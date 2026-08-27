'use client';

import { useState, type FormEvent } from 'react';
import Link from 'next/link';
import { authApi } from '@/lib/endpoints';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { getErrorMessage } from '@/lib/utils';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await authApi.requestPasswordReset(email);
      setMessage(res.detail);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <h1 className="font-display text-center text-2xl font-medium text-foreground">Reset your password</h1>
        <p className="mt-2 text-center text-sm text-foreground-muted">
          We&apos;ll email you a link to choose a new one.
        </p>

        {message ? (
          <p className="mt-8 rounded-lg border border-success/30 bg-success/10 px-3 py-2 text-center text-sm text-success">
            {message}
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
            <Input
              label="Email"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            {error && (
              <p className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                {error}
              </p>
            )}
            <Button type="submit" isLoading={isSubmitting} className="w-full justify-center">
              Send reset link
            </Button>
          </form>
        )}

        <p className="mt-6 text-center text-sm text-foreground-muted">
          <Link href="/login" className="text-accent hover:underline">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
