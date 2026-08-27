import { describe, it, expect } from 'vitest';
import { cn, formatRuntime, formatYear, getPasswordStrength } from '../utils';

describe('cn', () => {
  it('merges class names and drops falsy values', () => {
    expect(cn('a', false && 'b', undefined, 'c')).toBe('a c');
  });
});

describe('formatYear', () => {
  it('extracts the year from an ISO date string', () => {
    expect(formatYear('2010-07-16')).toBe('2010');
  });

  it('returns an em dash placeholder for null', () => {
    expect(formatYear(null)).toBe('—');
  });
});

describe('formatRuntime', () => {
  it('formats hours and minutes', () => {
    expect(formatRuntime(148)).toBe('2h 28m');
  });

  it('formats sub-hour runtimes as minutes only', () => {
    expect(formatRuntime(45)).toBe('45m');
  });

  it('returns a placeholder for null/zero', () => {
    expect(formatRuntime(null)).toBe('—');
    expect(formatRuntime(0)).toBe('—');
  });
});

describe('getPasswordStrength', () => {
  it('rates a short, simple password as weak', () => {
    expect(getPasswordStrength('abc').score).toBe(0);
  });

  it('rates a long password with mixed case, numbers, and symbols as very strong', () => {
    const result = getPasswordStrength('Correct-Horse-Battery-9!');
    expect(result.score).toBe(4);
    expect(result.label).toBe('Very strong');
  });

  it('never exceeds the max score regardless of extra length', () => {
    const result = getPasswordStrength('A'.repeat(50) + 'a1!');
    expect(result.score).toBeLessThanOrEqual(4);
  });
});
