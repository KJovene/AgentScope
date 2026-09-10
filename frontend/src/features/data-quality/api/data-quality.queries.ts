import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@shared/api/query-keys';

import { dataQualityApi } from './data-quality.api';

/** Server-state hook. Components use this, never `dataQualityApi` directly. */
export function useDataQualityQuery(sourceId?: string) {
  return useQuery({
    queryKey: queryKeys.dataQuality.list({ sourceId: sourceId ?? null }),
    queryFn: ({ signal }) => dataQualityApi.get(sourceId, signal),
  });
}
