/**
 * Jarvis-style ambient HUD behind the assistant conversation: concentric rings
 * that rotate at different speeds, dashed arc segments, tick marks and a pulsing
 * core. Decorative only — inline SVG, sits behind the message list, and all
 * motion stops under reduced-motion (global CSS rule).
 */
export function ChatBackdrop({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 200 200"
      role="presentation"
      aria-hidden="true"
      fill="none"
      className={className}
    >
      {/* outer ring — slow, counter-clockwise */}
      <g className="chat-hud-spin-slow" style={{ transformOrigin: '100px 100px' }}>
        <circle cx="100" cy="100" r="88" stroke="hsl(var(--accent-1) / 0.28)" strokeWidth="1" />
        <circle
          cx="100"
          cy="100"
          r="88"
          stroke="hsl(var(--accent-1) / 0.5)"
          strokeWidth="2"
          strokeDasharray="40 220"
          strokeLinecap="round"
        />
        {Array.from({ length: 24 }).map((_, i) => (
          <line
            key={i}
            x1="100"
            y1="6"
            x2="100"
            y2="12"
            stroke="hsl(var(--accent-1) / 0.35)"
            strokeWidth="1.5"
            transform={`rotate(${i * 15} 100 100)`}
          />
        ))}
      </g>

      {/* mid ring — faster, clockwise */}
      <g className="chat-hud-spin-mid" style={{ transformOrigin: '100px 100px' }}>
        <circle cx="100" cy="100" r="62" stroke="hsl(var(--accent-2) / 0.4)" strokeWidth="1.5" strokeDasharray="6 10" />
        <path
          d="M100 46 A54 54 0 0 1 154 100"
          stroke="hsl(var(--accent-2) / 0.6)"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </g>

      {/* inner ring — slow, clockwise */}
      <g className="chat-hud-spin-rev" style={{ transformOrigin: '100px 100px' }}>
        <circle cx="100" cy="100" r="38" stroke="hsl(var(--accent-1) / 0.4)" strokeWidth="1" strokeDasharray="2 6" />
      </g>

      {/* core */}
      <circle cx="100" cy="100" r="10" fill="hsl(var(--accent-1) / 0.18)" className="chat-hud-core" />
      <circle cx="100" cy="100" r="4" fill="hsl(var(--accent-1) / 0.7)" />
    </svg>
  );
}
