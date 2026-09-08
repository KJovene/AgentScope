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
 * Not rendered yet — the mapping proposal is built on by I5.6 (chat) and
 * I5.7 (mapping edition). Kept loose on purpose: just enough to type-check
 * and round-trip, not to display.
 */
const mappingProposalSchema = z.object({
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
