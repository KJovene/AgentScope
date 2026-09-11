# Données

Ce dossier **ne contient pas** d'extraits de datasets par défaut : `.gitignore` exclut tout sauf
ce fichier. N'ajouter un extrait au dépôt que si ses conditions de redistribution le permettent
explicitement.

Deux fichiers de test seulement sont commités, et pour des raisons différentes :

| Fichier | Nature | Pourquoi il peut être commité |
| --- | --- | --- |
| `backend/tests/fixtures/tracelab/sample.jsonl` (2 sessions, 185 Kio) | **données réelles** extraites de TraceLab | TraceLab est sous **CC BY 4.0**, qui autorise la redistribution avec attribution — voir le [`NOTICE.md`](../backend/tests/fixtures/tracelab/NOTICE.md) qui l'accompagne |
| `backend/tests/fixtures/swe_chat/sample.jsonl` (2 sessions, 9 lignes) | **données fictives**, écrites à la main | reproduit le *schéma* réel de SWE-chat (noms de champs, `turn_type`, jointures) sans aucune donnée du dataset gated. Aucune licence tierce, donc aucun `NOTICE.md` |

C'est la fixture TraceLab que charge `make seed` — c'est-à-dire l'étape d'installation du
[README](../README.md#installation). Aucun téléchargement n'est nécessaire pour voir
l'application fonctionner.

## Sources

| Source | Référence | Format(s) | Version / date de récupération | Méthode de récupération | Sélection de l'extrait |
| --- | --- | --- | --- | --- | --- |
| TraceLab | https://github.com/uw-syfi/TraceLab | JSONL (`.jsonl.gz`) | release **`v0.0.1`**, publiée le 2026-06-22 · récupérée le **2026-09-07** | `make data-tracelab` → `scripts/tracelab_extract.py --fetch`, SHA256 vérifié contre l'empreinte publiée | 1 session sur 32, sessions entières, par provider (voir ci-dessous) |
| SWE-chat | https://huggingface.co/datasets/SALT-NLP/SWE-chat | Parquet multi-tables (`conversations` 1,3 Gio, `sessions`, `repositories`, `checkpoints`, `commits`) + transcripts bruts `transcripts/{session_id}.jsonl` | dataset **gated** (accès à accepter) · licence **ODC-BY** | `make data-swe-chat` → `scripts/swe_chat_extract.py` : `urllib` + `pyarrow`, petites tables en entier, `conversations` lu row-group par row-group en HTTP Range ; nécessite `$HF_TOKEN` | 1 session sur 64, session entière, par agent, **hors fragments dégénérés** (sessions sans aucun tour `assistant_response` ni `tool_use`) — aplati en JSONL (1 ligne = 1 tour de `conversations`) |
| Trace Commons | https://huggingface.co/datasets/trace-commons/agent-traces | `sessions/{harness}/*.jsonl` (formats natifs Claude Code / Codex / …), vue Parquet « 1 ligne = 1 session » avec `trace[]` jusqu'à ~2 500 éléments | _n/a_ | **pas d'intégration** : sert le test « structure inconnue » (I6.11) | _n/a_ |

---

## TraceLab — provenance détaillée (I0.10)

### Ce qu'est le jeu

Traces réelles d'agents de code (Claude Code et Codex) collectées puis **assainies** par le
SyFI Lab de l'University of Washington. Une ligne JSONL = **un aller-retour avec le modèle**
(un « round »), avec sa comptabilité de tokens, une liste ordonnée d'événements
(`timing_events[]`) et les appels d'outils imbriqués (`tools[]`).

### Version retenue et pourquoi

| | |
| --- | --- |
| Release épinglée | **`v0.0.1`** (2026-06-22) |
| Asset | `syfi_coding_trace.jsonl.gz` — 53 601 226 octets |
| SHA256 | `9d265eae69a31cae203848bea936f018148eed7ca8bf56050c5abe96da0b4e6b` |
| Récupéré le | 2026-09-07 |
| Licence données | [CC BY 4.0](https://github.com/uw-syfi/TraceLab/blob/main/LICENSE-DATASET.md) · code Apache-2.0 |

Une release `v0.0.2` (2026-07-24) existe, mais **`v0.0.1` est la seule version dont l'amont
publie l'empreinte SHA256 et les statistiques de référence**. Épingler une version vérifiable
prime sur épingler la plus récente : nos chiffres de test doivent être opposables. À
réévaluer si l'amont documente `v0.0.2`.

> On utilise le **JSONL publié**, pas la base DuckDB ni l'application fournies par le projet —
> conformément à l'énoncé.

### Contenu vérifié

Recomptés le 2026-09-07 sur le fichier téléchargé — **identiques aux chiffres annoncés par
l'amont**, ce qui valide au passage l'intégrité de la récupération :

| Mesure | Valeur |
| --- | ---: |
| Rounds (lignes JSONL) | 357 161 |
| dont `claude` / `codex` | 140 338 / 216 823 |
| Enregistrements d'outils | 432 510 |
| Sessions distinctes | 4 265 |
| Utilisateurs pseudonymes | 43 |
| Projets pseudonymes | 188 |
| Modèles distincts | 24 |
| Période couverte | 2025-09-23 → 2026-06-04 |
| Taille décompressée | 646 754 413 octets (617 Mio) |

### Méthode de sélection de l'extrait

617 Mio ne sont ni commitables ni confortables en développement. La sélection est
**déterministe** — pas de tirage aléatoire, pas de graine : quiconque repart du même fichier
épinglé obtient octet pour octet le même extrait.

1. **Unité de sélection : la session entière.** Toutes les lignes d'une session retenue sont
   conservées. Une session tronquée fausserait la normalisation (rounds orphelins) et tous
   les indicateurs de durée.
2. **Critère :** une session est retenue si `sha1(session_id) % modulo == 0`.
3. **Par provider.** Le critère est appliqué séparément à `claude` et `codex`, pour que les
   deux soient représentés même sur un très petit échantillon.

Deux extraits en découlent :

| Extrait | Commande | Rounds | Sessions | Taille | Suivi par git |
| --- | --- | ---: | --- | ---: | --- |
| **Développement** — `data/tracelab/extract-dev.jsonl` | `make data-tracelab` | 14 045 | 83 `claude` + 45 `codex` | 23 Mio | non (`.gitignore`) |
| **Fixture de test** — `backend/tests/fixtures/tracelab/sample.jsonl` | `make fixtures` | 103 | 1 `claude` + 1 `codex` | 185 Kio | **oui** |

Chaque extrait est accompagné d'un `*.meta.json` qui rejoue son bilan chiffré (règle,
modulo, comptages par provider). L'extrait de développement couvre 16 modèles et
26 utilisateurs pseudonymes — assez pour que le dashboard ait de quoi filtrer.

### Reproduire

```bash
make data-tracelab     # télécharge (53 Mio), vérifie le SHA256, écrit l'extrait de dev
make fixtures          # régénère la fixture commitée
```

Le script refuse d'aller plus loin si l'empreinte ne correspond pas.

### Attribution

> TraceLab — SyFI Lab, University of Washington. Jeu de données sous CC BY 4.0.
> *TraceLab: Characterizing Coding Agent Workloads for LLM Serving*, arXiv:2606.30560.

---

## Règles

- Utiliser le **fichier JSONL publié** de TraceLab, pas la base DuckDB ni l'app fournie.
- Extraits de **taille raisonnable**, représentatifs, sélection documentée.
- Données fictives autorisées **uniquement** pour les tests, jamais dans les dashboards. Une
  fixture fictive dit explicitement qu'elle l'est (cf. SWE-chat ci-dessus).
- Aucune donnée sensible ni secret dans le dépôt.
- Tout extrait de **données réelles** commité s'accompagne d'un `NOTICE.md` portant sa licence et
  son attribution.

## Brancher un extrait sur la stack

Les extraits ne servent à rien tant qu'ils ne sont pas importés. Une fois la stack levée
(`make up && make migrate`) :

| Commande | Ce qu'elle importe |
| --- | --- |
| `make seed` | grille tarifaire + fixture TraceLab commitée — hors ligne |
| `make seed-tracelab-dev` | `data/tracelab/extract-dev.jsonl` (après `make data-tracelab`) |
| `make seed-swe-chat` | `data/swe_chat/extract-dev.jsonl` (après `make data-swe-chat`) |
| `make seed-reset` | vide les données importées puis recharge ce qui est présent |

Chaque cible passe par `scripts/seed_import.py`, donc par l'API REST : mapping enregistré via
`POST /api/v1/mappings`, fichier envoyé à `POST /api/v1/imports`. Réimporter le même fichier ne
crée aucune ligne en double.
