import React, { useEffect, useState } from "react";
import { apiClient } from "@shared/api/client";
import { ApiError } from "@shared/api/types";
import type { ProblemDetails } from "@shared/api/types";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import type { ImportReport, PaginatedResponse, RejectRecord } from "../types.ts";

const STATUS_STYLES = {
  completed: { label: "Réussi", cls: "border-neon-green/60 text-neon-green" },
  partial: { label: "Partiel", cls: "border-warning/60 text-warning" },
  failed: { label: "Échec", cls: "border-danger/60 text-danger" },
} as const;

type KnownStatus = keyof typeof STATUS_STYLES;

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
    const s = STATUS_STYLES[status as KnownStatus] ?? STATUS_STYLES.failed;
    return (
      <span
        className={`shrink-0 border px-2 py-0.5 text-xs font-semibold uppercase tracking-wider ${s.cls}`}
      >
        {s.label}
      </span>
    );
  };

  const getMissingCount = (missing: number | Record<string, number>): number => {
    if (typeof missing === "number") return missing;
    return Object.values(missing || {}).reduce((acc, curr) => acc + curr, 0);
  };

  return (
    <section className="space-y-5">
      <div>
        <h2 className="cyber-title text-neon-cyan">Historique des imports</h2>
        <p className="mt-1 text-sm text-foreground-muted">
          Consultez l'ensemble des lots téléversés et le détail des rejets d'importation.
        </p>
      </div>

      <ApiErrorBanner error={error} onDismiss={() => setError(null)} />

      {loading ? (
        <div className="cyber-inset p-8 text-center text-sm text-foreground-muted">
          Chargement de l'historique…
        </div>
      ) : (
        <div className="space-y-4">
          {/* Liste des lots */}
          <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground-muted">
            Lots récents ({imports.length})
          </h3>
          {imports.length === 0 ? (
            <div className="cyber-inset p-4 text-center text-sm text-foreground-muted">
              Aucun import enregistré.
            </div>
          ) : (
            <ul className="stagger space-y-2">
              {imports.map((item) => {
                const selected = selectedImport?.id === item.id;
                return (
                  <li key={item.id}>
                    <button
                      onClick={() => handleSelectImport(item)}
                      aria-pressed={selected}
                      className={`w-full border p-4 text-left transition ${
                        selected
                          ? "border-neon-cyan bg-neon-cyan/10 text-foreground neon-cyan"
                          : "border-border bg-surface hover:border-border-strong"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-xs font-semibold">{item.id}</span>
                        {getStatusBadge(item.status)}
                      </div>
                      <div className="mt-2 space-y-1 text-xs text-foreground-muted">
                        <p>
                          Mapping : <span className="text-foreground">{item.mapping_id}</span>
                        </p>
                        <p>Date : {new Date(item.imported_at).toLocaleString()}</p>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

          {/* Détail du bilan sélectionné */}
          {selectedImport ? (
            <div className="cyber-card animate-fade-in space-y-5">
              <div className="flex items-center justify-between gap-3 border-b border-border pb-4">
                <div className="min-w-0">
                  <h3 className="truncate text-base font-bold">Bilan : {selectedImport.id}</h3>
                  <p className="text-xs text-foreground-muted">
                    Source : {selectedImport.source_id || "N/A"}
                  </p>
                </div>
                {getStatusBadge(selectedImport.status)}
              </div>

              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="cyber-inset p-3 text-center">
                  <p className="text-xs text-foreground-muted">Importés</p>
                  <p className="mt-1 text-2xl font-bold tabular-nums text-neon-green">
                    {selectedImport.imported_count}
                  </p>
                </div>
                <div className="cyber-inset p-3 text-center">
                  <p className="text-xs text-foreground-muted">Doublons</p>
                  <p className="mt-1 text-2xl font-bold tabular-nums text-warning">
                    {selectedImport.duplicate_count}
                  </p>
                </div>
                <div className="cyber-inset p-3 text-center">
                  <p className="text-xs text-foreground-muted">Rejets</p>
                  <p className="mt-1 text-2xl font-bold tabular-nums text-danger">
                    {selectedImport.rejected_count}
                  </p>
                </div>
                <div className="cyber-inset p-3 text-center">
                  <p className="text-xs text-foreground-muted">Champs manquants</p>
                  <p className="mt-1 text-2xl font-bold tabular-nums text-foreground">
                    {getMissingCount(selectedImport.missing_info_count)}
                  </p>
                </div>
              </div>

              {selectedImport.rejected_count > 0 && (
                <div className="space-y-3 border-t border-border pt-4">
                  <h4 className="text-sm font-semibold">Détail des lignes rejetées</h4>
                  {loadingRejects ? (
                    <p className="text-xs text-foreground-muted">Chargement des rejets…</p>
                  ) : (
                    <div className="overflow-x-auto border border-border">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-surface-muted uppercase text-foreground-muted">
                          <tr>
                            <th className="p-2.5">Ligne</th>
                            <th className="p-2.5">Code</th>
                            <th className="p-2.5">Raison</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {rejects.map((rej, idx) => (
                            <tr key={idx}>
                              <td className="p-2.5 tabular-nums">{rej.record_index}</td>
                              <td className="p-2.5 font-semibold text-danger">{rej.reason_code}</td>
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
            imports.length > 0 && (
              <div className="flex h-40 items-center justify-center border border-dashed border-border-strong p-6 text-center text-sm text-foreground-muted">
                Sélectionnez un lot pour afficher le détail du bilan.
              </div>
            )
          )}
        </div>
      )}
    </section>
  );
};
