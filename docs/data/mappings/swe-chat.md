# Mapping SWE-chat JSONL

## Version

- Mapping : `swe-chat-jsonl`, version 1
- Format : JSONL (produit par `scripts/swe_chat_extract.py` — aplatissement de la
  table Parquet `conversations`)
- Dataset : `SALT-NLP/SWE-chat` (HF), **gated**, licence **ODC-BY**
- Definition executable : `swe-chat.json`
- Fixture de verification : `backend/tests/fixtures/swe_chat/sample.jsonl`
  (2 sessions, schema reel reproduit)

## Ce qu'est une ligne

Le dataset est multi-tables (Parquet). On n'utilise que **`conversations`** :
**une ligne = un tour** (`turn`). `sessions` et `repositories` sont jointes en amont
par le script d'extraction et recopiees sur chaque ligne (`agent`, `repository`).

`turn_type` distingue la nature du tour : `user_prompt`, `assistant_thinking`,
`assistant_response`, `tool_use`, `tool_result`, `progress`, `file_snapshot`,
`system_event`…

## Correspondances

| Entite cible | `turn_type` retenu | Champ source | Champ cible | Transformation |
| --- | --- | --- | --- | --- |
| session | (tous) | `session_id` | `external_id` | identite, requis |
| session | | `agent` | `agent_name` | identite (`Claude Code`, `Codex`, `OpenCode`, `Agent`) |
| session | | `repository` | `repository_name` | identite |
| session | | `started_at` / `ended_at` | — | deduits par le normaliseur (enveloppe des appels) |
| model_call | `assistant_response` | `turn_number` | `sequence` | `to_int` |
| model_call | | `coalesce(model, agent)` | `model_name` | requis ; `model` sinon `agent` |
| model_call | | `output_tokens` | `completion_tokens` | `to_int` |
| model_call | | `cache_read_input_tokens` | `cached_tokens` | `to_int` |
| model_call | | `timestamp` | `started_at` / `ended_at` | datetime (instant unique) |
| tool_call | `tool_use` | `tool_name` | `tool_name` | identite, requis |
| tool_call | | `turn_number` | `model_call_sequence` | `to_int` |
| tool_call | | `timestamp` | `started_at` / `ended_at` | datetime |

`model` est `NULL` sur **tous** les tours des agents OpenCode et Codex. Plutot que
d'ecarter ces appels, `model_name` retombe sur l'`agent` (`coalesce`) : on garde
les tokens de la session, la dimension « modele » vaut alors `OpenCode` / `Codex`
(coût estimé indisponible pour ces libellés, faute de tarif).

## Ce que la source ne fournit pas (bien)

- **`prompt_tokens` par tour** : `input_tokens` vaut `0` ou `1` sur presque tous les
  tours — non exploitable. Seul `output_tokens` (sur `assistant_response`) est fiable.
  Les totaux reels sont `session_input_tokens` / `session_output_tokens` (non mappes,
  le modele cible n'a pas de champ « tokens de session »).
- **`cost_usd`** : absent.
- **`timestamp`** : souvent `NULL` pour les agents Codex et OpenCode → ces sessions
  restent sans duree (`missing_info` le signale).
- **`model_call_sequence`** des `tool_call` : approxime par `turn_number` du tour
  d'outil, pas par un vrai rattachement a l'appel modele parent.
- **sessions degenerees** : le dump contient des fragments 100 % `user_prompt`
  (ni appel modele ni appel d'outil). `scripts/swe_chat_extract.py` les ecarte a
  l'extraction (`requires_model_or_tool_activity`, cf. `data/README.md`).

## Verification bout-en-bout

`backend/tests/unit/test_swe_chat_mapping.py` charge le JSON versionne, lit la
fixture avec `JsonlReader`, et verifie : 2 sessions avec agent + depot, les
`model_call` sur `assistant_response` (`model_name` = `model` sinon `agent`),
`completion_tokens` et `cached_tokens` renseignes, les `tool_call` sur `tool_use`,
aucun rejet, et
l'enveloppe temporelle deduite quand les tours sont horodates.
