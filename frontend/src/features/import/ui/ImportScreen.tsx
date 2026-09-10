import React, { useState } from "react";
import { apiClient } from "@shared/api/client";
import { ApiError } from "@shared/api/types";
import type { ProblemDetails } from "@shared/api/types";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import type { ImportReport } from "../types";

interface ImportScreenProps {
  onImportCompleted?: (report: ImportReport) => void;
}

const METRIC_TONES = {
  imported: "text-neon-green",
  duplicate: "text-warning",
  rejected: "text-danger",
  missing: "text-foreground",
} as const;

export const ImportScreen: React.FC<ImportScreenProps> = ({ onImportCompleted }) => {
  const [mappingId, setMappingId] = useState<string>("tracelab-jsonl");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<ProblemDetails | null>(null);
  const [report, setReport] = useState<ImportReport | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
      setError(null);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0 || !mappingId.trim()) return;

    setLoading(true);
    setError(null);
    setReport(null);

    const formData = new FormData();
    formData.append("mapping_id", mappingId.trim());
    files.forEach((file) => formData.append("files", file));

    try {
      const result = await apiClient.post<ImportReport>("/imports", formData);
      setReport(result);
      if (onImportCompleted) onImportCompleted(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem);
      } else {
        setError({
          title: "Erreur inattendue",
          status: 500,
          detail: "Impossible de communiquer avec le serveur d'import.",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <section className="space-y-5">
      <div>
        <h2 className="cyber-title text-neon-cyan">Importer des traces</h2>
        <p className="mt-1 text-sm text-foreground-muted">
          Téléversez vos fichiers JSONL, CSV ou Parquet et appliquez une configuration de mapping.
        </p>
      </div>

      <ApiErrorBanner error={error} onDismiss={() => setError(null)} />

      <form onSubmit={handleSubmit} className="cyber-card space-y-6">
        {/* Choix du mapping */}
        <div>
          <label htmlFor="mapping-id" className="block text-sm font-medium">
            Identifiant du mapping <span className="text-danger">*</span>
          </label>
          <input
            id="mapping-id"
            type="text"
            value={mappingId}
            onChange={(e) => setMappingId(e.target.value)}
            placeholder="ex. tracelab-jsonl"
            required
            className="cyber-field mt-1"
          />
        </div>

        {/* Dépôt de fichiers */}
        <div>
          <label htmlFor="file-upload" className="block text-sm font-medium">
            Fichiers sources <span className="text-danger">*</span>
          </label>
          <div className="mt-1 flex justify-center border-2 border-dashed border-border-strong bg-surface-muted/50 px-6 py-8 transition hover:border-neon-cyan">
            <div className="space-y-2 text-center">
              <input
                id="file-upload"
                type="file"
                multiple
                accept=".jsonl,.csv,.parquet,.json"
                onChange={handleFileChange}
                className="hidden"
              />
              <span className="inline-block cursor-pointer border border-neon-cyan bg-neon-cyan/10 px-4 py-2 text-sm font-semibold uppercase tracking-wider text-neon-cyan transition hover:bg-neon-cyan/20">
                Parcourir les fichiers
              </span>
              <p className="text-xs text-foreground-muted">Formats supportés : JSONL, CSV, Parquet</p>
            </div>
          </div>
        </div>

        {/* Aperçu des fichiers */}
        {files.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">Fichiers sélectionnés ({files.length}) :</h3>
            <ul className="divide-y divide-border border border-border">
              {files.map((file, idx) => (
                <li
                  key={`${file.name}-${idx}`}
                  className="flex items-center justify-between gap-2 p-3 text-sm"
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <span className="truncate text-xs text-foreground">{file.name}</span>
                    <span className="shrink-0 text-xs text-foreground-muted">
                      ({formatFileSize(file.size)})
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeFile(idx)}
                    className="shrink-0 text-xs uppercase tracking-wider text-danger hover:underline"
                  >
                    Supprimer
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || files.length === 0 || !mappingId.trim()}
          className="w-full border border-neon-cyan bg-neon-cyan/15 py-2.5 text-sm font-semibold uppercase tracking-wider text-neon-cyan transition hover:bg-neon-cyan/25 hover:shadow-neon-cyan disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Importation en cours…" : "Lancer l'import"}
        </button>
      </form>

      {/* Bilan d'import */}
      {report && (
        <div className="cyber-card animate-fade-in space-y-4">
          <div className="flex items-center justify-between gap-3 border-b border-border pb-3">
            <h2 className="cyber-title">Bilan de l'importation</h2>
            <span
              className={`border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider ${
                report.status === "completed"
                  ? "border-neon-green/60 text-neon-green"
                  : "border-warning/60 text-warning"
              }`}
            >
              {report.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <ReportStat label="Importés" value={report.imported_count} tone={METRIC_TONES.imported} />
            <ReportStat label="Doublons" value={report.duplicate_count} tone={METRIC_TONES.duplicate} />
            <ReportStat label="Rejets" value={report.rejected_count} tone={METRIC_TONES.rejected} />
            <ReportStat
              label="Infos manquantes"
              value={
                typeof report.missing_info_count === "number"
                  ? report.missing_info_count
                  : JSON.stringify(report.missing_info_count)
              }
              tone={METRIC_TONES.missing}
            />
          </div>
        </div>
      )}
    </section>
  );
};

function ReportStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  tone: string;
}) {
  return (
    <div className="cyber-inset p-3 text-center">
      <p className="text-xs text-foreground-muted">{label}</p>
      <p className={`mt-1 text-xl font-bold tabular-nums ${tone}`}>{value}</p>
    </div>
  );
}
