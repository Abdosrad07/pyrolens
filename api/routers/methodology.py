"""Data & Methodology — documentation scientifique et technique exposée en API.

Endpoints :
- GET /api/v1/methodology
- GET /api/v1/methodology/satellites
- GET /api/v1/methodology/processing-steps

Tous les réponses sont issues des fichiers de documentation versionnés
(``docs/methodology.md``, ``docs/references.md``, ``config/pipeline.yaml``)
ou des artefacts métier (``config/pipeline.yaml`` → catalogue des capteurs).
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.routers.deps import apply_cache_headers, cache_guard, get_store
from api.store import ArtifactStore

router = APIRouter(prefix="/api/v1/methodology", tags=["Methodology"])

# ---------- aide -----------------------------------------------------------


def _first_lines(text: str, n: int = 12) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:n]) or "(document vide)"


# ---------- méthodologie --------------------------------------------------

@router.get(
    "/methodology",
    summary="Résumé de la méthode scientifique",
    description=(
        "Retourne un condensé de la documentation méthodologique (docs/methodology.md), "
        "avec les questions de recherche, les non-objectifs et les étapes principales."
    ),
    responses={
        200: {"description": "Résumé de la méthode."},
        404: {"description": "Fichier de documentation manquant."},
    },
)
def methodology(request: Request) -> dict:
    store: ArtifactStore = get_store(request)
    text = store.get_text("docs/methodology.md")
    if text is None:
        raise store.get_json("methodology.md") is None and {}
    return {"generated_at": store.get_json("methodology.md") or {}, "summary": _first_lines(text)}
