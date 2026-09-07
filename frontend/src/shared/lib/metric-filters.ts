import { z } from 'zod';

/**
 * The dashboard filter set — shared by the dashboard, the session list and the
 * data-quality view. Defined once here; consumed as URL search params so a
 * filtered view (and every drill-down) is shareable by link.
 */
export const metricFiltersSchema = z.object({
  sources: z.array(z.string()).default([]),
  agents: z.array(z.string()).default([]),
  models: z.array(z.string()).default([]),
  from: z.string().datetime().optional(),
  to: z.string().datetime().optional(),
});

export type MetricFilters = z.infer<typeof metricFiltersSchema>;

export const EMPTY_METRIC_FILTERS: MetricFilters = {
  sources: [],
  agents: [],
  models: [],
};

/** Serialize to the query params the API expects (repeated keys, ISO dates). */
export function metricFiltersToQuery(f: MetricFilters): Record<string, string[] | string | undefined> {
  return {
    source: f.sources,
    agent: f.agents,
    model: f.models,
    from: f.from,
    to: f.to,
  };
}

export function hasActiveFilters(f: MetricFilters): boolean {
  return (
    f.sources.length > 0 ||
    f.agents.length > 0 ||
    f.models.length > 0 ||
    f.from !== undefined ||
    f.to !== undefined
  );
}
