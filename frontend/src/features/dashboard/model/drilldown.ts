import type { MetricFilters } from '@shared/lib/metric-filters';

import type { TimeSeriesPoint } from '@shared/ui';

/**
 * Drill-down (I5.14): narrows the active filters to a single day, preserving
 * every other dimension (source/agent/model). Pure — kept separate from the
 * chart's onClick wiring so the date-range math is unit-testable on its own.
 */
export function dayDrillDownFilters(filters: MetricFilters, point: TimeSeriesPoint): MetricFilters {
  return {
    ...filters,
    from: `${point.period}T00:00:00Z`,
    to: `${point.period}T23:59:59Z`,
  };
}
