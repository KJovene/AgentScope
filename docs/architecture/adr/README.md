# Architecture Decision Records

Décisions courtes : contexte / décision / conséquences. Une décision par fichier,
`NNNN-titre-court.md`, jamais réécrite (on ajoute une nouvelle ADR qui remplace).

> Les six premières ADR reprennent et développent `PLAN.md` §2, figé au cadrage du Jour 1 (I0.8).

| # | Titre | Statut |
| --- | --- | --- |
| [0001](0001-stack-technique.md) | Stack technique (Python/FastAPI + React) | acceptée · 2026-09-07 |
| [0002](0002-monolithe-modulaire-clean-architecture.md) | Monolithe modulaire + Clean Architecture | acceptée · 2026-09-07 |
| [0003](0003-base-de-donnees.md) | Base de données (SQLite par défaut, Postgres en option) | acceptée · 2026-09-07 |
| [0004](0004-contrat-de-mapping.md) | Contrat de mapping (JSON versionné, transformations whitelistées) | acceptée · 2026-09-07 |
| [0005](0005-abstraction-ia.md) | Abstraction IA (`LLMProvider` + adaptateurs, config-driven) | acceptée · 2026-09-07 |
| [0006](0006-provenance.md) | Provenance (`raw_record`, rétention configurable) | acceptée · 2026-09-07 |

## Ajouter une ADR

1. Numéro suivant, nom de fichier `NNNN-titre-court.md`.
2. Sections : **Statut · Date · Décideurs · Contexte · Décision · Alternatives écartées ·
   Conséquences · Vérification · Références**.
3. Une décision qui en remplace une autre ne la modifie pas : elle la cite, et l'ancienne passe en
   statut « remplacée par ADR-NNNN ».
4. Ajouter la ligne dans le tableau ci-dessus.
