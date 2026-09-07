import { z } from 'zod';

import { env } from '@shared/config/env';

import { ApiError } from './api-error';

type QueryValue = string | number | boolean | null | undefined | Array<string | number>;

export interface RequestOptions {
  /** Query params. Arrays are repeated: `{ source: ['a', 'b'] }` -> `?source=a&source=b`. */
  query?: Record<string, QueryValue>;
  /** JSON body. Mutually exclusive with `formData`. */
  body?: unknown;
  /** Multipart body (file uploads). */
  formData?: FormData;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(
    `${env.apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`,
    window.location.origin,
  );
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) value.forEach((v) => url.searchParams.append(key, String(v)));
    else url.searchParams.set(key, String(value));
  }
  return url.toString();
}

async function request<T>(
  method: string,
  path: string,
  schema: z.ZodType<T>,
  options: RequestOptions = {},
): Promise<T> {
  const init: RequestInit = {
    method,
    signal: options.signal,
    headers: { Accept: 'application/json', ...options.headers },
  };

  if (options.formData) {
    init.body = options.formData;
  } else if (options.body !== undefined) {
    init.body = JSON.stringify(options.body);
    init.headers = { ...init.headers, 'Content-Type': 'application/json' };
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, options.query), init);
  } catch (cause) {
    throw new ApiError({ message: 'Network error', status: 0, kind: 'network', cause });
  }

  if (!response.ok) throw await ApiError.fromResponse(response);

  // 204 / empty body
  if (response.status === 204) return schema.parse(undefined);

  const raw: unknown = await response.json();
  const parsed = schema.safeParse(raw);
  if (!parsed.success) {
    throw new ApiError({
      message: 'Unexpected response shape from the API',
      status: response.status,
      kind: 'parse',
      cause: parsed.error,
    });
  }
  return parsed.data;
}

/**
 * The single HTTP client. Features never call `fetch` directly — they call
 * `http.get(path, zodSchema)` so every response is runtime-validated and every
 * error is an `ApiError` (DRY + type-safe end to end).
 */
export const http = {
  get: <T>(path: string, schema: z.ZodType<T>, options?: RequestOptions) =>
    request('GET', path, schema, options),
  post: <T>(path: string, schema: z.ZodType<T>, options?: RequestOptions) =>
    request('POST', path, schema, options),
  put: <T>(path: string, schema: z.ZodType<T>, options?: RequestOptions) =>
    request('PUT', path, schema, options),
  patch: <T>(path: string, schema: z.ZodType<T>, options?: RequestOptions) =>
    request('PATCH', path, schema, options),
  delete: <T>(path: string, schema: z.ZodType<T>, options?: RequestOptions) =>
    request('DELETE', path, schema, options),
};
