import { z } from 'zod';

import { mappingProposalSchema } from './analyze.contracts';

/**
 * Wire contracts for `POST /chat` (I4.4). Mirrors `schemas/chat.py` exactly —
 * in particular `role`, which the backend types as `Literal["user","assistant"]`
 * and nothing else.
 *
 * The endpoint is stateless by design (§5.3): the client resends the whole
 * history AND the proposal under discussion at every turn, and adopts the
 * revision the agent sends back.
 */

export const chatRoleSchema = z.enum(['user', 'assistant']);
export type ChatRole = z.infer<typeof chatRoleSchema>;

export const chatTurnSchema = z.object({
  role: chatRoleSchema,
  text: z.string(),
});
export type ChatTurn = z.infer<typeof chatTurnSchema>;

export const chatRequestSchema = z.object({
  conversation_id: z.string().min(1),
  /** Full history, last element = the new user message. */
  messages: z.array(chatTurnSchema).min(1),
  current_proposal: mappingProposalSchema,
  /** Free reference to the analysed file — informative server-side. */
  file_ref: z.string().nullable().optional(),
});
export type ChatRequest = z.infer<typeof chatRequestSchema>;

export const chatReplySchema = z.object({
  text: z.string(),
  /** `null` when the agent did not revise the proposal this turn. */
  revised_proposal: mappingProposalSchema.nullable(),
  /** Always the proposal in force after this turn. */
  current_proposal: mappingProposalSchema.nullable(),
});
export type ChatReply = z.infer<typeof chatReplySchema>;
