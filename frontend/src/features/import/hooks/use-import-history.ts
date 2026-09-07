import { useMemo, useState } from 'react';

import { useImportsQuery } from '../api/import.queries';
import { type ImportListParams } from '../api/import.contracts';
import { toImportRow } from '../model/import.mappers';

/**
 * Composite hook: owns the list's local params (paging/filter) and adapts the
 * query result into view rows. Keeps the page component declarative.
 */
export function useImportHistory() {
  const [params, setParams] = useState<ImportListParams>({ limit: 25, offset: 0 });
  const query = useImportsQuery(params);

  const rows = useMemo(() => (query.data?.items ?? []).map(toImportRow), [query.data]);

  return {
    rows,
    total: query.data?.total ?? 0,
    params,
    setParams,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
