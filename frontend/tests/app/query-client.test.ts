import { describe, expect, it } from 'vitest';

import { ApiError } from '@shared/api/api-error';
import { createQueryClient } from '@app/query-client';

describe('createQueryClient', () => {
  it('sets sane query/mutation defaults', () => {
    const qc = createQueryClient();
    const q = qc.getDefaultOptions().queries;
    expect(q?.staleTime).toBe(30_000);
    expect(q?.refetchOnWindowFocus).toBe(false);
    expect(qc.getDefaultOptions().mutations?.retry).toBe(false);
  });

  it('never retries a 4xx ApiError but retries transient errors up to twice', () => {
    const retry = createQueryClient().getDefaultOptions().queries?.retry as (
      n: number,
      e: unknown,
    ) => boolean;

    expect(retry(0, new ApiError({ message: 'bad', status: 404, kind: 'http' }))).toBe(false);
    expect(retry(0, new ApiError({ message: 'oops', status: 500, kind: 'http' }))).toBe(true);
    expect(retry(1, new Error('flaky'))).toBe(true);
    expect(retry(2, new Error('flaky'))).toBe(false);
  });
});
