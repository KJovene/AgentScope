import { describe, expect, it } from 'vitest';

import { dayDrillDownFilters } from '@features/dashboard/model/drilldown';
import { EMPTY_METRIC_FILTERS } from '@shared/lib/metric-filters';

describe('dayDrillDownFilters', () => {
  it('narrows the date range to the clicked day (start / end of day, UTC)', () => {
    const result = dayDrillDownFilters(EMPTY_METRIC_FILTERS, { period: '2026-01-15', value: 3 });

    expect(result.from).toBe('2026-01-15T00:00:00Z');
    expect(result.to).toBe('2026-01-15T23:59:59Z');
  });

  it('preserves every other active filter dimension', () => {
    const filters = { ...EMPTY_METRIC_FILTERS, sources: ['s1'], agents: ['claude'] };

    const result = dayDrillDownFilters(filters, { period: '2026-01-15', value: null });

    expect(result.sources).toEqual(['s1']);
    expect(result.agents).toEqual(['claude']);
  });

  it('overrides a previously active date range with the clicked day', () => {
    const filters = { ...EMPTY_METRIC_FILTERS, from: '2020-01-01T00:00:00Z', to: '2020-01-31T00:00:00Z' };

    const result = dayDrillDownFilters(filters, { period: '2026-06-01', value: 1 });

    expect(result.from).toBe('2026-06-01T00:00:00Z');
    expect(result.to).toBe('2026-06-01T23:59:59Z');
  });
});
