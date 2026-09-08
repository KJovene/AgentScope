# AgentScope — tâches de développement. `make` ou `make help` pour la liste.

SHELL := /bin/bash
COMPOSE := docker compose
BACKEND := backend
FRONTEND := frontend

.DEFAULT_GOAL := help

.PHONY: help
help: ## Affiche cette aide
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Cycle de vie de la stack
# ---------------------------------------------------------------------------

.PHONY: dev
dev: ## Lève db + backend + frontend en mode watch (Ctrl-C pour arrêter)
	$(COMPOSE) up --build

.PHONY: up
up: ## Lève la stack en arrière-plan
	$(COMPOSE) up -d --build

.PHONY: down
down: ## Arrête la stack (conserve le volume de la base)
	$(COMPOSE) down

.PHONY: build
build: ## (Re)construit les images sans démarrer
	$(COMPOSE) build

.PHONY: logs
logs: ## Suit les logs de tous les services
	$(COMPOSE) logs -f

.PHONY: ps
ps: ## État des services
	$(COMPOSE) ps

.PHONY: clean
clean: ## Arrête tout, supprime le volume db et les caches
	$(COMPOSE) down -v --remove-orphans
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/.mypy_cache backend/.coverage
	rm -rf frontend/dist frontend/node_modules/.tmp

# ---------------------------------------------------------------------------
# Shells
# ---------------------------------------------------------------------------

.PHONY: sh-backend
sh-backend: ## Shell dans le conteneur backend
	$(COMPOSE) exec $(BACKEND) bash

.PHONY: sh-frontend
sh-frontend: ## Shell dans le conteneur frontend
	$(COMPOSE) exec $(FRONTEND) sh

.PHONY: db-shell
db-shell: ## Ouvre psql sur la base
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-agentscope} -d $${POSTGRES_DB:-agentscope}

# ---------------------------------------------------------------------------
# Base de données (Alembic — opérationnel à partir de I1.3)
# ---------------------------------------------------------------------------

.PHONY: migrate
migrate: ## Applique les migrations (alembic upgrade head)
	$(COMPOSE) run --rm $(BACKEND) alembic upgrade head

.PHONY: migration
migration: ## Nouvelle migration : make migration m="ajout table sessions"
	$(COMPOSE) run --rm $(BACKEND) alembic revision --autogenerate -m "$(m)"

.PHONY: downgrade
downgrade: ## Annule la dernière migration
	$(COMPOSE) run --rm $(BACKEND) alembic downgrade -1

# ---------------------------------------------------------------------------
# Tests & qualité
# ---------------------------------------------------------------------------

.PHONY: test
test: test-backend test-frontend ## Lance tous les tests

.PHONY: test-backend
test-backend: ## Tests backend (pytest)
	$(COMPOSE) run --rm $(BACKEND) pytest

.PHONY: test-frontend
test-frontend: ## Tests frontend (vitest)
	$(COMPOSE) run --rm $(FRONTEND) npm run test

.PHONY: lint
lint: ## Lint backend (ruff) + frontend (eslint)
	$(COMPOSE) run --rm $(BACKEND) ruff check .
	$(COMPOSE) run --rm $(FRONTEND) npm run lint

.PHONY: format
format: ## Formate backend (ruff) + frontend (prettier)
	$(COMPOSE) run --rm $(BACKEND) ruff format .
	$(COMPOSE) run --rm $(FRONTEND) npm run format

.PHONY: typecheck
typecheck: ## Types backend (mypy) + frontend (tsc)
	$(COMPOSE) run --rm $(BACKEND) mypy agentscope
	$(COMPOSE) run --rm $(FRONTEND) npm run typecheck

.PHONY: arch
arch: ## Vérifie la règle des dépendances (import-linter)
	$(COMPOSE) run --rm $(BACKEND) lint-imports

.PHONY: openapi
openapi: ## Exporte backend/openapi.json puis régénère le client TS du frontend
	$(COMPOSE) run --rm $(BACKEND) python -m agentscope.interfaces.api.openapi openapi.json
	cp backend/openapi.json frontend/openapi.json
	$(COMPOSE) run --rm $(FRONTEND) npm run api:generate

.PHONY: ci
ci: lint typecheck arch test ## Ce que la CI exécute à chaque PR

# ---------------------------------------------------------------------------
# Données (I0.10 — provenance et méthode dans data/README.md)
# ---------------------------------------------------------------------------

.PHONY: data-tracelab
data-tracelab: ## Télécharge l'extrait TraceLab épinglé (SHA256 vérifié) + échantillon de dev
	python scripts/tracelab_extract.py --fetch --modulo 32 --out data/tracelab/extract-dev.jsonl

.PHONY: findings
findings: ## Recalcule les chiffres de docs/findings.md depuis l'extrait TraceLab (I6.7)
	python scripts/findings_tracelab.py

.PHONY: fixtures
fixtures: ## Régénère la fixture de test TraceLab commitée
	python scripts/tracelab_extract.py --fetch --modulo 32 --max-sessions-per-provider 1 --out backend/tests/fixtures/tracelab/sample.jsonl

# ---------------------------------------------------------------------------
# Installation locale (hors Docker)
# ---------------------------------------------------------------------------

.PHONY: install
install: ## Installe les dépendances en local (venv backend + npm frontend)
	cd backend && python -m venv .venv && ./.venv/bin/pip install --upgrade pip && ./.venv/bin/pip install -e ".[dev]"
	cd frontend && npm install

.PHONY: dev-local
dev-local: ## Lance backend + frontend en local (nécessite `make install` et une base joignable)
	cd backend && ./.venv/bin/uvicorn agentscope.main:app --reload &
	cd frontend && npm run dev
