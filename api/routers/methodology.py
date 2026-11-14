"""Data & Methodology — documentation scientifique exposée en API.

Endpoints (montés sous ``/api/v1``) :
- GET /methodology                 → ``text/markdown`` (docs/methodology.md)
- GET /methodology/satellites      → capteurs de l'inventaire (inventory.json)
- GET /methodology/processing-steps → étapes méthodologiques (titres du document)

Le contenu Markdown est lu depuis ``docs/methodology.md`` à la racine du projet
(même fichier que ``web/public/methodology.md`` servi en mode statique).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import Response

from api import PROJECT_ROOT
from api.errors import ApiError
from api.routers.deps import get_store
from api.store import ArtifactStore

router = APIRouter(tags=["Methodology"])

_METHODOLOGY_DOC = PROJECT_ROOT / "docs" / "methodology.md"
_METHODOLOGY_FALLBACK = PROJECT_ROOT / "web" / "public" / "methodology.md"

_STEP_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)


def _methodology_text() -> str:
    for candidate in (_METHODOLOGY_DOC, _METHODOLOGY_FALLBACK):
        try:
            return candidate.read_text(encoding="utf-8")
        except OSError:
            continue
    raise ApiError(404, "Documentation méthodologique indisponible.")


# ---------- méthodologie ----------------------------------------------------


@router.get(
    "/methodology",
    summary="Documentation méthodologique complète",
    description=(
        "Le document ``docs/methodology.md`` en Markdown brut (``text/markdown``), "
        "identique au fichier servi en mode statique."
    ),
    responses={200: {"content": {"text/markdown": {}}, "description": "Document méthodologique."}},
)
def methodology() -> Response:
    return Response(
        content=_methodology_text(),
        media_type="text/markdown; charset=utf-8",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get(
    "/methodology/satellites",
    summary="Capteurs couverts par l'étude",
    description=(
        "Liste des capteurs de l'inventaire (MODIS Terra, MODIS Aqua, VIIRS S-NPP) "
        "avec libellé, nom court et version retenue."
    ),
)
def satellites(request: Request) -> dict[str, Any]:
    store: ArtifactStore = get_store(request)
    inventory = store.get_json("inventory.json") or {}
    sensors = inventory.get("sensors", {}) or {}
    return {
        "generated_at": inventory.get("generated_at"),
        "data_origin": None,
        "satellites": [
            {
                "id": key,
                "label": sensor.get("label", key),
                "short_name": sensor.get("short_name"),
                "version_used": sensor.get("version_used") or sensor.get("configured_version"),
            }
            for key, sensor in sensors.items()
        ],
    }


@router.get(
    "/methodology/processing-steps",
    summary="Étapes de la méthode (titres du document)",
    description=(
        "Sections numérotées de ``docs/methodology.md`` extraites dynamiquement : "
        "aucune liste codée en dur, le document fait foi."
    ),
)
def processing_steps() -> dict[str, Any]:
    text = _methodology_text()
    steps = [
        {"order": int(order), "title": title}
        for order, title in _STEP_RE.findall(text)
    ]
    return {"steps": steps, "source": "docs/methodology.md"}
