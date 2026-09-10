/**
 * Decorative-only inline SVG (no external asset — CSP/offline safe). A HUD
 * "scope" motif: concentric rings, a sweeping wedge and a wire grid, stroked in
 * the blue + violet accents. Purely visual; hidden from assistive tech.
 */
export function CyberScope({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 200 200"
      role="presentation"
      aria-hidden="true"
      className={className}
      fill="none"
    >
      <defs>
        <linearGradient id="cs-sweep" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="hsl(var(--accent-1))" stopOpacity="0.5" />
          <stop offset="100%" stopColor="hsl(var(--accent-2))" stopOpacity="0" />
        </linearGradient>
      </defs>
      <g stroke="hsl(var(--accent-1))" strokeOpacity="0.35" strokeWidth="1">
        <circle cx="100" cy="100" r="82" />
        <circle cx="100" cy="100" r="56" />
        <circle cx="100" cy="100" r="30" />
        <line x1="100" y1="8" x2="100" y2="192" />
        <line x1="8" y1="100" x2="192" y2="100" />
      </g>
      <path d="M100 100 L100 18 A82 82 0 0 1 168 62 Z" fill="url(#cs-sweep)">
        <animateTransform
          attributeName="transform"
          type="rotate"
          from="0 100 100"
          to="360 100 100"
          dur="8s"
          repeatCount="indefinite"
        />
      </path>
      <g fill="hsl(var(--accent-2))" fillOpacity="0.7">
        <circle cx="138" cy="72" r="2.5" />
        <circle cx="72" cy="128" r="2" />
        <circle cx="120" cy="140" r="1.6" />
      </g>
    </svg>
  );
}
