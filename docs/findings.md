# Trois observations chiffrées tirées des données

Trois faits mesurés sur des traces réelles, avec de quoi les **refaire soi-même**. Aucun chiffre
n'est saisi à la main : tous sortent de
[`scripts/findings_tracelab.py`](../scripts/findings_tracelab.py), qui recalcule les numérateurs,
les dénominateurs et les contrôles de cohérence.

## Périmètre commun

| | |
| --- | --- |
| Source | **TraceLab** — [`uw-syfi/TraceLab`](https://github.com/uw-syfi/TraceLab), release **`v0.0.1`** (2026-06-22) |
| Asset | `syfi_coding_trace.jsonl.gz`, SHA256 `9d265eae…0b4e6b` (vérifié au téléchargement) |
| Extrait | 1 session sur 32, règle déterministe `sha1(session_id) % 32 == 0` — sessions **entières** |
| Volume | **128 sessions** (83 Claude Code · 45 Codex), **14 045 rounds**, **16 modèles distincts** |
| Période couverte | 2025-10-01 → 2026-06-04 (horodatages `timing_events`) |
| Licence des données | CC BY 4.0 |

Reproduire l'extrait puis les chiffres :

```bash
make data-tracelab                    # release épinglée, SHA256 vérifié, échantillonnage déterministe
python scripts/findings_tracelab.py   # réaffiche les trois observations
```

Une ligne du fichier source = **un aller-retour avec le modèle** (« round »), avec sa comptabilité
de tokens et ses appels d'outils imbriqués — voir [`data/README.md`](../data/README.md).

---

## Observation 1 — Chez Claude Code, 91,7 % des tokens d'entrée sont lus depuis le cache

| Mesure | Valeur |
| --- | --- |
| Tokens d'entrée, sessions Claude | **1 615 941 466** |
| … lus depuis le cache | **1 481 935 950** → **91,7 %** |
| … écrits dans le cache | 133 811 680 → 8,3 % |
| … hors cache | 193 836 → **0,012 %** |
| Rounds lisant le cache | **6 657 / 6 752** → **98,6 %** |

Les trois postes se somment exactement au total : le script le vérifie (`somme == total : True`).

**Ce que ça dit.** Le contexte d'un agent de code est presque intégralement re-servi depuis le
cache du fournisseur : le contenu réellement neuf à chaque tour est marginal. Une lecture de coût
qui ignorerait le cache surestimerait massivement la facture.

**Ce que ça dit sur l'outil.** Les 45 sessions Codex n'exposent **aucune** comptabilité de cache :
le champ n'existe pas dans leurs enregistrements. C'est exactement le cas que le principe
« [`NULL` n'est pas `0`](data/indicators.md) » protège — afficher « 0 % de cache » pour Codex
serait faux ; AgentScope affiche « non disponible » et l'indicateur reste **non comparable** entre
les deux fournisseurs.

**Reproduire** — dans le dashboard, une fois l'import câblé : filtre `source = tracelab`,
`agent = claude`, aucune borne de date, carte « Taux d'utilisation du cache ». En SQL :

```sql
SELECT SUM(cached_tokens) * 1.0 / NULLIF(SUM(prompt_tokens), 0) AS cache_hit_ratio
FROM v_session_metrics
WHERE source_name = 'tracelab' AND agent_name = 'claude';
```

---

## Observation 2 — 92,9 % des tokens d'entrée sont du contexte rejoué, et l'entrée pèse 378 fois la sortie

| Mesure | Valeur |
| --- | --- |
| Tokens d'entrée (toutes sessions) | **2 515 865 816** |
| … contexte rejoué (`prefix_tokens`) | **2 337 354 446** → **92,9 %** |
| … contenu nouveau (`newly_append_tokens`) | 178 511 370 → 7,1 % |
| Tokens de sortie | **6 658 475** |
| Ratio entrée / sortie | **378 : 1** (Claude **448 : 1** · Codex **295 : 1**) |

Là encore, `prefix + nouveau == total` est vérifié par le script.

**Ce que ça dit.** Un agent de code passe l'essentiel de sa consommation à **relire son propre
contexte**. Ce que le modèle écrit ne représente que 0,26 % du volume de tokens échangés. Un
tableau de bord qui n'afficherait qu'un « total de tokens » masquerait cette structure : c'est
pourquoi l'indicateur est **ventilé** entrée / sortie / cache
([`data/indicators.md`](data/indicators.md) §3.3).

**Reproduire** — filtre `source = tracelab`, sans autre filtre ; comparer les cartes
« tokens d'entrée » et « tokens de sortie ». En SQL :

```sql
SELECT SUM(prompt_tokens) AS entree,
       SUM(completion_tokens) AS sortie,
       SUM(prompt_tokens) * 1.0 / NULLIF(SUM(completion_tokens), 0) AS ratio
FROM v_session_metrics
WHERE source_name = 'tracelab';
```

---

## Observation 3 — Le taux d'erreur global (4,3 %) masque un écart de 1 à 40 entre outils

| Mesure | Valeur |
| --- | --- |
| Appels d'outils | **15 998** |
| En erreur | **694** → **4,3 %** |
| Claude Code | 6 055 appels · 222 erreurs → **3,7 %** |
| Codex | 9 943 appels · 472 erreurs → **4,7 %** |

Par outil (au moins 100 appels) :

| Outil | Appels | Erreurs | Taux |
| --- | ---: | ---: | ---: |
| `shell` | 274 | 67 | **24,5 %** |
| `write_stdin` | 2 414 | 129 | 5,3 % |
| `Bash` | 3 143 | 167 | 5,3 % |
| `exec_command` | 6 479 | 271 | 4,2 % |
| `Edit` | 762 | 16 | 2,1 % |
| `Read` | 1 244 | 24 | 1,9 % |
| `apply_patch` | 651 | 4 | **0,6 %** |
| `TaskUpdate` | 218 | 1 | 0,5 % |
| `Grep` · `Write` · `TaskCreate` | 157 · 120 · 117 | 0 | **0,0 %** |

**Ce que ça dit.** Les deux écarts intéressants ne sont pas entre fournisseurs (3,7 % contre
4,7 %, peu significatif) mais **entre outils** : `shell` échoue 40 fois plus souvent
qu'`apply_patch`. Les outils qui exécutent des commandes échouent ; ceux qui lisent ou écrivent
des fichiers presque jamais. Un chiffre global de 4,3 % n'aurait rien appris.

**Ce que ça dit sur l'outil.** C'est la justification directe de la vue `v_tool_usage`, qui
agrège `n_calls`, `n_errors` et `error_rate` **par outil et par source**, plutôt qu'un taux
unique. Attention à la comparaison : les noms d'outils ne sont pas normalisés entre fournisseurs
(`Bash` chez l'un, `shell` / `exec_command` chez l'autre) — les rapprocher relèverait d'un choix
de mapping, pas de la vue.

**Reproduire** — écran « Répartition des outils », filtre `source = tracelab`. En SQL :

```sql
SELECT tool_name, n_calls, n_errors, error_rate
FROM v_tool_usage
WHERE source_name = 'tracelab' AND n_calls >= 100
ORDER BY error_rate DESC;
```

---

## En complément — la distribution des sessions justifie la médiane

| Rounds par session | Valeur |
| --- | --- |
| Minimum | 1 |
| **Médiane** | **16** |
| Moyenne | 109,7 |
| p90 | 303 |
| Maximum | **2 015** |

La moyenne vaut près de **sept fois** la médiane : une poignée de sessions très longues tire tout
vers le haut. C'est la raison pour laquelle l'indicateur de durée est une **médiane** et pas une
moyenne ([`data/indicators.md`](data/indicators.md) §3.7), et pourquoi la troisième visualisation
du dashboard est une **distribution** et non une valeur unique.

---

## Limites

- Ces chiffres portent sur l'**extrait** (1 session sur 32), pas sur le jeu complet
  (357 161 rounds scannés). L'échantillonnage retient des sessions entières et déterministes, mais
  reste un échantillon.
- Ils sont calculés **directement sur le fichier source**, par le script ci-dessus, et non par le
  parcours d'import de l'application : le câblage API ↔ base est en cours (I4.2 / I4.6) et le
  mapping TraceLab n'est pas encore écrit (I2.11). Les requêtes SQL données dans chaque
  observation sont donc la **vérification à faire** une fois ces deux issues fusionnées — les
  valeurs doivent alors coïncider avec celles de ce document. Un écart signifierait un défaut de
  mapping, et c'est précisément ce qu'on veut pouvoir détecter.
- Les noms de colonnes cibles (`prompt_tokens`, `cached_tokens`, `agent_name`…) supposent le
  mapping TraceLab décrit dans [`data/mappings/`](data/mappings/) — à confirmer quand la fiche
  sera écrite.

---

## Outils IA et composants réutilisés

**Outils IA employés pendant le développement** — assistance à la rédaction de code, de tests et
de documentation, avec relecture humaine et revue de PR sur chaque contribution :
**Claude Code** (Anthropic). *Chaque membre complète ici les outils qu'il a réellement utilisés.*

**Composants externes réutilisés** — tous open source, aucun code recopié :

| Domaine | Composants |
| --- | --- |
| Backend | FastAPI, Uvicorn, Pydantic + pydantic-settings, SQLAlchemy 2, Alembic, psycopg, httpx, pandas, pyarrow, DuckDB |
| Qualité backend | pytest (+ cov, asyncio), ruff, mypy, **import-linter** |
| Frontend | React, TanStack Router, TanStack Query, Zustand, React Hook Form, zod, Tailwind CSS, clsx / tailwind-merge |
| Qualité frontend | Vite, Vitest, Testing Library, MSW, ESLint (+ **eslint-plugin-boundaries**), Prettier, orval, TypeScript |
| Données | jeu **TraceLab** (SyFI Lab, University of Washington) — CC BY 4.0, cité et non redistribué hors fixture de test |

Les versions exactes sont dans [`backend/pyproject.toml`](../backend/pyproject.toml) et
[`frontend/package.json`](../frontend/package.json).
