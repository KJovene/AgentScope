import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

import { cn } from '@shared/lib/cn';
import { type FontScale, useUiStore } from '@shared/stores/ui-store';

const FONT_SCALES: { value: FontScale; label: string }[] = [
  { value: 'normal', label: 'Normal' },
  { value: 'large', label: 'Large' },
  { value: 'xl', label: 'Extra' },
];

/**
 * Accessibility entry — a nav-style button rendered in the nav footer. Its panel
 * is rendered through a portal on <body> (so no ancestor stacking context can
 * hide it) as a fixed sheet, anchored just outside the nav.
 *
 * Controls: type scale, "Mode contraste pur" (kills neon/glow), reduced motion.
 * All write to `useUiStore`, mirrored onto `<html data-*>`.
 */
export function AccessibilityPanel() {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const btnRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLElement>(null);

  const fontScale = useUiStore((s) => s.fontScale);
  const pureContrast = useUiStore((s) => s.pureContrast);
  const reduceMotion = useUiStore((s) => s.reduceMotion);
  const setFontScale = useUiStore((s) => s.setFontScale);
  const togglePureContrast = useUiStore((s) => s.togglePureContrast);
  const toggleReduceMotion = useUiStore((s) => s.toggleReduceMotion);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    function onPointer(e: MouseEvent) {
      const t = e.target as Node;
      if (
        panelRef.current &&
        !panelRef.current.contains(t) &&
        btnRef.current &&
        !btnRef.current.contains(t)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onPointer);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('mousedown', onPointer);
    };
  }, [open]);

  return (
    <div data-testid="accessibility-widget">
      <button
        ref={btnRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={panelId}
        className={cn(
          'flex w-full items-center gap-3 border px-3 py-2.5 text-sm uppercase tracking-wider transition',
          open
            ? 'border-neon-violet text-neon-violet neon-violet'
            : 'border-border text-foreground-muted hover:border-neon-violet hover:text-neon-violet',
        )}
      >
        <span aria-hidden="true" className="text-base leading-none">
          ◉
        </span>
        <span className="hidden md:inline">Accessibilité</span>
      </button>

      {open &&
        createPortal(
          <section
            ref={panelRef}
            id={panelId}
            aria-label="Options d'accessibilité"
            className={cn(
              'hud hud-violet animate-flyout-left fixed bottom-4 left-4 z-[100] w-72 p-4 text-sm shadow-elev-lg',
              'md:left-[15rem]',
            )}
          >
            <h2 className="cyber-heading mb-3 text-xs text-neon-violet neon-text-violet">
              Accessibilité
            </h2>

            <fieldset className="mb-4">
              <legend className="mb-2 block text-xs text-foreground-muted">Taille du texte</legend>
              <div className="flex gap-1">
                {FONT_SCALES.map((opt) => {
                  const active = fontScale === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      aria-pressed={active}
                      onClick={() => setFontScale(opt.value)}
                      className={cn(
                        'flex-1 border px-2 py-1.5 text-xs uppercase tracking-wider transition',
                        active
                          ? 'border-neon-violet bg-neon-violet/10 text-neon-violet'
                          : 'border-border text-foreground-muted hover:border-border-strong hover:text-foreground',
                      )}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </fieldset>

            <ToggleRow
              label="Mode contraste pur"
              hint="Désactive les néons et lueurs"
              checked={pureContrast}
              onChange={togglePureContrast}
            />
            <ToggleRow
              label="Réduire les animations"
              hint="Coupe les effets de mouvement"
              checked={reduceMotion}
              onChange={toggleReduceMotion}
            />
          </section>,
          document.body,
        )}
    </div>
  );
}

function ToggleRow({
  label,
  hint,
  checked,
  onChange,
}: {
  label: string;
  hint: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <div className="mb-2 flex items-start justify-between gap-3 py-1">
      <span>
        <span className="block text-xs text-foreground">{label}</span>
        <span className="block text-[10px] text-foreground-muted">{hint}</span>
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={onChange}
        className={cn(
          'relative mt-0.5 h-5 w-10 shrink-0 border transition-colors',
          checked ? 'border-neon-green bg-neon-green/20' : 'border-border bg-surface-muted',
        )}
      >
        <span
          className={cn(
            'absolute top-0.5 h-3.5 w-3.5 transition-all',
            checked ? 'left-[22px] bg-neon-green' : 'left-0.5 bg-border-strong',
          )}
        />
      </button>
    </div>
  );
}
