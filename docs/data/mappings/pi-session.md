# Mapping pi-coding-agent JSONL

## Identité de la source

- Mapping : `pi-session-jsonl`, version 1
- Format : JSONL — export natif de session du [pi coding agent](https://pi.dev)
  ([format documenté ici](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/session.md))
- Licence / accès : fichiers exportés localement par l'utilisateur, pas de dataset public
- Definition executable : `pi-session.json`
- **Prérequis avant import : conversion**, voir ci-dessous — ce mapping ne s'applique
  jamais à un export "pi" brut

## Ce qu'est une ligne

Le fichier natif "pi" est un **journal d'événements** : une ligne = un événement
(`type: "session"`, `model_change`, `thinking_level_change`, `message`, …), relié au
précédent par `parentId`. Seul l'événement racine (`type: "session"`) porte
l'identifiant réel de la session — aucun autre événement ne le référence.

Le normaliseur d'AgentScope (`application/mapping/normalizer.py`) construit une
session **indépendamment pour chaque ligne** ; il n'a pas de mémoire inter-lignes et
ne peut donc pas suivre une chaîne `parentId` sur tout le fichier. Un export "pi" brut
n'est donc **pas directement mappable** : quasiment toutes les lignes seraient
rejetées (`external_id` manquant).

**`scripts/convert_pi_session_jsonl.py`** résout ce problème en amont : il suit la
chaîne `parentId` de chaque événement jusqu'à l'événement `session` racine, et
réécrit chaque ligne avec un champ `session_id` explicite ajouté (comme le fait déjà
TraceLab/SWE-chat nativement). Il ignore aussi silencieusement les lignes JSON
illisibles (troncatures d'export, collage accidentel de contenu XML observé dans un
fichier réel).

```bash
python scripts/convert_pi_session_jsonl.py session.jsonl --out session.flat.jsonl
```

C'est le fichier **converti** (`session.flat.jsonl`) qu'on importe avec ce mapping —
jamais le fichier "pi" original.

L'entité `model_call` est construite à partir des tours **assistant** (`type:
"message"`, `message.role: "assistant"`) : c'est là, et pas sur les événements
`model_change`, que vivent le modèle, le fournisseur et l'usage de tokens réels de
l'appel. `tool_call` est extrait des éléments `message.content[*]` de type
`"toolCall"` de ces mêmes tours.

## Correspondances

| Entité cible | Filtre (`where`) | Champ source | Champ cible | Transformation |
| --- | --- | --- | --- | --- |
| session | (toutes lignes) | `session_id` | `external_id` | identité, requis |
| session | | `started_at` / `ended_at` | — | déduits par le normaliseur (enveloppe des appels) |
| model_call | `type=message`, `message.role=assistant` | `message.model` | `model_name` | requis |
| model_call | | `message.provider` | `provider` | identité |
| model_call | | `message.usage.input` | `prompt_tokens` | `to_int` |
| model_call | | `message.usage.output` | `completion_tokens` | `to_int` |
| model_call | | `message.usage.cost.total` | `cost_usd` | `to_float` |
| model_call | | `timestamp` | `started_at` / `ended_at` | datetime (instant unique) |
| tool_call | `message.content[].type=toolCall` | `name` | `tool_name` | identité, requis |
| tool_call | | `timestamp` | `started_at` | datetime (hérité de la ligne parente) |

## Champs non mappés (`unmapped_fields`)

`cwd`, `parentId`, `thinkingLevel`, `modelId`, `stopReason`, `responseId`, `api` — pas
de champ cible correspondant (`parentId`/`thinkingLevel`/`modelId` sont consommés par
le script de conversion ou par les événements `model_change`/`thinking_level_change`,
qui ne produisent eux-mêmes aucune ligne : seuls les tours `message` assistant
alimentent `model_call`).

## Ce que la source ne fournit pas

- **`cached_tokens`** : le format sépare `usage.input` (tokens non mis en cache) de
  `usage.cacheRead` — le total réel serait leur somme, mais le langage de mapping ne
  sait combiner que **un seul** champ source par transformation (pas d'addition).
  Mapper `usage.cacheRead` directement dans `cached_tokens` viole l'invariant du
  domaine (« cached_tokens ne peut pas dépasser prompt_tokens », `prompt_tokens`
  valant alors `usage.input` seul) — le champ est donc laissé non mappé plutôt que
  produire une valeur incohérente.
- **`agent_name` / `repository_name`** : absents du format (le `cwd` de l'événement
  `session` est un chemin de poste de travail, pas un nom de dépôt exploitable).
- **`model_call_sequence`** des `tool_call` : pas de rattachement explicite à
  l'appel modèle parent dans le format source.

## Vérification

Vérifié manuellement de bout en bout sur un export réel (17 lignes, dont 2 lignes
finales corrompues ignorées par le convertisseur) via `POST /mappings/{id}/preview`
puis `POST /imports` : **10 lignes produites, 0 rejet** (1 session, 3 `model_call`,
6 `tool_call`), visibles dans le dashboard et la liste des sessions.

Pas encore de fixture ni de test automatisé backend pour cette source (contrairement
à TraceLab/SWE-chat) — à ajouter si `pi-coding-agent` devient une source régulière.

## Comparabilité

Le coût (`cost_usd`) est directement fourni par la source, contrairement à
TraceLab/SWE-chat qui dépendent de la grille tarifaire interne (`model_pricing`) — les
deux valeurs ne sont pas calculées de la même façon et peuvent diverger légèrement
pour un même modèle. `cached_tokens` étant systématiquement `NULL` ici, tout ratio de
cache calculé au dashboard affichera « non disponible » pour cette source.
