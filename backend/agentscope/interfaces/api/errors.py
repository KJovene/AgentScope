"""Gestion d'erreurs uniforme au format ``application/problem+json`` (RFC 7807).

Version minimale du squelette. Le mapping fin des erreurs métier vers des codes
HTTP est traité par l'issue I4.9.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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
            errors=errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _on_http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else None
        return _problem(status_code=exc.status_code, title="Erreur HTTP", detail=detail)

    @app.exception_handler(Exception)
    async def _on_unhandled(_request: Request, _exc: Exception) -> JSONResponse:
        return _problem(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Erreur interne",
        )
