"""Gestion d'erreurs uniforme au format ``application/problem+json`` (RFC 7807)."""

from __future__ import annotations

import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from agentscope.domain.errors import DomainError

_MEDIA_TYPE = "application/problem+json"


def _problem(
    *,
    status_code: int,
    title: str,
    detail: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"type": "about:blank", "title": title, "status": status_code}
    if detail:
        body["detail"] = detail
    if errors:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body, media_type=_MEDIA_TYPE)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _on_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return _problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Requête invalide",
            detail="Un ou plusieurs champs ne respectent pas le schéma attendu.",
            errors=errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _on_http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail_msg = exc.detail if isinstance(exc.detail, str) else None
        return _problem(
            status_code=exc.status_code,
            title=detail_msg or "Erreur HTTP",
            detail=detail_msg,
        )

    @app.exception_handler(DomainError)
    async def _on_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        return _problem(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Violation de règle métier",
            detail=str(exc),
        )

    @app.exception_handler(Exception)
    async def _on_unhandled(_request: Request, exc: Exception) -> JSONResponse:
        traceback.print_exc()
        return _problem(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Erreur interne",
            detail=str(exc),
        )
