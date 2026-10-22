"""Authentification optionnelle des endpoints d'écriture (expériences, validation).

Par défaut l'API est ouverte en lecture seule (D6 : MVP public). Si la variable
``PYROLENS_API_TOKEN`` est définie, les endpoints POST exigent
``Authorization: Bearer <jeton>``. Aucun secret n'est stocké côté API.
"""

from __future__ import annotations

from fastapi import Request

from api.errors import ApiError


async def require_token_if_configured(request: Request) -> None:
    expected = request.app.state.settings.api_token
    if not expected:
        return
    authorization = request.headers.get("authorization", "")
    if authorization != f"Bearer {expected}":
        raise ApiError(401, "Authentification requise : en-tête Authorization: Bearer <jeton>.")
