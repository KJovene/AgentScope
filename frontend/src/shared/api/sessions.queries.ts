import { useQuery } from '@tanstack/react-query';

import { queryKeys } from './query-keys';
import { sessionsApi, type SessionListParams } from './sessions.api';

export function useSessionsQuery(params: SessionListParams) {
  return useQuery({
    queryKey: queryKeys.sessions.list(params),
    queryFn: ({ signal }) => sessionsApi.list(params, signal),
  });
}

export function useSessionDetailQuery(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.sessions.detail(sessionId),
    queryFn: ({ signal }) => sessionsApi.detail(sessionId, signal),
    enabled: sessionId.length > 0,
  });
}
