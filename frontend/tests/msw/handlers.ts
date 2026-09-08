import { HttpResponse, http } from 'msw';

/**
 * Default happy-path handlers. Individual tests override per-endpoint with
 * `server.use(...)`. Keep fixtures minimal and shaped like the real contracts.
 */
export const handlers = [
  http.get('/api/imports', () =>
    HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 }),
  ),

  http.get('/api/metrics/indicators', () =>
    HttpResponse.json({
      session_count: 0,
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
    }),
  ),

  http.get('/api/metrics/timeseries', () =>
    HttpResponse.json({ metric: 'sessions', granularity: 'day', points: [] }),
  ),

  http.get('/api/sources', () => HttpResponse.json([])),
];
