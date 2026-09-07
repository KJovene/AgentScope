import { z } from 'zod';

/**
 * Single, validated entry point for build-time configuration.
 * Import `env` everywhere instead of touching `import.meta.env` directly (DRY + fail fast).
 */
const schema = z.object({
  VITE_API_BASE_URL: z.string().min(1).default('/api'),
});

const parsed = schema.safeParse(import.meta.env);

if (!parsed.success) {
  // Surface misconfiguration immediately rather than failing deep in a fetch.
  console.error('Invalid environment configuration', parsed.error.flatten().fieldErrors);
  throw new Error('Invalid environment configuration — see console.');
}

export const env = {
  apiBaseUrl: parsed.data.VITE_API_BASE_URL.replace(/\/$/, ''),
} as const;
