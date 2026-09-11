import { z } from 'zod';

/**
 * SINGLE SOURCE OF TRUTH for the source registry shape. Matches the wire
 * format (FastAPI/Pydantic, snake_case) exactly — shared across the
 * dashboard, session list and data-quality views (all consume `GET /sources`
 * to populate their source filter).
 */
export const sourceSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  format: z.string().nullable().optional(),
  session_count: z.number().int().nonnegative().default(0),
  created_at: z.string().datetime().nullable().optional(),
});
export type Source = z.infer<typeof sourceSchema>;

export const sourceListResponseSchema = z.array(sourceSchema);
