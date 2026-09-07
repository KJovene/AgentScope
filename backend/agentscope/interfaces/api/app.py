"""Fabrique de l'application FastAPI.

Point de composition unique : c'est ici (et dans ``dependencies.py``, à venir avec
I0.5 / I4.10) que les cas d'utilisation sont câblés à leurs adaptateurs. Pour
l'instant l'API n'expose que ``/health``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentscope.infrastructure.config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="AgentScope API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Les routes métier seront montées ici (EPIC 4) :
    # from agentscope.interfaces.api.routes import imports, mappings, metrics, sessions
    # app.include_router(imports.router, prefix="/api/v1")

    return app
