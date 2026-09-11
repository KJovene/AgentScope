import { describe, expect, it } from 'vitest';

import type { SessionItem } from '@shared/api/sessions.contracts';
import { breakdownBy, topSessionsByCost } from '@features/dashboard/model/breakdown';

function session(overrides: Partial<SessionItem>): SessionItem {
  return {
    session_id: 1,
    source_name: 'src',
    agent_name: 'agent',
    started_at: '2026-01-01T00:00:00Z',
    duration_ms: 1000,
    model_call_count: 1,
    tool_call_count: 0,
    total_tokens: 100,
    total_cost_usd: 1,
    error_count: 0,
    ...overrides,
  };
}

describe('breakdownBy', () => {
  it('counts sessions per category and computes each share', () => {
    const result = breakdownBy(
      [
        session({ session_id: 1, agent_name: 'a' }),
        session({ session_id: 2, agent_name: 'a' }),
        session({ session_id: 3, agent_name: 'b' }),
      ],
      'agent_name',
    );

    // Descending: the first row is the top of a horizontal bar axis.
    expect(result.map((d) => d.category)).toEqual(['a', 'b']);
    expect(result.find((d) => d.category === 'a')?.value).toBe(2);
    expect(result.find((d) => d.category === 'a')?.share).toBeCloseTo(2 / 3);
  });

  it('sums an arbitrary measure and skips rows where it is missing', () => {
    const result = breakdownBy(
      [
        session({ session_id: 1, source_name: 's1', total_cost_usd: 2 }),
        session({ session_id: 2, source_name: 's1', total_cost_usd: null }),
        session({ session_id: 3, source_name: 's2', total_cost_usd: 2 }),
      ],
      'source_name',
      (s) => s.total_cost_usd,
    );

    expect(result.find((d) => d.category === 's1')?.value).toBe(2);
    expect(result.find((d) => d.category === 's1')?.share).toBeCloseTo(0.5);
  });

  it('folds the tail past six slices into a single "Autres" category', () => {
    const sessions = Array.from({ length: 9 }, (_, i) =>
      session({ session_id: i, agent_name: `agent-${i}` }),
    );

    const result = breakdownBy(sessions, 'agent_name');

    expect(result).toHaveLength(7);
    expect(result.map((d) => d.category)).toContain('Autres');
  });

  it('returns nothing when the measure never yields a positive total', () => {
    expect(breakdownBy([], 'agent_name')).toEqual([]);
    expect(
      breakdownBy([session({ total_cost_usd: null })], 'source_name', (s) => s.total_cost_usd),
    ).toEqual([]);
  });
});

describe('topSessionsByCost', () => {
  it('returns the costliest sessions first and drops those without a cost', () => {
    const result = topSessionsByCost(
      [
        session({ session_id: 1, total_cost_usd: 0.5 }),
        session({ session_id: 2, total_cost_usd: null }),
        session({ session_id: 3, total_cost_usd: 9 }),
      ],
      2,
    );

    expect(result.map((s) => s.session_id)).toEqual([3, 1]);
  });
});
