"""Routes système : santé, méta, rapport scientifique."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from api.routers.deps import apply_cache_headers, cache_guard, get_store
from api.services.queries import known_pairs
from api.store import ArtifactStore
from api import __doc__ as _  # noqa: F401 — maintient l'import paquet explicite

try:
    from pyrolens import __version__ as PYROLENS_VERSION
except Exception:  # noqa: BLE001 — API servable sans pipeline importable
    PYROLENS_VERSION = "unknown"

router = APIRouter()


@router.get(
    "/health",
    summary="Santé du service",
    description="Réponse immédiate sans lecture d'artefact : statut, horodatage de synchronisation et version.",
)
def health(request: Request) -> dict:
    store: ArtifactStore = get_store(request)
    generated_at = None
    if store.has("generated_at.txt"):
        text = store.get_text("generated_at.txt")
        generated_at = text.strip() if text else None
    data_origin = None
    if store.has("baselines.json"):
        data_origin = (store.get_json("baselines.json") or {}).get("data_origin")
    return {
        "status": "ok",
        "generated_at": generated_at,
        "data_origin": data_origin,
        "project_version": PYROLENS_VERSION,
    }


@router.get(
    "/meta",
    summary="Métadonnées de l'étude",
    description="Période, configuration primaire, grilles, fenêtres, paires publiées et état de l'observabilité.",
)
def meta(request: Request, response: Response) -> dict:
    guard = cache_guard(request, "baselines.json", "observability.json", "execution.json")
    if guard is not None:
        return guard
    store = get_store(request)
    baselines = store.require_json("baselines.json")
    observability = store.get_json("observability.json") or {}
    execution = store.get_json("execution.json") or {}

    period = {"start": execution.get("period_start"), "end": execution.get("period_end")}
    apply_cache_headers(request, response, "baselines.json", "observability.json", "execution.json")
    return {
        "generated_at": baselines.get("generated_at"),
        "data_origin": baselines.get("data_origin"),
        "project_version": execution.get("project_version", PYROLENS_VERSION),
        "period": period,
        "primary": baselines.get("primary"),
        "grids_deg": baselines.get("grids_deg"),
        "window_days": baselines.get("window_days"),
        "pairs": known_pairs(baselines),
        "key_definitions": baselines.get("key_definitions"),
        "coverage_products_acquired": observability.get("coverage_products_acquired"),
        "interpretation_note": (
            "Le Jaccard mesure un recouvrement d'ensembles entre capteurs, pas une précision : "
            "aucune référence indépendante n'est mobilisée (H4/H6 non exécutés)."
        ),
    }


@router.get(
    "/fire-risk",
    summary="Risque d'activité de feu détectée (backtest)",
    description=(
        "Sert l'artefact `fire_risk.json` produit par `pyrolens predict`. "
        "Probabilités calibrées par cellule — estimation d'activité détectée, "
        "jamais une alerte incendie. 404 propre si l'artefact n'existe pas ; "
        "l'API ne recalcule jamais le modèle."
    ),
)
def fire_risk(request: Request, response: Response) -> dict:
    from api.errors import ApiError

    guard = cache_guard(request, "fire_risk.json")
    if guard is not None:
        return guard
    store = get_store(request)
    if not store.has("fire_risk.json"):
        raise ApiError(
            404,
            "Aucun artefact fire_risk.json : exécuter `pyrolens predict` "
            "(nécessite les CSV FIRMS dans data/raw/firms ou data/fixture).",
        )
    payload = store.require_json("fire_risk.json")
    apply_cache_headers(request, response, "fire_risk.json")
    return payload


@router.get(
    "/report",
    summary="Rapport scientifique",
    response_class=Response,
    responses={200: {"content": {"text/markdown": {}}, "description": "Rapport Markdown horodaté."}},
)
def report(request: Request, response: Response):
    guard = cache_guard(request, "scientific_report.md")
    if guard is not None:
        return guard
    store = get_store(request)
    content = store.require_text("scientific_report.md")
    apply_cache_headers(request, response, "scientific_report.md")
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers=dict(response.headers),
    )
