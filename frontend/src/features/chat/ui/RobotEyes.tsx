import { useEffect, useRef, useState } from 'react';

import { cn } from '@shared/lib/cn';
import { useUiStore } from '@shared/stores/ui-store';

const VIEW = 24;
/** The two "bar" eyes, in SVG user units. */
const EYES = [
  { x: 6.5, y: 3, w: 4, h: 18 },
  { x: 13.5, y: 3, w: 4, h: 18 },
] as const;
/** How far a bar can slide from centre (SVG units — ~25% of the icon). */
const MAX_TRAVEL = 5.5;
/** Pointer distance (px) at which travel is maxed out. */
const REACH = 55;

/**
 * The assistant's two vertical "bar" eyes — the glyph on the closed FloatingChat
 * button. Both bars slide toward the mouse pointer (wide range) and blink now
 * and then. Static + open when the viewer asked for reduced motion.
 */
export function RobotEyes({ className }: { className?: string }) {
  const ref = useRef<SVGSVGElement>(null);
  const reduceMotion = useUiStore((s) => s.reduceMotion);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (reduceMotion) {
      setOffset({ x: 0, y: 0 });
      return;
    }
    let frame = 0;
    function onMove(e: MouseEvent) {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        const el = ref.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        const cx = r.left + r.width / 2;
        const cy = r.top + r.height / 2;
        const dx = e.clientX - cx;
        const dy = e.clientY - cy;
        const angle = Math.atan2(dy, dx);
        const dist = Math.min(1, Math.hypot(dx, dy) / REACH);
        setOffset({
          x: Math.cos(angle) * MAX_TRAVEL * dist,
          y: Math.sin(angle) * MAX_TRAVEL * dist * 0.8,
        });
      });
    }
    window.addEventListener('mousemove', onMove);
    return () => {
      window.removeEventListener('mousemove', onMove);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [reduceMotion]);

  return (
    <svg
      ref={ref}
      viewBox={`0 0 ${VIEW} ${VIEW}`}
      className={cn('robot-eyes', className)}
      fill="currentColor"
      aria-hidden="true"
    >
      <g
        style={{
          transform: `translate(${offset.x}px, ${offset.y}px)`,
          transition: 'transform 0.07s linear',
        }}
      >
        {EYES.map((eye) => (
          <rect
            key={eye.x}
            x={eye.x}
            y={eye.y}
            width={eye.w}
            height={eye.h}
            rx="1.5"
            className="robot-eye"
            style={{ transformBox: 'fill-box', transformOrigin: 'center' }}
          />
        ))}
      </g>
    </svg>
  );
}
