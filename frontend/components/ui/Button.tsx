'use client';

import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary: 'bg-accent text-white hover:bg-accent-hover disabled:opacity-50',
  secondary: 'bg-surface-raised text-foreground border border-border hover:bg-border/60 disabled:opacity-50',
  ghost: 'bg-transparent text-foreground-muted hover:text-foreground hover:bg-surface-raised disabled:opacity-50',
  danger: 'bg-danger/10 text-danger border border-danger/30 hover:bg-danger/20 disabled:opacity-50',
};

const sizeClasses: Record<Size, string> = {
  sm: 'text-xs px-2.5 py-1.5 gap-1.5 rounded-md',
  md: 'text-sm px-4 py-2 gap-2 rounded-lg',
  lg: 'text-base px-5 py-2.5 gap-2 rounded-lg',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center font-medium transition-colors',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/50',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 size={16} className="animate-spin" />}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
