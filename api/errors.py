"""Erreurs de l'API : enveloppe unique ``{"error": {"code", "message"}}``.

Aucune pile d'exception ni chemin serveur n'est exposé dans les messages
(``docs/phase2/api_contract.md` §2) ; le détail est journalisé côté serveur.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("pyrolens.api")


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


class ApiError(Exception):
    """Erreur métier contrôlée, traduite en enveloppe JSON par les handlers."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def envelope(status_code: int, message: str) -> dict:
    return {"error": {"code": str(status_code), "message": message}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return UTF8JSONResponse(envelope(exc.status_code, exc.message), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = ".".join(str(part) for part in first.get("loc", []) if part not in ("body", "query"))
        message = first.get("message", "Paramètre invalide.")
        return UTF8JSONResponse(
            envelope(400, f"{loc}: {message}" if loc else message), status_code=400
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        default = {404: "Route inconnue.", 405: "Méthode non autorisée."}.get(
            exc.status_code, "Erreur HTTP."
        )
        detail = exc.detail if isinstance(exc.detail, str) and exc.detail else default
        return UTF8JSONResponse(envelope(exc.status_code, detail), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _internal_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("erreur interne : %s %s", request.method, request.url.path)
        return UTF8JSONResponse(envelope(500, "Erreur interne du serveur."), status_code=500)
