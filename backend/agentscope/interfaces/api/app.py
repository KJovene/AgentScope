"""Fabrique de l'application FastAPI.

Assemble le conteneur de composition, les gestionnaires d'erreurs et les routes.
Pour l'instant seules ``/health`` et le routeur vide ``/api/v1`` sont montées ;
les routes métier arrivent avec l'EPIC 4.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.interfaces.api.container import Container
from agentscope.interfaces.api.errors import register_exception_handlers

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = Container(settings)
        yield
        app.state.container.database.engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
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

    # Alias non versionné conservé pour les sondes d'orchestrateur.
    app.add_api_route("/health", health, tags=["meta"])
    app.include_router(api_router)

    return app
