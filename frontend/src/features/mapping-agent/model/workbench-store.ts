import { create } from 'zustand';

import { type MappingProposal } from '../api/analyze.contracts';
import { type ChatReply, type ChatRole, type ChatTurn } from '../api/chat.contracts';

/**
 * The conversation with the agent, and the proposal it is about — if any.
 *
 * Two ways in: a free conversation opened from the floating assistant
 * (`startGeneralSession`), or one anchored on a file analysed by `/analyze`
 * (`startSession`). Both talk to the same endpoint; only `current_proposal`
 * and `file_ref` differ.
 *
 * This state exists because `POST /chat` keeps none (§5.3) — the client owns
 * the history and the current proposal, and replaces the latter whenever the
 * agent revises it. It is client state, not server state, so it lives in a
 * store rather than in TanStack Query.
 */

/**
 * What we send when no file has been analysed. `definition` must be an object —
 * the API rejects anything else — and an empty one carries no claim.
 */
export const EMPTY_PROPOSAL: MappingProposal = {
  definition: {},
  explanations: [],
  ambiguities: [],
  unmapped_fields: [],
};

export interface ChatTurnView extends ChatTurn {
  id: string;
  /** Ambiguities of the proposal in force after this turn (assistant turns). */
  ambiguities: string[];
}

interface WorkbenchState {
  /** Stable id for the whole exchange, sent as `conversation_id`. */
  conversationId: string | null;
  /** Name of the analysed file, sent as `file_ref`; `null` in a free conversation. */
  fileRef: string | null;
  /** From `/analyze`, then whatever the agent last revised it into. */
  proposal: MappingProposal | null;
  turns: ChatTurnView[];
  /** Open a conversation with no file behind it. */
  startGeneralSession: () => void;
  /** Open a conversation about the proposal `/analyze` just returned. */
  startSession: (input: { fileRef: string; proposal: MappingProposal }) => void;
  appendUserTurn: (text: string) => void;
  applyReply: (reply: ChatReply) => void;
  reset: () => void;
}

function newId(): string {
  const uuid = globalThis.crypto?.randomUUID?.();
  return uuid ?? `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function makeTurn(role: ChatRole, text: string, ambiguities: string[] = []): ChatTurnView {
  return { id: newId(), role, text, ambiguities };
}

/**
 * The agent's opening lines. They are real `assistant` turns, sent back as part
 * of the history like any other — the backend accepts exactly `user` /
 * `assistant`.
 */
function generalOpeningTurn(): ChatTurnView {
  return makeTurn(
    'assistant',
    'Bonjour ! Je suis l’agent AgentScope. Posez-moi vos questions — ou analysez ' +
      'un fichier depuis « Ajouter une source » pour que nous parlions de son mapping.',
  );
}

function fileOpeningTurn(fileRef: string, proposal: MappingProposal): ChatTurnView {
  const mapped = proposal.explanations.length;
  const unmapped = proposal.unmapped_fields.length;
  return makeTurn(
    'assistant',
    `J'ai analysé « ${fileRef} » et proposé un mapping : ${mapped} correspondance(s), ` +
      `${unmapped} champ(s) non mappé(s). Demandez-moi d'expliquer ou de corriger une correspondance.`,
    proposal.ambiguities,
  );
}

export const useWorkbenchStore = create<WorkbenchState>((set) => ({
  conversationId: null,
  fileRef: null,
  proposal: null,
  turns: [],

  startGeneralSession: () =>
    set({
      conversationId: newId(),
      fileRef: null,
      proposal: EMPTY_PROPOSAL,
      turns: [generalOpeningTurn()],
    }),

  startSession: ({ fileRef, proposal }) =>
    set({
      conversationId: newId(),
      fileRef,
      proposal,
      turns: [fileOpeningTurn(fileRef, proposal)],
    }),

  appendUserTurn: (text) => set((s) => ({ turns: [...s.turns, makeTurn('user', text)] })),

  applyReply: (reply) =>
    set((s) => {
      // `current_proposal` is authoritative after each turn; keep ours if the
      // agent sent nothing back rather than dropping the proposal.
      const proposal = reply.current_proposal ?? s.proposal;
      return {
        proposal,
        turns: [...s.turns, makeTurn('assistant', reply.text, proposal?.ambiguities ?? [])],
      };
    }),

  reset: () => set({ conversationId: null, fileRef: null, proposal: null, turns: [] }),
}));

/** The wire history: the view model minus what only the UI needs. */
export function toWireMessages(turns: ChatTurnView[]): ChatTurn[] {
  return turns.map(({ role, text }) => ({ role, text }));
}
