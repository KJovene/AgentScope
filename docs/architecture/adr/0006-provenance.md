# ADR-0006 — Provenance : chaque ligne normalisée remonte à son enregistrement brut

- **Statut :** acceptée
- **Date :** 2026-09-07
- **Décideurs :** WS-domain + WS-ingestion

## Contexte

La traçabilité est explicitement notée (critère « modèle de données, normalisation, traçabilité »).
Deux situations la rendent indispensable :

- Un chiffre du dashboard paraît faux. Sans lien vers la donnée d'origine, impossible de trancher
  entre une erreur de mapping, une valeur absente de la source et un bug d'agrégation.
- Un import est partiel. « 120 lignes importées, 7 rejetées » n'a de valeur que si l'on peut
  **montrer** les 7 lignes et dire pourquoi.

Par ailleurs, un mapping corrigé doit pouvoir être rejoué sans redemander le fichier à l'utilisateur.

## Décision

**Tout enregistrement lu est persisté tel quel** dans `raw_record` : `payload_json` (le contenu
d'origine), `record_sha256`, `record_index` (position 0-based dans le fichier), rattaché à un
`import_batch`.

Chaque ligne normalisée — `session`, `model_call`, `tool_call` — porte :

- une clé étrangère **`raw_record_id`** vers l'enregistrement dont elle est issue ;
- son appartenance à l'`import_batch` qui l'a produite.

Les enregistrements refusés sont conservés dans **`import_reject`** avec leur `payload_json`, leur
`record_index` et un `reason_code` issu d'un vocabulaire contrôlé (`unparseable_record`,
`missing_required_field`, `transform_failed`, `unknown_target_field`, `duplicate_in_file`,
`schema_violation`) plus un `reason_detail` lisible.

**La rétention du brut est configurable** (I1.7). Par défaut, tout est conservé ; l'option ne sert
qu'à borner les très gros extraits — dans ce cas on garde les **hashs** et les **payloads des
rejets**, jamais moins.

L'idempotence repose sur la même chaîne : `import_batch.file_sha256` unique par source, clé naturelle
par entité (`external_id` fourni par la source, sinon synthétisé par
`sha1(source_id | entity | key_fields)`), et `bulk_upsert(on_conflict="ignore")`. Réimporter le même
fichier ne crée aucun doublon.

## Alternatives écartées

| Alternative | Raison du rejet |
| --- | --- |
| Ne conserver que les données normalisées | Rend impossibles l'audit d'un chiffre et le rejeu d'un mapping corrigé ; le fichier source n'est pas toujours encore disponible. |
| Garder le fichier source sur disque, sans découpage | Donne une provenance au niveau du fichier, pas de la ligne : on ne peut ni pointer un enregistrement précis, ni le hasher, ni le relier à une session. |
| Ne journaliser les rejets qu'en compteur | Un compteur ne s'explique pas. « 7 rejets » sans les 7 lignes ne permet aucune correction. |

## Conséquences

- **Positives** — Depuis la vue session détaillée, on remonte jusqu'à l'enregistrement d'origine.
  Un mapping corrigé se rejoue sur les `raw_record` déjà stockés, sans re-téléversement. Les
  compteurs de bilan (`imported`, `duplicate`, `rejected`, `missing_info`) sont adossés à des lignes
  réelles, donc démontrables.
- **Négatives assumées** — Le stockage vaut environ **deux fois** la taille de la source
  (brut + normalisé). C'est le motif de l'option de rétention.
- **Sécurité** — `payload_json` peut contenir des données sensibles. Il n'est **jamais** transmis à
  un fournisseur IA sans passer par `SensitiveFilter` (ADR-0005), et n'est exposé que dans la vue de
  détail, à la demande.
- **Règle liée** — Une valeur absente reste `NULL` et n'est **jamais** convertie en `0` : la
  provenance ne servirait à rien si la normalisation inventait des valeurs.

## Vérification

Depuis une ligne normalisée, un test remonte à son `raw_record` et à son `import_batch` (I1.7) ;
un réimport du même fichier produit 0 ligne dupliquée et des compteurs identiques (I2.7).

## Références

`docs/PLAN.md` §4, §5.4 · `docs/data/relational-model.md` · [ADR-0004](0004-contrat-de-mapping.md) ·
[ADR-0005](0005-abstraction-ia.md)
