import React, { useState } from "react";
import type { MetricDefinition } from "../types";

interface IndicatorCardProps {
  definition: MetricDefinition;
  value: number | null;
  formatter?: (val: number) => string;
}

export const IndicatorCard: React.FC<IndicatorCardProps> = ({
  definition,
  value,
  formatter = (v) => v.toLocaleString("fr-FR"),
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const displayValue = value !== null ? formatter(value) : "N/A";

  return (
    <div className="relative rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {definition.label}
        </span>
        <button
          type="button"
          aria-label={`Définition de ${definition.label}`}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          onFocus={() => setShowTooltip(true)}
          onBlur={() => setShowTooltip(false)}
          className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-900"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          {displayValue}
        </span>
        <span className="text-xs text-slate-500">{definition.unit}</span>
      </div>

      {showTooltip && (
        <div
          role="tooltip"
          className="absolute z-20 top-12 left-2 right-2 rounded-md border border-slate-200 bg-slate-900 p-3 text-xs text-slate-100 shadow-xl dark:border-slate-700 dark:bg-slate-800"
        >
          <p className="font-semibold text-indigo-300">{definition.label}</p>
          <div className="mt-2 space-y-1 text-[11px]">
            <p><strong className="text-slate-400">Calcul :</strong> {definition.calculation}</p>
            <p><strong className="text-slate-400">Unité :</strong> {definition.unit}</p>
            <p><strong className="text-slate-400">Périmètre :</strong> {definition.scope}</p>
            <p><strong className="text-slate-400">Si NULL :</strong> {definition.nullMeaning}</p>
          </div>
        </div>
      )}
    </div>
  );
};
