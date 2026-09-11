import { useEffect, useRef, useState } from 'react';

import { cn } from '@shared/lib/cn';
import { ErrorState } from '@shared/ui';

import { type ChatRequest } from '../api/chat.contracts';
import { useChatMutation } from '../api/chat.queries';
import { toWireMessages, useWorkbenchStore } from '../model/workbench-store';
import { ChatBackdrop } from './ChatBackdrop';
import { RobotAvatar } from './RobotAvatar';

/**
 * I5.6 — the conversation with the agent.
 *
 * It opens on its own the first time it is mounted, so the floating assistant
 * is usable without importing anything. Once a file has been analysed, the same
 * conversation is anchored on the proposal `/analyze` returned, and the header
 * says which file is on the table.
 */
export function AgentChat({ className }: { className?: string }) {
  const { conversationId, fileRef, proposal, turns, startGeneralSession, appendUserTurn, applyReply } =
    useWorkbenchStore();

  const chat = useChatMutation();
  const [draft, setDraft] = useState('');
  const lastPayload = useRef<ChatRequest | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!conversationId) startGeneralSession();
  }, [conversationId, startGeneralSession]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, chat.isPending]);

  const send = (payload: ChatRequest) => {
    lastPayload.current = payload;
    chat.mutate(payload, { onSuccess: applyReply });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || chat.isPending) return;

    // The session is opened by the mount effect; nothing to send before it is.
    const opened = useWorkbenchStore.getState();
    if (!opened.conversationId || !opened.proposal) return;

    appendUserTurn(text);
    setDraft('');
    chat.reset();

    // Read back after the append: the server is stateless, so the request
    // carries the whole history including the message just typed.
    const { turns: history, proposal: current, fileRef: ref } = useWorkbenchStore.getState();
    send({
      conversation_id: opened.conversationId,
      messages: toWireMessages(history),
      current_proposal: current ?? opened.proposal,
      file_ref: ref,
    });
  };

  return (
    <div
      className={cn(
        'relative flex min-h-0 w-full flex-col overflow-hidden border border-border bg-surface',
        className,
      )}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 overflow-hidden"
      >
        <ChatBackdrop className="absolute left-1/2 top-1/2 h-[125%] w-[125%] -translate-x-1/2 -translate-y-1/2 opacity-[0.16]" />
      </div>

      <div className="relative z-10 flex items-center justify-between gap-3 border-b border-border bg-surface-raised px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <RobotAvatar className="h-9 w-9" />
          <div className="min-w-0">
            <h2 className="cyber-heading text-sm text-neon-cyan neon-text-cyan">
              Assistant AgentScope
            </h2>
            <p className="truncate text-[11px] text-foreground-muted">
              {fileRef && proposal
                ? `${fileRef} — ${proposal.explanations.length} correspondance(s), ${proposal.unmapped_fields.length} non mappé(s)`
                : 'Discussion libre — aucun fichier analysé'}
            </p>
          </div>
        </div>
        <span className="shrink-0 border border-neon-green/60 px-2 py-0.5 text-[10px] uppercase tracking-widest text-neon-green">
          online
        </span>
      </div>

      <div
        role="log"
        aria-live="polite"
        aria-label="Conversation avec l'assistant"
        className="relative z-10 flex-1 space-y-5 overflow-y-auto p-4"
      >
        {turns.map((turn) => (
          <div
            key={turn.id}
            className={cn('flex w-full', turn.role === 'user' ? 'justify-end' : 'justify-start')}
          >
            <div
              className={cn(
                'max-w-[80%] border p-3 text-sm',
                turn.role === 'user'
                  ? 'border-neon-cyan/70 bg-neon-cyan/10 text-foreground'
                  : 'border-border bg-surface-muted text-foreground',
              )}
            >
              <div className="whitespace-pre-wrap">{turn.text}</div>

              {turn.ambiguities.length > 0 && (
                <div className="mt-3 border border-warning/60 bg-warning/10 p-3 text-foreground">
                  <p className="text-xs font-bold uppercase tracking-wider text-warning">
                    Précision requise
                  </p>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-xs">
                    {turn.ambiguities.map((ambiguity) => (
                      <li key={ambiguity}>{ambiguity}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {chat.isPending && (
          <div className="flex justify-start">
            <div className="flex space-x-1 border border-border bg-surface-muted p-4">
              {[0, 0.2, 0.4].map((delay) => (
                <span
                  key={delay}
                  className="h-2 w-2 animate-bounce rounded-full bg-neon-cyan"
                  style={{ animationDelay: `${delay}s` }}
                />
              ))}
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {chat.isError && (
        <div className="px-4 pb-2">
          <ErrorState
            error={chat.error}
            onRetry={() => lastPayload.current && send(lastPayload.current)}
          />
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border p-3">
        <label className="sr-only" htmlFor="agent-chat-input">
          Message pour l'assistant
        </label>
        <input
          id="agent-chat-input"
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={chat.isPending}
          placeholder="Posez votre question à l'agent…"
          className="min-w-0 flex-1 border border-border bg-surface-muted px-3 py-2 text-sm text-foreground placeholder:text-foreground-muted focus:border-neon-cyan focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!draft.trim() || chat.isPending}
          className="border border-neon-cyan bg-neon-cyan/10 px-4 py-2 text-sm font-semibold uppercase tracking-wider text-neon-cyan transition hover:bg-neon-cyan/20 disabled:opacity-40"
        >
          Envoyer
        </button>
      </form>
    </div>
  );
}
