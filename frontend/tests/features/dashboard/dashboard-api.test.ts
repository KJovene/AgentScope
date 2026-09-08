import { HttpResponse, http } from 'msw';
import { describe, expect, it } from 'vitest';

import { dashboardApi } from '@features/dashboard/api/dashboard.api';
import { EMPTY_METRIC_FILTERS } from '@shared/lib/metric-filters';

import { server } from '../../msw/server';

const indicators = {
  session_count: 1,
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
};

describe('dashboardApi transport', () => {
  it('getIndicators() calls GET /metrics/indicators with the filter query params', async () => {
    let url: URL | undefined;
    server.use(
      http.get('/api/metrics/indicators', ({ request }) => {
        url = new URL(request.url);
        return HttpResponse.json(indicators);
      }),
    );

    const res = await dashboardApi.getIndicators({ ...EMPTY_METRIC_FILTERS, sources: ['s1'] });

    expect(res.session_count).toBe(1);
    expect(url?.searchParams.getAll('sources')).toEqual(['s1']);
  });

  it('getTimeseries() calls GET /metrics/timeseries with metric + granularity', async () => {
    let url: URL | undefined;
    server.use(
      http.get('/api/metrics/timeseries', ({ request }) => {
        url = new URL(request.url);
        return HttpResponse.json({ metric: 'tokens', granularity: 'day', points: [] });
      }),
    );

    const res = await dashboardApi.getTimeseries(EMPTY_METRIC_FILTERS, 'tokens', 'day');

    expect(res.metric).toBe('tokens');
    expect(url?.searchParams.get('metric')).toBe('tokens');
    expect(url?.searchParams.get('granularity')).toBe('day');
  });

  it('getIndicators() raises an http ApiError on a 500', async () => {
    server.use(
      http.get('/api/metrics/indicators', () =>
        HttpResponse.json({ title: 'Erreur serveur', status: 500 }, { status: 500 }),
      ),
    );

    await expect(dashboardApi.getIndicators(EMPTY_METRIC_FILTERS)).rejects.toMatchObject({
      status: 500,
      kind: 'http',
    });
  });

  it('getToolUsage() calls GET /metrics/tool-usage with the filter query params', async () => {
    let url: URL | undefined;
    server.use(
      http.get('/api/metrics/tool-usage', ({ request }) => {
        url = new URL(request.url);
        return HttpResponse.json([
          { tool_name: 'bash', n_calls: 10, n_errors: 1, avg_duration_ms: 200 },
        ]);
      }),
    );

    const res = await dashboardApi.getToolUsage({ ...EMPTY_METRIC_FILTERS, agents: ['claude'] });

    expect(res).toHaveLength(1);
    expect(res[0]?.tool_name).toBe('bash');
    expect(url?.searchParams.getAll('agents')).toEqual(['claude']);
  });
});
