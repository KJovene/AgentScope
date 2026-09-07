/**
 * Central registry of TanStack Query keys. One place to look, no stringly-typed
 * keys scattered across features, and cache invalidation stays consistent (DRY).
 *
 * Convention: `queryKeys.<feature>.<resource>(params?)` returns a readonly tuple.
 */
export const queryKeys = {
  imports: {
    all: ['imports'] as const,
    list: (params: Record<string, unknown>) => ['imports', 'list', params] as const,
    detail: (id: string) => ['imports', 'detail', id] as const,
    rejects: (id: string, params: Record<string, unknown>) =>
      ['imports', 'detail', id, 'rejects', params] as const,
  },
  mappings: {
    all: ['mappings'] as const,
    list: () => ['mappings', 'list'] as const,
    detail: (id: string) => ['mappings', 'detail', id] as const,
    preview: (id: string, fileRef: string) => ['mappings', 'preview', id, fileRef] as const,
  },
  analyze: {
    result: (fileRef: string) => ['analyze', fileRef] as const,
  },
  chat: {
    conversation: (conversationId: string) => ['chat', conversationId] as const,
  },
  metrics: {
    all: ['metrics'] as const,
    indicators: (filters: Record<string, unknown>) => ['metrics', 'indicators', filters] as const,
    timeseries: (filters: Record<string, unknown>, metric: string, granularity: string) =>
      ['metrics', 'timeseries', metric, granularity, filters] as const,
    toolUsage: (filters: Record<string, unknown>) => ['metrics', 'tool-usage', filters] as const,
  },
  sessions: {
    all: ['sessions'] as const,
    list: (filters: Record<string, unknown>) => ['sessions', 'list', filters] as const,
    detail: (id: string) => ['sessions', 'detail', id] as const,
  },
  sources: {
    all: ['sources'] as const,
    list: () => ['sources', 'list'] as const,
  },
  dataQuality: {
    all: ['data-quality'] as const,
    list: (filters: Record<string, unknown>) => ['data-quality', filters] as const,
  },
} as const;
