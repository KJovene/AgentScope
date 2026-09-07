"""Fabrique de l'application FastAPI.

Assemble le conteneur de composition, les gestionnaires d'erreurs et les routes.
Pour l'instant seules ``/health`` et le routeur vide ``/api/v1`` sont montées ;
les routes métier arrivent avec l'EPIC 4.
"""

from __future__ import annotations

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
