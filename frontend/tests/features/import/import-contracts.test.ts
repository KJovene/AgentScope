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
  source_id: 'src-tracelab',
  mapping_id: 'demo',
  status: 'completed',
  imported_at: '2026-01-01T00:00:00Z',
  imported_count: 3,
  duplicate_count: 0,
  rejected_count: 1,
  missing_info_count: 0,
};

describe('import.contracts', () => {
  it('importStatusSchema accepts any backend status string', () => {
    expect(importStatusSchema.safeParse('completed').success).toBe(true);
    expect(importStatusSchema.safeParse('partial').success).toBe(true);
  });

  it('importBatchSchema accepts a well-formed batch', () => {
    expect(importBatchSchema.parse(validBatch)).toEqual(validBatch);
  });

  it('importBatchSchema accepts a per-field missing_info_count breakdown', () => {
    expect(
      importBatchSchema.safeParse({ ...validBatch, missing_info_count: { session_id: 2 } })
        .success,
    ).toBe(true);
  });

  it('importBatchSchema rejects a negative count and a bad datetime', () => {
    expect(importBatchSchema.safeParse({ ...validBatch, imported_count: -1 }).success).toBe(false);
    expect(importBatchSchema.safeParse({ ...validBatch, imported_at: 'nope' }).success).toBe(
      false,
    );
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

  it('importRejectSchema mirrors the backend RejectRecord shape', () => {
    expect(
      importRejectSchema.parse({
        record_index: 2,
        reason_code: 'missing_required_field',
        reason_detail: 'no sid',
      }).reason_code,
    ).toBe('missing_required_field');
  });

  it('createImportInputSchema requires a mappingId and at least one File', () => {
    const file = new File(['{}'], 'a.jsonl');
    expect(createImportInputSchema.parse({ mappingId: 'm', files: [file] }).files).toHaveLength(1);
    expect(createImportInputSchema.safeParse({ mappingId: '', files: [file] }).success).toBe(false);
    expect(createImportInputSchema.safeParse({ mappingId: 'm', files: [] }).success).toBe(false);
  });
});
