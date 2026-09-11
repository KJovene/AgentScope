import { z } from 'zod';

import { paginated, paginationParamsSchema } from '@shared/types/pagination';

/**
 * SINGLE SOURCE OF TRUTH for the import feature's data shapes.
 * Types are inferred from these zod schemas — never hand-write a parallel interface.
 * (Later these can be generated from the backend OpenAPI via `npm run api:generate`.)
 */

/** Backend `status` is a free string (see `ImportReport.status`); no fixed enum. */
export const importStatusSchema = z.string();

/** Mirrors `ImportReport` (backend/agentscope/interfaces/api/schemas/imports.py) exactly. */
export const importBatchSchema = z.object({
  id: z.string(),
  source_id: z.string().nullable().optional(),
  mapping_id: z.string(),
  status: importStatusSchema,
  imported_at: z.string().datetime().nullable().optional(),
  imported_count: z.number().int().nonnegative(),
  duplicate_count: z.number().int().nonnegative(),
  rejected_count: z.number().int().nonnegative(),
  // The backend may return either a total or a per-field breakdown.
  missing_info_count: z.union([z.number().int().nonnegative(), z.record(z.string(), z.number())]),
});
export type ImportBatch = z.infer<typeof importBatchSchema>;

export const importListParamsSchema = paginationParamsSchema.extend({
  source: z.string().optional(),
  status: importStatusSchema.optional(),
});
export type ImportListParams = z.infer<typeof importListParamsSchema>;

export const importListResponseSchema = paginated(importBatchSchema);

/** Mirrors `RejectRecord` (backend/agentscope/interfaces/api/schemas/imports.py). */
export const importRejectSchema = z.object({
  record_index: z.number().int(),
  reason_code: z.string(),
  reason_detail: z.string(),
  payload: z.record(z.string(), z.unknown()).default({}),
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
