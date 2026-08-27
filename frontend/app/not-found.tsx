import Link from 'next/link';
import { Film } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
      <Film size={40} className="text-foreground-muted" />
      <h1 className="mt-4 font-display text-2xl font-medium text-foreground">Page not found</h1>
      <p className="mt-2 max-w-sm text-sm text-foreground-muted">
        The page you&apos;re looking for doesn&apos;t exist, or the reel ran out early.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
