# ADR-0002 — Monolithe modulaire structuré en Clean Architecture

- **Statut :** acceptée
- **Date :** 2026-09-07
- **Décideurs :** WS-platform + WS-domain (lead archi)

## Contexte

Cinq workstreams travaillent en parallèle sur le même dépôt (domaine, ingestion, IA, API/dashboard,
plateforme). Sans frontières explicites, le code des quatre premiers se mélange en quelques jours et
la maintenabilité — 7 points de l'évaluation — s'effondre. À l'inverse, l'application n'a **aucun
besoin de mise à l'échelle indépendante** : un seul utilisateur, en local.

Le critère « IA interchangeable » impose par ailleurs que le cœur métier ne connaisse ni le SDK d'un
fournisseur, ni FastAPI, ni SQLAlchemy.

## Décision

**Un seul déployable** (monolithe), découpé en quatre packages dont les dépendances ne vont que vers
l'intérieur :

```
interfaces/ (API REST)          infrastructure/ (DB, readers, LLM, profiling, config)
          \                                /
           v                              v
              application/ (use cases + PORTS)
                        |
                        v
                   domain/ (entités, règles pures — n'importe RIEN)
```

- `domain/` : entités, value objects, erreurs métier. **Aucun import de framework, ORM, HTTP ou SDK IA.**
- `application/` : use cases et **ports** (interfaces abstraites). N'importe que `domain`.
- `infrastructure/` : implémente les ports (SQLAlchemy, lecteurs de fichiers, adaptateurs LLM, profileur, settings).
- `interfaces/` : adaptateurs entrants (routes FastAPI, DTO Pydantic, injection de dépendances).

Le **câblage** ports ↔ implémentations se fait **uniquement** dans `interfaces/api/dependencies.py`
et `main.py`. Aucun autre module n'instancie une implémentation concrète.

La règle est **vérifiée automatiquement** par `import-linter` (contrats déjà déclarés dans
`backend/pyproject.toml`) : un contrat `layers` pour le sens des dépendances, un contrat `forbidden`
qui interdit à `domain` d'importer `fastapi`, `sqlalchemy`, `pydantic`, `httpx`, `pandas`,
`pyarrow`, `duckdb`.

## Alternatives écartées

| Alternative | Raison du rejet |
| --- | --- |
| Microservices | Aucun besoin d'échelle ou de déploiement indépendant ; coût d'exploitation et de débogage sans contrepartie sur un sprint de quatre jours. |
| Découpage « par framework » (`models/` `views/` `services/`) | Ne crée pas de frontière vérifiable : le métier finit par importer l'ORM, et l'IA cesse d'être remplaçable. |
| Package unique avec conventions de nommage | Une convention non outillée n'est pas une frontière : elle cède à la première urgence du vendredi. |

## Conséquences

- **Positives** — Les use cases se testent sans base de données ni serveur HTTP, en injectant des
  doubles des ports. Remplacer SQLite par PostgreSQL (ADR-0003) ou Anthropic par Ollama (ADR-0005)
  ne touche pas une ligne de `domain` ni de `application`. Les workstreams se synchronisent sur des
  ports figés au Jour 1 (§5.2) plutôt que sur du code en cours d'écriture.
- **Négatives assumées** — Ajouter une capacité coûte trois gestes au lieu d'un : le port, son
  adaptateur, le câblage. Cette cérémonie est acceptée ; elle est le prix de la frontière.
- **Effet CI** — Une PR qui fait importer `infrastructure` depuis `domain` échoue en CI, même si les
  tests passent.

## Vérification

`lint-imports` (I0.11) dans la CI ; `import agentscope.domain` ne tire aucun paquet tiers (I1.1).

## Références

`docs/PLAN.md` §3, §5.2 · `backend/pyproject.toml` (`[tool.importlinter]`) · [ADR-0005](0005-abstraction-ia.md)
