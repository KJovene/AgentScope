from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.interfaces.api.container import Container
from agentscope.interfaces.api.errors import register_exception_handlers

api_router = APIRouter(prefix="/api/v1")

# Import et montage automatique de tous les routeurs de modules d'interfaces
ROUTE_MODULES = [
    "imports",
    "analyze",
    "mappings",
    "chat",
    "metrics",
    "sessions",
    "sources",
    "data_quality",
]

for module_name in ROUTE_MODULES:
    try:
        mod = __import__(f"agentscope.interfaces.api.routes.{module_name}", fromlist=["router"])
        if hasattr(mod, "router"):
            api_router.include_router(mod.router)
    except ImportError:
        pass


@api_router.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


def create_app(settings: Settings | None = None) -> FastAPI:
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

    # Alias global non versionné
    app_instance.add_api_route("/health", health, tags=["meta"])
    app_instance.include_router(api_router)

    return app_instance


app = create_app()
