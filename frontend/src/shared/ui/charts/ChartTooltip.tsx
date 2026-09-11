import type { ReactNode } from 'react';

/**
 * Cyberpunk tooltip for every Recharts chart — beveled panel, neon hairline,
 * monospace. Shape matches Recharts' `content` render-prop payload (kept loose
 * so it works across Line/Bar charts without importing recharts' internal types).
 */
interface TooltipEntry {
  name?: ReactNode;
  value?: number | string;
  color?: string;
  dataKey?: string | number;
}

export function ChartTooltip({
  active,
  label,
  payload,
  valueFormatter = (v) => String(v),
  labelFormatter,
}: {
  active?: boolean;
  label?: ReactNode;
  payload?: TooltipEntry[];
  valueFormatter?: (value: number | string) => string;
  /** Expands a shortened axis tick back to its full meaning (e.g. a bucket span). */
  labelFormatter?: (label: ReactNode) => ReactNode;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const heading = label == null ? null : (labelFormatter?.(label) ?? label);

  return (
    <div className="border border-neon-cyan bg-surface px-3 py-2 text-xs shadow-neon-cyan">
      {heading != null && (
        <p className="mb-1 font-semibold uppercase tracking-wider text-foreground">{heading}</p>
      )}
      <ul className="space-y-0.5">
        {payload.map((entry, i) => (
          <li key={`${entry.dataKey ?? i}`} className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className="inline-block h-2 w-2"
              style={{ background: entry.color }}
            />
            <span className="text-foreground-muted">{entry.name}</span>
            <span className="ml-auto font-semibold text-foreground">
              {entry.value == null ? '—' : valueFormatter(entry.value)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
