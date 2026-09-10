import { describe, expect, it } from 'vitest';

import { chatReplySchema, chatRequestSchema } from '@features/mapping-agent/api/chat.contracts';

const proposal = {
  definition: { source_format: 'jsonl', entities: {} },
  explanations: [
    {
      target_field: 'session.external_id',
      source_field: 'session_id',
      rationale: 'clé naturelle',
      confidence: 0.8,
    },
  ],
  ambiguities: ['`agent` ambigu'],
  unmapped_fields: ['debug'],
};

describe('chat contracts (I4.4 wire format)', () => {
  it('accepts a well-formed request', () => {
    const result = chatRequestSchema.safeParse({
      conversation_id: 'c1',
      messages: [
        { role: 'assistant', text: 'Voici ma proposition.' },
        { role: 'user', text: 'Pourquoi ce champ ?' },
      ],
      current_proposal: proposal,
      file_ref: 'trace.jsonl',
    });

    expect(result.success).toBe(true);
  });

  // The backend types `role` as Literal["user","assistant"]. A UI-side "agent"
  // role is what produced `body.messages.0.role` 422s.
  it('rejects the "agent" role the backend does not know', () => {
    const result = chatRequestSchema.safeParse({
      conversation_id: 'c1',
      messages: [{ role: 'agent', text: 'Bonjour !' }],
      current_proposal: proposal,
    });

    expect(result.success).toBe(false);
    if (result.success) return;
    expect(result.error.issues[0]?.path).toEqual(['messages', 0, 'role']);
  });

  it('rejects a definition that is not an object', () => {
    const result = chatRequestSchema.safeParse({
      conversation_id: 'c1',
      messages: [{ role: 'user', text: 'x' }],
      current_proposal: { ...proposal, definition: 'default_mapping' },
    });

    expect(result.success).toBe(false);
    if (result.success) return;
    expect(result.error.issues[0]?.path).toEqual(['current_proposal', 'definition']);
  });

  it('rejects an empty history — the backend requires at least one turn', () => {
    const result = chatRequestSchema.safeParse({
      conversation_id: 'c1',
      messages: [],
      current_proposal: proposal,
    });

    expect(result.success).toBe(false);
  });

  it('parses a reply that carries no revision', () => {
    const reply = chatReplySchema.parse({
      text: 'Je garde la correspondance actuelle.',
      revised_proposal: null,
      current_proposal: proposal,
    });

    expect(reply.revised_proposal).toBeNull();
    expect(reply.current_proposal?.ambiguities).toEqual(['`agent` ambigu']);
  });
});
