export type TransformType = "none" | "uppercase" | "lowercase" | "trim" | "date_iso" | "cast_integer";

export interface MappingRow {
  id: string;
  sourceField: string;
  targetField: string;
  transform: TransformType;
  required?: boolean;
}

export interface ValidationError {
  rowId: string;
  field: "sourceField" | "targetField" | "transform";
  message: string;
}

export interface PreviewRow {
  rowIndex: number;
  sourceData: Record<string, string>;
  transformedData: Record<string, string>;
  isValid: boolean;
  rejectReason?: string;
}

export interface DryRunResult {
  totalRows: number;
  validRowsCount: number;
  rejectedRowsCount: number;
  rows: PreviewRow[];
}

export const validateMappings = (rows: MappingRow[], requiredTargetFields: string[] = []): ValidationError[] => {
  const errors: ValidationError[] = [];
  const targetCounts = new Map<string, number>();

  rows.forEach((row) => {
    // Validation champ source requis
    if (!row.sourceField.trim()) {
      errors.push({
        rowId: row.id,
        field: "sourceField",
        message: "Le champ source ne peut pas être vide.",
      });
    }

    // Validation champ cible requis
    if (!row.targetField.trim()) {
      errors.push({
        rowId: row.id,
        field: "targetField",
        message: "Le champ cible est obligatoire.",
      });
    } else {
      targetCounts.set(row.targetField, (targetCounts.get(row.targetField) || 0) + 1);
    }
  });

  // Détection des doublons sur les champs cibles
  rows.forEach((row) => {
    if (row.targetField && (targetCounts.get(row.targetField) || 0) > 1) {
      errors.push({
        rowId: row.id,
        field: "targetField",
        message: `Le champ cible « ${row.targetField} » est assigné plusieurs fois.`,
      });
    }
  });

  // Vérification des champs cibles obligatoires manquants
  const mappedTargets = new Set(rows.map((r) => r.targetField));
  requiredTargetFields.forEach((reqTarget) => {
    if (!mappedTargets.has(reqTarget)) {
      errors.push({
        rowId: "global",
        field: "targetField",
        message: `Le champ requis « ${reqTarget} » n'est pas associé.`,
      });
    }
  });

  return errors;
};
