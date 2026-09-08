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

    # Alias global non versionnÃ©
    app_instance.add_api_route("/health", health, tags=["meta"])
    app_instance.include_router(api_router)

    return app_instance

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.interfaces.api.routes import (
    analyze,
    chat,
    imports,
    mappings,
    metrics,
    sessions,
    sources,
)
from agentscope.interfaces.api.schemas.common import ProblemDetail

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Fabrique de l'app : une instance neuve à chaque appel (isolation en tests)."""
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Parcours principal : importer -> vérifier -> normaliser -> explorer. "
            "I4.1 : endpoints stub renvoyant des fixtures pour débloquer le frontend."
        ),
    )

    @app.get("/health", tags=["platform"])
    @app.get(f"{API_PREFIX}/health", tags=["platform"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (
        imports.router,
        analyze.router,
        mappings.router,
        chat.router,
        sessions.router,
        sources.router,
    ):
        app.include_router(router, prefix=API_PREFIX)
    app.include_router(metrics.router, prefix=API_PREFIX)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        problem = ProblemDetail(title=exc.detail, status=exc.status_code, detail=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(problem),
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        problem = ProblemDetail(
            title="Entrée invalide",
            status=422,
            detail="Un ou plusieurs champs ne respectent pas le schéma attendu.",
            errors=jsonable_encoder(exc.errors()),
        )
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(problem),
            media_type="application/problem+json",
        )

    return app


app = create_app()
