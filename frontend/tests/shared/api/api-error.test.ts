import { describe, expect, it } from 'vitest';

import { ApiError } from '@shared/api/api-error';

describe('ApiError', () => {
  it('carries status / kind / problem', () => {
    const err = new ApiError({
      message: 'boom',
      status: 500,
      kind: 'http',
      problem: { type: 'about:blank', title: 'Boom', status: 500 },
    });
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe('ApiError');
    expect(err.status).toBe(500);
    expect(err.kind).toBe('http');
    expect(err.problem?.title).toBe('Boom');
  });

  it('fieldErrors flattens problem.errors, ignoring entries without a field', () => {
    const err = new ApiError({
      message: 'invalid',
      status: 422,
      kind: 'http',
      problem: {
        type: 'about:blank',
        title: 'Invalid',
        status: 422,
        errors: [
          { field: 'name', message: 'required' },
          { message: 'no field here' },
        ],
      },
    });
    expect(err.fieldErrors).toEqual({ name: 'required' });
  });

  it('fieldErrors is empty when there is no problem', () => {
    expect(new ApiError({ message: 'x', status: 0, kind: 'network' }).fieldErrors).toEqual({});
  });

  it('fromResponse parses a problem+json body', async () => {
    const response = new Response(
      JSON.stringify({ title: 'Not found', status: 404, detail: 'nope' }),
      { status: 404, statusText: 'Not Found' },
    );
    const err = await ApiError.fromResponse(response);
    expect(err.status).toBe(404);
    expect(err.kind).toBe('http');
    expect(err.message).toBe('Not found');
    expect(err.problem?.detail).toBe('nope');
  });

  it('fromResponse falls back to status text on a non-JSON body', async () => {
    const response = new Response('<html>500</html>', { status: 503, statusText: 'Unavailable' });
    const err = await ApiError.fromResponse(response);
    expect(err.problem).toBeUndefined();
    expect(err.message).toBe('503 Unavailable');
  });
});
