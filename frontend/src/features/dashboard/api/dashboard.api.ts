import { http } from '@shared/api/http-client';
import { metricFiltersToQuery, type MetricFilters } from '@shared/lib/metric-filters';

import {
  indicatorsResponseSchema,
  timeseriesResponseSchema,
  type Granularity,
  type TimeseriesMetric,
} from './dashboard.contracts';

/**
 * Thin transport layer: build the request, delegate parsing/errors to `http`.
 * No React, no caching, no formatting here.
 */
export const dashboardApi = {
  getIndicators: (filters: MetricFilters, signal?: AbortSignal) =>
    http.get('/metrics/indicators', indicatorsResponseSchema, {
      query: metricFiltersToQuery(filters),
      signal,
    }),

  getTimeseries: (
    filters: MetricFilters,
    metric: TimeseriesMetric,
    granularity: Granularity,
    signal?: AbortSignal,
  ) =>
    http.get('/metrics/timeseries', timeseriesResponseSchema, {
      query: { ...metricFiltersToQuery(filters), metric, granularity },
      signal,
    }),
};
