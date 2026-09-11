import { renderHook, waitFor } from '@testing-library/react';
import { HttpResponse, http } from 'msw';
import { describe, expect, it } from 'vitest';

import { sourceListResponseSchema } from '@shared/api/sources.contracts';
import { sourcesApi } from '@shared/api/sources.api';
import { useSourcesQuery } from '@shared/api/sources.queries';

import { server } from '../../msw/server';
import { queryWrapper } from '../../utils';

const rawSource = {
  id: 's1',
  name: 'TraceLab',
  description: null,
  format: 'jsonl',
  session_count: 12,
  created_at: '2026-01-01T00:00:00Z',
};

describe('sources.contracts', () => {
  it('sourceListResponseSchema accepts a well-formed list', () => {
    expect(sourceListResponseSchema.parse([rawSource])).toEqual([rawSource]);
  });

  it('sourceListResponseSchema defaults session_count to 0 when absent', () => {
    const { session_count: _drop, ...withoutCount } = rawSource;
    const [parsed] = sourceListResponseSchema.parse([withoutCount]);
    expect(parsed?.session_count).toBe(0);
  });
});

describe('sourcesApi transport', () => {
  it('list() calls GET /sources and parses the array', async () => {
    server.use(http.get('/api/sources', () => HttpResponse.json([rawSource])));

    const res = await sourcesApi.list();

    expect(res).toEqual([rawSource]);
  });
});

describe('useSourcesQuery', () => {
  it('returns the sources from sourcesApi.list', async () => {
    server.use(http.get('/api/sources', () => HttpResponse.json([rawSource])));

    const { result } = renderHook(() => useSourcesQuery(), { wrapper: queryWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.name).toBe('TraceLab');
  });
});
