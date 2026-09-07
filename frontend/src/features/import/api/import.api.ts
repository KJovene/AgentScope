import { http } from '@shared/api/http-client';

import {
  type CreateImportInput,
  type ImportListParams,
  importBatchSchema,
  importListResponseSchema,
  rejectListResponseSchema,
} from './import.contracts';

/**
 * Thin transport layer: build the request, delegate parsing/errors to `http`.
 * No React, no caching, no formatting here.
 */
export const importApi = {
  list: (params: ImportListParams, signal?: AbortSignal) =>
    http.get('/imports', importListResponseSchema, { query: { ...params }, signal }),

  getById: (id: string, signal?: AbortSignal) =>
    http.get(`/imports/${id}`, importBatchSchema, { signal }),

  listRejects: (id: string, params: { limit: number; offset: number }, signal?: AbortSignal) =>
    http.get(`/imports/${id}/rejects`, rejectListResponseSchema, { query: params, signal }),

  create: (input: CreateImportInput) => {
    const formData = new FormData();
    formData.append('mapping_id', input.mappingId);
    input.files.forEach((file) => formData.append('files', file, file.name));
    return http.post('/imports', importBatchSchema, { formData });
  },
};
