import { describe, expect, it } from 'vitest';

import {
  analyzeResultSchema,
  fieldProfileSchema,
  fieldProfileSetSchema,
} from '@features/mapping-agent/api/analyze.contracts';

const validField = {
  path: 'usage.input_tokens',
  inferred_type: 'int',
  null_ratio: 0.04,
  distinct_count: 87,
  sample_values: [120, 340, 58],
};

describe('analyze.contracts', () => {
  it('fieldProfileSchema accepts a well-formed field profile', () => {
    expect(fieldProfileSchema.parse(validField)).toEqual(validField);
  });

  it('fieldProfileSchema rejects a null_ratio outside [0, 1]', () => {
    expect(fieldProfileSchema.safeParse({ ...validField, null_ratio: 1.5 }).success).toBe(false);
  });

  it('fieldProfileSetSchema validates the envelope', () => {
    const parsed = fieldProfileSetSchema.parse({ record_count: 500, fields: [validField] });
    expect(parsed.fields).toHaveLength(1);
  });

  it('analyzeResultSchema validates a full /analyze response', () => {
    const parsed = analyzeResultSchema.parse({
      profile: { record_count: 500, fields: [validField] },
      proposal: {
        definition: { source_format: 'jsonl' },
        explanations: [
          {
            target_field: 'model_call.prompt_tokens',
            source_field: 'usage.input_tokens',
            rationale: 'cohérent',
            confidence: 0.92,
          },
        ],
        ambiguities: [],
        unmapped_fields: ['debug'],
      },
    });
    expect(parsed.profile.record_count).toBe(500);
    expect(parsed.proposal.unmapped_fields).toEqual(['debug']);
  });
});
