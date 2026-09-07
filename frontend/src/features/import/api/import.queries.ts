import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@shared/api/query-keys';

import { importApi } from './import.api';
import { type CreateImportInput, type ImportListParams } from './import.contracts';

/** Server-state hooks. Components use these, never `importApi` directly. */

export function useImportsQuery(params: ImportListParams) {
  return useQuery({
    queryKey: queryKeys.imports.list(params),
    queryFn: ({ signal }) => importApi.list(params, signal),
  });
}

export function useImportQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.imports.detail(id),
    queryFn: ({ signal }) => importApi.getById(id, signal),
  });
}

export function useImportRejectsQuery(id: string, params: { limit: number; offset: number }) {
  return useQuery({
    queryKey: queryKeys.imports.rejects(id, params),
    queryFn: ({ signal }) => importApi.listRejects(id, params, signal),
  });
}

export function useCreateImportMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateImportInput) => importApi.create(input),
    onSuccess: () => {
      // Import changes lists and every metric.
      void qc.invalidateQueries({ queryKey: queryKeys.imports.all });
      void qc.invalidateQueries({ queryKey: queryKeys.metrics.all });
      void qc.invalidateQueries({ queryKey: queryKeys.dataQuality.all });
    },
  });
}
