import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http as mswHttp } from 'msw';
import { beforeEach, describe, expect, it } from 'vitest';

import { useWorkbenchStore } from '@features/mapping-agent/model/workbench-store';
import { AgentChat } from '@features/mapping-agent/ui/AgentChat';

import { server } from '../../msw/server';
import { renderWithClient } from '../../utils';

const proposal = {
  definition: { source_format: 'jsonl', entities: {} },
  explanations: [
    {
      target_field: 'session.external_id',
      source_field: 'session_id',
      rationale: 'clé naturelle',
      confidence: 0.9,
    },
  ],
  ambiguities: [],
  unmapped_fields: ['debug'],
};

/** Capture what the component actually puts on the wire. */
function captureChatRequest(reply: Record<string, unknown>) {
  const seen: { body?: Record<string, unknown> } = {};
  server.use(
    mswHttp.post('/api/chat', async ({ request }) => {
      seen.body = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json(reply);
    }),
  );
  return seen;
}

async function ask(question: string) {
  await userEvent.type(screen.getByLabelText(/Message pour l'assistant/), question);
  await userEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
}

describe('AgentChat (I5.6)', () => {
  beforeEach(() => useWorkbenchStore.getState().reset());

  it('opens a conversation on its own, with no file imported', () => {
    renderWithClient(<AgentChat />);

    expect(screen.getByRole('log')).toHaveTextContent(/Je suis l’agent AgentScope/);
    expect(screen.getByText(/Discussion libre/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Envoyer' })).toBeInTheDocument();
  });

  // The regression guard: the payload the component actually sends. The 422s
  // came from a role of "agent" and a `definition` that was a string.
  it('sends a wire-legal payload with an empty proposal when no file is analysed', async () => {
    const seen = captureChatRequest({
      text: 'Je peux expliquer un mapping.',
      revised_proposal: null,
      current_proposal: null,
    });

    renderWithClient(<AgentChat />);
    await ask('Que sais-tu faire ?');

    await waitFor(() => expect(seen.body).toBeDefined());
    expect(seen.body).toMatchObject({
      conversation_id: expect.any(String),
      file_ref: null,
      current_proposal: { definition: {}, explanations: [], ambiguities: [], unmapped_fields: [] },
      messages: [
        { role: 'assistant', text: expect.stringContaining('AgentScope') },
        { role: 'user', text: 'Que sais-tu faire ?' },
      ],
    });

    expect(await screen.findByText('Je peux expliquer un mapping.')).toBeInTheDocument();
  });

  it('anchors on the proposal returned by /analyze once a file is analysed', async () => {
    const seen = captureChatRequest({
      text: 'La clé naturelle est `session_id`.',
      revised_proposal: null,
      current_proposal: proposal,
    });

    useWorkbenchStore.getState().startSession({ fileRef: 'trace.jsonl', proposal });
    renderWithClient(<AgentChat />);

    const header = screen.getByRole('heading', { name: 'Assistant AgentScope' }).parentElement;
    expect(header).toHaveTextContent('trace.jsonl');
    expect(header).toHaveTextContent('1 correspondance(s)');

    await ask('Pourquoi ce champ ?');

    await waitFor(() => expect(seen.body).toBeDefined());
    expect(seen.body).toMatchObject({
      file_ref: 'trace.jsonl',
      current_proposal: { definition: { source_format: 'jsonl', entities: {} } },
      messages: [
        { role: 'assistant', text: expect.stringContaining('trace.jsonl') },
        { role: 'user', text: 'Pourquoi ce champ ?' },
      ],
    });
  });

  it('adopts the revised proposal and highlights its ambiguities', async () => {
    const revised = { ...proposal, ambiguities: ['`agent` : outil ou modèle ?'] };
    captureChatRequest({
      text: 'J’ai revu la correspondance.',
      revised_proposal: revised,
      current_proposal: revised,
    });

    useWorkbenchStore.getState().startSession({ fileRef: 'trace.jsonl', proposal });
    renderWithClient(<AgentChat />);
    await ask('Corrige `agent`');

    expect(await screen.findByText('Précision requise')).toBeInTheDocument();
    expect(screen.getByText('`agent` : outil ou modèle ?')).toBeInTheDocument();
    expect(useWorkbenchStore.getState().proposal).toEqual(revised);
  });

  it('surfaces an API error without losing the conversation', async () => {
    server.use(
      mswHttp.post('/api/chat', () =>
        HttpResponse.json(
          { title: 'Requête invalide', status: 422, detail: 'Champ inattendu.' },
          { status: 422 },
        ),
      ),
    );

    renderWithClient(<AgentChat />);
    await ask('Explique');

    expect(await screen.findByText('Champ inattendu.')).toBeInTheDocument();
    expect(screen.getByText('Explique')).toBeInTheDocument();
  });
});
