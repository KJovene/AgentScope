import { z } from 'zod';

/**
 * SINGLE SOURCE OF TRUTH for the mapping-agent feature's data shapes.
 * Matches the wire format (FastAPI/Pydantic, snake_case) exactly — the
 * camelCase view model used by the UI lives in `model/analyze.mappers.ts`.
 */

export const fieldProfileSchema = z.object({
  path: z.string(),
  inferred_type: z.string(),
  null_ratio: z.number().min(0).max(1),
  distinct_count: z.number().int().nonnegative(),
  sample_values: z.array(z.unknown()),
});
export type FieldProfile = z.infer<typeof fieldProfileSchema>;

export const fieldProfileSetSchema = z.object({
  record_count: z.number().int().nonnegative(),
  fields: z.array(fieldProfileSchema),
});
export type FieldProfileSet = z.infer<typeof fieldProfileSetSchema>;

/**
 * The proposal `/analyze` returns and `/chat` discusses (I5.6). `definition` is
 * an object, never a string — the backend rejects anything else. Kept loose on
 * its inner shape on purpose: the mapping definition is opaque to the UI.
 */
export const mappingProposalSchema = z.object({
  definition: z.record(z.string(), z.unknown()),
  explanations: z.array(
    z.object({
      target_field: z.string(),
      source_field: z.string().nullable(),
      rationale: z.string(),
      confidence: z.number(),
    }),
  ),
  ambiguities: z.array(z.string()),
  unmapped_fields: z.array(z.string()),
});
export type MappingProposal = z.infer<typeof mappingProposalSchema>;

export const analyzeResultSchema = z.object({
  profile: fieldProfileSetSchema,
  proposal: mappingProposalSchema,
});
export type AnalyzeResult = z.infer<typeof analyzeResultSchema>;

export const analyzeFileInputSchema = z.object({
  file: z.instanceof(File),
});
export type AnalyzeFileInput = z.infer<typeof analyzeFileInputSchema>;
