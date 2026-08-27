'use client';

import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'w-full rounded-lg border bg-surface px-3 py-2 text-sm text-foreground placeholder:text-foreground-muted',
            'focus:outline-none focus:ring-2 focus:ring-accent/40 transition-shadow',
            error ? 'border-danger' : 'border-border',
            className
          )}
          {...props}
        />
        {hint && !error && <p className="text-xs text-foreground-muted">{hint}</p>}
        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string; error?: string }
>(({ className, label, error, id, ...props }, ref) => {
  const areaId = id || props.name;
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={areaId} className="text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        id={areaId}
        className={cn(
          'w-full rounded-lg border bg-surface px-3 py-2 text-sm text-foreground placeholder:text-foreground-muted',
          'focus:outline-none focus:ring-2 focus:ring-accent/40 transition-shadow resize-none',
          error ? 'border-danger' : 'border-border',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  );
});
Textarea.displayName = 'Textarea';
