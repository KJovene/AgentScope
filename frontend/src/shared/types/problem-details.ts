import { z } from 'zod';

/**
 * RFC 7807 `application/problem+json` — the backend's uniform error shape (PLAN.md §5.3).
 */
export const problemDetailsSchema = z.object({
  type: z.string().default('about:blank'),
  title: z.string(),
  status: z.number().int(),
  detail: z.string().optional(),
  errors: z
    .array(z.object({ field: z.string().optional(), message: z.string() }))
    .optional(),
});

export type ProblemDetails = z.infer<typeof problemDetailsSchema>;
