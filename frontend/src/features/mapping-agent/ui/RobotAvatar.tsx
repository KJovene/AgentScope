import { useEffect, useRef, useState } from 'react';

import { cn } from '@shared/lib/cn';
import { useUiStore } from '@shared/stores/ui-store';

const VIEW = 36;
/** Eye socket centres in SVG user units. */
const EYES = [
  { x: 13, y: 18 },
  { x: 23, y: 18 },
] as const;
const MAX_TRAVEL = 1.7; // how far a pupil can slide from its socket centre

interface Offset {
  x: number;
  y: number;
}

/**
 * Cyberpunk assistant mascot. Its two pupils track the mouse pointer (each eye
 * aims independently). Tracking is disabled when the viewer asked for reduced
 * motion — the eyes then sit centred.
 */
export function RobotAvatar({ className }: { className?: string }) {
  const wrapRef = useRef<HTMLSpanElement>(null);
  const reduceMotion = useUiStore((s) => s.reduceMotion);
  const [pupils, setPupils] = useState<[Offset, Offset]>([
    { x: 0, y: 0 },
    { x: 0, y: 0 },
  ]);

  useEffect(() => {
    if (reduceMotion) {
      setPupils([
        { x: 0, y: 0 },
        { x: 0, y: 0 },
      ]);
      return;
    }

    let frame = 0;
    function onMove(e: MouseEvent) {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        const el = wrapRef.current;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const unit = rect.width / VIEW;
        const next = EYES.map((eye) => {
          const cx = rect.left + eye.x * unit;
          const cy = rect.top + eye.y * unit;
          const angle = Math.atan2(e.clientY - cy, e.clientX - cx);
          const dist = Math.min(1, Math.hypot(e.clientX - cx, e.clientY - cy) / 90);
          return {
            x: Math.cos(angle) * MAX_TRAVEL * dist,
            y: Math.sin(angle) * MAX_TRAVEL * dist,
          };
        }) as [Offset, Offset];
        setPupils(next);
      });
    }

    window.addEventListener('mousemove', onMove);
    return () => {
      window.removeEventListener('mousemove', onMove);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [reduceMotion]);

  return (
    <span ref={wrapRef} className={cn('inline-block shrink-0', className)} aria-hidden="true">
      <svg viewBox={`0 0 ${VIEW} ${VIEW}`} fill="none" className="h-full w-full">
        {/* antenna */}
        <line x1="18" y1="3" x2="18" y2="7" stroke="hsl(var(--accent-2))" strokeWidth="1.5" />
        <circle cx="18" cy="2.5" r="1.6" fill="hsl(var(--accent-2))" className="animate-pulse-neon" />

        {/* head — bevelled cyber panel */}
        <path
          d="M8 8 h16 a3 3 0 0 1 3 3 v12 a3 3 0 0 1 -3 3 h-4 l-2 2 l-2 -2 h-6 a3 3 0 0 1 -3 -3 v-12 a3 3 0 0 1 3 -3 z"
          fill="hsl(var(--surface-raised))"
          stroke="hsl(var(--accent-1))"
          strokeWidth="1.5"
        />

        {/* ear bolts */}
        <rect x="4" y="14" width="2" height="6" fill="hsl(var(--accent-1))" />
        <rect x="30" y="14" width="2" height="6" fill="hsl(var(--accent-1))" />

        {/* eye sockets */}
        {EYES.map((eye) => (
          <circle
            key={eye.x}
            cx={eye.x}
            cy={eye.y}
            r="3.4"
            fill="hsl(var(--surface-muted))"
            stroke="hsl(var(--accent-1) / 0.5)"
            strokeWidth="0.75"
          />
        ))}

        {/* pupils — follow the cursor */}
        {EYES.map((eye, i) => {
          const p = pupils[i] ?? { x: 0, y: 0 };
          return (
            <circle
              key={`p-${eye.x}`}
              cx={eye.x}
              cy={eye.y}
              r="1.7"
              fill="hsl(var(--accent-1))"
              style={{
                filter: 'drop-shadow(0 0 3px hsl(var(--accent-1) / calc(0.7 * var(--glow, 1))))',
                transform: `translate(${p.x}px, ${p.y}px)`,
                transition: 'transform 0.08s linear',
              }}
            />
          );
        })}

        {/* mouth — grille */}
        <g stroke="hsl(var(--accent-1) / 0.7)" strokeWidth="1.2">
          <line x1="13" y1="25" x2="13" y2="27" />
          <line x1="16" y1="25" x2="16" y2="27" />
          <line x1="19" y1="25" x2="19" y2="27" />
          <line x1="22" y1="25" x2="22" y2="27" />
        </g>
      </svg>
    </span>
  );
}
