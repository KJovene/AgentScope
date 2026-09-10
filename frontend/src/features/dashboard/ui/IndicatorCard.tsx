import React, { useState } from "react";
import type { MetricDefinition } from "../types";

interface IndicatorCardProps {
  definition: MetricDefinition;
  value: number | null;
  formatter?: (val: number) => string;
  accent?: "cyan" | "violet";
  /** Secondary line under the value: a derived ratio, an average, a count. */
  caption?: string;
  /** Small qualifier next to the label, e.g. "Estimé" for a priced-from-grid cost. */
  badge?: string;
  /** Relative variation against the previous period, as a ratio (0.12 = +12 %). */
  delta?: number | null;
  /**
   * Whether a rise is good. Drives the status color, which is reserved for
   * values that genuinely mean better/worse. Leave undefined for a neutral
   * volume metric, where "more" is neither good nor bad.
   */
  higherIsBetter?: boolean;
  /** Footer slot — a proportion bar or any compact breakdown of the value. */
  children?: React.ReactNode;
}

const ACCENT = {
  cyan: {
    edge: "edge-top-cyan",
    value: "neon-text-cyan",
    hover: "hover:border-neon-cyan hover:text-neon-cyan",
    tip: "border-neon-cyan text-neon-cyan",
  },
  violet: {
    edge: "edge-top-violet",
    value: "neon-text-violet",
    hover: "hover:border-neon-violet hover:text-neon-violet",
    tip: "border-neon-violet text-neon-violet",
  },
} as const;

/**
 * Renders the variation as arrow + signed percentage, never color alone: the
 * glyph and the sign carry the direction for a reader who cannot separate the
 * two status hues.
 */
function DeltaBadge({ delta, higherIsBetter }: { delta: number; higherIsBetter?: boolean }) {
  const rising = delta > 0;
  const flat = Math.abs(delta) < 0.001;

  const tone = flat || higherIsBetter === undefined
    ? "text-foreground-muted"
    : rising === higherIsBetter
      ? "text-success"
      : "text-danger";

  const arrow = flat ? "→" : rising ? "↑" : "↓";
  const sign = rising ? "+" : "";

  return (
    <span
      className={`flex shrink-0 items-center gap-1 whitespace-nowrap text-[11px] font-semibold tabular-nums ${tone}`}
      title="Variation par rapport à la période précédente de même durée"
    >
      <span aria-hidden="true">{arrow}</span>
      {sign}
      {(delta * 100).toFixed(1)} %
    </span>
  );
}

export const IndicatorCard: React.FC<IndicatorCardProps> = ({
  definition,
  value,
  formatter = (v) => v.toLocaleString("fr-FR"),
  accent = "cyan",
  caption,
  badge,
  delta,
  higherIsBetter,
  children,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const a = ACCENT[accent];

  const isNA = value === null;
  const displayValue = isNA ? "N/A" : formatter(value);

  return (
    <div className={`cyber-card relative ${a.edge}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-foreground-muted">
          {definition.label}
          {badge && (
            <span className="border border-border px-1 py-px text-[9px] font-medium normal-case tracking-normal">
              {badge}
            </span>
          )}
        </span>
        <button
          type="button"
          aria-label={`Définition de ${definition.label}`}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          onFocus={() => setShowTooltip(true)}
          onBlur={() => setShowTooltip(false)}
          className={`border border-border p-1 text-foreground-muted transition ${a.hover}`}
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>

      <div className="mt-3 flex items-baseline justify-between gap-2">
        <span
          className={`text-2xl font-bold ${
            isNA ? "text-foreground-muted" : `text-foreground ${a.value}`
          }`}
        >
          {displayValue}
        </span>
        <span className="text-xs text-foreground-muted">{definition.unit}</span>
      </div>

      {(caption || (delta != null && !isNA)) && (
        <div className="mt-2 flex items-center justify-between gap-2">
          <span className="text-[11px] text-foreground-muted">{caption}</span>
          {delta != null && !isNA && (
            <DeltaBadge delta={delta} higherIsBetter={higherIsBetter} />
          )}
        </div>
      )}

      {children && <div className="mt-3">{children}</div>}

      {showTooltip && (
        <div
          role="tooltip"
          className={`absolute left-2 right-2 top-12 z-20 border bg-surface-raised p-3 text-xs text-foreground shadow-elev-lg ${a.tip}`}
        >
          <p className="font-semibold">{definition.label}</p>
          <div className="mt-2 space-y-1 text-[11px] text-foreground">
            <p><strong className="text-foreground-muted">Calcul :</strong> {definition.calculation}</p>
            <p><strong className="text-foreground-muted">Unité :</strong> {definition.unit}</p>
            <p><strong className="text-foreground-muted">Périmètre :</strong> {definition.scope}</p>
            <p><strong className="text-foreground-muted">Si NULL :</strong> {definition.nullMeaning}</p>
          </div>
        </div>
      )}
    </div>
  );
};
