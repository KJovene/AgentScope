import { describe, expect, it } from 'vitest';

import { env } from '@shared/config/env';

describe('env', () => {
  it('exposes a trimmed apiBaseUrl', () => {
    expect(typeof env.apiBaseUrl).toBe('string');
    expect(env.apiBaseUrl.endsWith('/')).toBe(false);
  });
});
