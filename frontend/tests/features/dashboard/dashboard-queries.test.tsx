import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('@features/dashboard/api/dashboard.api', () => ({
  dashboardApi: {
    getIndicators: vi.fn(),
    getTimeseries: vi.fn(),
    getToolUsage: vi.fn(),
  },
}));

import { dashboardApi } from '@features/dashboard/api/dashboard.api';
import {
  useIndicatorsQuery,
  useTimeseriesQuery,
  useToolUsageQuery,
} from '@features/dashboard/api/dashboard.queries';
import { EMPTY_METRIC_FILTERS } from '@shared/lib/metric-filters';

import { queryWrapper } from '../../utils';

const mockedApi = vi.mocked(dashboardApi, true);

afterEach(() => vi.clearAllMocks());

describe('dashboard query hooks', () => {
  it('useIndicatorsQuery returns the indicators from dashboardApi.getIndicators', async () => {
    mockedApi.getIndicators.mockResolvedValueOnce({
      session_count: 7,
      model_call_count: 0,
      tool_call_count: 0,
      error_count: 0,
      total_tokens: null,
      prompt_tokens: null,
      completion_tokens: null,
      cached_tokens: null,
      total_cost_usd: null,
      error_rate: null,
      cache_hit_ratio: null,
      median_session_duration_ms: null,
    });

    const { result } = renderHook(() => useIndicatorsQuery(EMPTY_METRIC_FILTERS), {
      wrapper: queryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.session_count).toBe(7);
    expect(mockedApi.getIndicators).toHaveBeenCalledWith(EMPTY_METRIC_FILTERS, expect.anything());
  });

  it('useTimeseriesQuery returns the points from dashboardApi.getTimeseries', async () => {
    mockedApi.getTimeseries.mockResolvedValueOnce({
      metric: 'sessions',
      granularity: 'day',
      points: [{ period: '2026-01-01', value: 3 }],
    });

    const { result } = renderHook(
      () => useTimeseriesQuery(EMPTY_METRIC_FILTERS, 'sessions', 'day'),
      { wrapper: queryWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.points).toHaveLength(1);
    expect(mockedApi.getTimeseries).toHaveBeenCalledWith(
      EMPTY_METRIC_FILTERS,
      'sessions',
      'day',
      expect.anything(),
    );
  });

  it('useTimeseriesQuery surfaces the rejected error', async () => {
    mockedApi.getTimeseries.mockRejectedValueOnce(
      Object.assign(new Error('nope'), { status: 500, name: 'ApiError' }),
    );

    const { result } = renderHook(
      () => useTimeseriesQuery(EMPTY_METRIC_FILTERS, 'sessions', 'day'),
      { wrapper: queryWrapper() },
    );

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as unknown as { status: number }).status).toBe(500);
  });

  it('useToolUsageQuery returns the items from dashboardApi.getToolUsage', async () => {
    mockedApi.getToolUsage.mockResolvedValueOnce([
      { tool_name: 'bash', n_calls: 10, n_errors: 1, avg_duration_ms: 200 },
    ]);

    const { result } = renderHook(() => useToolUsageQuery(EMPTY_METRIC_FILTERS), {
      wrapper: queryWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.tool_name).toBe('bash');
    expect(mockedApi.getToolUsage).toHaveBeenCalledWith(EMPTY_METRIC_FILTERS, expect.anything());
  });
});
