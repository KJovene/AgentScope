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
