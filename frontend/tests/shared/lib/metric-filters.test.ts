import { describe, expect, it } from 'vitest';

import {
  EMPTY_METRIC_FILTERS,
  hasActiveFilters,
  metricFiltersSchema,
  metricFiltersToQuery,
  type MetricFilters,
} from '@shared/lib/metric-filters';

describe('metric-filters', () => {
  it('schema fills array defaults', () => {
    expect(metricFiltersSchema.parse({})).toEqual({ sources: [], agents: [], models: [] });
  });

  it('schema rejects a non-datetime "from"', () => {
    expect(metricFiltersSchema.safeParse({ from: 'yesterday' }).success).toBe(false);
  });

  it('EMPTY_METRIC_FILTERS has no active filter', () => {
    expect(hasActiveFilters(EMPTY_METRIC_FILTERS)).toBe(false);
  });

  it('hasActiveFilters detects each dimension', () => {
    const base = EMPTY_METRIC_FILTERS;
    expect(hasActiveFilters({ ...base, sources: ['a'] })).toBe(true);
    expect(hasActiveFilters({ ...base, agents: ['a'] })).toBe(true);
    expect(hasActiveFilters({ ...base, models: ['a'] })).toBe(true);
    expect(hasActiveFilters({ ...base, from: '2026-01-01T00:00:00Z' })).toBe(true);
    expect(hasActiveFilters({ ...base, to: '2026-01-01T00:00:00Z' })).toBe(true);
  });

  it('metricFiltersToQuery maps to the API param names', () => {
    const f: MetricFilters = {
      sources: ['s1'],
      agents: ['a1'],
      models: ['m1'],
      from: '2026-01-01T00:00:00Z',
      to: undefined,
    };
    expect(metricFiltersToQuery(f)).toEqual({
      source: ['s1'],
      agent: ['a1'],
      model: ['m1'],
      from: '2026-01-01T00:00:00Z',
      to: undefined,
    });
  });
});
