import React, { useState, useMemo } from "react";
import { validateMappings, type MappingRow, type TransformType } from "../types";

interface MappingEditorProps {
  initialRows: MappingRow[];
  availableSourceFields: string[];
  availableTargetFields: string[];
  requiredTargetFields?: string[];
  onSave?: (rows: MappingRow[]) => void;
}

export const MappingEditor: React.FC<MappingEditorProps> = ({
  initialRows,
  availableSourceFields,
  availableTargetFields,
  requiredTargetFields = [],
  onSave,
}) => {
  const [rows, setRows] = useState<MappingRow[]>(initialRows);

  // Validation en temps réel dérivée de l'état
  const validationErrors = useMemo(
    () => validateMappings(rows, requiredTargetFields),
    [rows, requiredTargetFields]
  );

  const getRowError = (rowId: string, field: "sourceField" | "targetField" | "transform") => {
    return validationErrors.find((err) => err.rowId === rowId && err.field === field)?.message;
  };

  const handleRowChange = (id: string, key: keyof MappingRow, value: string) => {
    setRows((prev) =>
      prev.map((row) => (row.id === id ? { ...row, [key]: value } : row))
    );
  };

  const handleAddRow = () => {
    const newRow: MappingRow = {
      id: `row-${Date.now()}`,
      sourceField: availableSourceFields[0] || "",
      targetField: "",
      transform: "none",
    };
    setRows((prev) => [...prev, newRow]);
  };

  const handleRemoveRow = (id: string) => {
    setRows((prev) => prev.filter((row) => row.id !== id));
  };

  const globalErrors = validationErrors.filter((err) => err.rowId === "global");
  const isValid = validationErrors.length === 0;

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Édition des correspondances
          </h3>
          <p className="text-xs text-slate-500">
            Associez chaque champ source à un champ cible du schéma métier.
          </p>
        </div>
        <button
          onClick={handleAddRow}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          + Ajouter un champ
        </button>
      </div>

      {/* Erreurs globales */}
      {globalErrors.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
          <ul className="list-inside list-disc space-y-1">
            {globalErrors.map((err, i) => (
              <li key={i}>{err.message}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Table de mapping */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-900 dark:text-slate-400">
            <tr>
              <th className="p-3">Champ source</th>
              <th className="p-3">Champ cible</th>
              <th className="p-3">Transformation</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {rows.map((row) => {
              const sourceError = getRowError(row.id, "sourceField");
              const targetError = getRowError(row.id, "targetField");

              return (
                <tr key={row.id} className="align-top">
                  {/* Source */}
                  <td className="p-3">
                    <select
                      value={row.sourceField}
                      onChange={(e) => handleRowChange(row.id, "sourceField", e.target.value)}
                      className={`w-full rounded-md border px-3 py-1.5 text-xs focus:outline-none ${
                        sourceError
                          ? "border-red-500 bg-red-50 focus:ring-1 focus:ring-red-500"
                          : "border-slate-300 dark:border-slate-700 dark:bg-slate-900"
                      }`}
                    >
                      <option value="">-- Sélectionner --</option>
                      {availableSourceFields.map((field) => (
                        <option key={field} value={field}>
                          {field}
                        </option>
                      ))}
                    </select>
                    {sourceError && <p className="mt-1 text-[10px] text-red-600">{sourceError}</p>}
                  </td>

                  {/* Target */}
                  <td className="p-3">
                    <select
                      value={row.targetField}
                      onChange={(e) => handleRowChange(row.id, "targetField", e.target.value)}
                      className={`w-full rounded-md border px-3 py-1.5 text-xs focus:outline-none ${
                        targetError
                          ? "border-red-500 bg-red-50 focus:ring-1 focus:ring-red-500 dark:bg-red-950/20"
                          : "border-slate-300 dark:border-slate-700 dark:bg-slate-900"
                      }`}
                    >
                      <option value="">-- Sélectionner --</option>
                      {availableTargetFields.map((field) => (
                        <option key={field} value={field}>
                          {field} {requiredTargetFields.includes(field) ? "*" : ""}
                        </option>
                      ))}
                    </select>
                    {targetError && <p className="mt-1 text-[10px] text-red-600">{targetError}</p>}
                  </td>

                  {/* Transform */}
                  <td className="p-3">
                    <select
                      value={row.transform}
                      onChange={(e) =>
                        handleRowChange(row.id, "transform", e.target.value as TransformType)
                      }
                      className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-xs focus:outline-none dark:border-slate-700 dark:bg-slate-900"
                    >
                      <option value="none">Aucune</option>
                      <option value="uppercase">MAJUSCULE</option>
                      <option value="lowercase">minuscule</option>
                      <option value="trim">Supprimer espaces</option>
                      <option value="date_iso">Format Date ISO</option>
                      <option value="cast_integer">Convertir en Entier</option>
                    </select>
                  </td>

                  {/* Actions */}
                  <td className="p-3 text-right">
                    <button
                      onClick={() => handleRemoveRow(row.id)}
                      className="text-xs text-red-600 hover:text-red-800 dark:text-red-400"
                    >
                      Supprimer
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer / Validation */}
      <div className="flex items-center justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
        <span className="text-xs text-slate-500">
          {isValid
            ? "✅ Toutes les correspondances sont valides."
            : `❌ ${validationErrors.length} erreur(s) détectée(s).`}
        </span>
        <button
          onClick={() => onSave && onSave(rows)}
          disabled={!isValid}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 dark:bg-indigo-500"
        >
          Enregistrer le mapping
        </button>
      </div>
    </div>
  );
};
