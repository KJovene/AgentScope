import { z } from 'zod';

import { paginated, paginationParamsSchema } from '@shared/types/pagination';

/**
 * SINGLE SOURCE OF TRUTH for the import feature's data shapes.
 * Types are inferred from these zod schemas — never hand-write a parallel interface.
 * (Later these can be generated from the backend OpenAPI via `npm run api:generate`.)
 */

export const importStatusSchema = z.enum(['pending', 'running', 'succeeded', 'failed']);

export const importBatchSchema = z.object({
  id: z.string(),
  sourceName: z.string(),
  originalFilename: z.string(),
  fileFormat: z.enum(['jsonl', 'csv', 'parquet']),
  status: importStatusSchema,
  importedAt: z.string().datetime(),
  importedCount: z.number().int().nonnegative(),
  duplicateCount: z.number().int().nonnegative(),
  rejectedCount: z.number().int().nonnegative(),
  missingInfoCount: z.number().int().nonnegative(),
});
export type ImportBatch = z.infer<typeof importBatchSchema>;

export const importListParamsSchema = paginationParamsSchema.extend({
  source: z.string().optional(),
  status: importStatusSchema.optional(),
});
export type ImportListParams = z.infer<typeof importListParamsSchema>;

export const importListResponseSchema = paginated(importBatchSchema);

export const rejectReasonCodeSchema = z.enum([
  'unparseable_record',
  'missing_required_field',
  'transform_failed',
  'unknown_target_field',
  'duplicate_in_file',
  'schema_violation',
]);

export const importRejectSchema = z.object({
  id: z.string(),
  recordIndex: z.number().int(),
  reasonCode: rejectReasonCodeSchema,
  reasonDetail: z.string(),
});
export type ImportReject = z.infer<typeof importRejectSchema>;

export const rejectListParamsSchema = paginationParamsSchema;
export const rejectListResponseSchema = paginated(importRejectSchema);

/** Request payload for POST /imports (multipart is built in the api layer). */
export const createImportInputSchema = z.object({
  mappingId: z.string().min(1),
  files: z.array(z.instanceof(File)).min(1, 'Sélectionnez au moins un fichier.'),
});
export type CreateImportInput = z.infer<typeof createImportInputSchema>;
