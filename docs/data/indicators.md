# Définitions des indicateurs

Une fiche par indicateur : **ce qu'il mesure, comment il est calculé à la ligne près, son unité,
son périmètre, et ce qu'il fait d'une valeur absente.** Un chiffre affiché dans le dashboard doit
pouvoir être reproduit à la main depuis la base — la requête est donnée dans chaque fiche.

Source de vérité du calcul : les vues de
[`backend/agentscope/infrastructure/persistence/views.py`](../../backend/agentscope/infrastructure/persistence/views.py)
et le service de lecture
[`queries/metrics.py`](../../backend/agentscope/infrastructure/persistence/queries/metrics.py).
Le modèle relationnel est décrit dans [`relational-model.md`](relational-model.md).

---

## 1. Trois règles qui s'appliquent partout

**1. `NULL` n'est jamais `0`.** Une donnée que la source ne fournit pas reste absente jusqu'à
l'écran, où elle s'affiche « non disponible ». Concrètement : `SUM()` sur des colonnes toutes
nulles renvoie `NULL` (et non `0`), les dénominateurs passent par `NULLIF(x, 0)`, et le service
renvoie `None`. Un vrai comptage nul — une session sans aucun appel d'outil — vaut bien `0` : la
distinction est portée par `COALESCE(..., 0)` sur les comptages et par son absence sur les
mesures.

**2. Tout est en UTC.** Les instants sont normalisés à l'ingestion. Le découpage par jour utilise
`date(started_at)` (SQLite) ou `CAST(started_at AS date)` (PostgreSQL).

**3. Une session sans horodatage n'est pas comptée dans le temps.** Elle reste dans les
comptages, mais sort des séries temporelles (`WHERE started_at IS NOT NULL`) et de la durée
médiane (`duration_ms IS NOT NULL`). Elle n'est jamais convertie en zéro ni en date arbitraire.

### La chaîne de calcul

```
tables normalisées          v_session_metrics            SqlMetricsQueryService        API
session / model_call   →   une ligne par session   →   agrégation + filtres      →   /metrics/*
tool_call                  (pré-agrégée)               (SQL + médiane Python)
```

Tous les indicateurs de la section 3 sont calculés sur **`v_session_metrics`**, filtrée par la
même clause `WHERE`. C'est ce qui garantit qu'ils restent cohérents entre eux quand on bouge un
filtre.

### Les filtres communs

`MetricFilter` — un tuple vide ou `None` signifie « pas de filtre sur cette dimension ».

| Filtre | Colonne / condition | Remarque |
| --- | --- | --- |
| `sources` | `source_name IN (…)` | nom de la source (`tracelab`, …) |
| `agents` | `agent_name IN (…)` | agent ayant produit la session |
| `models` | `session_id IN (SELECT session_id FROM model_call WHERE model_name IN (…))` | **filtre au niveau session** : une session est retenue dès qu'**un** de ses appels utilise le modèle — ses autres appels restent donc dans l'agrégat |
| `repositories` | `repository_name IN (…)` | dépôt de code, pour les sources qui en fournissent un |
| `date_from` | `started_at >= :date_from` | borne **incluse** |
| `date_to` | `started_at < :date_to` | borne **exclue** |

---

## 2. Ce qui compte comme une erreur

Un appel est en erreur quand son `status` vaut **`error` ou `timeout`**. Cette liste est unique et
partagée par le domaine, les vues et le service (`_ERROR_STATUSES`). Les trois autres statuts —
`success`, `cancelled`, `unknown` — ne comptent **pas** comme des erreurs : `unknown` signifie que
la source n'a pas dit comment l'appel s'est terminé, ce n'est pas un échec.

Le nombre d'erreurs d'une session est la somme de ses appels modèle et de ses appels d'outil en
erreur : `n_errors = n_model_errors + n_tool_errors`.

---

## 3. Fiches des indicateurs

Les douze champs renvoyés par `GET /api/v1/metrics/indicators`.

