import { http } from '@shared/api/http-client';

import { chatReplySchema, chatRequestSchema, type ChatRequest } from './chat.contracts';

/**
 * Thin transport layer for the mapping agent conversation.
 *
 * The request is validated against its own schema before it leaves: a payload
 * that does not match `ChatRequest` fails here, with the offending field named,
 * instead of coming back as an opaque 422 from the API.
 */
export const chatApi = {
  chat: (input: ChatRequest) =>
    http.post('/chat', chatReplySchema, { body: chatRequestSchema.parse(input) }),
};
