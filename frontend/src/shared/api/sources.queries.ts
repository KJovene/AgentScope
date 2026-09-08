import { useQuery } from '@tanstack/react-query';

import { queryKeys } from './query-keys';
import { sourcesApi } from './sources.api';

/**
 * Source registry (rarely changes) — a long `staleTime` avoids refetching it
 * every time a filter panel mounts.
 */
export function useSourcesQuery() {
  return useQuery({
    queryKey: queryKeys.sources.list(),
    queryFn: ({ signal }) => sourcesApi.list(signal),
    staleTime: 5 * 60_000,
  });
}

