import { describe, expect, it } from 'vitest';

import { cn } from '@shared/lib/cn';

describe('cn', () => {
  it('joins truthy class names', () => {
    expect(cn('a', 'b')).toBe('a b');
  });

  it('drops falsy values', () => {
    expect(cn('a', false, null, undefined, '')).toBe('a');
  });

  it('resolves conflicting tailwind utilities (last wins)', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4');
  });

  it('supports conditional object syntax', () => {
    expect(cn({ a: true, b: false })).toBe('a');
  });
});
