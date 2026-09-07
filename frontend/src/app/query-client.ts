import { QueryClient } from '@tanstack/react-query';

import { ApiError } from '@shared/api/api-error';

/**
 * One QueryClient for the app. Defaults chosen so features don't repeat retry /
 * staleTime config on every `useQuery` (DRY).
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          // Never retry 4xx — the request is wrong, retrying won't help.
          if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false;
          return failureCount < 2;
        },
      },
      mutations: {
        retry: false,
      },
    },
  });
}
