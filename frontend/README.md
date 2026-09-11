# frontend

Interface web d'AgentScope. **React 19 · Vite 6 · TypeScript · TanStack Router · TanStack
Query · Zustand · Zod · Recharts · TailwindCSS**.

```bash
npm install
cp .env.example .env.development.local     # git-ignored, lu par `vite dev` (pas par vitest)
npm run dev        # http://localhost:5173, /api proxifié vers le backend (port 8000)
npm run typecheck && npm run lint && npm test
npm run api:generate   # (optionnel) régénère le client depuis backend/openapi.json
```

En Docker, `docker-compose.yml` injecte directement `VITE_API_BASE_URL` et
`VITE_API_PROXY_TARGET` : le `.env.development.local` ne sert qu'en exécution locale.

En pratique on lance plutôt toute la stack depuis la racine — `make up` — pour avoir une API et
des données en face : voir le [README principal](../README.md).

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
- **« Non disponible » ≠ 0.** Une métrique absente ne devient jamais un zéro à l'écran :
  `EmptyState` / libellé explicite. C'est la règle portée de bout en bout par le backend
  ([`../docs/data/indicators.md`](../docs/data/indicators.md)).
- **Un état = un seul endroit.**
  | Type d'état | Où | Outil |
  | --- | --- | --- |
  | Données serveur | `feature/api/*.queries.ts` | TanStack Query |
  | Filtres partageables par URL (dashboard, drill-down) | search params de la route | `use-metric-filters` + `validateSearch` |
  | État client global (thème, layout, accessibilité) | `shared/stores/ui-store.ts` | Zustand |
  | État UI éphémère (dialogue, brouillon) | composant / `useDisclosure` | React |

## Arborescence

```
src/
  main.tsx                      # point d'entrée : <StrictMode><AppProviders/>
  app/
    providers.tsx               # QueryClientProvider + RouterProvider (+ devtools en dev)
    router.tsx                  # createRouter + queryClient dans le contexte
    query-client.ts             # defaults TanStack Query (retry, staleTime) — DRY
    Layout.tsx                  # chrome commun
    routes/                     # routes fichier (plugin TanStack Router)
      __root.tsx                # layout, navigation, thème, assistant flottant, accessibilité
      index.tsx                 # "/"          → DashboardScreen, validateSearch = metricFiltersSchema
      imports.index.tsx         # "/imports"   → ImportScreen / ImportHistoryScreen
      imports.$importId.tsx     # "/imports/:id" → ImportReportPage (bilan + rejets)
      sessions.index.tsx        # "/sessions"  → SessionListPage
      sessions.$sessionId.tsx   # "/sessions/:id" → SessionDetailPage (timeline)
      sources.new.tsx           # "/sources/new" → AddSourcePage (agent de mapping)
      chat.tsx                  # "/chat"      → AgentChat en pleine page
  shared/
    api/    http-client.ts · client.ts · api-error.ts · query-keys.ts · types.ts
            sources.* · sessions.* · dimensions.*   (référentiels partagés par plusieurs features)
    config/ env.ts              # import.meta.env validé par zod
    lib/    cn.ts · format.ts · metric-filters.ts
    ui/     Button · Card · Spinner · Skeleton · EmptyState · ErrorState · CyberDecor · charts/
    components/  MetricCard · PageHeader · ApiErrorBanner · filters/
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
    dashboard/         # indicateurs, séries, répartition des outils, top sessions
    import/            # upload, historique, bilan et rejets — implémentation de référence
    mapping-agent/     # profil de fichier inconnu, chat avec l'agent, éditeur et dry-run de mapping
    session-detail/    # liste des sessions + timeline d'une session
    data-quality/      # complétude, rejets et champs manquants par lot d'import
    accessibility/     # panneau contraste / taille de texte / animations
  styles/index.css              # directives Tailwind + tokens de thème (light/dark)
tests/                          # vitest + Testing Library ; MSW mocke l'API au niveau réseau
  app/ features/ shared/ msw/ e2e/ (Playwright)
```

Contrat détaillé des features : [`src/features/README.md`](src/features/README.md).

## Alias d'import

`@/*` → `src/*` · `@app/*` · `@shared/*` · `@features/*`. Les imports relatifs profonds
(`../../..`) sont interdits par le lint.

## État d'avancement

Tous les écrans du parcours sont en place et alimentés par l'API réelle : dashboard (indicateurs,
série temporelle, répartition des outils, distribution des durées, filtres URL, drill-down),
imports (upload, historique, bilan, rejets), sessions (liste + timeline), agent de mapping
(profil, chat, éditeur, prévisualisation), panneau qualité, assistant flottant, accessibilité.

**Dette connue à résorber** (voir le [README principal](../README.md#statut)) :

- `npm run typecheck` échoue. `src/features/chat/` est du **code mort** — un doublon de l'ancien
  écran de chat, remplacé par `features/mapping-agent/ui/AgentChat.tsx` ; il importe des modules
  qui n'existent pas et n'est référencé par aucune route. À supprimer.
- 35 tests sur 228 sont rouges, dont plusieurs qui visent des composants renommés
  (`@features/dashboard/ui/DataQualityPanel` vit désormais dans `features/data-quality`,
  `ImportHistoryPage` → `ImportHistoryScreen`).
- `shared/api/` héberge des modules de données (`sources`, `sessions`, `dimensions`) partagés par
  plusieurs features. C'est volontaire — mais ils doivent rester des **référentiels**, pas de la
  logique de feature.
