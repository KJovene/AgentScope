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

1. [Installation — du `git clone` aux données en base](#installation)
2. [Vérifier son installation](#vérifier-son-installation)
3. [Charger plus de données](#charger-plus-de-données)
4. [Configuration & clés IA](#configuration--clés-ia)
5. [Le parcours principal](#le-parcours-principal)
6. [L'API REST](#lapi-rest)
7. [Installation sans Docker](#installation-sans-docker)
8. [Dépannage](#dépannage)
9. [Architecture & stack](#architecture)
10. [Statut du projet](#statut)

---

## Installation

Quatre commandes, dans l'ordre. À la fin, l'application tourne **avec des données réelles en
base** : des sessions d'agents de code, leurs appels modèle et leurs appels d'outils.

```bash
git clone https://github.com/KJovene/AgentScope.git
cd AgentScope
cp .env.example .env          # 1 — configuration (aucun secret, fonctionne tel quel)
make up                       # 2 — construit et lève db + backend + frontend
make migrate                  # 3 — crée les tables et les vues du dashboard
make seed                     # 4 — charge la grille tarifaire + un jeu de traces réelles
```

Puis ouvrir **<http://localhost:5173>**.

Le détail de chaque étape est ci-dessous, avec l'équivalent `docker compose` quand `make` n'est
pas disponible.

### Prérequis

| Outil | Version | Vérifier | Nécessaire pour |
| --- | --- | --- | --- |
| Docker + Docker Compose | Docker 24+, Compose v2 | `docker compose version` | toute l'application |
| Git | 2.x | `git --version` | cloner le dépôt |
| Python | 3.12+ | `python --version` | l'étape 4 (`make seed`) et les scripts de `scripts/` |
| `make` *(optionnel)* | GNU Make 3.81+ | `make --version` | raccourcis ; sinon, commandes `docker compose` |

Python et Node tournent **dans les conteneurs** : rien à installer pour l'application elle-même.
Le Python de l'hôte ne sert qu'aux scripts de `scripts/`, qui n'utilisent que la bibliothèque
standard (aucun `pip install`) — ils parlent à l'API par HTTP.

Sous Windows, `make` est fourni par **Git Bash**. Les cibles `make` choisissent `python3` ou
`python` selon ce qui répond ; pour forcer un interpréteur : `make seed PYTHON=py`.

### 1 — Cloner et configurer

```bash
git clone https://github.com/KJovene/AgentScope.git
cd AgentScope
cp .env.example .env
```

`.env` fonctionne **tel quel** : valeurs par défaut sans secret, fournisseur IA `fake` (aucun
appel réseau). Une clé n'est nécessaire que pour faire tourner l'agent de mapping sur un modèle
réel — voir [Configuration & clés IA](#configuration--clés-ia).

> Ne pas sauter cette étape : `docker-compose.yml` monte `./.env` dans le conteneur backend. Sans
> le fichier, Docker crée un **dossier** à sa place et la configuration IA n'est jamais lue.

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

### 3 — Créer le schéma

```bash
make migrate     # équivalent : docker compose run --rm backend alembic upgrade head
```

Crée les tables du modèle relationnel (`source`, `repository`, `mapping`, `import_batch`,
`raw_record`, `session`, `model_call`, `tool_call`, `import_reject`, `field_profile`,
`model_pricing`) et les quatre vues du dashboard (`v_session_metrics`, `v_daily_activity`,
`v_tool_usage`, `v_data_quality`).
Modèle détaillé : [`docs/data/relational-model.md`](docs/data/relational-model.md).

### 4 — Charger les données

```bash
make seed        # = make seed-pricing puis make seed-tracelab
```

Deux choses en une :

| Cible | Ce qu'elle charge | D'où |
| --- | --- | --- |
| `make seed-pricing` | la grille tarifaire (USD / million de tokens) | [`docs/data/model-pricing.json`](docs/data/model-pricing.json) |
| `make seed-tracelab` | la **fixture TraceLab commitée** : 2 sessions, 103 rounds | `backend/tests/fixtures/tracelab/sample.jsonl` |

Aucun réseau, aucun téléchargement : la fixture est dans le dépôt (TraceLab est sous CC BY 4.0,
qui autorise la redistribution avec attribution). La grille tarifaire sert à **estimer**
`cost_usd` quand la source ne déclare pas de coût — sans elle, le coût reste « non disponible »,
il n'est jamais remplacé par `0`.

Ce que fait réellement `scripts/seed_import.py` : il enregistre le mapping de la source
(`docs/data/mappings/tracelab.json`) via `POST /api/v1/mappings`, puis envoie le fichier à
`POST /api/v1/imports`. **Aucun accès direct à la base** — c'est exactement le chemin qu'emprunte
un import lancé depuis l'interface.

Sortie attendue (le bilan complet est écrit en JSON sur la sortie standard) :

```
→ http://localhost:8000  |  mapping tracelab.json
  mapping « tracelab-jsonl » créé (v1)
  importés=103 doublons=0 rejetés=0
```

**Relancer la commande ne duplique rien** — c'est la garantie d'idempotence, vérifiable
immédiatement :

```
  mapping « tracelab-jsonl » déjà enregistré — réutilisé
  importés=0 doublons=103 rejetés=0
```

### 5 — Vérifier que les données sont bien là

```bash
curl "http://localhost:8000/api/v1/metrics/indicators"
```

Doit renvoyer des compteurs non nuls (`session_count`, `model_call_count`, `tool_call_count`…).
Puis ouvrir <http://localhost:5173> : le dashboard affiche les indicateurs, la série temporelle
d'activité, la répartition des outils et la distribution des durées.

> **Rien ne s'affiche ?** Un dashboard sans données affiche « non disponible », **jamais 0** :
> c'est le comportement attendu, pas une panne. Vérifier que l'étape 4 s'est bien terminée avec
> `curl http://localhost:8000/api/v1/imports`.

---

## Vérifier son installation

```bash
make test        # pytest (backend) + vitest (frontend)
make arch        # règle des dépendances (import-linter) — 5 contrats
make ci          # la passe complète : lint + typecheck + arch + test
```

`make arch` vérifie que le sens des dépendances de la Clean Architecture est respecté : `domain`
n'importe rien, `application` ne connaît que `domain`, les adaptateurs d'infrastructure ne
s'appellent pas entre eux.

Contrôle rapide sans passer par les tests :

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/v1/metrics/indicators"
curl "http://localhost:8000/api/v1/data-quality"
```

> **État des suites au 2026-09-11.** Backend : **355 tests verts**, 1 ignoré, couverture 91 %.
> Frontend : **193 tests verts sur 228** — 35 tests d'écrans sont rouges, et `npm run typecheck`
> échoue sur du code mort (`src/features/chat/`, remplacé par `features/mapping-agent/`) et sur
> des tests qui visent des composants renommés. `make ci` n'est donc pas vert de bout en bout
> aujourd'hui ; voir [Statut](#statut).

---

## Charger plus de données

La fixture de l'étape 4 suffit à voir l'application fonctionner, mais elle est minuscule
(2 sessions). Pour un dashboard réellement peuplé :

### Extrait TraceLab de développement — 128 sessions, 14 045 rounds

```bash
make data-tracelab       # télécharge la release épinglée (53 Mio), vérifie le SHA256, échantillonne
make seed-tracelab-dev   # importe l'extrait obtenu
```

`make data-tracelab` écrit `data/tracelab/extract-dev.jsonl` (23 Mio, non commité) et son
`*.meta.json`, qui rejoue le bilan chiffré. La sélection est **déterministe** — 1 session sur 32,
sessions entières, `sha1(session_id) % 32 == 0` : quiconque repart du même fichier épinglé obtient
octet pour octet le même extrait. Le script refuse d'aller plus loin si l'empreinte SHA256 ne
correspond pas. Provenance, licence et méthode : [`data/README.md`](data/README.md).

### Deuxième source — SWE-chat

```bash
make install             # nécessaire : le script lit du Parquet (pyarrow), pas seulement du JSON
export HF_TOKEN=…        # dataset gated : accès à accepter sur Hugging Face
make data-swe-chat
make seed-swe-chat
```

Le mapping est déjà écrit ([`docs/data/mappings/swe-chat.md`](docs/data/mappings/swe-chat.md)) :
l'import se fait sans passer par l'agent IA.

### Repartir de zéro

```bash
make seed-reset          # vide les données importées (garde le schéma) puis recharge ce qui est présent
make clean && make up && make migrate && make seed    # remise à zéro complète, volume inclus
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
| `AGENTSCOPE_LLM_PROVIDER` | `fake` | `fake` (aucun appel réseau) · `anthropic` · `openai` |
| `AGENTSCOPE_LLM_MODEL` | — | identifiant du modèle, jamais en dur dans le code |
| `AGENTSCOPE_LLM_BASE_URL` | — | endpoint des fournisseurs compatibles OpenAI (Ollama, LM Studio, OpenRouter…) |
| `AGENTSCOPE_LLM_API_KEY` | — | **clé secrète — jamais dans le dépôt** |

### Utiliser un modèle réel

L'agent de mapping (écran « Source », assistant flottant) est le **seul** consommateur d'un
modèle. Avec le fournisseur `fake` par défaut il renvoie une proposition identité déterministe :
assez pour parcourir l'interface et faire tourner les tests, pas pour produire un vrai mapping.

1. Renseigner dans `.env` :

   ```bash
   AGENTSCOPE_LLM_PROVIDER=anthropic
   AGENTSCOPE_LLM_MODEL=<identifiant du modèle>
   AGENTSCOPE_LLM_API_KEY=<votre clé>
   ```

   Pour un modèle **local** (aucune clé nécessaire) :

   ```bash
   AGENTSCOPE_LLM_PROVIDER=openai
   AGENTSCOPE_LLM_BASE_URL=http://host.docker.internal:11434/v1
   AGENTSCOPE_LLM_MODEL=<modèle servi par Ollama>
   ```

   > Il n'existe **pas** de valeur `ollama` pour `AGENTSCOPE_LLM_PROVIDER`. Ollama, LM Studio et
   > OpenRouter exposent une API compatible OpenAI : on les atteint avec
   > `AGENTSCOPE_LLM_PROVIDER=openai` et `AGENTSCOPE_LLM_BASE_URL` pointé vers le serveur — même
   > code, aucune branche dédiée ([ADR-0005](docs/architecture/adr/0005-abstraction-ia.md)).

2. Redémarrer le backend : `docker compose up -d backend` (la configuration est lue au démarrage).
3. Le reste de l'application est inchangé : l'import, les indicateurs et le dashboard n'appellent
   aucun modèle, et l'agent ne fait que **proposer** — aucune écriture en base.

Procédure complète, recettes par fournisseur et dépannage :
[`docs/ai/providers.md`](docs/ai/providers.md) et
[`docs/ai/model-switch.md`](docs/ai/model-switch.md).

> **Les tests n'appellent jamais un modèle réel** : ils utilisent `FakeLLMProvider`, déterministe
> et hors réseau. Aucune clé n'est nécessaire pour `make test`.

---

## Le parcours principal

Le parcours, de bout en bout : **fichier de traces → import normalisé → indicateur affiché**.
Les quatre entrées de la navigation :

1. **Dashboard** (`/`) — indicateurs (sessions, appels, tokens ventilés entrée / sortie / cache,
   coût, taux d'erreur, taux d'utilisation du cache, durée médiane), série temporelle d'activité,
   répartition des outils, distribution des durées, top sessions. Filtres source / agent / modèle
   / dépôt / période, partageables par URL. Une donnée indisponible s'affiche « non disponible »,
   **jamais 0**.
2. **Imports** (`/imports`) — déposer un ou plusieurs fichiers (`.jsonl`, `.csv`, `.parquet`),
   choisir le mapping, lancer l'import. Retour : bilan `importés / doublons / rejetés`, avec la
   raison de chaque rejet (`reason_code`). L'historique et le détail d'un import sont consultables
   (`/imports/{id}`).
3. **Sessions** (`/sessions`) — liste filtrée et paginée, puis le détail d'une session
   (`/sessions/{id}`) : timeline `model_call` / `tool_call`, tokens, coût, erreurs, lien de
   provenance vers l'enregistrement brut.
4. **Source** (`/sources/new`) — déposer un fichier dont la structure n'est pas connue :
   l'application le profile (types, taux de nuls, exemples), l'agent IA propose un mapping et
   explique ses choix, on corrige dans l'éditeur, on prévisualise (dry-run), puis on valide. Le
   mapping enregistré est réutilisable **sans** l'agent.

L'**assistant** est accessible partout par le bouton flottant, et en pleine page sur `/chat`.
Un panneau d'accessibilité (contraste, taille de texte, animations) est disponible depuis la barre
de navigation.

### Ce que le parcours fait réellement aujourd'hui

| Étape | État |
| --- | --- |
| Modèle relationnel + migrations + dépôts + vues | ✅ opérationnel |
| Lecteurs JSONL / CSV / Parquet, moteur de mapping, normalisation, idempotence | ✅ opérationnel |
| Endpoints REST branchés sur la base (plus aucune fixture) | ✅ opérationnel |
| Écrans dashboard / imports / sessions / source | ✅ livrés et alimentés par l'API |
| Agent de mapping (`/analyze`, `/chat`, `/mappings/{id}/preview`) | ✅ livré — la qualité de la proposition dépend du fournisseur configuré |
| Deux sources intégrées (TraceLab, SWE-chat) | ✅ mappings écrits et testés bout-en-bout |

Avancement détaillé et critères de vérification : [`docs/PLAN.md`](docs/PLAN.md) §7.

---

## L'API REST

Préfixe **`/api/v1`**, documentation interactive sur <http://localhost:8000/docs>, erreurs au
format `application/problem+json`.

| Méthode | Chemin | Rôle |
| --- | --- | --- |
| `GET` | `/health` · `/api/v1/health` | sonde de vie |
| `POST` | `/api/v1/imports` | importer un ou plusieurs fichiers avec un mapping |
| `GET` | `/api/v1/imports` · `/{id}` · `/{id}/rejects` | historique, bilan, rejets détaillés |
| `POST` | `/api/v1/analyze` | fichier inconnu → profil de champs + proposition de mapping |
| `POST` | `/api/v1/chat` | dialoguer avec l'agent sur une proposition (sans effet de bord DB) |
| `GET` `POST` `PUT` | `/api/v1/mappings` · `/api/v1/mappings/{id}` | CRUD des mappings versionnés |
| `POST` | `/api/v1/mappings/{id}/preview` | dry-run : aperçu des lignes et des rejets simulés |
| `GET` | `/api/v1/metrics/indicators` · `/timeseries` · `/dimensions` · `/tool-usage` | indicateurs et séries, filtrables |
| `GET` | `/api/v1/sessions` · `/api/v1/sessions/{id}` | liste paginée, détail avec timeline |
| `GET` | `/api/v1/sources` · `/api/v1/sources/{name}/repositories` | référentiel des sources |
| `GET` | `/api/v1/data-quality` | complétude, rejets et champs manquants par lot d'import |
| `GET` `POST` | `/api/v1/model-pricing` | grille tarifaire (estimation du coût) |

Filtres communs aux endpoints `/metrics/*` : `sources`, `agents`, `models`, `repositories`,
`from`, `to`. Définition précise de chaque indicateur (calcul SQL, unité, traitement des `NULL`) :
[`docs/data/indicators.md`](docs/data/indicators.md).

Régénérer le client TypeScript du frontend depuis le schéma OpenAPI : `make openapi`.

---

## Installation sans Docker

Nécessite **Python 3.12+** et **Node 20+**. Une base PostgreSQL joignable est optionnelle : par
défaut le backend utilise SQLite (`sqlite:///./agentscope.db`).

**Linux / macOS**

```bash
make install     # venv backend (pip install -e ".[dev]") + npm install
make dev-local   # uvicorn (port 8000) + vite (port 5173)
```

Puis, dans un autre terminal, le schéma et les données :

```bash
cd backend && ./.venv/bin/alembic upgrade head && cd ..
make seed
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

Puis charger les données : `make seed`, ou directement
`python scripts/seed_pricing.py` et
`python scripts/seed_import.py --mapping docs/data/mappings/tracelab.json backend/tests/fixtures/tracelab/sample.jsonl`.

---

## Dépannage

| Symptôme | Cause probable / solution |
| --- | --- |
| `failed to connect to the docker API` | Docker Desktop n'est pas démarré — le lancer, puis réessayer. |
| `port is already allocated` | Un service occupe déjà 5432 / 8000 / 5173 → changer `DB_PORT`, `BACKEND_PORT` ou `FRONTEND_PORT` dans `.env`, puis `make up`. |
| `make seed` : `python3: command not found` | Pas de Python sur l'hôte, ou un alias Windows non fonctionnel → installer Python 3.12+, ou forcer l'interpréteur : `make seed PYTHON=py`. |
| `make seed` : connexion refusée | La stack n'est pas levée, ou l'API écoute ailleurs → `make ps`, puis `make seed API=http://localhost:<BACKEND_PORT>`. |
| Le dashboard est vide, tout affiche « non disponible » | Aucune donnée en base : lancer `make seed` (étape 4). Vérifier avec `curl http://localhost:8000/api/v1/imports`. |
| Le coût affiche « non disponible » | La source ne déclare pas de coût **et** aucun tarif n'existe pour ce modèle → `make seed-pricing`, puis compléter `docs/data/model-pricing.json` si le modèle manque. |
| Le frontend affiche une erreur d'API | Vérifier que le backend répond : `curl http://localhost:8000/health`, puis `make logs`. |
| Le frontend sert un vieux module, erreur d'export incohérente avec le fichier | Cache Vite périmé derrière le bind mount → `docker compose restart frontend`. |
| `make` introuvable sous Windows | Utiliser **Git Bash**, ou taper les commandes `docker compose` équivalentes indiquées ci-dessus. |
| Base incohérente après un changement de schéma | `make clean` (⚠️ supprime le volume) puis `make up && make migrate && make seed`. |
| Modifications backend non prises en compte | Le code est monté en volume avec `--reload` ; si une **dépendance** change, reconstruire : `make build`. |
| L'agent répond toujours la même chose, très mécaniquement | `AGENTSCOPE_LLM_PROVIDER` est resté à `fake` — voir [Configuration & clés IA](#configuration--clés-ia). |
| `POST /analyze` renvoie 400 avec le fournisseur `fake` | Attendu : la proposition identité du fournisseur factice n'est pas un mapping valide pour un fichier quelconque, et l'application refuse plutôt que d'écrire n'importe quoi. Configurer un modèle réel. |

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
| `frontend/src` | UI React (dashboard, imports, sessions, agent de mapping) | API REST |

Cette règle est **vérifiée automatiquement** par `make arch` (5 contrats `import-linter`).

Composants, points d'extension et parcours d'import détaillés :
[`docs/architecture/components.md`](docs/architecture/components.md) ·
Décisions : [ADR](docs/architecture/adr/) · Modèle de données : [`docs/data/`](docs/data/) ·
IA interchangeable : [`docs/ai/`](docs/ai/) ·
Observations chiffrées sur les données réelles : [`docs/findings.md`](docs/findings.md).

### Stack

- **Backend** : Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, psycopg, pandas / pyarrow / DuckDB
  pour le profilage et les formats tabulaires, jsonschema pour la validation des mappings.
  SQLite par défaut, PostgreSQL via configuration.
- **Frontend** : React 19, Vite 6, TypeScript, TanStack Router + Query, Zustand, zod, Recharts,
  Tailwind CSS.
- **IA** : port `LLMProvider` + adaptateurs (Anthropic, OpenAI-compatible — dont Ollama, LM Studio
  et OpenRouter via `base_url` —, Fake pour les tests). Fournisseur / modèle / endpoint / clé
  **par variables d'environnement**.
- **Qualité** : pytest (+ cov, asyncio), ruff, mypy, import-linter · vitest, Testing Library, MSW,
  ESLint (+ `eslint-plugin-boundaries`), Prettier, Playwright, orval.

---

## Statut

| Livrable | État |
| --- | --- |
| Structure du dépôt & Clean Architecture (`import-linter` vert, 5 contrats) | ✅ |
| Docker Compose + Makefile + `.env.example` | ✅ |
| Modèle relationnel, migrations Alembic, dépôts, 4 vues agrégées | ✅ |
| Moteur de mapping, normalisation, import idempotent | ✅ |
| Port `LLMProvider` + adaptateurs Fake / Anthropic / OpenAI-compatible + factory par config | ✅ |
| Agent de mapping : `AnalyzeUnknownFile`, `ChatAboutMapping`, `PreviewMapping` | ✅ |
| API REST branchée sur la base (plus aucune fixture) | ✅ |
| Frontend — dashboard, imports, sessions, agent de mapping, assistant | ✅ écrans livrés |
| Deux sources intégrées et documentées (TraceLab, SWE-chat) | ✅ |
| Trois observations chiffrées reproductibles ([`docs/findings.md`](docs/findings.md)) | ✅ |
| Tests backend — 355 verts, 1 ignoré, couverture 91 % | ✅ |
| Tests frontend (193/228) et `npm run typecheck` | 🟡 35 tests rouges ; code mort à retirer (`src/features/chat/`) |
| Compte rendu de vérification avec 2 modèles IA réels | ⬜ gabarit prêt ([`docs/ai/verification-report.md`](docs/ai/verification-report.md)) |
| CI GitHub Actions à chaque PR | ⬜ `.github/workflows/e2e.yml` est entièrement commenté ; aucun workflow actif |
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
