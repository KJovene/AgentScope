# Passe sécurité I7.7

Date : 2026-09-08

## Résultat

- `gitleaks detect` : vert avec `.gitleaks.toml`.
- Les deux détections historiques étaient des valeurs fictives dans des fixtures de tests ; les fixtures ont été remplacées et les deux commits historiques sont explicitement allowlistés.
- Le bundle frontend produit par `vite build` ne contient aucune clé ou valeur de secret connue (`sk-test`, `api_key=`, `LLM_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`).
- Les variables sensibles backend sont lues depuis l’environnement via `Settings`; aucun secret réel n’est fourni par les fichiers `.env.example`.
- `DefaultSensitiveFilter` est actif dans `DefaultFieldProfiler` et `PromptBuilder`.
- Tests ciblés : `9 passed` pour le profilage et la construction de prompts.

## Limite connue

`npm run build` reste bloqué par des erreurs frontend préexistantes de typecheck et de fichiers générés/imports manquants. Le bundle a néanmoins été produit et vérifié par `vite build` directement.
