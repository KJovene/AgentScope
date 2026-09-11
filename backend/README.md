# backend

API et cœur métier d'AgentScope (Python 3.12, FastAPI, Clean Architecture).

```
agentscope/
  domain/          # entités & règles pures — n'importe RIEN d'externe
    entities.py · value_objects.py · retention.py · _invariants.py · errors.py
  application/
    ports/         # interfaces abstraites : repositories, unit_of_work, source_reader,
                   # llm_provider, profiler, metrics, data_quality, sources, imports,
                   # mapping_crud, pricing_registry, repository_registry, provenance, workbench
    mapping/       # contrat de mapping, validation, transformations whitelistées, normalizer,
                   # prompt_builder, sensitive_filter, target_schema, file_format
    use_cases/     # import_file, import_queries, manage_mappings,
                   # analyze_unknown_file, chat_about_mapping, preview_mapping
  infrastructure/
    persistence/   # ORM SQLAlchemy, repositories, unit_of_work, migrations Alembic,
                   # views.py (4 vues), queries/ (metrics, data_quality, sources),
                   # services/ (mappings, imports, pricing, repositories)
    readers/       # jsonl / csv / parquet
    llm/           # adaptateurs fake / anthropic / openai + factory pilotée par config
    profiling/     # field_profiler
    security/      # sensitive_filter — réexport ; l'implémentation vit dans application/mapping/
    services/      # workbench_service — façade des 3 cas d'utilisation de l'agent
    config/        # settings via variables d'environnement (préfixe AGENTSCOPE_)
  interfaces/
    api/           # app FastAPI, container (point de composition), dependencies,
                   # routes/, schemas/ Pydantic, errors (problem+json), openapi
  main.py          # point d'entrée ASGI : `uvicorn agentscope.main:app`
tests/
  unit/ integration/ e2e/ fixtures/
```

## Règle des dépendances

`domain` ← `application` ← `infrastructure` / `interfaces`. `domain` n'importe rien ;
`application` n'importe que `domain`. Cinq contrats `import-linter` déclarés dans
`pyproject.toml` la vérifient — en local (`make arch`, ou `lint-imports`) **et** dans la suite
`pytest` (`tests/unit/test_architecture.py`).

Détail des contrats et de ce que chacun empêche :
[`../docs/architecture/components.md`](../docs/architecture/components.md) §2.

## Développer

Tout se lance depuis la racine du dépôt (voir le [README principal](../README.md)) :

```bash
make up          # stack complète
make migrate     # alembic upgrade head
make test        # pytest (+ vitest côté front)
make sh-backend  # shell dans le conteneur
```

Hors Docker :

```bash
python -m venv .venv
./.venv/bin/pip install -e ".[dev]"
./.venv/bin/alembic upgrade head
./.venv/bin/uvicorn agentscope.main:app --reload
./.venv/bin/pytest
```

Base par défaut : SQLite (`sqlite:///./agentscope.db`). PostgreSQL via
`AGENTSCOPE_DATABASE_URL` — c'est ce que positionne `docker-compose.yml`.

## Points de repère

| Je veux… | Aller voir |
| --- | --- |
| comprendre ce que produit un import | `application/use_cases/import_file.py` |
| ajouter une transformation de mapping | `application/mapping/transforms.py` (registre whitelisté) + son test |
| ajouter un format de fichier | `infrastructure/readers/` + branchement dans `interfaces/api/container.py` |
| ajouter un fournisseur IA | `infrastructure/llm/` + `factory.py` ([`../docs/ai/providers.md`](../docs/ai/providers.md) §4) |
| ajouter un indicateur | `infrastructure/persistence/views.py` + migration + `ports/metrics.py` + `queries/metrics.py` + `routes/metrics.py` |
| savoir comment un chiffre est calculé | [`../docs/data/indicators.md`](../docs/data/indicators.md) |

## État

355 tests verts (1 ignoré), couverture **91 %**, `import-linter` vert sur les 5 contrats.
Toutes les routes sont branchées sur la base : `interfaces/api/fixtures.py` n'est plus servi.
