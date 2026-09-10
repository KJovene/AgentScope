# Mapping TraceLab JSONL

## Version

- Mapping: `tracelab-jsonl`, version 1
- Format: JSONL
- Dataset: TraceLab `v0.0.1`, extrait dans `backend/tests/fixtures/tracelab/sample.jsonl`
- Bilan: 103 rounds, 2 sessions, 72 rounds Claude et 31 rounds Codex
- Definition executable: `tracelab.json`

## Correspondances

| Entite cible | Champ source | Champ cible | Transformation |
| --- | --- | --- | --- |
| session | `session_id` | `external_id` | identite, requis |
| session | `provider` | `agent_name` | identite |
| session | `started_at` / `ended_at` | — | deduits par le normaliseur (enveloppe des appels) |
| model_call | `round_index` | `sequence` | `to_int` |
| model_call | `model` | `model_name` | identite, requis |
| model_call | `provider` | `provider` | identite |
| model_call | `input_tokens_total` | `prompt_tokens` | `to_int` |
| model_call | `output_tokens` | `completion_tokens` | `to_int` |
| model_call | `claude_cache_read_input_tokens` | `cached_tokens` | `to_int` (rounds Claude ; NULL cote Codex) |
| model_call | `timing_events.0.timestamp` | `started_at` | datetime |
| model_call | `timing_events.-1.timestamp` | `ended_at` | datetime (dernier evenement du round) |
| tool_call | `tool_name` | `tool_name` | identite, requis |
| tool_call | `round_index` | `model_call_sequence` | `to_int` |
| tool_call | `is_error` | `status` | `map_enum`: `false` -> `success`, `true` -> `error` |
| tool_call | `is_error` | `error_type` | `map_enum`: `true` -> `tool_error` |
| tool_call | `input_chars` | `input_bytes` | `to_int` |
| tool_call | `result_chars` | `output_bytes` | `to_int` |
| tool_call | `emitted_at` | `started_at` | datetime |
| tool_call | `result_at` | `ended_at` | datetime |

Les timestamps vivent dans le tableau `timing_events[]` (ordre chronologique) : le
segment entier d'un chemin `from` indexe la liste, negatif compris
(`timing_events.-1.timestamp`).

Le mapping ne borne pas la session (iteration par round : on ne voit jamais sa fin). Le
normaliseur **deduit l'enveloppe** : `session.started_at` / `ended_at` = min / max des
`started_at` / `ended_at` des appels rattaches. Une borne mappee explicitement, si une
autre source en fournit une, serait conservee. `duration_ms` et
`median_session_duration_ms` sont donc disponibles pour TraceLab.

Le `sequence` des `tool_call` n'est pas mappe : `tool_index` est reinitialise a chaque
round et entrerait en collision avec l'unicite `(session_id, sequence)` de la table. Le
normaliseur attribue donc un ordinal positionnel par session (ordre du fichier). Le
rattachement au round reste porte par `model_call_sequence` (= `round_index`).

Les champs non mappes sont listes dans `tracelab.json`. Ils restent disponibles dans la
provenance brute. `cost_usd` n'est pas fourni par TraceLab (comptabilite tokens
uniquement) : les indicateurs de cout sont « non disponibles » pour cette source.

## Verification bout-en-bout

Le test `backend/tests/unit/test_normalizer.py::test_bout_en_bout_tracelab` charge cette definition JSON, lit l'extrait reel avec le lecteur JSONL, puis verifie:

- 2 sessions TraceLab et 103 appels modele;
- des appels d'outil rattaches a une session connue;
- au moins un appel d'outil en erreur;
- aucun rejet de normalisation.

Le test `test_tracelab_reimport_zero_doublon` verifie en plus que la repetition des memes enregistrements ne cree pas de nouvelles entites.
