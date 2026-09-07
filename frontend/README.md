# frontend

Interface web d'AgentScope. **React 19 · Vite 6 · TypeScript · TanStack Router · TanStack
Query · Zustand · Zod · TailwindCSS**.

```bash
npm install
cp .env.example .env.local
npm run dev        # http://localhost:5173, /api proxifié vers le backend (port 8000)
npm run typecheck && npm run lint && npm test
npm run api:generate   # (optionnel) régénère le client depuis backend/openapi.json
```

## Principes

- **Feature-sliced + Clean Architecture.** `app/` compose, `features/*` portent le métier UI,
  `shared/*` est la base commune. Les dépendances vont dans un seul sens :
  `shared ← features ← app`. Un feature n'importe jamais l'intérieur d'un autre feature.
  Vérifié par ESLint (`eslint.config.js`, plugin `boundaries` + `no-restricted-imports`).
- **Zod = source de vérité unique.** Chaque `feature/api/*.contracts.ts` définit des schémas
  zod ; les types sont `z.infer<...>`, jamais réécrits à la main. Le client HTTP valide
  **chaque** réponse à l'exécution.
- **DRY par construction.** Un seul client HTTP, un seul type d'erreur (`ApiError` ↔
  `application/problem+json`), un registre central de query keys, un module de formatage, un
  helper `cn()` pour les classes Tailwind, des tokens de couleur sémantiques (aucun hex dans les
  composants).
- **Un état = un seul endroit.**
  | Type d'état | Où | Outil |
  | --- | --- | --- |
  | Données serveur | `feature/api/*.queries.ts` | TanStack Query |
  | Filtres partageables par URL (dashboard, drill-down) | search params de la route | `use-metric-filters` + `validateSearch` |
  | État client global (thème, layout) | `shared/stores/ui-store.ts` | Zustand |
  | État UI éphémère (dialogue, brouillon) | composant / `useDisclosure` | React |

## Arborescence

```
src/
  main.tsx                      # point d'entrée : <StrictMode><AppProviders/>
  app/
    providers.tsx               # QueryClientProvider + RouterProvider (+ devtools en dev)
    router.tsx                  # createRouter + queryClient dans le contexte
    query-client.ts             # defaults TanStack Query (retry, staleTime) — DRY
    routes/                     # routes fichier (plugin TanStack Router)
      __root.tsx                # layout, navigation, thème
      index.tsx                 # "/" -> DashboardPage, validateSearch = metricFiltersSchema
      imports.index.tsx · imports.$importId.tsx
      sources.new.tsx · sessions.$sessionId.tsx
  shared/
    api/    http-client.ts · api-error.ts · query-keys.ts
    config/ env.ts              # import.meta.env validé par zod
    lib/    cn.ts · format.ts · metric-filters.ts
    ui/     Button · Card · Spinner · EmptyState · ErrorState · index.ts · charts/
    components/  MetricCard · PageHeader · filters/
    hooks/  use-debounce · use-disclosure · use-metric-filters
    stores/ ui-store.ts
    types/  pagination.ts · problem-details.ts
  features/
    <feature>/
      api/    <f>.contracts.ts (zod) · <f>.api.ts (transport) · <f>.queries.ts (hooks)
      model/  <f>.mappers.ts (DTO -> view model + formatage) · [<f>.store.ts]
      ui/     composants présentiels + pages
      hooks/  hooks composites (orchestration api + model)
      index.ts   # API publique du feature — les routes n'importent QUE ça
    import/            # implémentation de référence (à copier)
    mapping-agent/ dashboard/ session-detail/ data-quality/
  styles/index.css              # directives Tailwind + tokens de thème (light/dark)
  test/ setup.ts · msw/         # MSW : l'API est mockée au niveau réseau
```

Contrat détaillé des features : [`src/features/README.md`](src/features/README.md).

## Alias d'import

`@/*` → `src/*` · `@app/*` · `@shared/*` · `@features/*`. Les imports relatifs profonds
(`../../..`) sont interdits par le lint.

## État d'avancement

Squelette + couche `shared` + feature `import` de référence en place. À construire (voir
`../PLAN.md` EPIC 5) : upload & assistant d'import (I5.2, I5.5–I5.8), dashboard indicateurs +
visualisations + filtres + drill-down (I5.9–I5.14), vue session (I5.15), panneau qualité (I5.16).
