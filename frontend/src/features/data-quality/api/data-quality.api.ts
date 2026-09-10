import { http } from '@shared/api/http-client';

import { dataQualityResponseSchema } from './data-quality.contracts';

/** Thin transport layer: build the request, delegate parsing/errors to `http`. */
export const dataQualityApi = {
  get: (sourceId: string | undefined, signal?: AbortSignal) =>
    http.get('/data-quality', dataQualityResponseSchema, {
      query: { source_id: sourceId },
      signal,
    }),
};
