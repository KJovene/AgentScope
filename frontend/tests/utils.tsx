import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, type RenderOptions } from '@testing-library/react';
import { type ReactElement, type ReactNode } from 'react';

/** A QueryClient with retries off so failing tests fail fast. */
export function makeTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      // Keep the default gcTime — a 0 here aborts in-flight fetches as soon as
      // a query goes inactive.
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

export function renderWithClient(
  ui: ReactElement,
  options: RenderOptions & { client?: QueryClient } = {},
) {
  const { client = makeTestQueryClient(), ...rest } = options;
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, ...render(ui, { wrapper: Wrapper, ...rest }) };
}

export function queryWrapper(client = makeTestQueryClient()) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}
