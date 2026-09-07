import { createRouter } from '@tanstack/react-router';

import { routeTree } from './routeTree.gen';
import { createQueryClient } from './query-client';

export const queryClient = createQueryClient();

export const router = createRouter({
  routeTree,
  // Available in every loader / component via `useRouteContext()` (see __root.tsx).
  context: { queryClient },
  defaultPreload: 'intent',
  scrollRestoration: true,
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
