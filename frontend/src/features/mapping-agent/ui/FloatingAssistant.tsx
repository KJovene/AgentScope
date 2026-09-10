import { useEffect, useId, useState } from 'react';

import { cn } from '@shared/lib/cn';

import { useWorkbenchStore } from '../model/workbench-store';

import { AgentChat } from './AgentChat';

/**
 * The mapping agent as a fixed floating widget, bottom-right. Collapsed it is a
 * beveled neon button; expanded it unfolds a cyberpunk dialog window hosting the
 * full <AgentChat />. The trigger button keeps its position when the panel
 * opens — the panel is absolutely anchored to the button, not laid out beside it.
 *
 * The conversation stands on its own: open the panel and the agent is there, no
 * import required. It reads the same store as "Ajouter une source", so once a
 * file has been analysed the exchange carries on about that proposal, from any
 * page — the dot on the button marks that a file is under discussion.
 */
export function FloatingAssistant() {
  const [open, setOpen] = useState(false);
  const hasFile = useWorkbenchStore((s) => s.fileRef !== null);
  const dialogId = useId();

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {open && (
        <div
          id={dialogId}
          role="dialog"
          aria-label="Assistant AgentScope"
          className={cn(
            'animate-chat-in absolute bottom-[4.5rem] right-0 origin-bottom-right',
            'h-[min(70vh,560px)] w-[min(90vw,384px)]',
            'border border-neon-cyan bg-surface shadow-elev-lg',
          )}
        >
          <AgentChat className="h-full" />
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={dialogId}
        aria-label={open ? "Fermer l'assistant" : "Ouvrir l'assistant"}
        className={cn(
          'relative flex h-14 w-14 items-center justify-center border bg-surface text-2xl transition',
          open
            ? 'border-neon-magenta text-neon-magenta neon-magenta'
            : 'border-neon-cyan text-neon-cyan neon-cyan hover:animate-none',
          !open && hasFile && 'animate-pulse-neon',
        )}
      >
        <span aria-hidden="true">{open ? '×' : '▮▮'}</span>
        {hasFile && !open && (
          <span
            aria-hidden="true"
            className="absolute -right-1 -top-1 h-3 w-3 border border-surface bg-neon-green"
          />
        )}
      </button>
    </div>
  );
}
