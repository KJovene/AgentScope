import { describe, expect, it } from 'vitest';

import { problemDetailsSchema } from '@shared/types/problem-details';

describe('problemDetailsSchema', () => {
  it('defaults type and accepts a minimal body', () => {
    const parsed = problemDetailsSchema.parse({ title: 'Oops', status: 500 });
    expect(parsed.type).toBe('about:blank');
    expect(parsed.detail).toBeUndefined();
  });

  it('accepts field errors', () => {
    const parsed = problemDetailsSchema.parse({
      title: 'Invalid',
      status: 422,
      errors: [{ field: 'x', message: 'required' }, { message: 'global' }],
    });
    expect(parsed.errors).toHaveLength(2);
  });

  it('rejects a non-integer status', () => {
    expect(problemDetailsSchema.safeParse({ title: 'x', status: 1.5 }).success).toBe(false);
  });
});
