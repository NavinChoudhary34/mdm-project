'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  page: number;
  hasNext: boolean;
  hasPrevious: boolean;
  onChange: (page: number) => void;
  totalCount?: number;
  pageSize?: number;
}

export function Pagination({ page, hasNext, hasPrevious, onChange, totalCount, pageSize = 20 }: PaginationProps) {
  if (!hasNext && !hasPrevious) return null;

  const totalPages = totalCount ? Math.max(1, Math.ceil(totalCount / pageSize)) : undefined;

  return (
    <div className="mt-8 flex items-center justify-center gap-3">
      <button
        onClick={() => onChange(page - 1)}
        disabled={!hasPrevious}
        className="flex items-center gap-1 rounded-lg border border-border bg-surface px-3 py-1.5 text-sm text-foreground-muted transition-colors hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
      >
        <ChevronLeft size={16} /> Prev
      </button>
      <span className="font-mono text-sm text-foreground-muted">
        Page {page}
        {totalPages ? ` of ${totalPages}` : ''}
      </span>
      <button
        onClick={() => onChange(page + 1)}
        disabled={!hasNext}
        className="flex items-center gap-1 rounded-lg border border-border bg-surface px-3 py-1.5 text-sm text-foreground-muted transition-colors hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
      >
        Next <ChevronRight size={16} />
      </button>
    </div>
  );
}
