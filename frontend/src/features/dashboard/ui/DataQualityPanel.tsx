import React from "react";
import type { DataQualityMetrics, SourceQuality } from "../types";

interface DataQualityPanelProps {
  metrics: DataQualityMetrics;
}

export const DataQualityPanel: React.FC<DataQualityPanelProps> = ({ metrics }) => {
  const getQualityColor = (percentage: number) => {
    if (percentage >= 90) return "text-emerald-600 dark:text-emerald-400";
    if (percentage >= 75) return "text-amber-500 dark:text-amber-400";
    return "text-red-600 dark:text-red-400";
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return "bg-emerald-500";
    if (percentage >= 75) return "bg-amber-500";
    return "bg-red-500";
  };

  const renderSourceCard = (source: SourceQuality) => (
    <div
      key={source.id}
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="mb-4 flex items-center justify-between">
        <h4 className="font-semibold text-slate-800 dark:text-slate-200">{source.sourceName}</h4>
        <span className={`text-sm font-bold ${getQualityColor(source.completeness)}`}>
          {source.completeness.toFixed(1)}% complet
        </span>
      </div>

      {/* Barre de complétude */}
      <div className="mb-6 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className={`h-full ${getProgressColor(source.completeness)} transition-all duration-500`}
          style={{ width: `${source.completeness}%` }}
        />
      </div>

      {/* Statistiques des lignes */}
      <div className="mb-6 grid grid-cols-3 gap-2 text-center text-xs">
        <div className="rounded bg-slate-50 py-2 dark:bg-slate-800/50">
          <span className="block text-slate-500">Total</span>
          <span className="font-semibold text-slate-700 dark:text-slate-300">{source.totalRows}</span>
        </div>
        <div className="rounded bg-emerald-50 py-2 dark:bg-emerald-950/20">
          <span className="block text-emerald-600/70">Valides</span>
          <span className="font-semibold text-emerald-700 dark:text-emerald-400">{source.validRows}</span>
        </div>
        <div className="rounded bg-red-50 py-2 dark:bg-red-950/20">
          <span className="block text-red-600/70">Rejets</span>
          <span className="font-semibold text-red-700 dark:text-red-400">{source.rejectedRows}</span>
        </div>
      </div>

      {/* Champs manquants */}
      <div>
        <h5 className="mb-2 text-xs font-semibold uppercase text-slate-500">
          Champs les plus manquants
        </h5>
        {source.missingFields.length > 0 ? (
          <ul className="space-y-2 text-sm">
            {source.missingFields.map((field, idx) => (
              <li key={idx} className="flex items-center justify-between text-slate-600 dark:text-slate-400">
                <span className="truncate pr-2">⚠️ {field.field}</span>
                <span className="shrink-0 text-xs text-amber-600 dark:text-amber-500">
                  {field.percentage.toFixed(1)}% vide ({field.emptyCount})
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-emerald-600 dark:text-emerald-400">✅ Aucun champ critique manquant.</p>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* En-tête global */}
      <div className="flex flex-col items-start gap-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between dark:border-slate-800 dark:bg-slate-950">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
            Qualité des données importées
          </h2>
          <p className="text-sm text-slate-500">
            Aperçu de la complétude et des anomalies détectées par source d'origine.
          </p>
        </div>

        <div className="flex gap-4">
          <div className="text-right">
            <span className="block text-xs font-medium uppercase text-slate-500">Complétude Globale</span>
            <span className={`text-2xl font-bold ${getQualityColor(metrics.globalCompleteness)}`}>
              {metrics.globalCompleteness.toFixed(1)}%
            </span>
          </div>
          <div className="h-10 w-px bg-slate-200 dark:bg-slate-800" />
          <div className="text-left">
            <span className="block text-xs font-medium uppercase text-slate-500">Taux de Rejet</span>
            <span className={`text-2xl font-bold ${metrics.globalRejectionRate > 10 ? 'text-red-600' : 'text-emerald-600'} dark:${metrics.globalRejectionRate > 10 ? 'text-red-400' : 'text-emerald-400'}`}>
              {metrics.globalRejectionRate.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Grille des sources */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {metrics.sources.map(renderSourceCard)}
        {metrics.sources.length === 0 && (
          <div className="col-span-full rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500 dark:border-slate-700">
            Aucune source de données analysée pour le moment.
          </div>
        )}
      </div>
    </div>
  );
};
