'use client';

import { useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // In a real deployment this is where an error-reporting service call would go.
    console.error('Unhandled application error:', error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
      <AlertTriangle size={40} className="text-danger" />
      <h1 className="mt-4 font-display text-2xl font-medium text-foreground">Something went wrong</h1>
      <p className="mt-2 max-w-sm text-sm text-foreground-muted">
        An unexpected error occurred. You can try again, or head back to the dashboard.
      </p>
      <Button className="mt-6" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}
