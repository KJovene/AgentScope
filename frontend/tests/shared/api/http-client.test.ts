import { HttpResponse, http as mswHttp } from 'msw';
import { describe, expect, it } from 'vitest';
import { z } from 'zod';

import { ApiError } from '@shared/api/api-error';
import { http } from '@shared/api/http-client';

import { server } from '../../msw/server';

const itemSchema = z.object({ id: z.string() });

describe('http client', () => {
  it('GET parses the response against the schema and repeats array query params', async () => {
    let seen: URL | undefined;
    server.use(
      mswHttp.get('/api/things', ({ request }) => {
        seen = new URL(request.url);
        return HttpResponse.json({ id: 'ok' });
      }),
    );

    const data = await http.get('/things', itemSchema, {
      query: { source: ['a', 'b'], limit: 10, skip: undefined, none: null },
    });

    expect(data).toEqual({ id: 'ok' });
    expect(seen?.searchParams.getAll('source')).toEqual(['a', 'b']);
    expect(seen?.searchParams.get('limit')).toBe('10');
    expect(seen?.searchParams.has('skip')).toBe(false);
    expect(seen?.searchParams.has('none')).toBe(false);
  });

  it('POST sends a JSON body with the right content-type', async () => {
    let contentType: string | null = null;
    let body: unknown;
    server.use(
      mswHttp.post('/api/things', async ({ request }) => {
        contentType = request.headers.get('content-type');
        body = await request.json();
        return HttpResponse.json({ id: 'created' });
      }),
    );

    const data = await http.post('/things', itemSchema, { body: { id: 'x' } });
    expect(data).toEqual({ id: 'created' });
    expect(contentType).toContain('application/json');
    expect(body).toEqual({ id: 'x' });
  });

  it('POST forwards FormData without forcing a JSON content-type', async () => {
    let contentType: string | null = null;
    server.use(
      mswHttp.post('/api/upload', ({ request }) => {
        contentType = request.headers.get('content-type');
        return HttpResponse.json({ id: 'up' });
      }),
    );
    const fd = new FormData();
    fd.append('f', new File(['x'], 'x.txt'));
    await expect(http.post('/upload', itemSchema, { formData: fd })).resolves.toEqual({ id: 'up' });
    expect(contentType ?? '').not.toContain('application/json');
  });

  it('throws an http ApiError carrying the problem body on a 4xx/5xx', async () => {
    server.use(
      mswHttp.get('/api/boom', () =>
        HttpResponse.json({ title: 'Boom', status: 500 }, { status: 500 }),
      ),
    );
    await expect(http.get('/boom', itemSchema)).rejects.toMatchObject({
      name: 'ApiError',
      status: 500,
      kind: 'http',
    });
  });

  it('throws a parse ApiError when the response shape is unexpected', async () => {
    server.use(mswHttp.get('/api/wrong', () => HttpResponse.json({ nope: true })));
    const err = (await http.get('/wrong', itemSchema).catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.kind).toBe('parse');
  });

  it('throws a network ApiError when fetch itself fails', async () => {
    server.use(mswHttp.get('/api/offline', () => HttpResponse.error()));
    const err = (await http.get('/offline', itemSchema).catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.kind).toBe('network');
    expect(err.status).toBe(0);
  });

  it('handles a 204 with an "undefined-tolerant" schema', async () => {
    server.use(mswHttp.delete('/api/things/1', () => new HttpResponse(null, { status: 204 })));
    await expect(http.delete('/things/1', z.undefined())).resolves.toBeUndefined();
  });
});
