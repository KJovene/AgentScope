import { renderHook, waitFor } from '@testing-library/react';
import { HttpResponse, http } from 'msw';
import { describe, expect, it } from 'vitest';

import { sessionListResponseSchema } from '@shared/api/sessions.contracts';
import { sessionsApi } from '@shared/api/sessions.api';
import { useSessionsQuery } from '@shared/api/sessions.queries';
import { EMPTY_METRIC_FILTERS } from '@shared/lib/metric-filters';

import { server } from '../../msw/server';
import { queryWrapper } from '../../utils';

const rawSession = {
  session_id: 1,
  source_name: 'TraceLab',
  agent_name: 'claude',
  repository_name: null,
  started_at: '2026-01-01T00:00:00Z',
  duration_ms: 4200,
  model_call_count: 2,
  tool_call_count: 1,
  total_tokens: 500,
  total_cost_usd: 0.02,
  error_count: 0,
};

describe('sessions.contracts', () => {
  it('sessionListResponseSchema accepts a well-formed page', () => {
    const page = { items: [rawSession], total: 1, limit: 200, offset: 0 };
    expect(sessionListResponseSchema.parse(page)).toEqual(page);
  });

  it('sessionListResponseSchema accepts a null duration_ms (no timing)', () => {
    const page = { items: [{ ...rawSession, duration_ms: null }], total: 1, limit: 200, offset: 0 };
    expect(sessionListResponseSchema.parse(page).items[0]?.duration_ms).toBeNull();
  });
});

describe('sessionsApi transport', () => {
  it('list() calls GET /sessions with the filters + pagination query params', async () => {
    let url: URL | undefined;
    server.use(
      http.get('/api/sessions', ({ request }) => {
        url = new URL(request.url);
        return HttpResponse.json({ items: [rawSession], total: 1, limit: 200, offset: 0 });
      }),
    );

    const res = await sessionsApi.list({ ...EMPTY_METRIC_FILTERS, limit: 200, offset: 0 });

    expect(res.items).toHaveLength(1);
    expect(url?.searchParams.get('limit')).toBe('200');
    expect(url?.searchParams.get('offset')).toBe('0');
  });
});

describe('useSessionsQuery', () => {
  it('returns the page from sessionsApi.list', async () => {
    server.use(
      http.get('/api/sessions', () =>
        HttpResponse.json({ items: [rawSession], total: 1, limit: 200, offset: 0 }),
      ),
    );

    const { result } = renderHook(
      () => useSessionsQuery({ ...EMPTY_METRIC_FILTERS, limit: 200, offset: 0 }),
      { wrapper: queryWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items[0]?.duration_ms).toBe(4200);
  });
});
