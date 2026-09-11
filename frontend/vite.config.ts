import { fileURLToPath, URL } from 'node:url';

import react from '@vitejs/plugin-react';
import { TanStackRouterVite } from '@tanstack/router-plugin/vite';
import { defineConfig } from 'vitest/config';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    // Generates src/app/routeTree.gen.ts from src/app/routes/**
    TanStackRouterVite({ routesDirectory: './src/app/routes', generatedRouteTree: './src/app/routeTree.gen.ts' }),
    react(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@shared': fileURLToPath(new URL('./src/shared', import.meta.url)),
      '@features': fileURLToPath(new URL('./src/features', import.meta.url)),
      '@app': fileURLToPath(new URL('./src/app', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Backend API — same-origin in dev, no CORS config needed.
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    // Every test lives under tests/ (not colocated with source).
    include: ['tests/**/*.test.{ts,tsx}'],
    setupFiles: ['./tests/setup.ts'],
    css: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'html'],
      // Unit-test surface only. Bootstrap, generated code, router file-route
      // wrappers and pure type modules carry no logic worth asserting.
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/**/*.d.ts',
        'src/**/*.gen.ts',
        'src/api/generated/**',
        'src/app/routes/**',
        'src/app/router.tsx',
        'src/app/providers.tsx',
        'src/**/index.ts',
      ],
      thresholds: {
        lines: 80,
        statements: 80,
        functions: 80,
        branches: 80,
      },
    },
  },
});
