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
| model_call | `round_index` | `sequence` | `to_int` |
| model_call | `model` | `model_name` | identite, requis |
| model_call | `provider` | `provider` | identite |
| model_call | `input_tokens_total` | `prompt_tokens` | `to_int` |
| model_call | `output_tokens` | `completion_tokens` | `to_int` |
| tool_call | `tool_index` | `sequence` | `to_int` |
| tool_call | `tool_name` | `tool_name` | identite, requis |
| tool_call | `round_index` | `model_call_sequence` | `to_int` |
| tool_call | `is_error` | `status` | `map_enum`: `false` -> `success`, `true` -> `error` |
| tool_call | `is_error` | `error_type` | `map_enum`: `true` -> `tool_error` |
| tool_call | `input_chars` | `input_bytes` | `to_int` |
| tool_call | `result_chars` | `output_bytes` | `to_int` |

Les champs non mappes sont listes dans `tracelab.json`. Ils restent disponibles dans la provenance brute et ne sont pas necessaires aux indicateurs v1.

## Verification bout-en-bout

Le test `backend/tests/unit/test_normalizer.py::test_bout_en_bout_tracelab` charge cette definition JSON, lit l'extrait reel avec le lecteur JSONL, puis verifie:

- 2 sessions TraceLab et 103 appels modele;
- des appels d'outil rattaches a une session connue;
- au moins un appel d'outil en erreur;
- aucun rejet de normalisation.

Le test `test_tracelab_reimport_zero_doublon` verifie en plus que la repetition des memes enregistrements ne cree pas de nouvelles entites.
