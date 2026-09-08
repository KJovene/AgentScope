import { describe, expect, it } from 'vitest';

import { toFieldProfileSetView } from '@features/mapping-agent/model/analyze.mappers';

describe('analyze.mappers', () => {
  it('toFieldProfileSetView maps snake_case DTO to a camelCase view model', () => {
    const view = toFieldProfileSetView({
      record_count: 500,
      fields: [
        {
          path: 'usage.input_tokens',
          inferred_type: 'int',
          null_ratio: 0.04,
          distinct_count: 87,
          sample_values: [120, 340],
        },
      ],
    });

    expect(view).toEqual({
      recordCount: 500,
      fields: [
        {
          path: 'usage.input_tokens',
          inferredType: 'int',
          nullRatio: 0.04,
          distinctCount: 87,
          sampleValues: [120, 340],
        },
      ],
    });
  });
});
