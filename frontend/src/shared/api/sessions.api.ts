import { http } from '@shared/api/http-client';
import { metricFiltersToQuery, type MetricFilters } from '@shared/lib/metric-filters';

import { sessionListResponseSchema } from './sessions.contracts';

export type SessionListParams = MetricFilters & { limit: number; offset: number };

/** Thin transport layer: build the request, delegate parsing/errors to `http`. */
export const sessionsApi = {
  list: (params: SessionListParams, signal?: AbortSignal) =>
    http.get('/sessions', sessionListResponseSchema, {
      query: { ...metricFiltersToQuery(params), limit: params.limit, offset: params.offset },
      signal,
    }),
};
