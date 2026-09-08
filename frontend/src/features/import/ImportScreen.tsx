import React, { useState } from "react";
import { apiClient } from "@shared/api/client";
import { ApiError } from "@shared/api/types";
import type { ProblemDetails } from "@shared/api/types";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import type { ImportReport } from "./types";

interface ImportScreenProps {
  onImportCompleted?: (report: ImportReport) => void;
}

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
    <div className="mx-auto max-w-4xl space-y-6">
    <div>
    <h1 className="text-2xl font-bold tracking-tight">Importer des traces</h1>
    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
    Téléversez vos fichiers JSONL, CSV ou Parquet et appliquez une configuration de mapping.
    </p>
    </div>

    <ApiErrorBanner error={error} onDismiss={() => setError(null)} />

    <form onSubmit={handleSubmit} className="space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
    {/* Choix du mapping */}
    <div>
    <label htmlFor="mapping-id" className="block text-sm font-medium">
    Identifiant du mapping <span className="text-red-500">*</span>
    </label>
    <input
    id="mapping-id"
    type="text"
    value={mappingId}
    onChange={(e) => setMappingId(e.target.value)}
    placeholder="ex. tracelab-jsonl"
    required
    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900"
    />
    </div>

    {/* Dépôt de fichiers */}
    <div>
    <label htmlFor="file-upload" className="block text-sm font-medium">
    Fichiers sources <span className="text-red-500">*</span>
    </label>
    <div className="mt-1 flex justify-center rounded-md border-2 border-dashed border-slate-300 px-6 py-8 dark:border-slate-700">
    <div className="space-y-2 text-center">
    <input
    id="file-upload"
    type="file"
    multiple
    accept=".jsonl,.csv,.parquet,.json"
    onChange={handleFileChange}
    className="hidden"
    />
    <span className="inline-block cursor-pointer rounded-md bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-600 hover:bg-indigo-100 dark:bg-indigo-950 dark:text-indigo-300">
    Parcourir les fichiers
    </span>
    <p className="text-xs text-slate-500">Formats supportés : JSONL, CSV, Parquet</p>
    </div>
    </div>
    </div>

    {/* Aperçu des fichiers */}
    {files.length > 0 && (
      <div className="space-y-2">
      <h3 className="text-sm font-medium">Fichiers sélectionnés ({files.length}) :</h3>
      <ul className="divide-y divide-slate-200 rounded-md border border-slate-200 dark:divide-slate-800 dark:border-slate-800">
      {files.map((file, idx) => (
        <li key={`${file.name}-${idx}`} className="flex items-center justify-between p-3 text-sm">
        <div className="flex items-center space-x-2 truncate">
        <span className="font-mono text-xs text-slate-500">{file.name}</span>
        <span className="text-xs text-slate-400">({formatFileSize(file.size)})</span>
        </div>
        <button
        type="button"
        onClick={() => removeFile(idx)}
        className="text-xs text-red-600 hover:underline dark:text-red-400"
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
    className="w-full rounded-md bg-indigo-600 py-2,5 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
    >
    {loading ? "Importation en cours…" : "Lancer l'import"}
    </button>
    </form>

    {/* Bilan d'import */}
    {report && (
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3 dark:border-slate-800">
      <h2 className="text-lg font-bold">Bilan de l'importation</h2>
      <span
      className={`rounded px-2,5 py-1 text-xs font-semibold ${
        report.status === "completed"
        ? "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300"
        : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
        }`}
        >
        {report.status}
        </span>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-md bg-slate-50 p-3 text-center dark:bg-slate-900">
        <p className="text-xs text-slate-500">Importés</p>
        <p className="mt-1 text-xl font-bold text-slate-900 dark:text-slate-100">
        {report.imported_count}
        </p>
        </div>
        <div className="rounded-md bg-slate-50 p-3 text-center dark:bg-slate-900">
        <p className="text-xs text-slate-500">Doublons</p>
        <p className="mt-1 text-xl font-bold text-slate-900 dark:text-slate-100">
        {report.duplicate_count}
        </p>
        </div>
        <div className="rounded-md bg-slate-50 p-3 text-center dark:bg-slate-900">
        <p className="text-xs text-slate-500">Rejets</p>
        <p className="mt-1 text-xl font-bold text-slate-900 dark:text-slate-100">
        {report.rejected_count}
        </p>
        </div>
        <div className="rounded-md bg-slate-50 p-3 text-center dark:bg-slate-900">
        <p className="text-xs text-slate-500">Infos manquantes</p>
        <p className="mt-1 text-xl font-bold text-slate-900 dark:text-slate-100">
        {report.missing_info_count}
        </p>
        </div>
        </div>
        </div>
      )}
      </div>
    );
  };
