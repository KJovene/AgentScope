import { describe, expect, it } from 'vitest';

import { type ImportBatch } from '@features/import/api/import.contracts';
import { rejectReasonLabel, toImportRow } from '@features/import/model/import.mappers';

const batch: ImportBatch = {
  id: 'sha1',
  sourceName: 'TraceLab',
  originalFilename: 'trace.jsonl',
  fileFormat: 'jsonl',
  status: 'succeeded',
  importedAt: '2026-01-02T10:00:00Z',
  importedCount: 1200,
  duplicateCount: 0,
  rejectedCount: 3,
  missingInfoCount: 2,
};

describe('toImportRow', () => {
  it('maps and formats a batch into a table row', () => {
    const row = toImportRow(batch);
    expect(row.id).toBe('sha1');
    expect(row.source).toBe('TraceLab');
    expect(row.filename).toBe('trace.jsonl');
    expect(row.format).toBe('JSONL');
    expect(row.status).toBe('succeeded');
    expect(row.statusLabel).toBe('Terminé');
    expect(row.imported).toMatch(/1[\s ]?200/);
    expect(row.rejected).toBe('3');
    expect(row.missingInfo).toBe('2');
    expect(row.importedAt).toMatch(/2026/);
    expect(row.hasRejects).toBe(true);
  });

  it('hasRejects is false when rejectedCount is 0', () => {
    expect(toImportRow({ ...batch, rejectedCount: 0 }).hasRejects).toBe(false);
  });

  it.each([
    ['pending', 'En attente'],
    ['running', 'En cours'],
    ['failed', 'Échoué'],
  ] as const)('status %s -> label %s', (status, label) => {
    expect(toImportRow({ ...batch, status }).statusLabel).toBe(label);
  });
});

describe('rejectReasonLabel', () => {
  it('translates every controlled code', () => {
    expect(rejectReasonLabel('unparseable_record')).toBe('Enregistrement illisible');
    expect(rejectReasonLabel('missing_required_field')).toBe('Champ requis manquant');
    expect(rejectReasonLabel('transform_failed')).toBe('Échec de transformation');
    expect(rejectReasonLabel('unknown_target_field')).toBe('Champ cible inconnu');
    expect(rejectReasonLabel('duplicate_in_file')).toBe('Doublon dans le fichier');
    expect(rejectReasonLabel('schema_violation')).toBe('Violation du schéma');
  });
});
