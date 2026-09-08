import { afterEach, describe, expect, it, vi } from 'vitest';

import { apiClient } from '@shared/api/client';
import { ApiError } from '@shared/api/types';

function mockFetchOnce(body: unknown, init: ResponseInit = { status: 200 }) {
  const payload = typeof body === 'string' || body === undefined ? body : JSON.stringify(body);
  return vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(new Response(payload as BodyInit, init));
}

afterEach(() => vi.restoreAllMocks());

describe('apiClient', () => {
  it('GET resolves the JSON body and hits the /api/v1 base', async () => {
    const spy = mockFetchOnce({ ok: 1 });
    await expect(apiClient.get('/imports')).resolves.toEqual({ ok: 1 });
    expect(spy).toHaveBeenCalledWith('/api/v1/imports', {
      headers: { Accept: 'application/json' },
    });
  });

  it('POST serializes a JSON body with a content-type header', async () => {
    const spy = mockFetchOnce({ id: 'x' }, { status: 201 });
    await apiClient.post('/mappings', { name: 'm' });
    const [, init] = spy.mock.calls[0]!;
    expect(init?.method).toBe('POST');
    expect((init?.headers as Record<string, string>)['Content-Type']).toBe('application/json');
    expect(init?.body).toBe(JSON.stringify({ name: 'm' }));
  });

  it('POST passes FormData through untouched (no JSON content-type)', async () => {
    const spy = mockFetchOnce({ id: 'x' }, { status: 201 });
    const fd = new FormData();
    fd.append('mapping_id', 'm');
    await apiClient.post('/imports', fd);
    const [, init] = spy.mock.calls[0]!;
    expect(init?.body).toBe(fd);
    expect(init?.headers).toEqual({});
  });

  it('returns {} on 204 No Content', async () => {
    mockFetchOnce(undefined, { status: 204 });
    await expect(apiClient.get('/thing')).resolves.toEqual({});
  });

  it('throws ApiError with the parsed problem body on error', async () => {
    mockFetchOnce({ title: 'Nope', status: 404, detail: 'missing' }, { status: 404 });
    const err = (await apiClient.get('/imports/x').catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.problem).toEqual({ title: 'Nope', status: 404, detail: 'missing' });
  });

  it('throws ApiError with a synthetic problem when the error body is not JSON', async () => {
    mockFetchOnce('<html>502</html>', { status: 502, statusText: 'Bad Gateway' });
    const err = (await apiClient.get('/imports').catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.problem.status).toBe(502);
    expect(err.problem.title).toMatch(/indisponible/i);
  });
});
