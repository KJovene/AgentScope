import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { queryWrapper } from '../../utils';

vi.mock('@features/import/api/import.api', () => ({
  importApi: {
    list: vi.fn(),
    getById: vi.fn(),
    listRejects: vi.fn(),
    create: vi.fn(),
  },
}));

import { importApi } from '@features/import/api/import.api';
import {
  useCreateImportMutation,
  useImportQuery,
  useImportRejectsQuery,
  useImportsQuery,
} from '@features/import/api/import.queries';
import { useImportHistory } from '@features/import/hooks/use-import-history';
import { makeTestQueryClient } from '../../utils';

const mockedApi = vi.mocked(importApi, true);

const batch = {
  id: 'sha-1',
  source_id: 'src-tracelab',
  mapping_id: 'tracelab-jsonl',
  status: 'completed',
  imported_at: '2026-01-02T10:00:00Z',
  imported_count: 10,
  duplicate_count: 1,
  rejected_count: 2,
  missing_info_count: 0,
};

afterEach(() => vi.clearAllMocks());

describe('import query hooks', () => {
  it('useImportsQuery returns the page from importApi.list', async () => {
    mockedApi.list.mockResolvedValueOnce({ items: [batch], total: 1, limit: 50, offset: 0 });
    const { result } = renderHook(() => useImportsQuery({ limit: 50, offset: 0 }), {
      wrapper: queryWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total).toBe(1);
    expect(mockedApi.list).toHaveBeenCalledWith({ limit: 50, offset: 0 }, expect.anything());
  });

  it('useImportQuery surfaces the rejected error', async () => {
    mockedApi.getById.mockRejectedValueOnce(
      Object.assign(new Error('nope'), { status: 404, name: 'ApiError' }),
    );
    const { result } = renderHook(() => useImportQuery('missing'), { wrapper: queryWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as unknown as { status: number }).status).toBe(404);
  });

  it('useImportRejectsQuery fetches the rejects page for an import', async () => {
    mockedApi.listRejects.mockResolvedValueOnce({
      items: [{ record_index: 3, reason_code: 'missing_required_field', reason_detail: 'x' }],
      total: 1,
      limit: 50,
      offset: 0,
    });
    const { result } = renderHook(
      () => useImportRejectsQuery('sha-1', { limit: 50, offset: 0 }),
      { wrapper: queryWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items[0]?.reason_code).toBe('missing_required_field');
    expect(mockedApi.listRejects).toHaveBeenCalledWith(
      'sha-1',
      { limit: 50, offset: 0 },
      expect.anything(),
    );
  });
});

describe('useCreateImportMutation', () => {
  it('posts the import and invalidates imports / metrics / data-quality caches', async () => {
    mockedApi.create.mockResolvedValueOnce({ id: 'sha-1' } as never);
    const client = makeTestQueryClient();
    const invalidate = vi.spyOn(client, 'invalidateQueries').mockResolvedValue(undefined);

    const { result } = renderHook(() => useCreateImportMutation(), {
      wrapper: queryWrapper(client),
    });

    result.current.mutate({ mappingId: 'demo', files: [new File(['{}'], 'a.jsonl')] });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.create).toHaveBeenCalledOnce();
    const invalidated = invalidate.mock.calls.map((c) => c[0]?.queryKey?.[0]);
    expect(invalidated).toEqual(expect.arrayContaining(['imports', 'metrics', 'data-quality']));
  });
});

describe('useImportHistory', () => {
  it('adapts query items into formatted rows and exposes paging state', async () => {
    mockedApi.list.mockResolvedValue({ items: [batch], total: 1, limit: 25, offset: 0 });
    const { result } = renderHook(() => useImportHistory(), { wrapper: queryWrapper() });

    await waitFor(() => expect(result.current.rows).toHaveLength(1));
    expect(result.current.rows[0]?.statusLabel).toBe('Réussi');
    expect(result.current.total).toBe(1);
    expect(result.current.params).toEqual({ limit: 25, offset: 0 });
    expect(typeof result.current.setParams).toBe('function');
  });

  it('reports the error state with empty rows', async () => {
    mockedApi.list.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useImportHistory(), { wrapper: queryWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.rows).toEqual([]);
  });
});
