import React, { useState } from "react";
import type { DryRunResult, PreviewRow } from "../types";

interface MappingPreviewProps {
  dryRunResult: DryRunResult;
  onBackToEdit: () => void;
  onConfirmImport: () => void;
  isSubmitting?: boolean;
}

export const MappingPreview: React.FC<MappingPreviewProps> = ({
  dryRunResult,
  onBackToEdit,
  onConfirmImport,
  isSubmitting = false,
}) => {
  const [activeTab, setActiveTab] = useState<"valid" | "rejected">("valid");

  const validRows = dryRunResult.rows.filter((r) => r.isValid);
  const rejectedRows = dryRunResult.rows.filter((r) => !r.isValid);

  const displayedRows = activeTab === "valid" ? validRows : rejectedRows;

  // Extraction dynamique des colonnes depuis le premier échantillon
  const targetHeaders = displayedRows.length > 0
    ? Object.keys(displayedRows[0]?.transformedData || {})
    : [];

  return (
    <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
      {/* En-tête et Synthèse */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Prévisualisation du mapping (Dry-run)
          </h3>
          <p className="text-xs text-slate-500">
            Vérifiez l'aperçu de la transformation avant l'exécution définitive.
          </p>
        </div>

        {/* Badges Statistiques */}
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-slate-100 px-3 py-1.5 text-center dark:bg-slate-900">
            <span className="block text-[10px] text-slate-500 uppercase">Total</span>
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
              {dryRunResult.totalRows}
            </span>
          </div>
          <div className="rounded-lg bg-emerald-50 px-3 py-1.5 text-center dark:bg-emerald-950/30">
            <span className="block text-[10px] text-emerald-600 uppercase">Valides</span>
            <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400">
              {dryRunResult.validRowsCount}
            </span>
          </div>
          <div className="rounded-lg bg-amber-50 px-3 py-1.5 text-center dark:bg-amber-950/30">
            <span className="block text-[10px] text-amber-600 uppercase">Rejets simulés</span>
            <span className="text-xs font-bold text-amber-700 dark:text-amber-400">
              {dryRunResult.rejectedRowsCount}
            </span>
          </div>
        </div>
      </div>

      {/* Onglets de sélection */}
      <div className="flex border-b border-slate-200 text-xs dark:border-slate-800">
        <button
          onClick={() => setActiveTab("valid")}
          className={`border-b-2 px-4 py-2 font-medium transition-colors ${
            activeTab === "valid"
              ? "border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          }`}
        >
          Lignes valides ({validRows.length})
        </button>
        <button
          onClick={() => setActiveTab("rejected")}
          className={`border-b-2 px-4 py-2 font-medium transition-colors ${
            activeTab === "rejected"
              ? "border-amber-600 text-amber-600 dark:border-amber-400 dark:text-amber-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
          }`}
        >
          Rejets simulés ({rejectedRows.length})
        </button>
      </div>

      {/* Table de prévisualisation */}
      <div className="overflow-x-auto">
        {displayedRows.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            Aucune ligne à afficher dans cette catégorie.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 uppercase text-slate-500 dark:bg-slate-900 dark:text-slate-400">
              <tr>
                <th className="p-3 w-16">Ligne</th>
                {activeTab === "rejected" && <th className="p-3 text-red-600">Motif du rejet</th>}
                {targetHeaders.map((header) => (
                  <th key={header} className="p-3">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {displayedRows.map((row: PreviewRow) => (
                <tr
                  key={row.rowIndex}
                  className={!row.isValid ? "bg-amber-50/40 dark:bg-amber-950/10" : ""}
                >
                  <td className="p-3 font-mono text-slate-400">#{row.rowIndex}</td>
                  {activeTab === "rejected" && (
                    <td className="p-3 font-medium text-red-600 dark:text-red-400">
                      {row.rejectReason || "Erreur de transformation"}
                    </td>
                  )}
                  {targetHeaders.map((header) => (
                    <td key={header} className="p-3 text-slate-700 dark:text-slate-300">
                      {row.transformedData[header] ?? "-"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
        <button
          onClick={onBackToEdit}
          disabled={isSubmitting}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
        >
          ← Modifier le mapping
        </button>

        <button
          onClick={onConfirmImport}
          disabled={isSubmitting || dryRunResult.validRowsCount === 0}
          className="rounded-lg bg-emerald-600 px-5 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 dark:bg-emerald-500"
        >
          {isSubmitting ? "Importation..." : "Valider et lancer l'import"}
        </button>
      </div>
    </div>
  );
};
