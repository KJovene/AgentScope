import { z } from 'zod';

/**
 * SINGLE SOURCE OF TRUTH for the data-quality panel shape. Mirrors
 * `agentscope.interfaces.api.schemas.data_quality` (snake_case wire format).
 */
export const dataQualityBatchSchema = z.object({
  import_batch_id: z.string(),
  source_name: z.string(),
  imported_count: z.number().int().nonnegative(),
  duplicate_count: z.number().int().nonnegative(),
  rejected_count: z.number().int().nonnegative(),
  missing_info_count: z.number().int().nonnegative(),
  /** Ratio in [0, 1]; null when the source gives no way to compute it. */
  completeness_rate: z.number().nullable().optional(),
  imported_at: z.string().datetime().nullable().optional(),
});
export type DataQualityBatch = z.infer<typeof dataQualityBatchSchema>;

export const dataQualityResponseSchema = z.object({
  batches: z.array(dataQualityBatchSchema).default([]),
});
export type DataQualityResponse = z.infer<typeof dataQualityResponseSchema>;
