# features/

One folder per user-facing capability. **Features never import each other's
internals** — only `@shared/*` and, rarely, another feature's public `index.ts`.
ESLint enforces this (`eslint.config.js` → `boundaries`).

## The 4-layer contract (same in every feature)

| Folder | Contains | May import |
| --- | --- | --- |
| `api/` | `*.contracts.ts` (zod schemas = source of truth, types are `z.infer`), `*.api.ts` (transport, uses `@shared/api/http-client`), `*.queries.ts` (TanStack Query hooks) | `@shared/*` |
| `model/` | `*.mappers.ts` (DTO → view model + formatting via `@shared/lib/format`), `*.selectors.ts`, optional `*.store.ts` (Zustand slice for **feature-local UI state only**) | `api/`, `@shared/*` |
| `ui/` | Presentational components + page components. Receive already-shaped/formatted data. | `model/`, `@shared/ui`, `@shared/components` |
| `hooks/` | Composite hooks orchestrating `api` + `model` for a page | `api/`, `model/` |
| `index.ts` | The feature's **public API**. Routes import from here. | — |

## State ownership (no duplication)

- **Server data** → TanStack Query (`api/*.queries.ts`). Never copied into Zustand.
- **URL-shareable UI state** (dashboard filters, drill-down) → URL search params via
  `@shared/hooks/use-metric-filters` + a route's `validateSearch`.
- **Global client state** (theme, layout) → `@shared/stores/ui-store`.
- **Ephemeral local UI state** (open dialog, form draft) → component state / `useDisclosure`,
  or a small feature `model/*.store.ts` if shared across the feature's components.

## Adding a feature

Copy `import/` (the reference implementation) and rename. Register its pages in
`src/app/routes/`.
