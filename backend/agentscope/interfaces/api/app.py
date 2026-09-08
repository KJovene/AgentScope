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

api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(imports.router)
api_router.include_router(analyze.router)
api_router.include_router(mappings.router)
api_router.include_router(chat.router)
api_router.include_router(metrics.router)
api_router.include_router(sessions.router)
api_router.include_router(sources.router)
api_router.include_router(data_quality.router)


@api_router.get("/health", tags=["platform"])
def health() -> dict[str, str]:
    return {"status": "ok"}


def create_app(settings: Settings | None = None) -> FastAPI:
    """Fabrique de l'application FastAPI."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = Container(settings)
        yield
        if hasattr(app.state.container, "database"):
            app.state.container.database.engine.dispose()

    app_instance = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Parcours principal : importer -> vérifier -> normaliser -> explorer.",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app_instance)

    # Alias non versionné et routeur /api/v1
    app_instance.add_api_route("/health", health, tags=["platform"])
    app_instance.include_router(api_router)

    return app_instance


app = create_app()
