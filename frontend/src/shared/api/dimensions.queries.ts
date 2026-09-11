import { useQuery } from '@tanstack/react-query';

import { dimensionsApi } from './dimensions.api';
import { queryKeys } from './query-keys';

/**
 * Available filter values (rarely change) — a long `staleTime` avoids refetching
 * them every time the filter panel mounts, mirroring `useSourcesQuery`.
 */
export function useFilterDimensionsQuery() {
  return useQuery({
    queryKey: queryKeys.metrics.dimensions(),
    queryFn: ({ signal }) => dimensionsApi.get(signal),
    staleTime: 5 * 60_000,
  });
}
