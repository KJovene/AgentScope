import { z } from 'zod';

import { paginated } from '@shared/types/pagination';

/**
 * SINGLE SOURCE OF TRUTH for the session list shape. Matches the wire format
 * (FastAPI/Pydantic, snake_case) exactly — shared across the dashboard
 * (duration distribution, drill-down target) and the session list/detail views.
 */
export const sessionItemSchema = z.object({
  session_id: z.number().int(),
  source_name: z.string(),
  agent_name: z.string().nullable().optional(),
  repository_name: z.string().nullable().optional(),
  started_at: z.string().datetime().nullable().optional(),
  duration_ms: z.number().int().nullable().optional(),
  model_call_count: z.number().int().nonnegative(),
  tool_call_count: z.number().int().nonnegative(),
  total_tokens: z.number().nullable().optional(),
  total_cost_usd: z.number().nullable().optional(),
  error_count: z.number().int().nonnegative(),
});
export type SessionItem = z.infer<typeof sessionItemSchema>;

export const sessionListResponseSchema = paginated(sessionItemSchema);

/** One entry of the chronological timeline returned by `GET /sessions/{id}`. */
export const timelineEntrySchema = z.object({
  kind: z.string(),
  sequence: z.number().int(),
  name: z.string(),
  status: z.string(),
  error_type: z.string().nullable().optional(),
  started_at: z.string().datetime().nullable().optional(),
  ended_at: z.string().datetime().nullable().optional(),
  duration_ms: z.number().int().nullable().optional(),
  prompt_tokens: z.number().int().nullable().optional(),
  completion_tokens: z.number().int().nullable().optional(),
  total_tokens: z.number().int().nullable().optional(),
  cost_usd: z.number().nullable().optional(),
});
export type TimelineEntry = z.infer<typeof timelineEntrySchema>;

export const sessionDetailSchema = z.object({
  session_id: z.number().int(),
  source_name: z.string(),
  external_id: z.string(),
  agent_name: z.string().nullable().optional(),
  repository_name: z.string().nullable().optional(),
  started_at: z.string().datetime().nullable().optional(),
  ended_at: z.string().datetime().nullable().optional(),
  duration_ms: z.number().int().nullable().optional(),
  total_tokens: z.number().int().nullable().optional(),
  total_cost_usd: z.number().nullable().optional(),
  error_count: z.number().int().nonnegative(),
  has_raw_record: z.boolean(),
  timeline: z.array(timelineEntrySchema).default([]),
});
export type SessionDetail = z.infer<typeof sessionDetailSchema>;
