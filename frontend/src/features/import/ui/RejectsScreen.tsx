import React, { useCallback, useEffect, useState } from "react";
import { apiClient } from "@shared/api/client";
import { ApiError } from "@shared/api/types";
import type { ProblemDetails } from "@shared/api/types";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import { REASON_CODE_EXPLANATIONS } from "../model/reason-code-explanations";
import type { PaginatedResponse, RejectRecord } from "../types";

export const RejectsScreen: React.FC<{ importId?: string }> = ({ importId = "batch-123" }) => {
  const [rejects, setRejects] = useState<RejectRecord[]>([]);
  const [selectedReject, setSelectedReject] = useState<RejectRecord | null>(null);
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ProblemDetails | null>(null);

  const fetchRejects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<PaginatedResponse<RejectRecord>>(
        `/imports/${importId}/rejects?limit=100&offset=0`
      );
      setRejects(data.items);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem);
      } else {
        setError({
          title: "Erreur de chargement",
          status: 500,
          detail: "Impossible de récupérer la liste des rejets.",
        });
      }
    } finally {
      setLoading(false);
    }
  }, [importId]);

  useEffect(() => {
    void fetchRejects();
  }, [fetchRejects]);

  const filteredRejects = rejects.filter(
    (r) =>
      r.reason_code.toLowerCase().includes(searchFilter.toLowerCase()) ||
      r.reason_detail.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analyse des Rejets d'Import</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Inspection détaillée des lignes rejetées pour le lot <span className="font-mono font-semibold">{importId}</span>.
        </p>
      </div>

      <ApiErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="flex items-center justify-between gap-4">
        <input
          type="text"
          placeholder="Filtrer par code ou motif..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          className="w-72 rounded-md border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        />
        <span className="text-xs text-slate-500">{filteredRejects.length} rejets affichés</span>
      </div>

      {loading ? (
        <div className="p-8 text-center text-sm text-slate-500">Chargement des rejets...</div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Liste des rejets */}
          <div className="lg:col-span-2 overflow-x-auto rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 dark:bg-slate-900">
                <tr>
                  <th className="p-3">Ligne</th>
                  <th className="p-3">Code Rejet</th>
                  <th className="p-3">Motif Brut</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {filteredRejects.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-slate-500">
                      Aucun rejet ne correspond aux critères.
                    </td>
                  </tr>
                ) : (
                  filteredRejects.map((item, idx) => {
                    return (
                      <tr
                        key={idx}
                        className={`hover:bg-slate-50 dark:hover:bg-slate-900/50 ${
                          selectedReject === item ? "bg-indigo-50/50 dark:bg-indigo-950/30" : ""
                        }`}
                      >
                        <td className="p-3 font-mono font-medium">{item.record_index}</td>
                        <td className="p-3">
                          <span className="rounded bg-red-100 px-2 py-0.5 font-mono text-xs font-semibold text-red-800 dark:bg-red-950 dark:text-red-300">
                            {item.reason_code}
                          </span>
                        </td>
                        <td className="p-3 text-slate-600 dark:text-slate-300">{item.reason_detail}</td>
                        <td className="p-3">
                          <button
                            onClick={() => setSelectedReject(item)}
                            className="text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
                          >
                            Inspecter
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Panneau latéral explicatif */}
          <div className="lg:col-span-1">
            {selectedReject ? (
              <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                <h3 className="text-base font-bold">Ligne #{selectedReject.record_index}</h3>

                {(() => {
                  const meta = REASON_CODE_EXPLANATIONS[selectedReject.reason_code] || {
                    label: selectedReject.reason_code,
                    explanation: "Code d'erreur générique ou personnalisé.",
                    action: "Vérifier le schéma d'intégration.",
                  };
                  return (
                    <div className="space-y-3 text-xs">
                      <div>
                        <p className="font-semibold text-slate-500">Qualification</p>
                        <p className="mt-0.5 text-sm font-medium text-slate-800 dark:text-slate-200">
                          {meta.label}
                        </p>
                      </div>
                      <div>
                        <p className="font-semibold text-slate-500">Explication</p>
                        <p className="mt-0.5 text-slate-600 dark:text-slate-400">{meta.explanation}</p>
                      </div>
                      <div>
                        <p className="font-semibold text-slate-500">Action recommandée</p>
                        <p className="mt-0.5 text-indigo-700 dark:text-indigo-300">{meta.action}</p>
                      </div>
                    </div>
                  );
                })()}

                {selectedReject.payload && (
                  <div className="border-t border-slate-200 pt-3 dark:border-slate-800">
                    <p className="text-xs font-semibold text-slate-500">Donnée brute (Payload)</p>
                    <pre className="mt-1 max-h-48 overflow-auto rounded bg-slate-100 p-2 font-mono text-[11px] text-slate-800 dark:bg-slate-900 dark:text-slate-200">
                      {JSON.stringify(selectedReject.payload, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-slate-300 p-4 text-center text-xs text-slate-400 dark:border-slate-800">
                Cliquez sur "Inspecter" pour voir l'explication explicite et la donnée brute d'un rejet.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
