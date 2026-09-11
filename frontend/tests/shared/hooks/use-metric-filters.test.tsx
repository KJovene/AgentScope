import { renderHook, act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const navigate = vi.fn();
let search: Record<string, unknown> = { sources: ['a'], agents: [], models: [] };

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => navigate,
  useSearch: () => search,
}));

import { useMetricFilters } from '@shared/hooks/use-metric-filters';

describe('useMetricFilters', () => {
  beforeEach(() => {
    navigate.mockClear();
    search = { sources: ['a'], agents: [], models: [] };
  });

  it('exposes the current search as filters', () => {
    const { result } = renderHook(() => useMetricFilters());
    expect(result.current.filters.sources).toEqual(['a']);
  });

  it('setFilters navigates in place, merging the patch', () => {
    const { result } = renderHook(() => useMetricFilters());
    act(() => result.current.setFilters({ agents: ['x'] }));

    expect(navigate).toHaveBeenCalledTimes(1);
    const arg = navigate.mock.calls[0]![0];
    expect(arg.to).toBe('.');
    expect(arg.replace).toBe(true);
    expect(arg.search({ sources: ['a'] })).toEqual({ sources: ['a'], agents: ['x'] });
  });

  it('reset navigates to an empty search', () => {
    const { result } = renderHook(() => useMetricFilters());
    act(() => result.current.reset());
    expect(navigate).toHaveBeenCalledWith({ to: '.', search: {}, replace: true });
  });
});