### 3.1 Sessions

| | |
| --- | --- |
| **Mesure** | nombre de sessions retenues par les filtres |
| **Calcul** | `COUNT(*) FROM v_session_metrics WHERE <filtres>` |
| **Unité** | nombre |
| **Périmètre** | toutes les sources ; une session sans horodatage est comptée |
| **Valeurs manquantes** | sans objet — un comptage vaut `0`, jamais `NULL` |
| **Comparabilité** | comparable entre sources, **à condition** de savoir ce qu'une « session » représente dans chacune — voir la fiche de mapping de la source |
| **Champ API** | `session_count` |

### 3.2 Appels modèle · Appels d'outil

| | |
| --- | --- |
| **Mesure** | volume d'activité sous les sessions retenues |
| **Calcul** | `COALESCE(SUM(n_model_calls), 0)` et `COALESCE(SUM(n_tool_calls), 0)` sur `v_session_metrics` — eux-mêmes issus d'un `COUNT(*) GROUP BY session_id` sur `model_call` / `tool_call` |
| **Unité** | nombre |
| **Périmètre** | idem filtres |
| **Valeurs manquantes** | une session sans appel compte `0` — c'est une information, pas une absence |
| **Comparabilité** | comparable ; attention, une source peut agréger plusieurs échanges dans un seul enregistrement |
| **Champs API** | `model_call_count`, `tool_call_count` |

### 3.3 Tokens consommés

