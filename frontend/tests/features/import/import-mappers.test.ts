import { describe, expect, it } from 'vitest';

import { type ImportBatch } from '@features/import/api/import.contracts';
import { rejectReasonLabel, toImportRow } from '@features/import/model/import.mappers';

const batch: ImportBatch = {
  id: 'sha1',
  source_id: 'src-tracelab',
  mapping_id: 'tracelab-jsonl',
  status: 'completed',
  imported_at: '2026-01-02T10:00:00Z',
  imported_count: 1200,
  duplicate_count: 0,
  rejected_count: 3,
  missing_info_count: 2,
};

describe('toImportRow', () => {
  it('maps and formats a batch into a table row', () => {
    const row = toImportRow(batch);
    expect(row.id).toBe('sha1');
    expect(row.sourceId).toBe('src-tracelab');
    expect(row.mappingId).toBe('tracelab-jsonl');
    expect(row.status).toBe('completed');
    expect(row.statusLabel).toBe('Réussi');
    expect(row.imported).toMatch(/1[\s ]?200/);
    expect(row.rejected).toBe('3');
    expect(row.missingInfo).toBe('2');
    expect(row.importedAt).toMatch(/2026/);
    expect(row.hasRejects).toBe(true);
  });

  it('hasRejects is false when rejected_count is 0', () => {
    expect(toImportRow({ ...batch, rejected_count: 0 }).hasRejects).toBe(false);
  });

  it('sums missing_info_count when the backend returns a per-field breakdown', () => {
    expect(
      toImportRow({ ...batch, missing_info_count: { session_id: 2, tool_name: 3 } }).missingInfo,
    ).toBe('5');
  });

  it.each([
    ['completed', 'Réussi'],
    ['partial', 'Partiel'],
    ['failed', 'Échoué'],
  ] as const)('status %s -> label %s', (status, label) => {
    expect(toImportRow({ ...batch, status }).statusLabel).toBe(label);
  });

  it('falls back to the raw status when unknown', () => {
    expect(toImportRow({ ...batch, status: 'weird' }).statusLabel).toBe('weird');
  });
});

describe('rejectReasonLabel', () => {
  it('returns the backend reason code as-is', () => {
    expect(rejectReasonLabel('unparseable_record')).toBe('unparseable_record');
  });
});
