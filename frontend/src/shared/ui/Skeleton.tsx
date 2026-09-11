import { cn } from '@shared/lib/cn';

/**
 * Shimmer placeholder shown while server data loads — replaces bare "Chargement…"
 * text so a loading screen still has structure and motion.
 */
export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div aria-hidden="true" style={style} className={cn('skeleton', className)} />;
}

const FAUX_BARS = [40, 68, 52, 84, 60, 92, 48, 76, 58, 70];

/** Full chart-body placeholder: faux bars rising from a baseline. */
export function ChartSkeleton({ height = 280 }: { height?: number }) {
  return (
    <div
      role="status"
      aria-label="Chargement du graphique"
      className="flex items-end gap-2"
      style={{ height }}
    >
      {FAUX_BARS.map((h, i) => (
        <Skeleton key={i} className="flex-1" style={{ height: `${h}%` }} />
      ))}
      <span className="sr-only">Chargement…</span>
    </div>
  );
}
