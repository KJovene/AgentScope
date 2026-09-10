import { z } from 'zod';

/**
 * SINGLE SOURCE OF TRUTH for `GET /metrics/dimensions`: the distinct values that
 * actually exist in the database, feeding the closed-choice filters.
 *
 * Deliberately unscoped by the active filters — a selected value must stay
 * offered even when the rest of the filter set excludes all of its sessions,
 * otherwise it could not be removed from its own dropdown.
 */
export const filterDimensionsSchema = z.object({
  agents: z.array(z.string()).default([]),
  models: z.array(z.string()).default([]),
});
export type FilterDimensions = z.infer<typeof filterDimensionsSchema>;
