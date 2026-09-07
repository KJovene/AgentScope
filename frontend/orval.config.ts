import { defineConfig } from 'orval';

/**
 * Optional: generate zod contracts + a typed client from the backend OpenAPI
 * (PLAN.md §5.3). Run `npm run api:generate` once the backend publishes the spec.
 * Until then, feature `api/*.contracts.ts` files are written by hand following the
 * same shape (zod schema -> `z.infer` type).
 */
export default defineConfig({
  agentscope: {
    // Copié depuis backend/openapi.json par `make openapi`.
    input: './openapi.json',
    output: {
      mode: 'tags-split',
      target: './src/api/generated',
      client: 'react-query',
      httpClient: 'fetch',
      clean: true,
      override: {
        query: { useQuery: true, signal: true },
      },
    },
  },
});
