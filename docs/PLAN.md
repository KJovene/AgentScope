# AgentScope — Plan de réalisation

> Plan opérationnel pour le sprint (Jour 1 → vendredi soir).
> Équipe : **6+ personnes**. Stack retenue : **Python / FastAPI (backend) + React / Vite / TypeScript (frontend)**.
> Ce document sert de source pour créer le tableau **GitHub Projects** (chaque `Ixx` = une issue).

---

## Sommaire

1. [Objectif et critères d'évaluation](#1-objectif-et-critères-dévaluation)
2. [Décisions techniques (ADR résumés)](#2-décisions-techniques-adr-résumés)
3. [Architecture Clean — couches et arborescence](#3-architecture-clean--couches-et-arborescence)
4. [Modèle de données (viser 3NF)](#4-modèle-de-données-viser-3nf)
5. [Contrats d'interface à figer le Jour 1](#5-contrats-dinterface-à-figer-le-jour-1)
6. [Organisation de l'équipe et workstreams](#6-organisation-de-léquipe-et-workstreams)
7. [Backlog découpé — EPICs et issues](#7-backlog-découpé--epics-et-issues)
8. [Planning Jour 1 → Jour 4](#8-planning-jour-1--jour-4)
9. [Configuration GitHub Projects](#9-configuration-github-projects)
10. [Stratégie de tests et CI](#10-stratégie-de-tests-et-ci)
11. [Livrables du vendredi soir](#11-livrables-du-vendredi-soir)
12. [Risques et parades](#12-risques-et-parades)
13. [Annexe — script de création des issues](#13-annexe--script-de-création-des-issues)

---

## 1. Objectif et critères d'évaluation

**Parcours principal, non négociable :** `importer → vérifier → normaliser → explorer`.
Tout le reste (2ᵉ source, agent conversationnel, prolongements) passe **après** un parcours principal fiable.

| Critère d'évaluation | Points | EPICs concernés |
| --- | ---: | --- |
| Architecture, Clean Architecture, maintenabilité, IA interchangeable | 7 | EPIC 1, EPIC 3, EPIC 0 |
| Modèle de données, normalisation, traçabilité | 4 | EPIC 1, EPIC 2 |
| Ingestion + agent IA + dashboard + justesse des indicateurs | 4 | EPIC 2, EPIC 3, EPIC 4, EPIC 5 |
| Travail d'équipe, GitHub Projects, revues de PR | 3 | EPIC 0, processus |
| Publication open source, documentation, reproductibilité | 2 | EPIC 6 |

**Conséquences sur les priorités :**
- **P0** = parcours principal + séparation réelle des couches + IA pilotée par configuration + tests exigés par l'énoncé.
- **P1** = 2ᵉ source via l'UI, agent conversationnel, drill-down depuis les graphes, vue session détaillée.
- **P2** = prolongements (import par URL, détection d'anomalies, Q&A sur les données, connexion Hugging Face).

> Un import **partiel bien expliqué** vaut mieux qu'un import « réussi » qui produit de faux chiffres.

---

## 2. Décisions techniques (ADR résumés)

À committer dans `docs/architecture/adr/` le Jour 1. Format court : contexte / décision / conséquences.

- **ADR-0001 — Stack.** Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic ; frontend React 18 + Vite + TypeScript + TanStack Query + Recharts (ou ECharts). Justification : écosystème data mûr (pandas, pyarrow, DuckDB) pour JSONL/CSV/Parquet et le profilage ; Clean Architecture éprouvée en Python.
- **ADR-0002 — Monolithe modulaire + Clean Architecture.** Trois couches (`domain`, `application`, `infrastructure`/`interfaces`). Le cœur métier ne dépend ni de FastAPI, ni de la base, ni d'un fournisseur IA. Règle des dépendances vérifiée automatiquement par `import-linter`.
- **ADR-0003 — Base de données.** SQLite par défaut (zéro install, reproductible depuis un clone) ; PostgreSQL possible via une seule variable d'environnement. Le SQL reste standard ; migrations Alembic.
- **ADR-0004 — Contrat de mapping.** Un document JSON versionné, validé par JSON Schema. Les transformations sont un **registre whitelisté** de fonctions nommées. **Aucun code produit par l'IA n'est exécuté.**
- **ADR-0005 — Abstraction IA.** Interface `LLMProvider` + adaptateurs (Anthropic, OpenAI-compatible incluant Ollama/LM Studio, Fake). Fournisseur / modèle / endpoint / clé **par configuration**, jamais en dur. Les réponses des modèles sont converties vers le contrat de mapping puis validées par l'application.
- **ADR-0006 — Provenance.** Chaque enregistrement normalisé référence son enregistrement brut d'origine (`raw_record`) et son `import_batch`. Rétention du brut configurable.

---

## 3. Architecture Clean — couches et arborescence

### Règle des dépendances

```
        interfaces/ (API REST, plus tard CLI)      infrastructure/ (DB, readers, LLM, profiling, config)
                        \                                   /
                         \                                 /
                          v                               v
                              application/  (use cases + PORTS)
                                        |
                                        v
                                   domain/  (entités, règles pures — n'importe RIEN)
```

- `domain/` : entités, value objects, erreurs métier. **Aucun import de framework, ORM, HTTP, SDK IA.**
- `application/` : use cases + **ports** (interfaces abstraites). Importe uniquement `domain`.
- `infrastructure/` : implémente les ports (SQLAlchemy, lecteurs de fichiers, adaptateurs LLM, profileur, settings).
- `interfaces/` : adaptateurs entrants (routes FastAPI, DTO Pydantic, injection de dépendances).
- La composition (câblage ports ↔ implémentations) se fait **uniquement** dans `interfaces/api/dependencies.py` + `main.py`.

### Arborescence cible

```
backend/
  agentscope/
    domain/
      entities.py              # Session, ModelCall, ToolCall, Repository, ImportBatch, Mapping, FieldProfile
      value_objects.py         # TokenUsage, TimeRange, Provenance, RejectReason
      errors.py                # DomainError, InvalidMappingError, ...
    application/
      ports/
        repositories.py        # SessionRepository, ModelCallRepository, ToolCallRepository,
                               # ImportRepository, MappingRepository, RejectRepository
        source_reader.py       # SourceReader
        llm_provider.py        # LLMProvider, MappingProposal
        metrics.py             # MetricsQueryService
        profiler.py            # FieldProfiler, SensitiveFilter
      mapping/
        contract.py            # dataclasses du contrat de mapping
        validator.py           # validation JSON Schema + sémantique
        transforms.py          # REGISTRE whitelisté des transformations
        normalizer.py          # Mapping + records bruts -> lignes normalisées + rejets
      use_cases/
        import_file.py
        list_imports.py
        get_import_report.py
        analyze_unknown_file.py
        chat_about_mapping.py
        preview_mapping.py
        manage_mappings.py
        query_metrics.py
        get_session_detail.py
    infrastructure/
      persistence/
        orm_models.py
        repositories/
        migrations/            # Alembic
        views.sql             # vues agrégées dashboard
      readers/
        jsonl_reader.py
        csv_reader.py
        parquet_reader.py
      llm/
        fake_provider.py
        anthropic_provider.py
        openai_provider.py    # couvre OpenAI + Ollama/LM Studio via base_url
        factory.py
      profiling/
        field_profiler.py
        sensitive_filter.py
      config/
        settings.py           # lecture env, aucune valeur secrète par défaut
    interfaces/
      api/
        app.py
        dependencies.py
        routes/
        schemas/
    main.py
  tests/
    unit/ integration/ e2e/
    fixtures/
frontend/
  src/
    app/                      # routing, layout, thème
    features/
      import/
      mapping-agent/
      dashboard/
      session-detail/
      data-quality/
    shared/
      api/                    # client TypeScript généré depuis l'OpenAPI
      components/ charts/ hooks/
docs/
  architecture/ (components.md, adr/)
  data/ (relational-model.md, indicators.md, mappings/)
  ai/ (providers.md, model-switch.md, verification-report.md)
  findings.md
data/
  README.md                  # provenance, versions, dates de récupération, méthode de sélection
```

---

## 4. Modèle de données (viser 3NF)

### Tables de base

| Table | Une ligne représente… | Clés / contraintes notables |
| --- | --- | --- |
| `source` | un projet source de traces (TraceLab, SWE-chat, Trace Commons…) | PK `id` ; `name` unique |
| `import_batch` | **un import** (une exécution d'ingestion d'un fichier) | PK `id` ; FK `source_id`, `mapping_id` ; `file_sha256` unique par `source_id` (idempotence) ; colonnes de bilan : `imported_count`, `duplicate_count`, `rejected_count`, `missing_info_count`, `status`, `imported_at` |
| `raw_record` | **un enregistrement d'origine** tel que reçu (provenance) | PK `id` ; FK `import_batch_id` ; `record_index` ; `payload_json` ; `record_sha256` |
| `repository` | un dépôt de code référencé par des sessions (SWE-chat) | PK `id` ; FK `source_id` ; (`source_id`,`name`) unique |
| `session` | **une session d'agent** | PK `id` ; FK `source_id`, `import_batch_id`, `repository_id?`, `raw_record_id` ; (`source_id`,`external_id`) **unique** |
| `model_call` | **un appel à un modèle** dans une session | PK `id` ; FK `session_id`, `raw_record_id` ; (`session_id`,`external_id`) unique (ou `seq` si pas d'id source) ; `prompt_tokens`, `completion_tokens`, `total_tokens`, `cached_tokens?`, `cost_usd?`, `status`, `error_type?`, `started_at`, `ended_at`, `duration_ms` |
| `tool_call` | **un appel d'outil** dans une session | PK `id` ; FK `session_id`, `model_call_id?`, `raw_record_id` ; (`session_id`,`external_id`\|`seq`) unique ; `tool_name`, `status`, `error_type?`, timings, `input_bytes?`, `output_bytes?` |
| `mapping` | **une configuration de mapping** enregistrée et réutilisable | PK `id` ; FK `source_id` ; (`name`,`version`) unique ; `source_format`, `definition_json`, `is_active`, `created_at`, `created_by` |
| `import_reject` | **un enregistrement rejeté** lors d'un import, avec explication | PK `id` ; FK `import_batch_id` ; `record_index`, `reason_code`, `reason_detail`, `payload_json` |
| `field_profile` | **un champ profilé** d'un fichier analysé | PK `id` ; FK `import_batch_id` ; `field_path`, `inferred_type`, `null_ratio`, `distinct_count`, `sample_values_json` |

### Vues agrégées (couche dashboard, ne remettent pas en cause la 3NF des tables de base)

- `v_session_metrics` — par session : `source`, `agent`, `model`, `started_at`, `duration_ms`, `n_model_calls`, `n_tool_calls`, `total_tokens`, `cached_tokens`, `total_cost_usd`, `n_errors`.
- `v_daily_activity` — par (`source`, `day`) : `n_sessions`, `n_model_calls`, `n_tool_calls`, `total_tokens`.
- `v_tool_usage` — par (`source`, `tool_name`) : `n_calls`, `n_errors`, `avg_duration_ms`.
- `v_data_quality` — par `import_batch` : compteurs de bilan + ratio de complétude des champs clés.

### Justification 3NF et exceptions assumées

- Tables de base en 3NF : pas de dépendance transitive ; les libellés (nom de source, nom de dépôt) sont sortis dans `source` / `repository`.
- **Exception 1 — colonnes JSON** (`raw_record.payload_json`, `mapping.definition_json`, `*.sample_values_json`) : données semi-structurées de provenance / documents de configuration, non décomposables sans perte de sens. Assumé.
- **Exception 2 — `model_call.total_tokens`** : valeur dérivée (`prompt + completion`) conservée pour la performance des agrégats. Recalculée à l'ingestion, testée pour cohérence.
- **Valeurs manquantes** : jamais converties en `0`. Colonnes nullables + traitement explicite dans les indicateurs (`NULL` ⇒ « non disponible », exclu des moyennes, signalé dans l'UI).
- **Idempotence** : `import_batch.file_sha256` unique par source + clés naturelles par entité + `INSERT … ON CONFLICT DO NOTHING` (ou UPSERT) ⇒ un réimport ne double aucune ligne.

### Indicateurs (≥ 4, chacun avec une fiche de définition dans `docs/data/indicators.md`)

| Indicateur | Calcul | Unité | Périmètre | Valeurs manquantes |
| --- | --- | --- | --- | --- |
| Sessions | `COUNT(session)` filtré | nombre | par source/agent/modèle/période | n/a |
| Tokens consommés | `SUM(model_call.total_tokens)` ; ventilé in / out / cached | tokens | idem | lignes sans usage exclues, signalé |
| Coût estimé | `SUM(model_call.cost_usd)` | USD | sources fournissant le coût | « non disponible » si la source ne le fournit pas — pas de 0 |
| Répartition des outils | `COUNT(tool_call) GROUP BY tool_name` + taux d'erreur | nombre / % | idem | — |
| Durée médiane de session | médiane de `session.duration_ms` | s | sessions avec début et fin connus | sessions sans timing exclues, comptées à part |
| Taux d'erreur | `n_errors / (n_model_calls + n_tool_calls)` | % | idem | — |
| Taux d'utilisation du cache | `SUM(cached_tokens) / SUM(prompt_tokens)` | % | sources exposant `cached_tokens` | non affiché si absent |

> Les métriques non comparables entre sources (ex. coût absent d'une source) restent **séparées** ou explicitement signalées.

### Visualisations (≥ 3) + vue détaillée

1. Série temporelle d'activité (sessions / tokens par jour).
2. Barres empilées : tokens par modèle **ou** répartition des appels d'outils.
3. Distribution de la durée des sessions (histogramme / box plot).
4. (bonus) Heatmap des erreurs par outil.
5. **Vue session détaillée** : timeline des `model_call` + `tool_call`, tokens, coût, erreurs, lien vers l'enregistrement brut.
6. **Drill-down** obligatoire : depuis un point de graphe → liste filtrée des sessions → vue session.

---

## 5. Contrats d'interface à figer le Jour 1

Ces quatre contrats permettent aux workstreams de travailler **en parallèle sans se bloquer**. Ils sont figés le matin du Jour 1, en réunion de 45 min, puis versionnés. Toute évolution passe par une PR étiquetée `contract` relue par les workstreams impactés.

**Principes transverses :**
- Aucune syntaxe de requête ou d'arguments embarquée dans une string : tout est du JSON structuré, validable par JSON Schema.
- Les DTO (structures d'échange) sont *le* contrat. Les `Protocol` ne sont que leur enveloppe.
- Périmètre v1 explicite : **un fichier → une ou plusieurs entités issues des mêmes enregistrements** (imbrication JSON). La jointure multi-fichiers (ex. `sessions.csv` + `calls.csv`) est **hors périmètre v1**.
- **Pas d'authentification en v1** (outil mono-utilisateur lancé en local) — décision assumée, à réévaluer plus tard.
- Tous les instants sont normalisés en **UTC ISO-8601** ; unités fixées par le schéma (`_ms`, `_usd`, `tokens`).

### 5.1 Contrat de mapping (JSON)

```jsonc
{
  "mapping_id": "uuid",
  "name": "tracelab-jsonl",
  "version": 1,
  "source_format": "jsonl",                 // jsonl | csv | parquet
  "constants": { "source_name": "TraceLab", "source_version": "2024-06" },
  "entities": {
    "session": {
      "iterate": { "path": "", "where": [] },      // path="" => enregistrement racine
      "identity": { "key_fields": ["session_id"] },  // sert à synthétiser external_id si absent
      "fields": {
        "external_id": { "from": "session_id", "transform": "identity", "required": true,
                         "on_error": "reject" },
        "agent_name":  { "from": "agent", "transform": "lower", "required": false,
                         "on_error": "null" },
        "started_at":  { "from": "ts_start", "transform": "to_iso8601",
                         "args": { "unit": "epoch_ms" }, "required": false, "on_error": "null" }
      }
    },
    "model_call": {
      "iterate": { "path": "events", "where": [["type", "eq", "model"]] },
      "parent": { "entity": "session", "key_from": "session_id" },
      "identity": { "key_fields": ["session_id", "seq"] },
      "fields": {
        "prompt_tokens":     { "from": "usage.input_tokens",  "transform": "to_int", "on_error": "null" },
        "completion_tokens": { "from": "usage.output_tokens", "transform": "to_int", "on_error": "null" },
        "model_name":        { "from": "model", "transform": "identity", "required": true, "on_error": "reject" }
      }
    },
    "tool_call": {
      "iterate": { "path": "events", "where": [["type", "eq", "tool"]] },
      "parent": { "entity": "session", "key_from": "session_id" },
      "identity": { "key_fields": ["session_id", "seq"] },
      "fields": {
        "tool_name": { "from": "name", "transform": "identity", "required": true, "on_error": "reject" },
        "status":    { "from": "status", "transform": "map_enum",
                       "args": { "mapping": { "ok": "success", "err": "error" }, "default": "unknown" },
                       "required": false, "on_error": "null" }
      }
    }
  },
  "unmapped_fields": ["debug", "internal_flags"]   // ce que l'app déclare ne pas savoir interpréter
}
```

**`iterate`** : `path` = chemin pointé vers un tableau (`""` = l'enregistrement lui-même) ; `where` = liste de triplets `[champ, op, valeur]`, `op` ∈ `eq|ne|in|exists|gt|lt`. Aucune expression n'est évaluée comme du code.

**`identity.key_fields`** : si `external_id` est absent de la source, l'`external_id` de la ligne est `sha1(source_id | entity | valeurs des key_fields)` — stable d'un import à l'autre, base de l'idempotence.

**`parent`** : comment une entité fille retrouve la clé de sa session (champ présent dans l'enregistrement, ou hérité du parent pour l'imbrication JSON).

**`on_error`** (par champ) : `reject` (l'enregistrement part dans `import_reject`), `null` (valeur mise à `NULL` + comptée dans `missing_info`), `skip` (champ ignoré). Un champ `required` dont la valeur est absente ⇒ `reject`.

**Registre des transformations whitelistées** — objet `{ "transform": "<nom>", "args": { … } }`, aucune autre acceptée :

| Nom | Args | Effet |
| --- | --- | --- |
| `identity` | — | valeur inchangée |
| `to_int` / `to_float` | — | conversion numérique |
| `to_iso8601` | `unit` ∈ `epoch_s\|epoch_ms\|iso`, `input_format?` | → instant UTC ISO-8601 |
| `lower` / `upper` / `trim` | — | normalisation de chaîne |
| `json_stringify` | — | sérialise un objet en texte |
| `const` | `value` | valeur constante |
| `coalesce` | `fields: [...]` | premier champ non nul |
| `map_enum` | `mapping: {k: v}`, `default?` | table de correspondance |
| `split` | `sep`, `index` | découpe et prend l'élément |
| `regex_extract` | `pattern`, `group?` | extrait par regex |
| `cents_to_usd` / `ms_to_s` | — | conversions d'unité |

### 5.2 Ports et DTO

Les DTO sont figés le Jour 1 (dataclasses dans `domain/` ou `application/`). Les `Protocol` en dépendent.

```python
# --- DTO (le vrai contrat) ---
@dataclass(frozen=True)
class RawRecord:
    index: int                     # position dans le fichier source (0-based)
    payload: dict                  # enregistrement d'origine, tel que lu
    sha256: str                    # hash du payload canonicalisé

@dataclass(frozen=True)
class FieldProfile:
    path: str                      # ex. "usage.input_tokens"
    inferred_type: str             # string | int | float | bool | datetime | object | array | null
    null_ratio: float
    distinct_count: int
    sample_values: list[object]    # échantillon déjà passé par SensitiveFilter

@dataclass(frozen=True)
class FieldProfileSet:
    record_count: int
    fields: list[FieldProfile]

@dataclass(frozen=True)
class RejectedRecord:
    record_index: int
    reason_code: str               # vocabulaire contrôlé (cf. 5.4)
    reason_detail: str
    payload: dict

@dataclass(frozen=True)
class NormalizationResult:
    sessions: list[SessionRow]
    model_calls: list[ModelCallRow]
    tool_calls: list[ToolCallRow]
    rejects: list[RejectedRecord]
    missing_info: dict[str, int]   # champ cible -> nb de valeurs absentes tolérées

@dataclass(frozen=True)
class FieldExplanation:
    target_field: str              # "model_call.prompt_tokens"
    source_field: str | None
    rationale: str
    confidence: float              # 0..1, calculé/estimé par l'agent

@dataclass(frozen=True)
class MappingProposal:
    definition: dict               # conforme au contrat 5.1, NON persisté tel quel
    explanations: list[FieldExplanation]
    ambiguities: list[str]         # points que l'agent signale comme incertains
    unmapped_fields: list[str]

@dataclass(frozen=True)
class ChatReply:
    text: str
    revised_proposal: MappingProposal | None

@dataclass(frozen=True)
class MetricFilter:
    sources: list[str] = ()
    agents: list[str] = ()
    models: list[str] = ()
    date_from: datetime | None = None
    date_to: datetime | None = None

# --- Ports ---
class SourceReader(Protocol):
    def supports(self, fmt: str) -> bool: ...
    def read(self, source: BinaryIO) -> Iterator[RawRecord]: ...   # streaming ; ligne invalide -> RawRecord marqué (payload brut + flag), jamais d'exception

class FieldProfiler(Protocol):
    def profile(self, records: Iterable[RawRecord], sample_size: int) -> FieldProfileSet: ...

class SensitiveFilter(Protocol):
    def scrub(self, value: object) -> object: ...                  # masque emails, clés, tokens, chemins home

class Normalizer(Protocol):
    def normalize(self, records: Iterable[RawRecord], mapping: MappingDefinition) -> NormalizationResult: ...

class LLMProvider(Protocol):
    name: str
    def propose_mapping(self, profile: FieldProfileSet, sample: list[dict],
                        target_schema: TargetSchema) -> MappingProposal: ...
    def chat(self, conversation_id: str, messages: list[ChatMessage],
             context: MappingContext) -> ChatReply: ...

class UnitOfWork(Protocol):
    """Transaction explicite : ImportFile est atomique (tout ou rien)."""
    sessions: SessionRepository
    model_calls: ModelCallRepository
    tool_calls: ToolCallRepository
    imports: ImportRepository
    def __enter__(self) -> "UnitOfWork": ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

class Clock(Protocol):
    def now(self) -> datetime: ...

class MetricsQueryService(Protocol):
    def indicators(self, f: MetricFilter) -> Indicators: ...
    def timeseries(self, f: MetricFilter, metric: str, granularity: str) -> list[Point]: ...
    def sessions(self, f: MetricFilter, page: Page) -> Paginated[SessionRow]: ...
    def session_detail(self, session_id: str) -> SessionDetail: ...

# Repositories : add / bulk_upsert(on_conflict="ignore") / get / list / count — un port par agrégat.
# Politique de conflit v1 : ignore-on-conflict (le premier import gagne).
```

### 5.3 Contrat API REST

Préfixe `/api/v1`. OpenAPI publié le Jour 1 avec des endpoints **stub** renvoyant des fixtures, pour débloquer le frontend. Upload en `multipart/form-data`. Pagination **par offset** (`?limit=&offset=`, `limit` plafonné à 200), réponse `{ items, total, limit, offset }`.

| Méthode + route | Rôle | Notes |
| --- | --- | --- |
| `POST /imports` | téléverse 1..N fichiers + `mapping_id`, lance l'import | **synchrone en v1** (extraits de taille raisonnable) ; renvoie le bilan. Limite de taille documentée. |
| `GET /imports` · `GET /imports/{id}` · `GET /imports/{id}/rejects` | historique, bilan, rejets consultables | rejets paginés |
| `POST /analyze` | téléverse un fichier inconnu → `{ profile, proposal }` **éphémère** | ne crée aucune ressource ; `proposal` conforme au contrat 5.1 |
| `POST /mappings` | persiste un mapping (depuis une proposition corrigée) | renvoie `mapping_id` + `version` |
| `GET /mappings` · `GET /mappings/{id}` · `PUT /mappings/{id}` | CRUD, versionné et réutilisable | `PUT` crée une nouvelle version |
| `POST /mappings/{id}/preview` | dry-run de normalisation sur échantillon | renvoie lignes simulées + rejets simulés |
| `POST /chat` | `{ conversation_id, message, file_ref }` → `ChatReply` | pas d'effet de bord DB ; `file_ref` = handle du fichier/profil analysé |
| `GET /metrics/indicators` · `GET /metrics/timeseries` · `GET /metrics/tool-usage` | dashboard | filtres `sources,agents,models,from,to` (répétables) ; valeur indisponible ⇒ `null`, jamais `0` |
| `GET /sessions` · `GET /sessions/{id}` | liste filtrée paginée + vue détaillée | détail = timeline `model_call` + `tool_call` + lien provenance |
| `GET /sources` · `GET /data-quality` | référentiel sources + qualité des données | |

Erreurs au format `application/problem+json` (`type`, `title`, `status`, `detail`, `errors[]`).

### 5.4 Schéma de base v1

Publié par WS-A le Jour 1 (migration Alembic `0001_initial`). Toute évolution = nouvelle migration + note dans `docs/data/relational-model.md`. Décisions figées avec le schéma :

- **`session` ne porte pas de `model_name`** (une session a N appels, potentiellement multi-modèles) — exposé seulement dans `v_session_metrics`.
- **Idempotence** : `import_batch.file_sha256` unique par `source_id` + clé naturelle par entité (`external_id` fourni, sinon synthétisé via `identity.key_fields` — cf. 5.1) + `bulk_upsert(on_conflict="ignore")`. Un réimport ⇒ 0 ligne dupliquée, compteurs identiques.
- **Vocabulaire contrôlé** :
  - `*.status` ∈ `success | error | timeout | cancelled | unknown`
  - `*.error_type` ∈ `rate_limit | timeout | tool_error | model_error | validation | other | null`
  - `import_reject.reason_code` ∈ `unparseable_record | missing_required_field | transform_failed | unknown_target_field | duplicate_in_file | schema_violation`
- **Instants** : stockés en UTC (`TIMESTAMP` ISO) ; la conversion (`epoch_s`/`epoch_ms`/local) est faite par `to_iso8601` à la normalisation.
- **Provenance** : `raw_record.payload_json` stocké **par défaut** ; l'option de rétention (I1.7) ne sert qu'à borner les très gros extraits (garder alors hash + payloads des rejets).
- **Valeurs dérivées** : `model_call.total_tokens = prompt + completion` recalculé à l'ingestion, testé pour cohérence.

---

## 6. Organisation de l'équipe et workstreams

Cinq workstreams. À 6 personnes : une par workstream + le rôle Plateforme partagé ; à 8 : binôme sur B, C et D.

| WS | Domaine | Sortie principale | Label | Effectif conseillé |
| --- | --- | --- | --- | --- |
| **WS-A** | Domaine & modèle de données | entités, schéma SQL, migrations, repositories, vues, `MetricsQueryService` | `ws:domain` | 1 (lead archi) |
| **WS-B** | Ingestion & normalisation | lecteurs JSONL/CSV/Parquet, profileur, moteur de transformations, normalizer, bilan d'import, idempotence | `ws:ingestion` | 1–2 |
| **WS-C** | Agent IA & mapping | `LLMProvider` + adaptateurs, factory par config, construction de prompt, use cases analyse/chat/preview, validation du contrat, persistance des mappings | `ws:ai` | 1–2 |
| **WS-D** | API & Dashboard | routes FastAPI, client TS, écrans import / agent / dashboard / session, filtres, drill-down | `ws:dashboard` | 2 (1 API, 1 front) |
| **WS-E** | Plateforme | repo, CI/CD, branch protection, docker-compose, ADR, licence, README, doc archi & données, sélection des datasets, release | `ws:platform` | 1 (transverse) |

**Règles de collaboration :**
- Branches courtes `type/ws/xx-titre` (ex. `feat/ingestion/2-7-idempotence`).
- Une PR = une issue (`Closes #N`), relue par **un membre d'un autre WS quand elle touche un contrat**, sinon par n'importe quel membre. CI verte obligatoire.
- Intégration sur `main` **au moins deux fois par jour**. Jamais de « big bang » le vendredi.
- Les stubs (OpenAPI, FakeLLM, fixtures) sont livrés en priorité pour que personne n'attende.

---

## 7. Backlog découpé — EPICs et issues

Estimations en jours-personne : **S** ≈ ½ j · **M** ≈ 1 j · **L** ≈ 2 j.
« Dépend » = issues bloquantes. « Résultat vérifiable » = Definition of Done.

### EPIC 0 — Cadrage & Plateforme · `ws:platform`

| ID | Titre | Estim | Dépend | Résultat vérifiable |
| --- | --- | --- | --- | --- |
| I0.1 | Créer le dépôt, arborescence Clean Architecture, `.gitignore`, `.editorconfig`, licence open source | S | — | Le repo cloné compile côté back et front ; `LICENSE` présent |
| I0.2 | Configurer GitHub Projects (colonnes, champs, labels, templates issue/PR) | S | — | Tableau visible avec 5 colonnes, champs Workstream/Priorité/Estim/Jour, 2 templates |
| I0.3 | CI GitHub Actions : lint + types + tests back, build + tests front, couverture | M | I0.1 | Un workflow s'exécute sur chaque PR et bloque si rouge |
| I0.4 | Activer la protection de branche `main` (1 review + CI verte, pas de push direct) | S | I0.3 | Un push direct sur `main` est refusé |
| I0.5 | Squelette backend FastAPI : `main`, settings via env, healthcheck, conteneur DI vide | S | I0.1 | `GET /health` répond `200` |
| I0.6 | Squelette frontend React+Vite+TS : routing, layout, génération du client depuis l'OpenAPI | M | I0.1, I4.1 | `npm run dev` affiche le layout ; client TS généré |
| I0.7 | `docker-compose` (app + db) + `Makefile` (`make dev`, `make test`, `make migrate`) | S | I0.5 | `make dev` lève l'appli complète en une commande |
| I0.8 | Rédiger ADR-0001 à ADR-0006 | S | — | 6 fichiers dans `docs/architecture/adr/` |
| I0.9 | `.env.example` sans secret + doc de configuration LLM | S | — | Un nouvel arrivant configure l'appli sans deviner |
| I0.10 | Sélection & documentation de l'extrait **TraceLab** (version, date de récupération, méthode, taille) | S | — | `data/README.md` décrit la provenance ; extrait dispo pour les tests |
| I0.11 | `import-linter` : règles de dépendances entre couches, branché dans la CI | S | I0.3 | La CI échoue si `domain` importe `infrastructure` |

### EPIC 1 — Domaine & Modèle de données · `ws:domain`

| ID | Titre | Estim | Dépend | Résultat vérifiable |
| --- | --- | --- | --- | --- |
| I1.1 | Entités du domaine (dataclasses pures, zéro dépendance externe) | M | I0.1 | `import agentscope.domain` ne tire aucun paquet tiers ; tests unitaires des invariants |
| I1.2 | Schéma relationnel v1 + diagramme (mermaid/dbml) + « ce que représente une ligne » par table | M | I1.1 | `docs/data/relational-model.md` complet et relu |
| I1.3 | Migration Alembic `0001_initial` + contraintes d'unicité (idempotence) | M | I1.2 | `make migrate` crée toutes les tables ; contraintes vérifiées par test |
| I1.4 | Ports des repositories dans `application/ports` | S | I1.1 | Interfaces typées, sans implémentation |
| I1.5 | Implémentations SQLAlchemy des repositories + `bulk_upsert` | L | I1.3, I1.4 | Tests d'intégration SQLite : add / upsert / get / list / count |
| I1.6 | Vues agrégées dashboard (`v_session_metrics`, `v_daily_activity`, `v_tool_usage`, `v_data_quality`) + migration | M | I1.3 | Les 4 vues existent et renvoient des lignes sur le jeu de test |
| I1.7 | Provenance : `raw_record` + FK depuis session/model_call/tool_call + rétention configurable | M | I1.3 | Depuis une ligne normalisée on remonte à l'enregistrement brut ; test |
| I1.8 | Doc « justification 3NF + exceptions » | S | I1.2 | Section dédiée dans `docs/data/relational-model.md` |
| I1.9 | Implémentation `MetricsQueryService` (lit les vues) | M | I1.6 | `indicators()` / `timeseries()` / `sessions()` / `session_detail()` testés |
| I1.10 | Support `repository` (2ᵉ source SWE-chat) : table + rattachement des sessions | S | I1.3 | Sessions SWE-chat reliées à un dépôt ; test |

### EPIC 2 — Ingestion & Normalisation · `ws:ingestion`

| ID | Titre | Estim | Dépend | Résultat vérifiable |
| --- | --- | --- | --- | --- |
| I2.1 | `SourceReader` + implémentation **JSONL** (streaming, tolère lignes invalides) | M | I5.2contrats §5.2 | Lit un JSONL de 10k lignes en flux ; lignes cassées → rejets, pas de crash |
| I2.2 | Implémentation `SourceReader` **CSV** (détection dialecte, encodage, en-têtes) | M | I2.1 | Lit un CSV réel ; test sur `;` et `,` |
| I2.3 | Implémentation `SourceReader` **Parquet** (pyarrow) | M | I2.1 | Lit un Parquet réel ; types préservés |
| I2.4 | `FieldProfiler` : types inférés, ratio de nuls, cardinalité, exemples, chemins imbriqués | M | I2.1 | Profil JSON stable et déterministe sur un échantillon donné |
| I2.5 | Moteur de transformations : registre whitelisté + tests exhaustifs par transform | M | contrats §5.1 | Chaque transform testée (cas nominal + erreur) ; transform inconnue rejetée |
| I2.6 | `Normalizer` : applique un `Mapping` → lignes par entité + collecte rejets/manquants | L | I2.5, I1.1 | Sur l'extrait TraceLab : produit sessions + model_calls + tool_calls cohérents |
| I2.7 | Idempotence : hash fichier + clés naturelles + upsert ; **test « réimport ⇒ 0 doublon »** | M | I2.6, I1.5 | Deux imports du même fichier → mêmes compteurs, aucune ligne dupliquée |
| I2.8 | Use case `ImportFile` : orchestration reader → normalizer → repos → bilan | M | I2.6, I1.5 | Retourne un `ImportReport` ; transaction atomique |
| I2.9 | Bilan d'import + persistance `import_reject` avec `reason_code` explicite | M | I2.8 | Bilan = importés / doublons / rejets / infos manquantes ; chaque rejet a une raison lisible |
| I2.10 | Use cases `ListImports` / `GetImportReport` / `ListRejects` | S | I2.9 | Historique et rejets consultables via l'API |
| I2.11 | Mapping intégré **TraceLab (JSONL)** : définition JSON versionnée + test bout-en-bout sur l'extrait réel | M | I2.6 | `docs/data/mappings/tracelab.md` + test vert sur données réelles |
| I2.12 | Mapping intégré **2ᵉ source (SWE-chat)** : définition + test bout-en-bout | M | I2.6, I1.10 | `docs/data/mappings/swe-chat.md` + test vert |
| I2.13 | Validation du contrat de mapping : JSON Schema + vérifs sémantiques ; **test « mapping invalide ⇒ refus expliqué »** | M | contrats §5.1 | Champ cible inconnu / transform non whitelistée / requis manquant → message clair |
| I2.14 | `SensitiveFilter` : masque emails, clés, tokens, chemins home avant tout échantillonnage | S | I2.4 | Un échantillon contenant une fausse clé ressort masqué ; test |

### EPIC 3 — Agent IA & Mapping · `ws:ai`

| ID | Titre | Estim | Dépend | Résultat vérifiable |
| --- | --- | --- | --- | --- |
| I3.1 | Interface `LLMProvider` + `MappingProposal` (contrat commun) + `LLMError` | S | contrats §5.1/5.2 | Interface typée, documentée, sans implémentation |
| I3.2 | Adaptateur `FakeLLMProvider` déterministe (fixtures) pour tests & CI | S | I3.1 | Renvoie toujours la même proposition pour une entrée donnée ; utilisé en CI |
| I3.3 | Adaptateur **Anthropic** (modèle via config, clé via env, timeout, retries) | M | I3.1 | Propose un mapping réel sur l'extrait TraceLab ; aucune clé dans le code |
| I3.4 | Adaptateur **OpenAI-compatible** (couvre OpenAI + Ollama/LM Studio via `base_url`) | M | I3.1 | Fonctionne avec un modèle local Ollama et un modèle OpenAI, même code |
| I3.5 | Factory de provider pilotée par configuration (provider / model / base_url / api_key) | S | I3.3, I3.4 | Changer de modèle = changer l'env, zéro modif de code ; test paramétré |
| I3.6 | Constructeur de prompt : schéma cible + profil + échantillon filtré ; durcissement « traces = données » | M | I2.4, I2.14 | Le prompt ne contient que profil + échantillon filtré ; texte des traces encadré, jamais exécuté comme instruction |
| I3.7 | Use case `AnalyzeUnknownFile` : profil + échantillon → proposition validée | M | I3.6, I2.13 | Sur un fichier inconnu : renvoie une proposition conforme au contrat ou une erreur explicite |
| I3.8 | Use case `ChatAboutMapping` : l'agent explique ses choix, signale les ambiguïtés, **ne touche pas la base** | M | I3.7 | Échange multi-tours ; aucune écriture DB ; ambiguïtés listées |
| I3.9 | Use case `PreviewMapping` : dry-run de normalisation sur échantillon → aperçu + rejets simulés | M | I2.6 | Aperçu avant validation ; identique au résultat d'import réel sur l'échantillon |
| I3.10 | Use cases `SaveMapping` / `UpdateMapping` / `ListMappings` / `GetMapping` (versionnés, réutilisables) | M | I1.5 | Un mapping enregistré est rechargé et réappliqué sans l'agent |
| I3.11 | Conversion réponse modèle → contrat commun + validation ; rejet propre si non conforme | M | I3.1, I2.13 | Réponse malformée du modèle → `LLMError` explicite, pas de crash |
| I3.12 | Tests : parcours analyse → validation → import avec `FakeLLM` ; mapping enregistré réutilisable après changement de modèle | M | I3.9, I3.10 | Suite verte sans appel réseau |
| I3.13 | Compte rendu de vérification avec **2 modèles réels** (doc, sans secrets) | S | I3.5 | `docs/ai/verification-report.md` : parcours OK avec les 2 configs |
| I3.14 | Doc : fournisseurs supportés, ajout d'un adaptateur, changement de modèle par config | S | I3.5 | `docs/ai/providers.md` + `docs/ai/model-switch.md` |

### EPIC 4 — API REST · `ws:dashboard` (rôle API)

| ID | Titre | Estim | Dépend | Résultat vérifiable |
| --- | --- | --- | --- | --- |
| I4.1 | Spéc OpenAPI + endpoints **stubs** renvoyant des fixtures | M | contrats §5.3 | `/docs` affiche tous les endpoints ; le front peut démarrer |
| I4.2 | `POST /imports` + `GET /imports` + `GET /imports/{id}` + `/rejects` | M | I2.10, I2.8 | Upload multi-fichiers → bilan ; historique et rejets exposés |
| I4.3 | `POST /analyze` + `POST /mappings/{id}/preview` | M | I3.7, I3.9 | Fichier inconnu → proposition ; preview renvoie l'aperçu |
| I4.4 | `POST /chat` (agent de mapping) | S | I3.8 | Conversation relayée ; pas d'effet de bord DB |
| I4.5 | CRUD `/mappings` | S | I3.10 | Créer / lister / modifier / récupérer un mapping |
| I4.6 | `GET /metrics/*` avec filtres source/agent/modèle/période | M | I1.9 | Indicateurs et séries filtrables ; valeurs indisponibles ≠ 0 dans la réponse |
| I4.7 | `GET /sessions` (liste filtrée paginée) + `GET /sessions/{id}` (vue détaillée) | M | I1.9 | Pagination stable ; détail = timeline model_call + tool_call |
| I4.8 | `GET /sources` + `GET /data-quality` | S | I1.6 | Référentiel + indicateurs de qualité par source |
| I4.9 | Gestion d'erreurs uniforme (`problem+json`) + validation d'entrée | S | I4.1 | Entrée invalide → 422 structuré ; erreurs métier → 4xx explicites |
| I4.10 | Câblage DI : use cases ↔ adaptateurs ↔ configuration | S | I0.5 | Un seul point de composition ; test de démarrage |

### EPIC 5 — Frontend & Dashboard · `ws:dashboard` (rôle front)

| ID | Titre | Estim | Dépend | Résultat vérifiable |
| --- | --- | --- | --- | --- |
| I5.1 | Layout, navigation, thème, client API typé, gestion d'erreurs UI | M | I0.6 | Navigation entre les 4 zones ; erreurs API affichées proprement |
| I5.2 | Écran Import : upload multi-fichiers, choix de la source, aperçu, lancement | M | I4.2 | Import réel depuis l'UI ; retour du bilan |
| I5.3 | Écran Historique des imports + détail du bilan | S | I4.2 | Liste + détail (importés / doublons / rejets / manquants) |
| I5.4 | Écran Rejets : liste consultable + explication par `reason_code` | S | I4.2 | Chaque rejet affiche une raison lisible |
| I5.5 | Écran « Ajouter une source » : upload d'un fichier inconnu → profil affiché | M | I4.3 | Profil des champs visible (types, nuls, exemples) |
| I5.6 | UI Chat agent : conversation, explications, ambiguïtés signalées | M | I4.4 | Échange multi-tours ; ambiguïtés mises en évidence |
| I5.7 | UI Édition de mapping : table champ source → champ cible + transform, validation en direct | L | I4.5, I4.3 | L'utilisateur corrige une correspondance ; erreurs de validation affichées |
| I5.8 | UI Prévisualisation du mapping (dry-run) avant validation | M | I4.3 | Aperçu des lignes + rejets simulés avant de valider l'import |
| I5.9 | Dashboard : 4 cartes indicateurs + tooltip de définition (calcul / unité / périmètre / NULL) | M | I4.6 | 4 indicateurs sur données réelles ; définitions accessibles |
| I5.10 | Viz 1 : série temporelle activité / tokens | M | I4.6 | Graphe alimenté par l'API ; réagit aux filtres |
| I5.11 | Viz 2 : répartition (outils ou tokens par modèle) — barres empilées | M | I4.6 | idem |
| I5.12 | Viz 3 : distribution de la durée des sessions | M | I4.6 | idem ; sessions sans timing exclues et signalées |
| I5.13 | Filtres globaux source / agent / modèle / période (état partagé) | M | I5.9 | Un changement de filtre met à jour indicateurs + viz |
| I5.14 | Drill-down : depuis un graphe → liste de sessions filtrée | M | I5.10, I4.7 | Clic sur un point → sessions correspondantes |
| I5.15 | Vue détaillée d'une session : timeline model_call + tool_call, tokens, coût, erreurs, lien provenance | L | I4.7 | Tous les appels d'une session visibles chronologiquement |
| I5.16 | Panneau « Qualité des données » : complétude, rejets, champs manquants par source | M | I4.8 | Qualité des données importées visible dans le dashboard |
| I5.17 | « Donnée indisponible ≠ 0 » : état vide explicite partout | S | I5.9 | Une métrique absente affiche « non disponible », jamais 0 |

### EPIC 6 — Documentation & Release · `ws:platform` (transverse, Jour 4)

| ID | Titre | Estim | Dépend | Résultat vérifiable |
| --- | --- | --- | --- | --- |
| I6.1 | README de prise en main (install depuis un clone, config des clés, lancer le parcours principal) | M | parcours P0 | Une personne extérieure reproduit le parcours en suivant le README |
| I6.2 | `CONTRIBUTING.md` + `CODE_OF_CONDUCT.md` + templates issue/PR | S | — | Fichiers présents et cohérents avec le workflow |
| I6.3 | `LICENSE` — choix explicite (MIT ou Apache-2.0) | S | — | Licence unique, mentionnée dans le README |
| I6.4 | Doc architecture : schéma des composants + sens des dépendances + lien vers ADR | M | EPIC 1/3 | `docs/architecture/components.md` avec diagramme |
| I6.5 | Doc données : diagramme relationnel + définitions des indicateurs + mappings de 2 sources | M | I1.2, I2.11, I2.12 | Tout est dans `docs/data/` |
| I6.6 | Doc IA : modèles testés, fournisseurs, procédure de changement de modèle | S | I3.14 | `docs/ai/` complet |
| I6.7 | **3 observations chiffrées** tirées des données réelles (sources + filtres pour les reproduire) | M | dashboard | `docs/findings.md` : 3 chiffres reproductibles |
| I6.8 | Notes de version `v0.1.0` (fonctionnalités livrées + limites connues) + mention des outils IA & composants réutilisés | S | — | `CHANGELOG.md` / release notes |
| I6.9 | Compte rendu de vérification du parcours d'identification + import avec **2 modèles IA** (sans secrets) | S | I3.13 | Joint au rendu |
| I6.10 | Créer la release taguée `v0.1.0` | S | tout P0 | Release GitHub visible avec notes |
| I6.11 | Test « structure inconnue » : importer un extrait **Trace Commons** non préparé depuis l'UI, documenter ce qui marche et ce que l'app déclare ne pas comprendre | M | parcours agent | Compte rendu : import partiel expliqué, `unmapped_fields` listés |

### EPIC 7 — Tests transverses & durcissement · tous WS (Jour 4, mais commencés plus tôt)

| ID | Titre | Estim | Dépend | Résultat vérifiable |
| --- | --- | --- | --- | --- |
| I7.1 | Test : un réimport ne crée pas de doublons | S | I2.7 | Vert en CI |
| I7.2 | Test : les relations sont conservées après import (session ↔ model_call ↔ tool_call ↔ raw_record) | S | I1.7 | Vert en CI |
| I7.3 | Test : un indicateur reste correct après jointure + filtrage | S | I1.9 | Valeur attendue calculée à la main = valeur de l'API |
| I7.4 | Test : un mapping invalide est refusé avec une explication | S | I2.13 | Vert en CI |
| I7.5 | Test e2e du parcours principal (Playwright) : fichier → import → indicateur affiché | M | parcours P0 | Vert en CI (ou job dédié) |
| I7.6 | Revue croisée d'architecture : sens des dépendances, cohérence des ports | S | — | Compte rendu court + `import-linter` vert |
| I7.7 | Passe sécurité : aucune clé dans le repo/bundle, secrets via env uniquement, `SensitiveFilter` actif sur tous les chemins vers l'IA | S | I2.14 | `gitleaks` vert ; revue manuelle du bundle front |

---

## 8. Planning Jour 1 → Jour 4

### Jour 1 — Cadrer et démarrer
**Objectif : une tranche verticale qui tourne — JSONL TraceLab → normalisation par un mapping écrit à la main → 1 indicateur affiché.**

- Réunion 45 min : figer les 4 contrats (§5).
- WS-E : I0.1, I0.2, I0.3, I0.4, I0.5, I0.7, I0.8, I0.9, I0.10, I0.11
- WS-A : I1.1, I1.2, I1.3, I1.4
- WS-B : I2.1, I2.5 (base), I2.8 (squelette)
- WS-C : I3.1, I3.2
- WS-D : I4.1, I4.10, I5.1, I0.6
- **Fin de journée :** `make dev` lève l'appli ; un import JSONL manuel produit des sessions ; le dashboard affiche « nombre de sessions ».

### Jour 2 — Construire le socle
**Objectif : ingestion fiable + 4 indicateurs + 3 visualisations sur données réelles + bilan d'import.**

- WS-A : I1.5, I1.6, I1.7, I1.9, I1.8
- WS-B : I2.2, I2.3, I2.4, I2.6, I2.7, I2.9, I2.10, I2.11, I2.13, I2.14
- WS-C : I3.6, I3.9, I3.11
- WS-D API : I4.2, I4.6, I4.7, I4.8, I4.9
- WS-D front : I5.2, I5.3, I5.4, I5.9, I5.10, I5.11, I5.12, I5.13, I5.17
- **Fin de journée :** import TraceLab reproductible et idempotent ; dashboard complet sur données réelles ; tests I7.1–I7.4 en cours de rédaction.

### Jour 3 — Ouvrir à d'autres sources
**Objectif : ajouter une 2ᵉ source depuis l'UI via l'agent, mapping éditable et prévisualisable, 2 modèles IA vérifiés.**

- WS-C : I3.3, I3.4, I3.5, I3.7, I3.8, I3.10, I3.12, I3.14
- WS-B : I2.12
- WS-A : I1.10
- WS-D API : I4.3, I4.4, I4.5
- WS-D front : I5.5, I5.6, I5.7, I5.8, I5.14, I5.15, I5.16
- **Fin de journée :** une 2ᵉ source est intégrée **sans toucher au code** ; l'agent explique son mapping ; parcours OK avec 2 configs de modèles.

### Jour 4 — Stabiliser et publier
**Objectif : tester une structure inconnue, corriger, documenter, publier `v0.1.0` vendredi soir.**

- Tous : I7.1–I7.7 (tests verrouillés et verts)
- I6.11 (Trace Commons, structure inconnue)
- WS-E : I6.1, I6.2, I6.3, I6.4, I6.5, I6.6, I6.7, I6.8, I6.9, I6.10
- I3.13 (compte rendu 2 modèles)
- Gel des fonctionnalités à midi ; l'après-midi = bugs + doc + release.
- **Vendredi soir :** dépôt public + GitHub Projects à jour + release `v0.1.0`.

---

## 9. Configuration GitHub Projects

### Colonnes (statuts)

`Backlog` → `Prêt (Ready)` → `En cours` → `En revue` → `Terminé`

- **Backlog** : toutes les issues créées, non encore priorisées pour un jour.
- **Prêt** : dépendances levées, contrat connu, responsable assigné.
- **En cours** : une seule par personne idéalement (limite WIP = 2).
- **En revue** : PR ouverte, liée à l'issue, en attente de relecture.
- **Terminé** : PR fusionnée, résultat vérifiable constaté.

### Champs personnalisés

| Champ | Type | Valeurs |
| --- | --- | --- |
| Workstream | Single select | WS-A, WS-B, WS-C, WS-D, WS-E |
| Priorité | Single select | P0, P1, P2 |
| Estimation | Single select | S, M, L |
| Jour cible | Single select | J1, J2, J3, J4 |
| Responsable | Assignee | — |

### Labels

`ws:domain` · `ws:ingestion` · `ws:ai` · `ws:dashboard` · `ws:platform`
`type:feat` · `type:test` · `type:docs` · `type:infra`
`contract` (touche une interface partagée — relecture inter-WS obligatoire)
`blocked` · `good-first-issue`

### Milestones

`J1 — Cadrage` · `J2 — Socle` · `J3 — Sources multiples` · `J4 — Stabilisation & release`

### Template d'issue

```markdown
## Contexte
<pourquoi cette tâche, lien vers l'EPIC>

## Résultat attendu (Definition of Done)
- [ ] <critère vérifiable 1>
- [ ] <critère vérifiable 2>
- [ ] Tests ajoutés / mis à jour
- [ ] Documentation mise à jour si contrat impacté

## Dépendances
Bloquée par : #… · Bloque : #…

## Interface impactée
<port / schéma DB / OpenAPI / contrat de mapping — ou "aucune">

## Workstream / Priorité / Estimation
WS-… / P… / …
```

### Template de PR

```markdown
Closes #<numéro>

## Ce que fait cette PR
…

## Comment vérifier
…

## Checklist
- [ ] CI verte
- [ ] Tests couvrant le changement
- [ ] Pas de secret / clé API
- [ ] `import-linter` vert (si backend)
- [ ] Relecteur d'un autre WS si label `contract`
```

### Règles de branche `main`

- Pas de push direct.
- 1 approbation minimum + tous les checks CI verts.
- Les PR étiquetées `contract` exigent l'approbation d'un membre de chaque WS impacté.

---

## 10. Stratégie de tests et CI

### Pyramide

| Niveau | Portée | Sans IA réelle ? | Sans UI ? |
| --- | --- | --- | --- |
| Unit | domaine, transformations, validation de mapping, calcul d'indicateurs | oui (`FakeLLMProvider`) | oui |
| Integration | repositories SQLite, use cases bout-en-bout, lecteurs de fichiers | oui | oui |
| Contract | conformité des réponses modèle au contrat de mapping | oui | oui |
| E2E | parcours principal via l'API + Playwright sur l'UI | oui | non |

### Tests exigés par l'énoncé (bloquants pour la release)

- I7.1 — réimport ⇒ pas de doublons.
- I7.2 — relations conservées après import.
- I7.3 — indicateur correct après jointure + filtrage.
- I7.4 — mapping invalide refusé avec explication.
- Compte rendu du parcours identification + import avec **2 modèles IA** (I6.9).

### Pipeline CI (`.github/workflows/ci.yml`)

1. `ruff` + `black --check` + `mypy`
2. `import-linter` (règle des dépendances)
3. `pytest` (unit + integration + contract) avec couverture
4. `npm run build` + `vitest`
5. `gitleaks` (aucun secret)
6. (job séparé, non bloquant si lent) Playwright e2e

Déclenché sur chaque PR ; obligatoire vert pour fusionner.

---

## 11. Livrables du vendredi soir

- [ ] Dépôt GitHub **public** : application, dépendances, migrations / scripts SQL, `.env.example` sans secret, tests.
- [ ] Lien du **GitHub Projects** reflétant le travail réel (pas rempli à la fin).
- [ ] **Release `v0.1.0`** identifiée avec notes de version (fonctionnalités livrées + limites connues).
- [ ] `README` de prise en main + `LICENSE` open source + `CONTRIBUTING`.
- [ ] Doc architecture : schéma des composants + dépendances + ADR.
- [ ] Doc données : diagramme relationnel + définitions des indicateurs + mappings de **2 sources distinctes**.
- [ ] Doc IA : modèles testés, fournisseurs supportés, procédure de changement de modèle.
- [ ] **3 observations chiffrées** tirées des données réelles, avec sources et filtres pour les reproduire.
- [ ] Compte rendu de vérification du parcours d'import avec **2 modèles IA** (sans secrets ni données sensibles).
- [ ] `data/README.md` : références des datasets, versions, dates de récupération, méthode de sélection des extraits.
- [ ] CI qui exécute les tests à chaque PR.

---

## 12. Risques et parades

| Risque | Impact | Parade |
| --- | --- | --- |
| Contrats d'interface qui bougent en cours de route | blocage inter-WS | Les figer le J1, toute évolution via PR `contract` relue par les WS impactés |
| L'agent IA passe trop de temps et retarde le parcours principal | parcours P0 non fiable | P0 fonctionne avec un mapping écrit à la main ; l'agent est P1 mais démarré tôt avec `FakeLLM` |
| Parquet / CSV plus délicats que prévu en JS | ingestion incomplète | Traitement fait côté Python (pyarrow) ; le front ne fait que téléverser |
| Coût / latence des appels modèles réels | CI lente, budget | CI 100 % `FakeLLM` ; modèles réels testés manuellement et documentés (I6.9) |
| Données sensibles envoyées au modèle | fuite | `SensitiveFilter` obligatoire sur tout chemin vers l'IA (I2.14) ; test dédié (I7.7) |
| Intégration « big bang » le vendredi | rendu cassé | Merge sur `main` ≥ 2×/jour ; tranche verticale dès le J1 |
| Structure inconnue de la correction non importable | perte de points | I6.11 s'entraîne sur Trace Commons ; l'app **explique** ce qu'elle ne sait pas interpréter |
| Chiffres faux dans le dashboard | perte de points majeure | Indicateurs calculés en SQL testé ; « donnée indisponible ≠ 0 » ; I7.3 |

---

## 13. Annexe — script de création des issues

Après avoir créé le dépôt et le Projet, exécuter (nécessite `gh` authentifié). Adapter `OWNER/REPO` et le numéro de projet.

```bash
#!/usr/bin/env bash
set -euo pipefail
REPO="OWNER/REPO"

# --- Labels ---
for l in "ws:domain:0e8a16" "ws:ingestion:1d76db" "ws:ai:5319e7" "ws:dashboard:fbca04" \
         "ws:platform:c5def5" "type:feat:a2eeef" "type:test:d4c5f9" "type:docs:0075ca" \
         "type:infra:bfd4f2" "contract:b60205" "blocked:e11d21" "good-first-issue:7057ff"; do
  name="${l%:*}"; color="${l##*:}"
  gh label create "$name" --repo "$REPO" --color "$color" --force
done

# --- Milestones ---
for m in "J1 — Cadrage" "J2 — Socle" "J3 — Sources multiples" "J4 — Stabilisation & release"; do
  gh api "repos/$REPO/milestones" -f title="$m" >/dev/null || true
done

# --- Issues : ID|Titre|labels|milestone ---
while IFS='|' read -r id title labels milestone; do
  [ -z "$id" ] && continue
  gh issue create --repo "$REPO" \
    --title "$id — $title" \
    --label "$labels" \
    --milestone "$milestone" \
    --body "Voir PLAN.md, section correspondante. Renseigner la Definition of Done depuis le template."
done <<'EOF'
I0.1|Dépôt + arborescence Clean Architecture + licence|ws:platform,type:infra|J1 — Cadrage
I0.2|Configurer GitHub Projects (colonnes, champs, labels, templates)|ws:platform,type:infra|J1 — Cadrage
I0.3|CI : lint + types + tests back + build front|ws:platform,type:infra|J1 — Cadrage
I0.4|Protection de branche main|ws:platform,type:infra|J1 — Cadrage
I0.5|Squelette backend FastAPI + settings env + healthcheck|ws:platform,type:feat|J1 — Cadrage
I0.6|Squelette frontend React+Vite+TS + client OpenAPI|ws:dashboard,type:feat|J1 — Cadrage
I0.7|docker-compose + Makefile|ws:platform,type:infra|J1 — Cadrage
I0.8|Rédiger ADR-0001 à ADR-0006|ws:platform,type:docs|J1 — Cadrage
I0.9|.env.example sans secret + doc config LLM|ws:platform,type:docs|J1 — Cadrage
I0.10|Sélection + doc extrait TraceLab (provenance, version, date)|ws:platform,type:docs|J1 — Cadrage
I0.11|import-linter : règles de dépendances dans la CI|ws:platform,type:infra|J1 — Cadrage
I1.1|Entités du domaine (dataclasses pures)|ws:domain,type:feat,contract|J1 — Cadrage
I1.2|Schéma relationnel v1 + diagramme + doc "une ligne = ?"|ws:domain,type:docs,contract|J1 — Cadrage
I1.3|Migration Alembic 0001 + contraintes d'unicité|ws:domain,type:feat,contract|J1 — Cadrage
I1.4|Ports des repositories|ws:domain,type:feat,contract|J1 — Cadrage
I1.5|Implémentations SQLAlchemy des repositories + bulk_upsert|ws:domain,type:feat|J2 — Socle
I1.6|Vues agrégées dashboard + migration|ws:domain,type:feat|J2 — Socle
I1.7|Provenance : raw_record + FK + rétention configurable|ws:domain,type:feat|J2 — Socle
I1.8|Doc justification 3NF + exceptions|ws:domain,type:docs|J2 — Socle
I1.9|Implémentation MetricsQueryService|ws:domain,type:feat|J2 — Socle
I1.10|Support repository (2e source SWE-chat)|ws:domain,type:feat|J3 — Sources multiples
I2.1|SourceReader + implémentation JSONL streaming|ws:ingestion,type:feat,contract|J1 — Cadrage
I2.2|SourceReader CSV (dialecte, encodage)|ws:ingestion,type:feat|J2 — Socle
I2.3|SourceReader Parquet (pyarrow)|ws:ingestion,type:feat|J2 — Socle
I2.4|FieldProfiler (types, nuls, cardinalité, exemples)|ws:ingestion,type:feat|J2 — Socle
I2.5|Moteur de transformations whitelistées + tests|ws:ingestion,type:feat,contract|J1 — Cadrage
I2.6|Normalizer : Mapping + records -> lignes + rejets|ws:ingestion,type:feat|J2 — Socle
I2.7|Idempotence + test réimport = 0 doublon|ws:ingestion,type:test|J2 — Socle
I2.8|Use case ImportFile (orchestration)|ws:ingestion,type:feat|J1 — Cadrage
I2.9|Bilan d'import + persistance des rejets avec reason_code|ws:ingestion,type:feat|J2 — Socle
I2.10|Use cases ListImports / GetImportReport / ListRejects|ws:ingestion,type:feat|J2 — Socle
I2.11|Mapping intégré TraceLab (JSONL) + test bout-en-bout|ws:ingestion,type:test|J2 — Socle
I2.12|Mapping intégré SWE-chat + test bout-en-bout|ws:ingestion,type:test|J3 — Sources multiples
I2.13|Validation contrat de mapping + test mapping invalide refusé|ws:ingestion,type:test,contract|J2 — Socle
I2.14|SensitiveFilter (masquage avant échantillonnage)|ws:ingestion,type:feat|J2 — Socle
I3.1|Interface LLMProvider + MappingProposal + LLMError|ws:ai,type:feat,contract|J1 — Cadrage
I3.2|Adaptateur FakeLLMProvider déterministe|ws:ai,type:test|J1 — Cadrage
I3.3|Adaptateur Anthropic (config + env)|ws:ai,type:feat|J3 — Sources multiples
I3.4|Adaptateur OpenAI-compatible (OpenAI + Ollama)|ws:ai,type:feat|J3 — Sources multiples
I3.5|Factory de provider pilotée par configuration|ws:ai,type:feat,contract|J3 — Sources multiples
I3.6|Constructeur de prompt + durcissement traces=données|ws:ai,type:feat|J2 — Socle
I3.7|Use case AnalyzeUnknownFile|ws:ai,type:feat|J3 — Sources multiples
I3.8|Use case ChatAboutMapping (sans écriture DB)|ws:ai,type:feat|J3 — Sources multiples
I3.9|Use case PreviewMapping (dry-run)|ws:ai,type:feat|J2 — Socle
I3.10|Use cases SaveMapping / UpdateMapping / List / Get|ws:ai,type:feat|J3 — Sources multiples
I3.11|Conversion réponse modèle -> contrat + validation|ws:ai,type:feat|J2 — Socle
I3.12|Tests parcours analyse->validation->import avec FakeLLM|ws:ai,type:test|J3 — Sources multiples
I3.13|Compte rendu vérification avec 2 modèles réels|ws:ai,type:docs|J4 — Stabilisation & release
I3.14|Doc fournisseurs + ajout adaptateur + changement de modèle|ws:ai,type:docs|J3 — Sources multiples
I4.1|OpenAPI + endpoints stubs (fixtures)|ws:dashboard,type:feat,contract|J1 — Cadrage
I4.2|Endpoints /imports (+rejects)|ws:dashboard,type:feat|J2 — Socle
I4.3|Endpoints /analyze + /mappings/{id}/preview|ws:dashboard,type:feat|J3 — Sources multiples
I4.4|Endpoint /chat|ws:dashboard,type:feat|J3 — Sources multiples
I4.5|CRUD /mappings|ws:dashboard,type:feat|J3 — Sources multiples
I4.6|Endpoints /metrics/* avec filtres|ws:dashboard,type:feat|J2 — Socle
I4.7|Endpoints /sessions + /sessions/{id}|ws:dashboard,type:feat|J2 — Socle
I4.8|Endpoints /sources + /data-quality|ws:dashboard,type:feat|J2 — Socle
I4.9|Gestion d'erreurs problem+json + validation|ws:dashboard,type:feat|J2 — Socle
I4.10|Câblage DI use cases <-> adaptateurs <-> config|ws:dashboard,type:infra|J1 — Cadrage
I5.1|Layout, navigation, thème, client API, erreurs UI|ws:dashboard,type:feat|J1 — Cadrage
I5.2|Écran Import (upload multi-fichiers, aperçu, lancement)|ws:dashboard,type:feat|J2 — Socle
I5.3|Écran Historique des imports + détail du bilan|ws:dashboard,type:feat|J2 — Socle
I5.4|Écran Rejets (liste + explication)|ws:dashboard,type:feat|J2 — Socle
I5.5|Écran Ajouter une source (profil affiché)|ws:dashboard,type:feat|J3 — Sources multiples
I5.6|UI Chat agent (explications, ambiguïtés)|ws:dashboard,type:feat|J3 — Sources multiples
I5.7|UI Édition de mapping (table + validation directe)|ws:dashboard,type:feat|J3 — Sources multiples
I5.8|UI Prévisualisation du mapping (dry-run)|ws:dashboard,type:feat|J3 — Sources multiples
I5.9|Dashboard : 4 cartes indicateurs + tooltip de définition|ws:dashboard,type:feat|J2 — Socle
I5.10|Viz 1 : série temporelle activité/tokens|ws:dashboard,type:feat|J2 — Socle
I5.11|Viz 2 : répartition (outils / tokens par modèle)|ws:dashboard,type:feat|J2 — Socle
I5.12|Viz 3 : distribution durée des sessions|ws:dashboard,type:feat|J2 — Socle
I5.13|Filtres globaux source/agent/modèle/période|ws:dashboard,type:feat|J2 — Socle
I5.14|Drill-down graphe -> liste de sessions|ws:dashboard,type:feat|J3 — Sources multiples
I5.15|Vue détaillée d'une session (timeline)|ws:dashboard,type:feat|J3 — Sources multiples
I5.16|Panneau Qualité des données|ws:dashboard,type:feat|J3 — Sources multiples
I5.17|Donnée indisponible != 0 (état vide explicite)|ws:dashboard,type:feat|J2 — Socle
I6.1|README de prise en main|ws:platform,type:docs|J4 — Stabilisation & release
I6.2|CONTRIBUTING + CODE_OF_CONDUCT + templates|ws:platform,type:docs|J4 — Stabilisation & release
I6.3|LICENSE (choix explicite)|ws:platform,type:docs|J4 — Stabilisation & release
I6.4|Doc architecture : composants + dépendances + ADR|ws:platform,type:docs|J4 — Stabilisation & release
I6.5|Doc données : diagramme + indicateurs + mappings 2 sources|ws:platform,type:docs|J4 — Stabilisation & release
I6.6|Doc IA : modèles testés + procédure de changement|ws:platform,type:docs|J4 — Stabilisation & release
I6.7|3 observations chiffrées reproductibles|ws:platform,type:docs|J4 — Stabilisation & release
I6.8|Notes de version v0.1.0|ws:platform,type:docs|J4 — Stabilisation & release
I6.9|Compte rendu import avec 2 modèles IA|ws:platform,type:docs|J4 — Stabilisation & release
I6.10|Créer la release v0.1.0|ws:platform,type:infra|J4 — Stabilisation & release
I6.11|Test structure inconnue (Trace Commons) depuis l'UI|ws:platform,type:test|J4 — Stabilisation & release
I7.1|Test : réimport = pas de doublons|ws:ingestion,type:test|J4 — Stabilisation & release
I7.2|Test : relations conservées après import|ws:domain,type:test|J4 — Stabilisation & release
I7.3|Test : indicateur correct après jointure + filtrage|ws:dashboard,type:test|J4 — Stabilisation & release
I7.4|Test : mapping invalide refusé avec explication|ws:ai,type:test|J4 — Stabilisation & release
I7.5|Test e2e parcours principal (Playwright)|ws:dashboard,type:test|J4 — Stabilisation & release
I7.6|Revue croisée d'architecture|ws:platform,type:test|J4 — Stabilisation & release
I7.7|Passe sécurité (secrets, SensitiveFilter, bundle)|ws:platform,type:test|J4 — Stabilisation & release
EOF
```

> Les titres de la liste ci-dessus peuvent aussi être collés directement dans « + Add item » du board (une ligne = une issue brouillon), puis complétés.
