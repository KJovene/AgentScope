import React, { useState } from "react";
import type { MetricDefinition } from "../types";

interface IndicatorCardProps {
  definition: MetricDefinition;
  value: number | null;
  formatter?: (val: number) => string;
  accent?: "cyan" | "violet";
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

export const IndicatorCard: React.FC<IndicatorCardProps> = ({
  definition,
  value,
  formatter = (v) => v.toLocaleString("fr-FR"),
  accent = "cyan",
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const a = ACCENT[accent];

  const isNA = value === null;
  const displayValue = isNA ? "N/A" : formatter(value);

  return (
    <div className={`cyber-card relative ${a.edge}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-foreground-muted">
          {definition.label}
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
          className={`text-2xl font-bold tabular-nums ${
            isNA ? "text-foreground-muted" : `text-foreground ${a.value}`
          }`}
        >
          {displayValue}
        </span>
        <span className="text-xs text-foreground-muted">{definition.unit}</span>
      </div>

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
