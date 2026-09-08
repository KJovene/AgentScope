# Mapping SWE-chat JSONL

## Version

- Mapping: `swe-chat-jsonl`, version 1
- Format: JSONL
- Fixture de verification: `backend/tests/fixtures/swe_chat/sample.jsonl`
- La fixture contient 3 tours, 2 sessions, 2 depots et 2 appels outil.
- Definition executable: `swe-chat.json`

## Correspondances

| Entite cible | Champ source | Champ cible | Transformation |
| --- | --- | --- | --- |
| session | `session_id` | `external_id` | identite, requis |
| session | `agent` | `agent_name` | identite |
| session | `repository` | `repository_name` | identite |
| model_call | `turn_index` | `sequence` | `to_int` |
| model_call | `model` | `model_name` | identite, requis |
| model_call | `provider` | `provider` | identite |
| model_call | `input_tokens` | `prompt_tokens` | `to_int` |
| model_call | `output_tokens` | `completion_tokens` | `to_int` |
| tool_call | `tool_index` | `sequence` | `to_int` |
| tool_call | `name` | `tool_name` | identite, requis |
| tool_call | `turn_index` | `model_call_sequence` | `to_int` |
| tool_call | `input_bytes` | `input_bytes` | `to_int` |
| tool_call | `output_bytes` | `output_bytes` | `to_int` |

Les champs hors perimetre sont listes dans `swe-chat.json` et restent disponibles dans la provenance brute.

## Verification bout-en-bout

Le test `backend/tests/unit/test_swe_chat_mapping.py::test_bout_en_bout_swe_chat` charge le JSON versionne, lit la fixture avec `JsonlReader`, puis verifie:

- 2 sessions avec leur depot rattache;
- 3 appels modele et leurs tokens;
- 2 appels outil rattaches a la bonne session et au bon tour;
- aucun rejet de normalisation.
