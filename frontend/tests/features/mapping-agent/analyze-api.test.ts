import { HttpResponse, http as mswHttp } from 'msw';
import { describe, expect, it } from 'vitest';

import { analyzeApi } from '@features/mapping-agent/api/analyze.api';

import { server } from '../../msw/server';

const analyzeResponse = {
  profile: {
    record_count: 2,
    fields: [
      {
        path: 'session_id',
        inferred_type: 'string',
        null_ratio: 0,
        distinct_count: 2,
        sample_values: ['s1', 's2'],
      },
    ],
  },
  proposal: {
    definition: { source_format: 'jsonl' },
    explanations: [],
    ambiguities: [],
    unmapped_fields: [],
  },
};

describe('analyzeApi transport', () => {
  it('analyze() POSTs the file to /analyze and parses the result', async () => {
    let method: string | undefined;
    server.use(
      mswHttp.post('/api/v1/analyze', ({ request }) => {
        method = request.method;
        return HttpResponse.json(analyzeResponse);
      }),
    );

    const file = new File(['{"session_id":"s1"}'], 'trace.jsonl');
    const result = await analyzeApi.analyze({ file });

    expect(method).toBe('POST');
    expect(result.profile.record_count).toBe(2);
    expect(result.profile.fields[0]?.path).toBe('session_id');
  });

  it('analyze() raises an http ApiError on a malformed file', async () => {
    server.use(
      mswHttp.post('/api/v1/analyze', () =>
        HttpResponse.json(
          { title: 'Fichier illisible', status: 422, detail: 'JSON invalide' },
          { status: 422 },
        ),
      ),
    );

    await expect(analyzeApi.analyze({ file: new File(['x'], 'bad.jsonl') })).rejects.toMatchObject(
      { status: 422, kind: 'http' },
    );
  });
});
