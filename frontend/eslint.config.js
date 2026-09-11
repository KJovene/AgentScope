import js from '@eslint/js';
import boundaries from 'eslint-plugin-boundaries';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'src/app/routeTree.gen.ts', 'src/api/generated/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      boundaries,
    },
    settings: {
      'boundaries/elements': [
        { type: 'app', pattern: 'src/app/**' },
        { type: 'feature', pattern: 'src/features/*/**', capture: ['feature'] },
        { type: 'shared', pattern: 'src/shared/**' },
      ],
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

      // --- Architecture boundaries (Clean Architecture, enforced) ---
      // shared/ is the DRY base: it must not depend on features or app.
      // A feature may only reach another feature through its public index (never deep imports),
      // but prefer lifting shared code into shared/ instead.
      'boundaries/element-types': [
        'error',
        {
          default: 'disallow',
          rules: [
            { from: 'app', allow: ['app', 'feature', 'shared'] },
            { from: 'feature', allow: ['shared', ['feature', { feature: '${feature}' }]] },
            { from: 'shared', allow: ['shared'] },
          ],
        },
      ],
      'boundaries/no-private': ['error', { allowUncles: false }],

      // Forbid deep imports across feature public API.
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@features/*/*'],
              message: 'Import a feature only through its public index: "@features/<name>".',
            },
            {
              group: ['../../*'],
              message: 'Use path aliases (@shared, @features, @app) instead of deep relative paths.',
            },
          ],
        },
      ],
    },
  },
  {
    // Node-executed codegen script (not part of the browser bundle).
    files: ['scripts/**/*.mjs'],
    languageOptions: {
      globals: { process: 'readonly' },
    },
  },
  {
    // Tests deliberately reach into internal modules and shared test helpers.
    files: ['tests/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': 'off',
      'boundaries/element-types': 'off',
      'boundaries/no-private': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', ignoreRestSiblings: true },
      ],
    },
  },
);
