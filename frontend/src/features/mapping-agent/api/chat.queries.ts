import { useMutation } from '@tanstack/react-query';

import { chatApi } from './chat.api';
import { type ChatRequest } from './chat.contracts';

/** Server-state hook. Components use this, never `chatApi` directly. */
export function useChatMutation() {
  return useMutation({
    mutationFn: (input: ChatRequest) => chatApi.chat(input),
  });
}
