import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@shared/api/query-keys';
import type { MetricFilters } from '@shared/lib/metric-filters';

import { dashboardApi } from './dashboard.api';
import type { Granularity, TimeseriesMetric } from './dashboard.contracts';

/** Server-state hooks. Components use these, never `dashboardApi` directly. */

export function useIndicatorsQuery(filters: MetricFilters) {
  return useQuery({
    queryKey: queryKeys.metrics.indicators(filters),
    queryFn: ({ signal }) => dashboardApi.getIndicators(filters, signal),
  });
}

export function useTimeseriesQuery(
  filters: MetricFilters,
  metric: TimeseriesMetric,
  granularity: Granularity = 'day',
) {
  return useQuery({
    queryKey: queryKeys.metrics.timeseries(filters, metric, granularity),
    queryFn: ({ signal }) => dashboardApi.getTimeseries(filters, metric, granularity, signal),
  });
}

export function useToolUsageQuery(filters: MetricFilters) {
  return useQuery({
    queryKey: queryKeys.metrics.toolUsage(filters),
    queryFn: ({ signal }) => dashboardApi.getToolUsage(filters, signal),
  });
}
