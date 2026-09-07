# ADR-0004 — Contrat de mapping : JSON versionné et transformations whitelistées

- **Statut :** acceptée
- **Date :** 2026-09-07
- **Décideurs :** WS-ingestion + WS-ai, arbitrée au cadrage du Jour 1

## Contexte

AgentScope doit importer des fichiers dont la structure **n'est pas connue à l'avance**, avec l'aide
d'un modèle de langage qui propose une correspondance entre les champs de la source et le modèle
cible. La solution la plus rapide serait de demander au modèle d'écrire le code de transformation et
de l'exécuter. Elle est inacceptable : elle revient à exécuter du code arbitraire produit par un
système non déterministe, sur des fichiers fournis par un tiers.

Il faut donc une représentation du mapping qui soit **assez expressive pour couvrir les sources
réelles, et assez fermée pour être validée avant exécution**.

## Décision

Le mapping est un **document JSON versionné** (structure complète en `docs/PLAN.md` §5.1), validé en
deux temps : d'abord par **JSON Schema**, puis par une validation sémantique (les entités et champs
cibles existent, les arguments de transformation sont cohérents).

Trois règles fermées :

1. **Les transformations sont un registre whitelisté** de fonctions nommées :
   `identity`, `to_int`, `to_float`, `to_iso8601`, `lower`, `upper`, `trim`, `json_stringify`,
   `const`, `coalesce`, `map_enum`, `split`, `regex_extract`, `cents_to_usd`, `ms_to_s`.
   Un mapping référençant un nom absent du registre est **rejeté à la validation**.
2. **Aucune expression n'est évaluée comme du code.** Les filtres d'itération sont des triplets
   `[champ, op, valeur]` avec `op ∈ eq|ne|in|exists|gt|lt`. Pas d'`eval`, pas d'`exec`, pas de
   mini-langage à interpréter.
3. **Aucun code produit par l'IA n'est exécuté.** La sortie du modèle est une *proposition*
   (`MappingProposal`), convertie vers ce contrat, validée, puis présentée à l'utilisateur ; elle
   n'est persistée qu'après cette validation (`POST /mappings`).

Le comportement en cas d'échec est déclaré **par champ** (`on_error` ∈ `reject | null | skip`), ce
qui rend l'import partiel explicable plutôt que silencieux. Les mappings sont versionnés
(`(name, version)` unique) et réutilisables d'un import à l'autre.

## Alternatives écartées

| Alternative | Raison du rejet |
| --- | --- |
| Code Python généré par le modèle, puis exécuté | Exécution de code arbitraire : ni auditable, ni reproductible, ni sûr. Rédhibitoire. |
| Mini-langage d'expressions (JSONPath, jq, template) | Demande un parser et un évaluateur à écrire et à durcir — du travail en plus et une surface d'attaque en plus, pour une expressivité dont on n'a pas besoin en v1. |
| Un mapping codé en dur par source connue | Ne répond pas à l'exigence : la correction se fera sur une source que nous n'avons jamais vue. |

## Conséquences

- **Positives** — Un mapping est un document : versionnable, diffable, relisible en PR, rejouable à
  l'identique. Il se **corrige à la main** et fonctionne sans IA, ce qui rend le parcours principal
  (P0) indépendant de l'agent (P1). La validation avant exécution permet de refuser un mapping
  incohérent plutôt que de produire de faux chiffres.
- **Négatives assumées** — L'expressivité est bornée. Une source exigeant une transformation absente
  du registre impose d'**ajouter cette transformation au registre**, avec son test, via une PR. Ce
  coût est délibéré : il maintient l'ensemble des transformations possibles fini et connu.
- **Périmètre v1** — Un fichier produit une ou plusieurs entités issues **des mêmes enregistrements**
  (imbrication JSON). La jointure multi-fichiers est hors périmètre.

## Vérification

Un mapping invalide est refusé par la validation avec un message exploitable ; `POST
/mappings/{id}/preview` rejoue le mapping en dry-run sur un échantillon et renvoie lignes et rejets
simulés.

## Références

`docs/PLAN.md` §5.1, §5.4 · `backend/agentscope/application/mapping/` · [ADR-0005](0005-abstraction-ia.md)
