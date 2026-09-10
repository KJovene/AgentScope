import '@testing-library/jest-dom/vitest';

import { configure } from '@testing-library/react';
import { afterAll, afterEach, beforeAll } from 'vitest';

import { server } from './msw/server';

// jsdom's storage is flaky across versions — provide a dependable in-memory one.
class MemoryStorage implements Storage {
  private map = new Map<string, string>();
  get length() {
    return this.map.size;
  }
  clear() {
    this.map.clear();
  }
  getItem(key: string) {
    return this.map.has(key) ? (this.map.get(key) as string) : null;
  }
  key(index: number) {
    return Array.from(this.map.keys())[index] ?? null;
  }
  removeItem(key: string) {
    this.map.delete(key);
  }
  setItem(key: string, value: string) {
    this.map.set(key, String(value));
  }
}

for (const name of ['localStorage', 'sessionStorage'] as const) {
  Object.defineProperty(globalThis, name, {
    value: new MemoryStorage(),
    configurable: true,
    writable: true,
  });
}

// jsdom has no ResizeObserver; Recharts' <ResponsiveContainer> needs one to measure its box.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
Object.defineProperty(globalThis, 'ResizeObserver', {
  value: ResizeObserverStub,
  configurable: true,
  writable: true,
});

// jsdom doesn't implement scrollTo; TanStack Router's scroll restoration calls it on navigation.
window.scrollTo = () => {};

/**
 * jsdom installs its own `AbortController`/`AbortSignal`, but `fetch` here is
 * Node's (undici), which rejects any signal that is not an instance of ITS
 * `AbortSignal` — "Expected signal to be an instance of AbortSignal". Every
 * TanStack Query fetch passes `signal`, so without this every request in a
 * component test fails as a network error.
 *
 * Forward the abort ourselves instead of handing the foreign signal to fetch:
 * the caller still sees an aborted promise, only the socket is not torn down.
 */
function patchFetchSignal() {
  const inner = globalThis.fetch;
  globalThis.fetch = ((input: RequestInfo | URL, init: RequestInit = {}) => {
    const { signal, ...rest } = init;
    if (!signal) return inner(input, init);
    if (signal.aborted) return Promise.reject(new DOMException('Aborted', 'AbortError'));

    return new Promise<Response>((resolve, reject) => {
      signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), {
        once: true,
      });
      inner(input, rest).then(resolve, reject);
    });
  }) as typeof fetch;
}

// The machine running CI-less coverage can be slow; give async utils room.
configure({ asyncUtilTimeout: 3000 });

// Mock the API at the network boundary so tests never hit a real backend.
// The signal patch is installed AFTER msw's interceptor so it sees the request
// first and can strip the foreign signal before msw builds a Request from it.
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
  patchFetchSignal();
});
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
