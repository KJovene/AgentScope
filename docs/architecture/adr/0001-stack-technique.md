# ADR-0001 — Stack technique : Python/FastAPI + React/Vite

- **Statut :** acceptée
- **Date :** 2026-09-07
- **Décideurs :** WS-platform, validée par les 5 workstreams au cadrage du Jour 1

## Contexte

AgentScope doit, en quatre jours et à 6+ personnes, ingérer des traces d'agents IA au format
**JSONL, CSV et Parquet**, les profiler, les normaliser vers un modèle relationnel, puis les
restituer dans un dashboard. Deux contraintes pèsent sur le choix de la stack :

- Le parcours principal (`importer → vérifier → normaliser → explorer`) doit être fiable dès le
  Jour 1 : pas de temps disponible pour écrire des briques que l'écosystème fournit déjà.
- L'évaluation porte sur l'architecture et la maintenabilité (7 points), donc sur la capacité à
  séparer réellement les couches et à rendre le fournisseur IA interchangeable.

## Décision

**Backend :** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 / pydantic-settings.
Traitement des données : `pandas`, `pyarrow`, `duckdb` (lecture Parquet, profilage de champs).

**Frontend :** React 18, Vite, TypeScript, TanStack Query, Recharts. Le client HTTP TypeScript est
**généré depuis l'OpenAPI** du backend (`orval`) : il n'est pas écrit à la main.

**Qualité :** `ruff` (lint + import order), `mypy --strict`, `pytest` + couverture,
`import-linter` pour la règle des dépendances — le tout branché dans la CI (I0.3, I0.11).

Le frontend **ne parse aucun fichier de traces** : il téléverse, le backend lit.

## Alternatives écartées

| Alternative | Raison du rejet |
| --- | --- |
| Node/TypeScript de bout en bout | Écosystème Parquet/colonnaire nettement plus faible en JS ; rien d'équivalent à `pyarrow` + `duckdb` pour le profilage de champs. |
| Django (+ DRF) | ORM et admin structurants mais orientés « framework au centre » ; on veut le framework en périphérie (ADR-0002). OpenAPI moins direct qu'avec FastAPI. |
| Java / Spring Boot | Mise en route et verbosité incompatibles avec un sprint de quatre jours. |

## Conséquences

- **Positives** — Le profilage et la lecture multi-format s'appuient sur des bibliothèques mûres.
  FastAPI publie l'OpenAPI nativement, ce qui permet de livrer des endpoints *stub* le Jour 1 et de
  débloquer le frontend (§5.3). Pydantic v2 sert de frontière de validation aux entrées HTTP, sans
  contaminer le domaine (voir ADR-0002).
- **Négatives assumées** — Deux langages, donc deux chaînes d'outillage et deux jobs de CI. Le
  contrat OpenAPI devient une frontière à maintenir : toute modification de route se répercute sur
  le client généré, et passe donc par une PR étiquetée `contract`.

## Vérification

`make dev` lève l'application complète (backend + frontend + base) en une commande ;
`make test` exécute lint, types et tests des deux côtés.

## Références

`docs/PLAN.md` §2, §3, §5.3 · `backend/pyproject.toml` · `frontend/package.json`
