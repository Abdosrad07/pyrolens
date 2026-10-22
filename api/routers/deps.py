"""Dépendances partagées des routeurs (settings, store, config, cache HTTP)."""

from __future__ import annotations

from typing import Any

from fastapi import Request, Response

from api.jobs import JobManager
from api.security import require_token_if_configured  # noqa: F401 — réexporté pour les routeurs
from api.services.queries import reject_unknown_params  # réexporté
from api.settings import Settings
from api.store import ArtifactStore, http_cache_headers

MAX_CACHE_AGE = "public, max-age=60"


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_store(request: Request) -> ArtifactStore:
    return request.app.state.store


def get_jobs(request: Request) -> JobManager:
    return request.app.state.jobs


def get_cfg(request: Request) -> Any:
    return request.app.state.cfg


def cache_guard(request: Request, *names: str) -> Response | None:
    """Réponse 304 si l'ETag du client correspond aux artefacts courants."""
    store = get_store(request)
    etag = store.etag(*names)
    if etag and request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": MAX_CACHE_AGE})
    return None


def apply_cache_headers(request: Request, response: Response, *names: str) -> None:
    response.headers.update(http_cache_headers(get_store(request), *names))
