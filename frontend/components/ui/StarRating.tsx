'use client';

import { useState } from 'react';
import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StarRatingProps {
  value: number; // 0-10 scale, rendered as 5 stars (half-star granularity)
  onChange?: (score: number) => void;
  readOnly?: boolean;
  size?: number;
}

export function StarRating({ value, onChange, readOnly = false, size = 20 }: StarRatingProps) {
  const [hoverScore, setHoverScore] = useState<number | null>(null);
  const displayValue = hoverScore ?? value;
  const starCount = 5;

  return (
    <div className="flex items-center gap-1" role={readOnly ? undefined : 'radiogroup'}>
      {Array.from({ length: starCount }).map((_, i) => {
        // Each star represents 2 points on the 1-10 scale.
        const starScore = (i + 1) * 2;
        const filled = displayValue >= starScore;
        return (
          <button
            key={i}
            type="button"
            disabled={readOnly}
            onMouseEnter={() => !readOnly && setHoverScore(starScore)}
            onMouseLeave={() => !readOnly && setHoverScore(null)}
            onClick={() => onChange?.(starScore)}
            className={cn('transition-transform', !readOnly && 'hover:scale-110 cursor-pointer')}
            aria-label={`Rate ${starScore} out of 10`}
          >
            <Star
              size={size}
              className={filled ? 'fill-warning text-warning' : 'text-border'}
              strokeWidth={1.5}
            />
          </button>
        );
      })}
      {value > 0 && <span className="ml-1 text-xs text-foreground-muted">{value}/10</span>}
    </div>
  );
}
