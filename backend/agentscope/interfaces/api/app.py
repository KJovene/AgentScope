"""Fabrique de l'application FastAPI.

``create_app()`` construit une instance neuve à chaque appel (isolation en tests).
Le conteneur de composition est créé dans le *lifespan* et exposé sur
``app.state.container`` ; les routes y accèdent via ``dependencies.py``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.interfaces.api.container import Container
from agentscope.interfaces.api.errors import register_exception_handlers
from agentscope.interfaces.api.routes import (
    analyze,
    chat,
    data_quality,
    imports,
    mappings,
    metrics,
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
        app.state.container = Container(settings)
        try:
            yield
        finally:
            container = getattr(app.state, "container", None)
            if container is not None and hasattr(container, "database"):
                container.database.engine.dispose()

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
