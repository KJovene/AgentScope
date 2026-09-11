import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { queryWrapper } from '../../utils';

vi.mock('@features/mapping-agent/api/analyze.api', () => ({
  analyzeApi: { analyze: vi.fn() },
}));

import { analyzeApi } from '@features/mapping-agent/api/analyze.api';
import { useAnalyzeMutation } from '@features/mapping-agent/api/analyze.queries';

const mockedApi = vi.mocked(analyzeApi, true);

afterEach(() => vi.clearAllMocks());

describe('useAnalyzeMutation', () => {
  it('calls analyzeApi.analyze with the selected file and returns the result', async () => {
    const analyzeResult = {
      profile: { record_count: 1, fields: [] },
      proposal: { definition: {}, explanations: [], ambiguities: [], unmapped_fields: [] },
    };
    mockedApi.analyze.mockResolvedValueOnce(analyzeResult);

    const { result } = renderHook(() => useAnalyzeMutation(), { wrapper: queryWrapper() });
    const file = new File(['{}'], 'trace.jsonl');

    result.current.mutate({ file });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockedApi.analyze).toHaveBeenCalledWith({ file });
    expect(result.current.data?.profile.record_count).toBe(1);
  });

  it('surfaces the rejected error', async () => {
    mockedApi.analyze.mockRejectedValueOnce(
      Object.assign(new Error('nope'), { status: 422, name: 'ApiError' }),
    );

    const { result } = renderHook(() => useAnalyzeMutation(), { wrapper: queryWrapper() });
    result.current.mutate({ file: new File(['x'], 'bad.jsonl') });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as unknown as { status: number }).status).toBe(422);
  });
});
