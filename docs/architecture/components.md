# Architecture — composants et dépendances

> Stub — à compléter dans l'issue **I6.4** (WS-platform). S'appuyer sur `PLAN.md` §3.

À produire ici :

- Schéma des composants (mermaid) : `domain`, `application` (use cases + ports),
  `infrastructure` (persistence, readers, llm, profiling, config), `interfaces` (API).
- Sens des dépendances et règle vérifiée par `import-linter` (I0.11).
- Points d'extension : ajouter un lecteur de format, ajouter un adaptateur LLM, ajouter un
  indicateur.
- Liste des décisions : voir [`adr/`](adr/).
