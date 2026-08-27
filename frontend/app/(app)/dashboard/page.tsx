'use client';

import { useMemo, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { cn, getErrorMessage, getPasswordStrength } from '@/lib/utils';
import type { ApiError } from '@/types';
import { ApiRequestError } from '@/lib/api';

const STRENGTH_COLORS = ['bg-danger', 'bg-danger', 'bg-warning', 'bg-success', 'bg-success'];

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [fieldErrors, setFieldErrors] = useState<ApiError>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const strength = useMemo(() => getPasswordStrength(password), [password]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    setFieldErrors({});
    setIsSubmitting(true);

    try {
      await register({
        username,
        email,
        password,
        password_confirm: passwordConfirm,
      });

      // After successful registration, go to the login page
      router.push('/login');
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setFieldErrors(err.body);
        if (err.body.detail) setFormError(err.body.detail);
      } else {
        setFormError(getErrorMessage(err));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  function fieldError(field: string): string | undefined {
    const value = fieldErrors[field];
    if (Array.isArray(value)) return value[0] as string;
    return typeof value === 'string' ? value : undefined;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-sm">
        <h1 className="font-display text-center text-2xl font-medium text-foreground">
          Create your account
        </h1>

        <p className="mt-2 text-center text-sm text-foreground-muted">
          Start building your movie library.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
          <Input
            label="Username"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            error={fieldError('username')}
            required
          />

          <Input
            label="Email"
            name="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={fieldError('email')}
            required
          />

          <div>
            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={fieldError('password')}
              required
            />

            {password.length > 0 && (
              <div className="mt-2">
                <div className="flex h-1.5 gap-1">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        'flex-1 rounded-full bg-border',
                        i < strength.score && STRENGTH_COLORS[strength.score]
                      )}
                    />
                  ))}
                </div>

                <p className="mt-1 text-xs text-foreground-muted">
                  {strength.label}
                </p>
              </div>
            )}
          </div>

          <Input
            label="Confirm password"
            name="password_confirm"
            type="password"
            autoComplete="new-password"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            error={fieldError('password_confirm')}
            required
          />

          {formError && (
            <p className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
              {formError}
            </p>
          )}

          <Button
            type="submit"
            isLoading={isSubmitting}
            className="w-full justify-center"
          >
            Register
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-foreground-muted">
          Already have an account?{' '}
          <Link href="/login" className="text-accent hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}