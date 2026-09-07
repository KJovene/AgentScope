# AgentScope

**Explorer des traces d'utilisation d'agents de développement IA : importer, vérifier, normaliser, explorer.**

AgentScope réunit des traces provenant de plusieurs sources (TraceLab, SWE-chat, …) dans un
modèle relationnel commun, et les rend lisibles dans un dashboard : activité, consommation de
tokens, répartition des outils, durée des sessions, erreurs, utilisation du cache.

Un **agent IA d'aide à l'import** permet d'ajouter une nouvelle source : il profile un fichier
inconnu, propose un mapping vers le modèle de données, explique ses choix et signale les
ambiguïtés. L'IA **propose** un mapping — elle ne modifie jamais la base. Le fournisseur et le
modèle sont choisis **par configuration**.

> ⚠️ Projet en cours d'initialisation (Jour 1). Cette page sera complétée par un vrai guide de
> prise en main (issue **I6.1**). En attendant :
> - Énoncé du sujet : [`docs/BRIEF.md`](docs/BRIEF.md)
> - Plan de réalisation, backlog et contrats d'interface : [`PLAN.md`](PLAN.md)

## Statut

| Livrable | État |
| --- | --- |
| Structure du dépôt & Clean Architecture | ✅ (I0.1) |
| Docker Compose + Makefile | ✅ (I0.7) |
| Squelettes backend / frontend | 🟡 amorcés (I0.5 : `/health` seul · I0.6 : couche `shared` + feature de référence) |
| GitHub Projects | ⬜ à faire (I0.2) |
| CI (tests à chaque PR) | ⬜ à faire (I0.3) |
| Parcours principal (fichier → indicateur) | ⬜ à faire (fin Jour 1) |
| Release `v0.1.0` | ⬜ vendredi soir |

## Architecture (cible)

Monolithe modulaire, Clean Architecture. Le cœur métier ne dépend ni du framework web, ni de la
base, ni d'un fournisseur d'IA.

```
interfaces/ (API REST)      infrastructure/ (DB, lecteurs de fichiers, LLM, profilage, config)
              \                          /
               v                        v
                   application/  (cas d'utilisation + PORTS)
                              |
                              v
                         domain/  (entités, règles pures — n'importe RIEN)
```

| Dossier | Rôle | Dépend de |
| --- | --- | --- |
| `backend/agentscope/domain` | entités et règles métier pures | rien |
| `backend/agentscope/application` | cas d'utilisation + ports (interfaces) | `domain` |
| `backend/agentscope/infrastructure` | implémentations : SQLAlchemy, lecteurs, adaptateurs LLM | `application`, `domain` |
| `backend/agentscope/interfaces` | API FastAPI, DTO, injection de dépendances | `application`, `domain` |
| `frontend/src` | UI React (import, agent de mapping, dashboard, vue session) | API REST |

Détails et décisions : [`docs/architecture/`](docs/architecture/) · Modèle de données :
[`docs/data/`](docs/data/) · IA interchangeable : [`docs/ai/`](docs/ai/).

## Stack

- **Backend** : Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, pandas / pyarrow / DuckDB pour le
  profilage et les formats tabulaires. SQLite par défaut, PostgreSQL via configuration.
- **Frontend** : React 18, Vite, TypeScript, TanStack Query, Recharts.
- **IA** : interface `LLMProvider` + adaptateurs (Anthropic, OpenAI-compatible dont Ollama, Fake
  pour les tests). Fournisseur / modèle / endpoint / clé **par variables d'environnement**.

## Démarrage

Prérequis : Docker + Docker Compose. `make help` liste toutes les cibles.

```bash
cp .env.example .env        # aucun secret n'est commité ; renseigner les clés IA si besoin
make dev                    # db (Postgres) + API (http://localhost:8000/health) + frontend (http://localhost:5173)
make test                   # tests backend (pytest) + frontend (vitest)
make migrate                # applique les migrations Alembic (opérationnel à partir de I1.3)
```

Sans Docker : `make install` puis `make dev-local` (nécessite Python 3.12 et Node 20).

> État actuel : la stack démarre de bout en bout, mais l'API n'expose encore que `/health`
> et le frontend affiche le squelette. Le parcours d'import arrive au fil des EPICs 2–5.

## Contribuer

Voir `CONTRIBUTING.md` (issue I0.2). En résumé : une issue = une PR (`Closes #N`), CI verte
obligatoire, relecture par un autre membre, les PR touchant un contrat d'interface (label
`contract`) sont relues par les workstreams impactés. Le suivi se fait sur le GitHub Projects du
groupe.

## Données & licence

Les extraits de datasets ne sont **pas** commités sauf autorisation de redistribution ; leur
provenance, version et méthode de récupération sont documentées dans [`data/README.md`](data/README.md).

Distribué sous licence **MIT** — voir [`LICENSE`](LICENSE).
