import { useEffect, useId, useState } from 'react';

import { cn } from '@shared/lib/cn';

import { ChatScreen } from './ChatScreen';
import { RobotEyes } from './RobotEyes';

/**
 * The Assistant Chat as a fixed floating widget, bottom-right. Collapsed it is a
 * beveled neon button; expanded it unfolds a cyberpunk dialog window hosting the
 * full <ChatScreen />. The trigger button keeps its position when the panel
 * opens — the panel is absolutely anchored to the button, not laid out beside it.
 */
export function FloatingChat({ sessionId = 'session-assistant' }: { sessionId?: string }) {
  const [open, setOpen] = useState(false);
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
          <ChatScreen sessionId={sessionId} />
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={dialogId}
        aria-label={open ? "Fermer l'assistant" : "Ouvrir l'assistant"}
        className={cn(
          'flex h-14 w-14 items-center justify-center border bg-surface text-2xl transition',
          open
            ? 'border-neon-magenta text-neon-magenta neon-magenta'
            : 'border-neon-cyan text-neon-cyan neon-cyan animate-pulse-neon hover:animate-none',
        )}
      >
        {open ? <span aria-hidden="true">×</span> : <RobotEyes className="h-9 w-9" />}
      </button>
    </div>
  );
}
