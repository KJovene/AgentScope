import { describe, expect, it } from 'vitest';

import {
  UNAVAILABLE,
  formatDate,
  formatDateTime,
  formatDuration,
  formatNumber,
  formatPercent,
  formatTokens,
  formatUsd,
} from '@shared/lib/format';

describe('format — missing values are never rendered as 0', () => {
  it.each([null, undefined, NaN])('formatTokens(%s) -> UNAVAILABLE', (value) => {
    expect(formatTokens(value as number | null | undefined)).toBe(UNAVAILABLE);
  });

  it('formatTokens compacts large numbers, keeps small ones plain', () => {
    expect(formatTokens(500)).toBe('500');
    expect(formatTokens(9_999)).not.toMatch(/k/i);
    expect(formatTokens(12_300)).toMatch(/k/i);
  });

  it('formatNumber', () => {
    expect(formatNumber(1234)).toMatch(/1[\s ]?234/);
    expect(formatNumber(null)).toBe(UNAVAILABLE);
    expect(formatNumber(NaN)).toBe(UNAVAILABLE);
  });

  it('formatUsd', () => {
    expect(formatUsd(12.5)).toMatch(/12,5/);
    expect(formatUsd(undefined)).toBe(UNAVAILABLE);
  });

  it('formatPercent expects a ratio in [0,1]', () => {
    expect(formatPercent(0.42)).toMatch(/42/);
    expect(formatPercent(null)).toBe(UNAVAILABLE);
  });

  it('formatDuration switches units', () => {
    expect(formatDuration(820)).toBe('820 ms');
    expect(formatDuration(5_000)).toBe('5 s');
    expect(formatDuration(72_000)).toBe('1 min 12 s');
    expect(formatDuration(undefined)).toBe(UNAVAILABLE);
  });

  it('formatDateTime / formatDate', () => {
    expect(formatDateTime('2026-01-02T10:00:00Z')).toMatch(/2026/);
    expect(formatDate('2026-01-02T10:00:00Z')).toMatch(/2026/);
    expect(formatDateTime(null)).toBe(UNAVAILABLE);
    expect(formatDate(undefined)).toBe(UNAVAILABLE);
    expect(formatDateTime('not-a-date')).toBe(UNAVAILABLE);
    expect(formatDate('not-a-date')).toBe(UNAVAILABLE);
  });
});
