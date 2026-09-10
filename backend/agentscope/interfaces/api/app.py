"""Fabrique de l'application FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.infrastructure.persistence import views as views_module
from agentscope.infrastructure.persistence.orm_models import Base
from agentscope.interfaces.api.container import Container
from agentscope.interfaces.api.errors import register_exception_handlers
from agentscope.interfaces.api.routes import (
    analyze,
    chat,
    data_quality,
    imports,
    mappings,
    metrics,
    model_pricing,
    sessions,
    sources,
)

API_PREFIX = "/api/v1"

_ROUTE_MODULES = (
    imports,
    analyze,
    mappings,
    chat,
    metrics,
    sessions,
    sources,
    data_quality,
    model_pricing,
)


def _api_router() -> APIRouter:
    router = APIRouter(prefix=API_PREFIX)
    for module in _ROUTE_MODULES:
        router.include_router(module.router)

    @router.get("/health", tags=["meta"])
    async def health_v1() -> dict[str, str]:
        return {"status": "ok"}

    return router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container = Container(settings)
        app.state.container = container

        # 1. Création des tables ORM absentes (idempotent).
        Base.metadata.create_all(bind=container.database.engine)

        # 2. (Re)création des vues agrégées — toujours réalignées sur views.py.
        #    On drop d'abord : `CREATE VIEW` échoue si la vue existe déjà avec un
        #    schéma périmé (ce bootstrap dev ne passe pas par Alembic, donc une
        #    colonne ajoutée à une vue — p. ex. `cost_is_estimated` — ne serait
        #    jamais prise en compte sur une base préexistante).
        with container.database.engine.begin() as conn:
            views_module.drop_all_views(conn)
            views_module.create_all_views(conn)

        try:
            yield
        finally:
            c = getattr(app.state, "container", None)
            if c is not None and hasattr(c, "database"):
                c.database.engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Parcours principal : importer -> vérifier -> normaliser -> explorer.",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(_api_router())
    return app


app = create_app()
