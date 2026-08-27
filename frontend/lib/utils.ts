import { type ClassValue, clsx } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatYear(dateStr: string | null): string {
  if (!dateStr) return '—';
  return new Date(dateStr).getFullYear().toString();
}

export function formatRuntime(minutes: number | null): string {
  if (!minutes) return '—';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays <= 0) return 'today';
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} week${Math.floor(diffDays / 7) > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return 'Something went wrong. Please try again.';
}

export interface PasswordStrength {
  score: 0 | 1 | 2 | 3 | 4;
  label: 'Very weak' | 'Weak' | 'Fair' | 'Strong' | 'Very strong';
}

/** Lightweight heuristic strength meter — not a substitute for the backend's
 * real validation (Django's password validators are the source of truth). */
export function getPasswordStrength(password: string): PasswordStrength {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/\d/.test(password) && /[^A-Za-z0-9]/.test(password)) score++;

  const labels: PasswordStrength['label'][] = ['Very weak', 'Weak', 'Fair', 'Strong', 'Very strong'];
  const clamped = Math.min(score, 4) as PasswordStrength['score'];
  return { score: clamped, label: labels[clamped] };
}
