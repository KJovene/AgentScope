import { z } from 'zod';

/**
 * SINGLE SOURCE OF TRUTH for the dashboard metrics shapes (indicators + time
 * series). Types are inferred from these zod schemas — never hand-write a
 * parallel interface (mirrors the `import` feature's contracts pattern).
 */

export const indicatorsResponseSchema = z.object({
  session_count: z.number().int().nonnegative(),
  model_call_count: z.number().int().nonnegative(),
  tool_call_count: z.number().int().nonnegative(),
  error_count: z.number().int().nonnegative(),
  total_tokens: z.number().nullable(),
  prompt_tokens: z.number().nullable(),
  completion_tokens: z.number().nullable(),
  cached_tokens: z.number().nullable(),
  total_cost_usd: z.number().nullable(),
  error_rate: z.number().nullable(),
  cache_hit_ratio: z.number().nullable(),
  median_session_duration_ms: z.number().nullable(),
});
export type IndicatorsResponse = z.infer<typeof indicatorsResponseSchema>;

/** Mirrors `agentscope.application.ports.metrics.TimeseriesMetric` (backend). */
export const timeseriesMetricSchema = z.enum([
  'sessions',
  'tokens',
  'model_calls',
  'tool_calls',
  'cost',
  'errors',
]);
export type TimeseriesMetric = z.infer<typeof timeseriesMetricSchema>;

/** Mirrors `agentscope.application.ports.metrics.Granularity` (backend). */
export const granularitySchema = z.enum(['day']);
export type Granularity = z.infer<typeof granularitySchema>;

export const timeseriesPointSchema = z.object({
  period: z.string(),
  value: z.number().nullable(),
});
export type TimeseriesPointResponse = z.infer<typeof timeseriesPointSchema>;

export const timeseriesResponseSchema = z.object({
  metric: timeseriesMetricSchema,
  granularity: granularitySchema,
  points: z.array(timeseriesPointSchema),
});
export type TimeseriesResponse = z.infer<typeof timeseriesResponseSchema>;
