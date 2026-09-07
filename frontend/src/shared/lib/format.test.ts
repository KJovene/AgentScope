import { describe, expect, it } from 'vitest';

import { UNAVAILABLE, formatDuration, formatPercent, formatTokens } from './format';

describe('format — missing values are never rendered as 0', () => {
  it.each([null, undefined, NaN])('formatTokens(%s) -> UNAVAILABLE', (value) => {
    expect(formatTokens(value as number | null | undefined)).toBe(UNAVAILABLE);
  });

  it('formatTokens compacts large numbers', () => {
    expect(formatTokens(500)).toBe('500');
    expect(formatTokens(12_300)).toMatch(/k/i);
  });

  it('formatPercent expects a ratio in [0,1]', () => {
    expect(formatPercent(0.42)).toMatch(/42/);
    expect(formatPercent(null)).toBe(UNAVAILABLE);
  });

  it('formatDuration switches units', () => {
    expect(formatDuration(820)).toBe('820 ms');
    expect(formatDuration(72_000)).toBe('1 min 12 s');
    expect(formatDuration(undefined)).toBe(UNAVAILABLE);
  });
});
