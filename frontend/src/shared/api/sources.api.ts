import { http } from '@shared/api/http-client';

import { sourceListResponseSchema } from './sources.contracts';

/** Thin transport layer: build the request, delegate parsing/errors to `http`. */
export const sourcesApi = {
  list: (signal?: AbortSignal) => http.get('/sources', sourceListResponseSchema, { signal }),
};
