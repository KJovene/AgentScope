import { beforeEach, describe, expect, it } from 'vitest';

import {
  EMPTY_PROPOSAL,
  toWireMessages,
  useWorkbenchStore,
} from '@features/mapping-agent/model/workbench-store';

const proposal = {
  definition: { source_format: 'jsonl' },
  explanations: [
    {
      target_field: 'session.external_id',
      source_field: 'session_id',
      rationale: 'clé naturelle',
      confidence: 0.9,
    },
  ],
  ambiguities: ['`agent` ambigu'],
  unmapped_fields: ['debug'],
};

const revised = { ...proposal, ambiguities: [], unmapped_fields: [] };

describe('workbench store (conversation state, §5.3)', () => {
  beforeEach(() => useWorkbenchStore.getState().reset());

  it('opens a session on the proposal returned by /analyze', () => {
    useWorkbenchStore.getState().startSession({ fileRef: 'trace.jsonl', proposal });
    const state = useWorkbenchStore.getState();

    expect(state.conversationId).toBeTruthy();
    expect(state.proposal).toEqual(proposal);
    expect(state.turns).toHaveLength(1);
    expect(state.turns[0]?.role).toBe('assistant');
    expect(state.turns[0]?.text).toContain('trace.jsonl');
    expect(state.turns[0]?.ambiguities).toEqual(['`agent` ambigu']);
  });

  it('keeps the full history — the server holds none', () => {
    const store = useWorkbenchStore.getState();
    store.startSession({ fileRef: 'trace.jsonl', proposal });
    store.appendUserTurn('Pourquoi ce champ ?');
    useWorkbenchStore.getState().applyReply({
      text: 'Parce que c’est la clé naturelle.',
      revised_proposal: null,
      current_proposal: proposal,
    });

    expect(toWireMessages(useWorkbenchStore.getState().turns)).toEqual([
      { role: 'assistant', text: expect.stringContaining('trace.jsonl') },
      { role: 'user', text: 'Pourquoi ce champ ?' },
      { role: 'assistant', text: 'Parce que c’est la clé naturelle.' },
    ]);
  });

  it('adopts the proposal the agent revised', () => {
    useWorkbenchStore.getState().startSession({ fileRef: 'trace.jsonl', proposal });
    useWorkbenchStore.getState().applyReply({
      text: 'J’ai levé l’ambiguïté.',
      revised_proposal: revised,
      current_proposal: revised,
    });

    const state = useWorkbenchStore.getState();
    expect(state.proposal).toEqual(revised);
    expect(state.turns.at(-1)?.ambiguities).toEqual([]);
  });

  it('keeps the current proposal when the reply carries none', () => {
    useWorkbenchStore.getState().startSession({ fileRef: 'trace.jsonl', proposal });
    useWorkbenchStore.getState().applyReply({
      text: 'Rien à réviser.',
      revised_proposal: null,
      current_proposal: null,
    });

    expect(useWorkbenchStore.getState().proposal).toEqual(proposal);
  });
});

describe('free conversation (floating assistant)', () => {
  beforeEach(() => useWorkbenchStore.getState().reset());

  it('opens without a file, on an empty proposal the API accepts', () => {
    useWorkbenchStore.getState().startGeneralSession();
    const state = useWorkbenchStore.getState();

    expect(state.conversationId).toBeTruthy();
    expect(state.fileRef).toBeNull();
    expect(state.proposal).toEqual(EMPTY_PROPOSAL);
    // `definition` must be an object: a string is what the API rejected.
    expect(typeof state.proposal?.definition).toBe('object');
    expect(state.turns).toHaveLength(1);
    expect(state.turns[0]?.role).toBe('assistant');
  });

  it('re-anchors on a file when one is analysed mid-conversation', () => {
    useWorkbenchStore.getState().startGeneralSession();
    useWorkbenchStore.getState().appendUserTurn('Bonjour');
    useWorkbenchStore.getState().startSession({ fileRef: 'trace.jsonl', proposal });

    const state = useWorkbenchStore.getState();
    expect(state.fileRef).toBe('trace.jsonl');
    expect(state.proposal).toEqual(proposal);
    expect(state.turns).toHaveLength(1);
  });
});
