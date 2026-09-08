import { describe, expect, it } from 'vitest';

import {
  createImportInputSchema,
  importBatchSchema,
  importListParamsSchema,
  importListResponseSchema,
  importRejectSchema,
  importStatusSchema,
} from '@features/import/api/import.contracts';

const validBatch = {
  id: 'sha',
  sourceName: 'demo',
  originalFilename: 'demo.jsonl',
  fileFormat: 'jsonl' as const,
  status: 'succeeded' as const,
  importedAt: '2026-01-01T00:00:00Z',
  importedCount: 3,
  duplicateCount: 0,
  rejectedCount: 1,
  missingInfoCount: 0,
};

describe('import.contracts', () => {
  it('importStatusSchema', () => {
    expect(importStatusSchema.options).toEqual(['pending', 'running', 'succeeded', 'failed']);
    expect(importStatusSchema.safeParse('done').success).toBe(false);
  });

  it('importBatchSchema accepts a well-formed batch', () => {
    expect(importBatchSchema.parse(validBatch)).toEqual(validBatch);
  });

  it('importBatchSchema rejects a negative count and a bad datetime', () => {
    expect(importBatchSchema.safeParse({ ...validBatch, importedCount: -1 }).success).toBe(false);
    expect(importBatchSchema.safeParse({ ...validBatch, importedAt: 'nope' }).success).toBe(false);
  });

  it('importListParamsSchema merges pagination defaults with optional filters', () => {
    expect(importListParamsSchema.parse({ source: 'demo' })).toEqual({
      limit: 50,
      offset: 0,
      source: 'demo',
    });
  });

  it('importListResponseSchema validates the envelope', () => {
    const parsed = importListResponseSchema.parse({
      items: [validBatch],
      total: 1,
      limit: 50,
      offset: 0,
    });
    expect(parsed.items).toHaveLength(1);
  });

  it('importRejectSchema enforces the controlled reason vocabulary', () => {
    expect(
      importRejectSchema.parse({
        id: 'r1',
        recordIndex: 2,
        reasonCode: 'missing_required_field',
        reasonDetail: 'no sid',
      }).reasonCode,
    ).toBe('missing_required_field');
    expect(
      importRejectSchema.safeParse({
        id: 'r1',
        recordIndex: 2,
        reasonCode: 'banana',
        reasonDetail: 'x',
      }).success,
    ).toBe(false);
  });

  it('createImportInputSchema requires a mappingId and at least one File', () => {
    const file = new File(['{}'], 'a.jsonl');
    expect(createImportInputSchema.parse({ mappingId: 'm', files: [file] }).files).toHaveLength(1);
    expect(createImportInputSchema.safeParse({ mappingId: '', files: [file] }).success).toBe(false);
    expect(createImportInputSchema.safeParse({ mappingId: 'm', files: [] }).success).toBe(false);
  });
});
