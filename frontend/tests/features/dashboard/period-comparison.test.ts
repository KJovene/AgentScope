import { describe, expect, it } from 'vitest';

import { EMPTY_METRIC_FILTERS } from '@shared/lib/metric-filters';
import {
  previousPeriod,
  relativeDelta,
  resolveCurrentPeriod,
} from '@features/dashboard/model/period-comparison';

describe('resolveCurrentPeriod', () => {
  it('prefers an explicit date filter', () => {
    const period = resolveCurrentPeriod(
      { ...EMPTY_METRIC_FILTERS, from: '2026-03-01T00:00:00.000Z', to: '2026-03-31T00:00:00.000Z' },
      [{ period: '2026-01-05', value: 1 }],
    );

    expect(period).toEqual({ from: '2026-03-01T00:00:00.000Z', to: '2026-03-31T00:00:00.000Z' });
  });

  it('falls back to the span the activity series covers', () => {
    const period = resolveCurrentPeriod(EMPTY_METRIC_FILTERS, [
      { period: '2026-01-03', value: 1 },
      { period: '2026-01-01', value: 2 },
    ]);

    expect(period).toEqual({
      from: '2026-01-01T00:00:00.000Z',
      to: '2026-01-03T23:59:59.999Z',
    });
  });

  it('returns null when neither a date filter nor a series is available', () => {
    expect(resolveCurrentPeriod(EMPTY_METRIC_FILTERS, [])).toBeNull();
  });
});

describe('previousPeriod', () => {
  it('returns a window of equal length that ends just before the current one', () => {
    const previous = previousPeriod({
      from: '2026-01-11T00:00:00.000Z',
      to: '2026-01-21T00:00:00.000Z',
    });

    expect(previous?.to).toBe('2026-01-10T23:59:59.999Z');
    expect(Date.parse(previous!.to) - Date.parse(previous!.from)).toBe(
      Date.parse('2026-01-21T00:00:00.000Z') - Date.parse('2026-01-11T00:00:00.000Z'),
    );
  });

  it('returns null for an empty or inverted window', () => {
    expect(
      previousPeriod({ from: '2026-01-11T00:00:00.000Z', to: '2026-01-11T00:00:00.000Z' }),
    ).toBeNull();
    expect(previousPeriod({ from: 'not-a-date', to: '2026-01-11T00:00:00.000Z' })).toBeNull();
  });
});

describe('relativeDelta', () => {
  it('computes the signed relative variation', () => {
    expect(relativeDelta(112, 100)).toBeCloseTo(0.12);
    expect(relativeDelta(80, 100)).toBeCloseTo(-0.2);
  });

  it('refuses to invent a baseline', () => {
    // Growth from zero is undefined, never "+100 %".
    expect(relativeDelta(5, 0)).toBeNull();
    expect(relativeDelta(null, 100)).toBeNull();
    expect(relativeDelta(5, null)).toBeNull();
  });
});
