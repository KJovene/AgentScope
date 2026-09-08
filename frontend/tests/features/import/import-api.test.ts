import { HttpResponse, http as mswHttp } from 'msw';
import { describe, expect, it } from 'vitest';

import { importApi } from '@features/import/api/import.api';

import { server } from '../../msw/server';

const batch = {
  id: 'sha-1',
  sourceName: 'TraceLab',
  originalFilename: 'trace.jsonl',
  fileFormat: 'jsonl',
  status: 'succeeded',
  importedAt: '2026-01-02T10:00:00Z',
  importedCount: 10,
  duplicateCount: 1,
  rejectedCount: 2,
  missingInfoCount: 0,
};

describe('importApi transport', () => {
  it('list() calls GET /imports with the pagination params and parses the page', async () => {
    let url: URL | undefined;
    server.use(
      mswHttp.get('/api/imports', ({ request }) => {
        url = new URL(request.url);
        return HttpResponse.json({ items: [batch], total: 1, limit: 25, offset: 0 });
      }),
    );
    const res = await importApi.list({ limit: 25, offset: 0 });
    expect(res.items[0]?.id).toBe('sha-1');
    expect(res.total).toBe(1);
    expect(url?.searchParams.get('limit')).toBe('25');
  });

  it('getById() calls GET /imports/:id', async () => {
    server.use(mswHttp.get('/api/imports/sha-1', () => HttpResponse.json(batch)));
    expect((await importApi.getById('sha-1')).originalFilename).toBe('trace.jsonl');
  });

  it('getById() raises an http ApiError on a 404', async () => {
    server.use(
      mswHttp.get('/api/imports/missing', () =>
        HttpResponse.json({ title: 'Introuvable', status: 404 }, { status: 404 }),
      ),
    );
    await expect(importApi.getById('missing')).rejects.toMatchObject({ status: 404, kind: 'http' });
  });

  it('listRejects() calls GET /imports/:id/rejects', async () => {
    server.use(
      mswHttp.get('/api/imports/sha-1/rejects', () =>
        HttpResponse.json({
          items: [
            { id: 'r1', recordIndex: 3, reasonCode: 'missing_required_field', reasonDetail: 'x' },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      ),
    );
    const res = await importApi.listRejects('sha-1', { limit: 50, offset: 0 });
    expect(res.items[0]?.reasonCode).toBe('missing_required_field');
  });

  it('create() POSTs to /imports and returns the parsed batch', async () => {
    let method: string | undefined;
    server.use(
      mswHttp.post('/api/imports', ({ request }) => {
        method = request.method;
        return HttpResponse.json(batch);
      }),
    );
    const res = await importApi.create({
      mappingId: 'demo',
      files: [new File(['{}'], 'a.jsonl')],
    });
    expect(method).toBe('POST');
    expect(res.id).toBe('sha-1');
  });
});
