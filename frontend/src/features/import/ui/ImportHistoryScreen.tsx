import React, { useEffect, useState } from "react";
import { apiClient } from "@shared/api/client";
import { ApiError } from "@shared/api/types";
import type { ProblemDetails } from "@shared/api/types";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import type { ImportReport, PaginatedResponse, RejectRecord } from "../types.ts";

export const ImportHistoryScreen: React.FC = () => {
  const [imports, setImports] = useState<ImportReport[]>([]);
  const [selectedImport, setSelectedImport] = useState<ImportReport | null>(null);
  const [rejects, setRejects] = useState<RejectRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingRejects, setLoadingRejects] = useState<boolean>(false);
  const [error, setError] = useState<ProblemDetails | null>(null);

  useEffect(() => {
    fetchImports();
  }, []);

  const fetchImports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<PaginatedResponse<ImportReport>>("/imports?limit=20&offset=0");
      setImports(data.items);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem);
      } else {
        setError({
          title: "Erreur de chargement",
          status: 500,
          detail: "Impossible de récupérer l'historique des imports.",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectImport = async (report: ImportReport) => {
    setSelectedImport(report);
    if (report.rejected_count > 0) {
      setLoadingRejects(true);
      try {
        const data = await apiClient.get<PaginatedResponse<RejectRecord>>(
          `/imports/${report.id}/rejects?limit=50&offset=0`
        );
        setRejects(data.items);
      } catch {
        setRejects([]);
      } finally {
        setLoadingRejects(false);
      }
    } else {
      setRejects([]);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800 dark:bg-green-950 dark:text-green-300">Réussi</span>;
      case "partial":
        return <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-950 dark:text-amber-300">Partiel</span>;
      default:
        return <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800 dark:bg-red-950 dark:text-red-300">Échec</span>;
    }
  };

  const getMissingCount = (missing: number | Record<string, number>): number => {
    if (typeof missing === "number") return missing;
    return Object.values(missing || {}).reduce((acc, curr) => acc + curr, 0);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Historique des imports</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Consultez l'ensemble des lots téléversés et le détail des rejets d'importation.
        </p>
      </div>

      <ApiErrorBanner error={error} onDismiss={() => setError(null)} />

      {loading ? (
        <div className="p-8 text-center text-sm text-slate-500">Chargement de l'historique…</div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Liste des imports */}
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
              Lots récents ({imports.length})
            </h2>
            {imports.length === 0 ? (
              <div className="rounded-lg border border-slate-200 bg-white p-4 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-950">
                Aucun import enregistré.
              </div>
            ) : (
              <div className="space-y-2">
                {imports.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleSelectImport(item)}
                    className={`w-full text-left rounded-lg border p-4 transition-colors ${
                      selectedImport?.id === item.id
                        ? "border-indigo-600 bg-indigo-50/50 dark:border-indigo-500 dark:bg-indigo-950/30"
                        : "border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-semibold">{item.id}</span>
                      {getStatusBadge(item.status)}
                    </div>
                    <div className="mt-2 text-xs text-slate-500 space-y-1">
                      <p>Mapping : <span className="font-mono text-slate-700 dark:text-slate-300">{item.mapping_id}</span></p>
                      <p>Date : {new Date(item.imported_at).toLocaleString()}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Panneau de détail du bilan */}
          <div className="lg:col-span-2">
            {selectedImport ? (
              <div className="space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
                  <div>
                    <h2 className="text-lg font-bold">Bilan : {selectedImport.id}</h2>
                    <p className="text-xs text-slate-500">Source : {selectedImport.source_id || "N/A"}</p>
                  </div>
                  {getStatusBadge(selectedImport.status)}
                </div>

                {/* Métriques d'import */}
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <div className="rounded-md bg-slate-50 p-3 text-center dark:bg-slate-900">
                    <p className="text-xs text-slate-500">Importés</p>
                    <p className="mt-1 text-2xl font-bold text-green-600 dark:text-green-400">
                      {selectedImport.imported_count}
                    </p>
                  </div>
                  <div className="rounded-md bg-slate-50 p-3 text-center dark:bg-slate-900">
                    <p className="text-xs text-slate-500">Doublons</p>
                    <p className="mt-1 text-2xl font-bold text-amber-600 dark:text-amber-400">
                      {selectedImport.duplicate_count}
                    </p>
                  </div>
                  <div className="rounded-md bg-slate-50 p-3 text-center dark:bg-slate-900">
                    <p className="text-xs text-slate-500">Rejets</p>
                    <p className="mt-1 text-2xl font-bold text-red-600 dark:text-red-400">
                      {selectedImport.rejected_count}
                    </p>
                  </div>
                  <div className="rounded-md bg-slate-50 p-3 text-center dark:bg-slate-900">
                    <p className="text-xs text-slate-500">Champs manquants</p>
                    <p className="mt-1 text-2xl font-bold text-slate-700 dark:text-slate-300">
                      {getMissingCount(selectedImport.missing_info_count)}
                    </p>
                  </div>
                </div>

                {/* Table des rejets */}
                {selectedImport.rejected_count > 0 && (
                  <div className="space-y-3 border-t border-slate-200 pt-4 dark:border-slate-800">
                    <h3 className="text-sm font-semibold">Détail des lignes rejetées</h3>
                    {loadingRejects ? (
                      <p className="text-xs text-slate-500">Chargement des rejets…</p>
                    ) : (
                      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-800">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-50 text-slate-500 dark:bg-slate-900">
                            <tr>
                              <th className="p-2.5">Ligne</th>
                              <th className="p-2.5">Code</th>
                              <th className="p-2.5">Raison</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                            {rejects.map((rej, idx) => (
                              <tr key={idx}>
                                <td className="p-2.5 font-mono">{rej.record_index}</td>
                                <td className="p-2.5 font-semibold text-red-600 dark:text-red-400">{rej.reason_code}</td>
                                <td className="p-2.5">{rej.reason_detail}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-400 dark:border-slate-800">
                Sélectionnez un lot dans la liste pour afficher le détail du bilan.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
