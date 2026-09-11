import { describe, expect, it } from 'vitest';

import { queryKeys } from '@shared/api/query-keys';

describe('queryKeys', () => {
  it('imports keys', () => {
    expect(queryKeys.imports.all).toEqual(['imports']);
    expect(queryKeys.imports.list({ limit: 25 })).toEqual(['imports', 'list', { limit: 25 }]);
    expect(queryKeys.imports.detail('id1')).toEqual(['imports', 'detail', 'id1']);
    expect(queryKeys.imports.rejects('id1', { offset: 0 })).toEqual([
      'imports',
      'detail',
      'id1',
      'rejects',
      { offset: 0 },
    ]);
  });

  it('mappings / analyze / chat keys', () => {
    expect(queryKeys.mappings.list()).toEqual(['mappings', 'list']);
    expect(queryKeys.mappings.detail('m1')).toEqual(['mappings', 'detail', 'm1']);
    expect(queryKeys.mappings.preview('m1', 'f1')).toEqual(['mappings', 'preview', 'm1', 'f1']);
    expect(queryKeys.analyze.result('f1')).toEqual(['analyze', 'f1']);
    expect(queryKeys.chat.conversation('c1')).toEqual(['chat', 'c1']);
  });

  it('metrics / sessions / sources / dataQuality keys', () => {
    expect(queryKeys.metrics.indicators({ a: 1 })).toEqual(['metrics', 'indicators', { a: 1 }]);
    expect(queryKeys.metrics.timeseries({ a: 1 }, 'sessions', 'day')).toEqual([
      'metrics',
      'timeseries',
      'sessions',
      'day',
      { a: 1 },
    ]);
    expect(queryKeys.metrics.toolUsage({})).toEqual(['metrics', 'tool-usage', {}]);
    expect(queryKeys.sessions.list({})).toEqual(['sessions', 'list', {}]);
    expect(queryKeys.sessions.detail('s1')).toEqual(['sessions', 'detail', 's1']);
    expect(queryKeys.sources.list()).toEqual(['sources', 'list']);
    expect(queryKeys.dataQuality.list({})).toEqual(['data-quality', {}]);
  });
});
