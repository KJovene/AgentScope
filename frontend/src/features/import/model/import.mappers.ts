import { formatDateTime, formatNumber } from '@shared/lib/format';

import { type ImportBatch, type ImportReject } from '../api/import.contracts';

const STATUS_LABELS: Record<string, string> = {
  completed: 'Réussi',
  partial: 'Partiel',
  failed: 'Échoué',
};

export interface ImportRow {
  id: string;
  mappingId: string;
  sourceId: string | null;
  status: string;
  statusLabel: string;
  importedAt: string;
  imported: string;
  duplicates: string;
  rejected: string;
  missingInfo: string;
  hasRejects: boolean;
}

/** `missing_info_count` is either a total or a per-field breakdown. */
function missingInfoTotal(missing: number | Record<string, number>): number {
  if (typeof missing === 'number') return missing;
  return Object.values(missing).reduce((acc, count) => acc + count, 0);
}

/** DTO -> table row. One place to map/format import batches (DRY). */
export function toImportRow(batch: ImportBatch): ImportRow {
  return {
    id: batch.id,
    mappingId: batch.mapping_id,
    sourceId: batch.source_id ?? null,
    status: batch.status,
    statusLabel: STATUS_LABELS[batch.status] ?? batch.status,
    importedAt: batch.imported_at ? formatDateTime(batch.imported_at) : '—',
    imported: formatNumber(batch.imported_count),
    duplicates: formatNumber(batch.duplicate_count),
    rejected: formatNumber(batch.rejected_count),
    missingInfo: formatNumber(missingInfoTotal(batch.missing_info_count)),
    hasRejects: batch.rejected_count > 0,
  };
}

export function rejectReasonLabel(code: ImportReject['reason_code']): string {
  return code;
}
