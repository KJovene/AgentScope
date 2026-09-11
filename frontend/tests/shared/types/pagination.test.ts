import { describe, expect, it } from 'vitest';
import { z } from 'zod';

import { paginated, paginationParamsSchema } from '@shared/types/pagination';

describe('pagination schemas', () => {
  it('paginationParamsSchema applies defaults', () => {
    expect(paginationParamsSchema.parse({})).toEqual({ limit: 50, offset: 0 });
  });

  it('paginationParamsSchema enforces bounds', () => {
    expect(paginationParamsSchema.safeParse({ limit: 0 }).success).toBe(false);
    expect(paginationParamsSchema.safeParse({ limit: 201 }).success).toBe(false);
    expect(paginationParamsSchema.safeParse({ offset: -1 }).success).toBe(false);
  });

  it('paginated() wraps an item schema in the standard envelope', () => {
    const schema = paginated(z.object({ id: z.string() }));
    const value = { items: [{ id: 'a' }], total: 1, limit: 25, offset: 0 };
    expect(schema.parse(value)).toEqual(value);
    expect(schema.safeParse({ ...value, total: -1 }).success).toBe(false);
  });
});
