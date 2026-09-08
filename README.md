# AgentScope

**Explorer des traces d'utilisation d'agents de développement IA : importer, vérifier, normaliser, explorer.**

AgentScope réunit des traces provenant de plusieurs sources (TraceLab, SWE-chat, …) dans un
modèle relationnel commun, et les rend lisibles dans un dashboard : activité, consommation de
tokens, répartition des outils, durée des sessions, erreurs, utilisation du cache.

Un **agent IA d'aide à l'import** permet d'ajouter une nouvelle source : il profile un fichier
inconnu, propose un mapping vers le modèle de données, explique ses choix et signale les
ambiguïtés. L'IA **propose** un mapping — elle ne modifie jamais la base. Le fournisseur et le
modèle sont choisis **par configuration**.

---

## Sommaire

1. [Prise en main](#prise-en-main) — du clone à l'application qui tourne
2. [Vérifier son installation](#vérifier-son-installation)
3. [Configuration & clés IA](#configuration--clés-ia)
4. [Le parcours principal](#le-parcours-principal)
5. [Données réelles](#données-réelles)
6. [Installation sans Docker](#installation-sans-docker)
7. [Dépannage](#dépannage)
8. [Architecture & stack](#architecture)
9. [Statut du projet](#statut)

---

## Prise en main

### Prérequis

| Outil | Version | Vérifier |
| --- | --- | --- |
| Docker + Docker Compose | Docker 24+, Compose v2 | `docker compose version` |
| Git | 2.x | `git --version` |
| `make` (optionnel) | GNU Make 3.81+ | `make --version` |

`make` n'est qu'un raccourci : chaque cible est une commande `docker compose` que l'on peut taper
à la main (l'équivalent est indiqué à chaque étape). Sous Windows, `make` est fourni par
**Git Bash** ; sinon, utiliser directement les commandes `docker compose`.

Rien d'autre n'est requis : Python et Node tournent **dans les conteneurs**. Pour une installation
locale hors Docker, voir [Installation sans Docker](#installation-sans-docker).

### 1 — Cloner et configurer

```bash
git clone https://github.com/KJovene/AgentScope.git
cd AgentScope
cp .env.example .env
```

`.env` fonctionne **tel quel** : valeurs par défaut sans secret, fournisseur IA `fake`
(aucun appel réseau). Une clé n'est nécessaire que pour faire tourner l'agent de mapping sur un
modèle réel — voir [Configuration & clés IA](#configuration--clés-ia).

### 2 — Lancer la stack

```bash
make up          # équivalent : docker compose up -d --build
```

Le premier démarrage construit les images (quelques minutes). Ensuite :

| Service | URL | Contenu |
| --- | --- | --- |
| Frontend | <http://localhost:5173> | l'application (Vite, rechargement à chaud) |
| API — santé | <http://localhost:8000/health> | `{"status":"ok"}` |
| API — documentation | <http://localhost:8000/docs> | Swagger UI, tous les endpoints |
| API — endpoints | `http://localhost:8000/api/v1/…` | l'API est **préfixée `/api/v1`** |
| PostgreSQL | `localhost:5432` | user / mot de passe / base : `agentscope` (modifiables dans `.env`) |

Autres cibles utiles :

```bash
make dev         # même chose en avant-plan, logs à l'écran (Ctrl-C pour arrêter)
make logs        # suit les logs des trois services
make ps          # état des services
make down        # arrête tout (le volume de base de données est conservé)
make clean       # arrête tout ET supprime le volume + les caches
make help        # liste toutes les cibles
```

### 3 — Appliquer les migrations

```bash
make migrate     # équivalent : docker compose run --rm backend alembic upgrade head
```

Crée les tables du modèle relationnel (`sessions`, `model_calls`, `tool_calls`, `raw_records`,
`sources`, `mappings`, `import_batches`) et les vues du dashboard.
Modèle détaillé : [`docs/data/relational-model.md`](docs/data/relational-model.md).

---

## Vérifier son installation

```bash
make test        # pytest (backend) + vitest (frontend)
make ci          # la passe complète : lint + typecheck + arch + test (à lancer avant de pousser)
```

`make arch` (inclus dans `make ci`) vérifie avec `import-linter` que le sens des dépendances de la
Clean Architecture est respecté : `domain` n'importe rien, `application` ne connaît que `domain`,
etc.

Contrôle rapide sans passer par les tests :

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/v1/metrics/indicators"
```

---

## Configuration & clés IA

Toute la configuration passe par des **variables d'environnement** (`.env` pour Docker Compose,
environnement du process en local). **Aucune clé n'est commitée** ; `.env` est ignoré par git.

### Variables de la stack (`.env`)

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `agentscope` | identifiants de la base |
| `DB_PORT` | `5432` | port PostgreSQL exposé sur l'hôte |
| `BACKEND_PORT` | `8000` | port de l'API sur l'hôte |
| `FRONTEND_PORT` | `5173` | port du frontend sur l'hôte |
| `AGENTSCOPE_RAW_RECORD_RETENTION` | `full` | `full` = payload brut conservé · `minimal` = index + SHA256 |

### Variables lues par le backend (préfixe `AGENTSCOPE_`)

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `AGENTSCOPE_DATABASE_URL` | `sqlite:///./agentscope.db` | positionnée sur PostgreSQL par `docker-compose.yml` |
| `AGENTSCOPE_CORS_ORIGINS` | `http://localhost:5173` | origines autorisées (liste séparée par des virgules) |
| `AGENTSCOPE_LLM_PROVIDER` | `fake` | `fake` (aucun appel réseau) · `anthropic` · `openai` · `ollama` |
| `AGENTSCOPE_LLM_MODEL` | — | identifiant du modèle, jamais en dur dans le code |
| `AGENTSCOPE_LLM_BASE_URL` | — | endpoint des fournisseurs compatibles OpenAI (Ollama, LM Studio…) |
| `AGENTSCOPE_LLM_API_KEY` | — | **clé secrète — jamais dans le dépôt** |

### Utiliser un modèle réel

1. Renseigner dans `.env` :

   ```bash
   AGENTSCOPE_LLM_PROVIDER=anthropic
   AGENTSCOPE_LLM_MODEL=<identifiant du modèle>
   AGENTSCOPE_LLM_API_KEY=<votre clé>
   ```

   Pour un modèle **local** (aucune clé nécessaire) :

   ```bash
   AGENTSCOPE_LLM_PROVIDER=ollama
   AGENTSCOPE_LLM_BASE_URL=http://host.docker.internal:11434/v1
   AGENTSCOPE_LLM_MODEL=<modèle servi par Ollama>
   ```

2. Redémarrer le backend : `docker compose up -d backend`.
3. Le reste de l'application est inchangé : seul l'agent de mapping utilise le modèle, et il ne
   fait que **proposer** — aucune écriture en base.

Procédure complète et fournisseurs pris en charge : [`docs/ai/providers.md`](docs/ai/providers.md)
et [`docs/ai/model-switch.md`](docs/ai/model-switch.md).

> **Les tests et la CI n'appellent jamais un modèle réel** : ils utilisent `FakeLLMProvider`,
> déterministe et hors réseau. Aucune clé n'est nécessaire pour `make test`.

---

## Le parcours principal

Le parcours cible, de bout en bout : **fichier de traces → import normalisé → indicateur affiché**.

1. **Import** (onglet _Imports & Ingestion_) — déposer un ou plusieurs fichiers (`.jsonl`, `.csv`,
   `.parquet`), choisir la source, lancer l'import. Retour : bilan `importés / doublons / rejetés`,
   avec la raison de chaque rejet.
2. **Ajouter une source inconnue** (onglet _Sources & Mapping_) — déposer un fichier dont la
   structure n'est pas connue : l'application le profile (types, taux de nuls, exemples), l'agent
   IA propose un mapping et explique ses choix, on corrige, on prévisualise (dry-run), puis on
   valide. Le mapping enregistré est réutilisable **sans** l'agent.
3. **Dashboard** (onglet _Tableau de bord_) — indicateurs, séries temporelles, répartition des
   outils, distribution des durées, filtres source / agent / modèle / période.
   Une donnée indisponible s'affiche « non disponible », **jamais 0**.
4. **Détail d'une session** (onglet _Qualité & Sessions_) — timeline `model_call` / `tool_call`,
   tokens, coût, erreurs, lien de provenance vers l'enregistrement brut.

### État actuel de ce parcours

Les couches sont livrées de bas en haut ; **le raccordement final API ↔ base est en cours** :

| Étape | État |
| --- | --- |
| Modèle relationnel + migrations + dépôts | ✅ opérationnel (`make migrate`) |
| Lecteurs JSONL / CSV / Parquet, moteur de mapping, normalisation, idempotence | ✅ opérationnel (couche `application`) |
| Endpoints REST | 🟡 **exposés et documentés dans `/docs`, mais ils renvoient encore des données de démonstration** (I4.1) — le câblage sur la base arrive avec I4.2 / I4.6 |
| Écrans frontend | 🟡 navigation et écrans en place, alimentés par ces endpoints |
| Agent de mapping | 🟡 contrat `LLMProvider` et `FakeLLMProvider` livrés, use cases en cours |

Autrement dit : aujourd'hui on peut lever la stack, parcourir l'interface et l'API, et exécuter
l'import réel via la couche métier et ses tests ; l'import réel **depuis l'UI** devient disponible
quand I4.2 est fusionnée. Cette section est mise à jour à ce moment-là.

Avancement détaillé et critères de vérification : [`docs/PLAN.md`](docs/PLAN.md) §7.

---

## Données réelles

Les extraits de datasets ne sont **pas** commités (sauf autorisation explicite de
redistribution). Pour récupérer l'extrait TraceLab épinglé :

```bash
make data-tracelab    # télécharge la release épinglée, vérifie le SHA256, échantillonne 1 session sur 32
```

Le script `scripts/tracelab_extract.py` nécessite Python 3.12+ sur la machine hôte. Provenance,
version, licence et méthode de sélection : [`data/README.md`](data/README.md).

Une fixture réduite est commitée pour les tests (TraceLab est sous CC BY 4.0, redistribution
autorisée avec attribution) : `backend/tests/fixtures/tracelab/sample.jsonl` +
[`NOTICE.md`](backend/tests/fixtures/tracelab/NOTICE.md).

---

## Installation sans Docker

Nécessite **Python 3.12+** et **Node 20+**. Une base PostgreSQL joignable est optionnelle : par
défaut le backend utilise SQLite (`sqlite:///./agentscope.db`).

**Linux / macOS**

```bash
make install     # venv backend (pip install -e ".[dev]") + npm install
make dev-local   # uvicorn (port 8000) + vite (port 5173)
```

**Windows** — les cibles `install` / `dev-local` supposent une arborescence de venv POSIX
(`.venv/bin/…`) ; lancer les commandes à la main :

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -e ".[dev]"
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\uvicorn agentscope.main:app --reload
```

```powershell
cd frontend
npm install
npm run dev
```

---

## Dépannage

| Symptôme | Cause probable / solution |
| --- | --- |
| `failed to connect to the docker API` | Docker Desktop n'est pas démarré — le lancer, puis réessayer. |
| `port is already allocated` | Un service occupe déjà 5432 / 8000 / 5173 → changer `DB_PORT`, `BACKEND_PORT` ou `FRONTEND_PORT` dans `.env`, puis `make up`. |
| Le frontend affiche une erreur d'API | Vérifier que le backend répond : `curl http://localhost:8000/health`, puis `make logs`. |
| `make` introuvable sous Windows | Utiliser **Git Bash**, ou taper les commandes `docker compose` équivalentes indiquées ci-dessus. |
| Base incohérente après un changement de schéma | `make clean` (⚠️ supprime le volume) puis `make up && make migrate`. |
| Modifications backend non prises en compte | Le code est monté en volume avec `--reload` ; si une **dépendance** change, reconstruire : `make build`. |

---

## Architecture

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

Cette règle est **vérifiée automatiquement** par `make arch`.

Composants, points d'extension et parcours d'import détaillés :
[`docs/architecture/components.md`](docs/architecture/components.md) ·
Décisions : [ADR](docs/architecture/adr/) · Modèle de données : [`docs/data/`](docs/data/) ·
IA interchangeable : [`docs/ai/`](docs/ai/).

### Stack

- **Backend** : Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, pandas / pyarrow / DuckDB pour le
  profilage et les formats tabulaires. SQLite par défaut, PostgreSQL via configuration.
- **Frontend** : React 18, Vite, TypeScript, TanStack Router + Query, Recharts.
- **IA** : interface `LLMProvider` + adaptateurs (Anthropic, OpenAI-compatible dont Ollama, Fake
  pour les tests). Fournisseur / modèle / endpoint / clé **par variables d'environnement**.

---

## Statut

| Livrable | État |
| --- | --- |
| Structure du dépôt & Clean Architecture (`import-linter` vert) | ✅ |
| Docker Compose + Makefile + `.env.example` | ✅ |
| Modèle relationnel, migrations Alembic, dépôts | ✅ |
| Moteur de mapping, normalisation, import idempotent (couche métier) | ✅ |
| Contrat `LLMProvider` + `FakeLLMProvider` (tests hors réseau) | ✅ |
| API REST — endpoints exposés | 🟡 stubs (fixtures) ; câblage base en cours |
| Frontend — layout, navigation, écrans | 🟡 amorcés |
| CI (tests à chaque PR) | ⬜ à faire |
| `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` / templates issue & PR | ✅ |
| Release `v0.1.0` | ⬜ à venir |

Backlog complet et critères de vérification : [`docs/PLAN.md`](docs/PLAN.md).

---

## Contribuer

Le guide complet est dans [`CONTRIBUTING.md`](CONTRIBUTING.md) : branches, commits, pull requests,
revue, Definition of Done. En résumé — les PR ciblent **`dev`** (`main` est la branche de
publication), une issue = une PR (`Closes #N`), une approbation minimum, et les PR touchant un
contrat d'interface (label `contract`) sont relues par les workstreams impactés. Le suivi se fait
sur le GitHub Projects du groupe.

La participation est soumise au [Code de conduite](CODE_OF_CONDUCT.md).

## Licence

Le code d'AgentScope — backend, frontend, scripts, documentation — est distribué sous licence
**MIT**, et sous elle seule : voir [`LICENSE`](LICENSE). En contribuant, vous acceptez que votre
contribution soit publiée sous cette licence.

**Les données ont leur propre licence**, distincte de celle du code. Les extraits de datasets ne
sont **pas** commités sauf autorisation explicite de redistribution ; leur provenance, version,
licence et méthode de récupération sont documentées dans [`data/README.md`](data/README.md). Seule
exception commitée : la fixture de test TraceLab, sous **CC BY 4.0** (redistribution autorisée avec
attribution) — voir [`backend/tests/fixtures/tracelab/NOTICE.md`](backend/tests/fixtures/tracelab/NOTICE.md).