| | |
| --- | --- |
| **Mesure** | tokens facturés par les appels modèle, ventilés entrée / sortie / cache |
| **Calcul** | `SUM(total_tokens)`, `SUM(prompt_tokens)`, `SUM(completion_tokens)`, `SUM(cached_tokens)` sur `v_session_metrics`, qui somme les colonnes correspondantes de `model_call` par session |
| **Unité** | tokens |
| **Périmètre** | sources qui exposent une comptabilité de tokens |
| **Valeurs manquantes** | `SUM` ignore les `NULL` ; si **aucune** ligne du périmètre n'a la valeur, le résultat est `NULL` → « non disponible », **jamais `0`**. Une source sans `cached_tokens` laisse donc la carte cache vide au lieu d'afficher un faux zéro |
| **Comparabilité** | `total_tokens` n'est pas repris de la source : il est **recalculé** à l'ingestion comme `prompt + completion` (une des deux valeurs absente compte pour 0 ; le total n'est `NULL` que si les deux le sont). `cached_tokens` n'est pas fourni par toutes les sources — comparer les totaux entre sources uniquement si les deux exposent la même ventilation |
| **Champs API** | `total_tokens`, `prompt_tokens`, `completion_tokens`, `cached_tokens` |

### 3.4 Coût estimé

| | |
| --- | --- |
| **Mesure** | coût déclaré par la source, jamais recalculé par AgentScope |
| **Calcul** | `SUM(total_cost_usd)` sur `v_session_metrics` ← `SUM(model_call.cost_usd)` |
| **Unité** | USD |
| **Périmètre** | **uniquement** les sources qui fournissent un coût |
| **Valeurs manquantes** | `NULL` → « non disponible ». AgentScope n'applique aucune grille tarifaire : un coût absent le reste |
| **Comparabilité** | **à signaler systématiquement.** Une source sans coût tire le total vers le bas si on l'agrège avec une source qui en a un : filtrer par source avant de comparer |
| **Champ API** | `total_cost_usd` |

### 3.5 Taux d'erreur

| | |
| --- | --- |
| **Mesure** | part des appels qui échouent |
| **Calcul** | `SUM(n_errors) / (SUM(n_model_calls) + SUM(n_tool_calls))` — calculé en Python après l'agrégation SQL |
| **Unité** | ratio entre 0 et 1 (affiché en %) |
| **Périmètre** | appels modèle **et** appels d'outil confondus |
| **Valeurs manquantes** | dénominateur nul (aucun appel dans le périmètre) → `None`, pas `0` |
| **Comparabilité** | dépend de la finesse avec laquelle chaque source rapporte ses statuts : une source qui ne distingue pas l'échec du succès affichera 0 % à tort — le signaler dans sa fiche de mapping |
| **Champ API** | `error_rate` · nombre brut : `error_count` |

### 3.6 Taux d'utilisation du cache

| | |
| --- | --- |
| **Mesure** | part des tokens d'entrée servis depuis le cache du fournisseur |
| **Calcul** | `SUM(cached_tokens) / SUM(prompt_tokens)` sur le périmètre filtré |
| **Unité** | ratio entre 0 et 1 (affiché en %) |
| **Périmètre** | sources exposant `cached_tokens` |
| **Valeurs manquantes** | `cached_tokens` absent **ou** `prompt_tokens` nul → `None`, l'indicateur n'est pas affiché |
| **Comparabilité** | non comparable entre fournisseurs : chacun compte le cache à sa manière (lecture, écriture, TTL). Comparer à source **et** modèle constants |
| **Champ API** | `cache_hit_ratio` |
| **Garde-fou** | le domaine refuse `cached_tokens > prompt_tokens` à la construction : un tel enregistrement devient un rejet à l'import, il ne peut pas fausser l'indicateur |
| **Note** | `v_session_metrics` expose aussi un ratio **par session** ; l'indicateur global n'en est pas la moyenne, mais le rapport des sommes — c'est volontaire, une moyenne de ratios donnerait le même poids à une session de 10 tokens et à une session d'un million |

### 3.7 Durée médiane de session

| | |
| --- | --- |
| **Mesure** | durée typique d'une session, insensible aux valeurs extrêmes |
| **Calcul** | médiane de `duration_ms` sur les sessions filtrées **ayant** `duration_ms IS NOT NULL`. `duration_ms` est calculé dans la vue, uniquement si `started_at` **et** `ended_at` sont connus. La médiane elle-même est calculée en Python (`statistics.median`) pour rester identique sur SQLite et PostgreSQL |
| **Unité** | **millisecondes** (l'UI convertit à l'affichage) |
| **Périmètre** | sessions chronométrées seulement |
| **Valeurs manquantes** | aucune session chronométrée → `None`. Les sessions non chronométrées sont **exclues du calcul**, pas comptées à zéro |
| **Comparabilité** | comparable si les sources bornent la session de la même façon ; une source qui ne fournit qu'un `started_at` disparaît entièrement de cet indicateur — le nombre de sessions exclues doit être lu dans le panneau Qualité |
| **Champ API** | `median_session_duration_ms` |

---

## 4. Séries temporelles

`GET /api/v1/metrics/timeseries?metric=…&granularity=day`

Agrégation par **jour** de `started_at`, sur les mêmes filtres, en excluant les sessions sans
horodatage.

| `metric` | Agrégation | Unité | Valeur absente |
| --- | --- | --- | --- |
| `sessions` | `COUNT(*)` | nombre | — |
| `tokens` | `SUM(total_tokens)` | tokens | `NULL` si aucune donnée ce jour-là |
| `model_calls` | `SUM(n_model_calls)` | nombre | — |
| `tool_calls` | `SUM(n_tool_calls)` | nombre | — |
| `cost` | `SUM(total_cost_usd)` | USD | `NULL` si la source ne fournit pas de coût |
| `errors` | `SUM(n_errors)` | nombre | — |

Seule la granularité `day` est implémentée ; toute autre valeur lève une erreur explicite plutôt
que de renvoyer un résultat approximatif. **Les jours sans session n'apparaissent pas** dans la
série : c'est au client de décider s'il affiche un trou ou un zéro — un jour sans donnée n'est pas
un jour à zéro session tant qu'on ne sait pas si l'import couvre cette période.

---

## 5. Répartition des outils

Vue `v_tool_usage`, par `(source_name, tool_name)` :

| Colonne | Calcul | Note |
| --- | --- | --- |
| `n_calls` | `COUNT(*)` | volume d'appels de l'outil |
| `n_errors` | appels en statut `error` / `timeout` | |
| `error_rate` | `n_errors / NULLIF(n_calls, 0)` | ratio 0–1 |
| `avg_duration_ms` | `AVG(durée)` sur les appels **chronométrés uniquement** | `NULL` si aucun appel de cet outil n'a de début **et** de fin |

Les noms d'outils ne sont **pas** normalisés entre sources : `Bash` chez un agent et `shell` chez
un autre restent deux lignes distinctes. Le rapprochement, s'il est souhaité, relève du mapping de
la source — pas de la vue.

---

## 6. Qualité des données

Vue `v_data_quality`, une ligne par import :

| Colonne | Sens |
| --- | --- |
| `record_count` | lignes lues dans le fichier |
| `imported_count` · `duplicate_count` · `rejected_count` | bilan de l'import |
| `missing_info_count` | lignes importées mais incomplètes (un champ cible attendu était absent) |
| `completeness_ratio` | `imported_count / NULLIF(record_count, 0)` — `NULL` sur un fichier vide, jamais `0` |
| `n_profiled_fields` · `avg_null_ratio` | champs profilés à l'import et leur taux de nuls moyen |

C'est le contre-poids des indicateurs : un chiffre flatteur calculé sur un import dont la moitié
des lignes a été rejetée n'a pas la même valeur. Les deux se lisent ensemble.

---

## 7. Vue détaillée d'une session

`GET /api/v1/sessions/{id}` ne passe pas par les vues : il lit `session`, `model_call` et
`tool_call` directement, et fusionne les deux types d'appels en une **timeline** ordonnée par
`started_at`, puis par type et par `sequence`. Les appels sans horodatage sont placés en fin de
liste, jamais réordonnés arbitrairement.

- `total_tokens` / `total_cost_usd` de la session : somme des appels **qui ont la valeur** ;
  `None` si aucun ne l'a.
- `error_count` : appels en `error` / `timeout` dans la timeline.
- `has_raw_record` : indique si la provenance est disponible, c'est-à-dire si la ligne brute
  d'origine est encore conservée (voir la politique de rétention,
  [ADR-0006](../architecture/adr/0006-provenance.md)).

