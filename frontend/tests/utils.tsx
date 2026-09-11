import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router';
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

/**
 * Renders a component that reads/writes TanStack Router search params (e.g.
 * via `useMetricFilters`) inside a minimal one-route memory router — the
 * component under test never needs the real `routeTree.gen`.
 */
export function renderRouted(
  ui: ReactElement,
  options: {
    client?: QueryClient;
    /** e.g. `'?sources=a&sources=b'` — defaults to no search params. */
    initialSearch?: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    validateSearch?: any;
  } = {},
) {
  const { client = makeTestQueryClient(), initialSearch = '', validateSearch } = options;

  const rootRoute = createRootRoute();
  const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    validateSearch,
    component: () => ui,
  });
  // A dummy target so `<Link to="/sessions/$sessionId">` resolves without
  // crashing in tests — never actually navigated to.
  const sessionDetailStubRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/sessions/$sessionId',
    component: () => null,
  });
  const router = createRouter({
    routeTree: rootRoute.addChildren([indexRoute, sessionDetailStubRoute]),
    history: createMemoryHistory({ initialEntries: [`/${initialSearch}`] }),
  });

  return {
    client,
    router,
    ...render(
      <QueryClientProvider client={client}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    ),
  };
}
