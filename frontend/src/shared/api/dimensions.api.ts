import { http } from '@shared/api/http-client';

import { filterDimensionsSchema } from './dimensions.contracts';

/** Thin transport layer: build the request, delegate parsing/errors to `http`. */
export const dimensionsApi = {
  get: (signal?: AbortSignal) =>
    http.get('/metrics/dimensions', filterDimensionsSchema, { signal }),
};
