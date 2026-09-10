import type { SessionItem } from '@shared/api/sessions.contracts';
import type { BreakdownDatum } from '@shared/ui';

import { UNAVAILABLE } from '@shared/lib/format';

/** Past this many slices, adjacent categories blur — the tail folds into "Autres". */
const MAX_SLICES = 6;

type Dimension = 'source_name' | 'agent_name' | 'repository_name';

/**
 * Groups the already-fetched session page by a nominal dimension and returns the
 * top slices with their share of the total. Pure, so the grouping is unit-testable
 * without a component.
 *
 * The tail is folded into a single "Autres" slice rather than cycling extra hues.
 */
export function breakdownBy(
  sessions: SessionItem[],
  dimension: Dimension,
  measure: (session: SessionItem) => number | null | undefined = () => 1,
): BreakdownDatum[] {
  const totals = new Map<string, number>();

  for (const session of sessions) {
    const value = measure(session);
    if (value == null || Number.isNaN(value)) continue;
    const key = session[dimension] ?? UNAVAILABLE;
    totals.set(key, (totals.get(key) ?? 0) + value);
  }

  const sorted = [...totals.entries()].sort((a, b) => b[1] - a[1]);
  const grandTotal = sorted.reduce((sum, [, value]) => sum + value, 0);
  if (grandTotal <= 0) return [];

  const head = sorted.slice(0, MAX_SLICES);
  const tailTotal = sorted.slice(MAX_SLICES).reduce((sum, [, value]) => sum + value, 0);
  const slices = tailTotal > 0 ? [...head, ['Autres', tailTotal] as const] : head;

  // A horizontal category axis renders the first row at the top, so the
  // descending sort already puts the largest slice there.
  return slices.map(([category, value]) => ({ category, value, share: value / grandTotal }));
}

/** The N costliest sessions of the page, largest first. Sessions without a cost are dropped. */
export function topSessionsByCost(sessions: SessionItem[], limit = 5): SessionItem[] {
  return sessions
    .filter((session) => session.total_cost_usd != null)
    .sort((a, b) => (b.total_cost_usd ?? 0) - (a.total_cost_usd ?? 0))
    .slice(0, limit);
}
