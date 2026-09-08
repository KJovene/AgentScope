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
      sessions: 0,
      totalTokens: null,
      totalCostUsd: null,
      errorRate: null,
    }),
  ),
];
