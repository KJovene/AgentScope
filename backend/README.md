# backend

API et cœur métier d'AgentScope (Python, Clean Architecture).

```
agentscope/
  domain/          # entités & règles pures — n'importe RIEN d'externe
  application/
    ports/         # interfaces abstraites (repositories, source_reader, llm_provider, metrics, profiler)
    mapping/       # contrat de mapping, validation, transformations whitelistées, normalizer
    use_cases/     # import_file, analyze_unknown_file, chat_about_mapping, preview_mapping, …
  infrastructure/
    persistence/   # ORM SQLAlchemy, repositories, migrations Alembic, vues SQL
    readers/       # jsonl / csv / parquet
    llm/           # adaptateurs (fake, anthropic, openai) + factory pilotée par config
    profiling/     # field_profiler, sensitive_filter
    config/        # settings via variables d'environnement
  interfaces/
    api/           # app FastAPI, routes, schemas Pydantic, injection de dépendances
  main.py          # point de composition
tests/
  unit/ integration/ e2e/ fixtures/
```

**Règle des dépendances** (vérifiée par `import-linter`, I0.11) :
`domain` ← `application` ← `infrastructure` / `interfaces`. `domain` n'importe rien ; `application`
n'importe que `domain`.

Squelette exécutable, outillage et `pyproject.toml` : issue **I0.5**.