---

## 8. Reproduire un chiffre à la main

Tout indicateur du dashboard doit être retrouvable en SQL. Exemple — le total de tokens de la
source `tracelab` sur septembre 2026 :

```sql
SELECT SUM(total_tokens) AS total_tokens
FROM v_session_metrics
WHERE source_name = 'tracelab'
  AND started_at >= '2026-09-01'
  AND started_at <  '2026-10-01';
```

Ouvrir un shell SQL sur la base de développement : `make db-shell`.

La même valeur doit sortir de l'API :

```bash
curl "http://localhost:8000/api/v1/metrics/indicators?sources=tracelab&date_from=2026-09-01T00:00:00Z&date_to=2026-10-01T00:00:00Z"
```

C'est exactement ce que vérifie le test I7.3 (« un indicateur reste correct après jointure et
filtrage ») : une valeur calculée à la main, comparée à la réponse de l'API.

---

## 9. État actuel

| Élément | État |
| --- | --- |
| Vue `v_session_metrics` + `SqlMetricsQueryService` (indicateurs, séries, sessions, détail) | ✅ implémentés et testés |
| Vues `v_daily_activity`, `v_tool_usage`, `v_data_quality` | 🟡 créées par la migration `0002`, **aucun service de lecture ne les interroge encore** |
| Endpoints `/metrics/*`, `/sessions/*` | 🟡 exposés, mais ils renvoient les fixtures de `interfaces/api/fixtures.py` (I4.1) — le câblage arrive avec I4.6 / I4.7 |
| Chiffres sur données réelles | ⬜ nécessite un mapping de source importé (I2.11) |

Les formules ci-dessus décrivent le code réellement écrit ; ce qui manque, c'est le fil entre la
route HTTP et ce code.
