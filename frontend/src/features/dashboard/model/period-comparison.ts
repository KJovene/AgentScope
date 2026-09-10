import type { MetricFilters } from '@shared/lib/metric-filters';
import type { TimeSeriesPoint } from '@shared/ui';

export interface Period {
  from: string;
  to: string;
}

/**
 * Resolves the window the dashboard is actually showing. An explicit date filter
 * wins; otherwise the window is inferred from the span the activity series
 * covers, so a comparison is still possible with no date filter set.
 *
 * Returns null when neither is available — the caller then shows no variation
 * rather than inventing a baseline.
 */
export function resolveCurrentPeriod(
  filters: MetricFilters,
  points: TimeSeriesPoint[],
): Period | null {
  if (filters.from && filters.to) return { from: filters.from, to: filters.to };

  const periods = points.map((p) => p.period).filter(Boolean).sort();
  const first = periods[0];
  const last = periods[periods.length - 1];
  if (!first || !last) return null;

  return { from: `${first}T00:00:00.000Z`, to: `${last}T23:59:59.999Z` };
}

/**
 * The window of equal length immediately preceding `period`. Ends one
 * millisecond before the current window starts, so the two never overlap.
 */
export function previousPeriod(period: Period): Period | null {
  const fromMs = Date.parse(period.from);
  const toMs = Date.parse(period.to);
  if (Number.isNaN(fromMs) || Number.isNaN(toMs) || toMs <= fromMs) return null;

  const span = toMs - fromMs;
  return {
    from: new Date(fromMs - span - 1).toISOString(),
    to: new Date(fromMs - 1).toISOString(),
  };
}

/**
 * Relative variation between the two windows, as a ratio (0.12 = +12 %).
 *
 * Null when there is no meaningful baseline: a missing value on either side, or
 * a previous window of zero. Growth from zero is undefined, never "+100 %".
 */
export function relativeDelta(
  current: number | null | undefined,
  previous: number | null | undefined,
): number | null {
  if (current == null || previous == null) return null;
  if (previous === 0) return null;
  return (current - previous) / Math.abs(previous);
}
