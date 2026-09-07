import { formatDateTime, formatNumber } from '@shared/lib/format';

import { type ImportBatch, type ImportReject } from '../api/import.contracts';

const REJECT_REASON_LABELS: Record<ImportReject['reasonCode'], string> = {
  unparseable_record: 'Enregistrement illisible',
  missing_required_field: 'Champ requis manquant',
  transform_failed: 'Échec de transformation',
  unknown_target_field: 'Champ cible inconnu',
  duplicate_in_file: 'Doublon dans le fichier',
  schema_violation: 'Violation du schéma',
};

const STATUS_LABELS: Record<ImportBatch['status'], string> = {
  pending: 'En attente',
  running: 'En cours',
  succeeded: 'Terminé',
  failed: 'Échoué',
};

export interface ImportRow {
  id: string;
  source: string;
  filename: string;
  format: string;
  statusLabel: string;
  status: ImportBatch['status'];
  importedAt: string;
  imported: string;
  duplicates: string;
  rejected: string;
  missingInfo: string;
  hasRejects: boolean;
}

/** DTO -> table row. One place to map/format import batches (DRY). */
export function toImportRow(batch: ImportBatch): ImportRow {
  return {
    id: batch.id,
    source: batch.sourceName,
    filename: batch.originalFilename,
    format: batch.fileFormat.toUpperCase(),
    status: batch.status,
    statusLabel: STATUS_LABELS[batch.status],
    importedAt: formatDateTime(batch.importedAt),
    imported: formatNumber(batch.importedCount),
    duplicates: formatNumber(batch.duplicateCount),
    rejected: formatNumber(batch.rejectedCount),
    missingInfo: formatNumber(batch.missingInfoCount),
    hasRejects: batch.rejectedCount > 0,
  };
}

export function rejectReasonLabel(code: ImportReject['reasonCode']): string {
  return REJECT_REASON_LABELS[code];
}
