import { CHART_SERIES_COLORS } from './chart-colors';

export interface ProportionSegment {
  key: string;
  label: string;
  value: number;
  color?: string;
}

/**
 * Single-row part-to-whole bar for a two- or three-way split (prompt vs
 * completion tokens, successful vs failed calls). A bar rather than a donut:
 * the segments are read against each other, not at a glance.
 *
 * Every segment is legended AND direct-labelled with its share, so identity is
 * never carried by color alone. A 2px surface gap separates fills instead of a
 * border drawn around them.
 */
export function ProportionBar({ segments }: { segments: ProportionSegment[] }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  if (total <= 0) return null;

  return (
    <div>
      <div className="flex h-2 w-full gap-[2px] overflow-hidden" role="presentation">
        {segments.map((segment, index) => (
          <span
            key={segment.key}
            className="block h-full"
            style={{
              width: `${(segment.value / total) * 100}%`,
              background: segment.color ?? CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length],
            }}
          />
        ))}
      </div>

      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-foreground-muted">
        {segments.map((segment, index) => (
          <li key={segment.key} className="flex items-center gap-1.5">
            <span
              aria-hidden="true"
              className="inline-block h-2 w-2 shrink-0"
              style={{
                background:
                  segment.color ?? CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length],
              }}
            />
            <span>{segment.label}</span>
            <span className="font-semibold tabular-nums text-foreground">
              {((segment.value / total) * 100).toFixed(1)} %
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
