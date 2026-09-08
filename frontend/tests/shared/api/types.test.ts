import { describe, expect, it } from 'vitest';

import { ApiError } from '@shared/api/types';

describe('shared/api/types ApiError', () => {
  it('uses detail as the message when present', () => {
    const err = new ApiError({ title: 'Titre', status: 400, detail: 'le détail' });
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe('ApiError');
    expect(err.message).toBe('le détail');
    expect(err.problem.status).toBe(400);
  });

  it('falls back to title when there is no detail', () => {
    const err = new ApiError({ title: 'Titre seul', status: 500 });
    expect(err.message).toBe('Titre seul');
  });
});
