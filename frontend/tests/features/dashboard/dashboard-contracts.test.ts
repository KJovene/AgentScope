import { describe, expect, it } from 'vitest';

import {
  granularitySchema,
  indicatorsResponseSchema,
  timeseriesMetricSchema,
  timeseriesResponseSchema,
} from '@features/dashboard/api/dashboard.contracts';

const validIndicators = {
  session_count: 42,
  model_call_count: 10,
  tool_call_count: 5,
  error_count: 1,
  total_tokens: 1000,
  prompt_tokens: 700,
  completion_tokens: 300,
  cached_tokens: null,
  total_cost_usd: 0.5,
  error_rate: 0.1,
  cache_hit_ratio: null,
  median_session_duration_ms: 1200,
};

describe('dashboard.contracts', () => {
  it('indicatorsResponseSchema accepts a well-formed payload with nullable metrics', () => {
    expect(indicatorsResponseSchema.parse(validIndicators)).toEqual(validIndicators);
  });

  it('indicatorsResponseSchema rejects a negative count', () => {
    expect(
      indicatorsResponseSchema.safeParse({ ...validIndicators, session_count: -1 }).success,
    ).toBe(false);
  });

  it('timeseriesMetricSchema only accepts the backend enum values', () => {
    expect(timeseriesMetricSchema.options).toEqual([
      'sessions',
      'tokens',
      'model_calls',
      'tool_calls',
      'cost',
      'errors',
    ]);
    expect(timeseriesMetricSchema.safeParse('bogus').success).toBe(false);
  });

  it('granularitySchema only accepts "day"', () => {
    expect(granularitySchema.safeParse('day').success).toBe(true);
    expect(granularitySchema.safeParse('week').success).toBe(false);
  });

  it('timeseriesResponseSchema accepts null values in points', () => {
    const payload = {
      metric: 'sessions',
      granularity: 'day',
      points: [
        { period: '2026-01-01', value: 3 },
        { period: '2026-01-02', value: null },
      ],
    };
    expect(timeseriesResponseSchema.parse(payload)).toEqual(payload);
  });
});
