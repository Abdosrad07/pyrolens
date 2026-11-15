"""Routes système : santé, méta, rapport scientifique, état des téléchargements."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response

from api.routers.deps import apply_cache_headers, cache_guard, get_jobs, get_store
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
    "/downloads/status",
    summary="État des téléchargements FIRMS (pipeline + archive)",
    description=(
        "Lecture légère des manifests et du disque : progression du pipeline "
        "data/raw/firms et volume du cache archive data/raw/archive. "
        "Aucun appel réseau — interrogeable en continu."
    ),
)
def downloads_status(request: Request) -> dict:
    root = Path(__file__).resolve().parents[2]
    firms_dir = root / "data" / "raw" / "firms"
    archive_dir = root / "data" / "raw" / "archive"
    manifest_path = root / "data" / "manifests" / "downloads.json"

    entries: list = []
    if manifest_path.exists():
        try:
            entries = json.loads(manifest_path.read_text(encoding="utf-8")).get("entries", [])
        except Exception:  # noqa: BLE001
            entries = []

    def _count_status(status: str) -> int:
        return sum(1 for e in entries if e.get("status") == status)

    # Le manifest cumule l'historique des runs : le dénominateur honnête est
    # le nombre de chemins uniques jamais acquis, pas le nombre d'entrées.
    unique_paths = {
        e.get("path") for e in entries if e.get("path") and e.get("status") in
        ("downloaded", "already_present")
    }
    total_unique = len(unique_paths)
    firms_files = len(list(firms_dir.glob("*.csv"))) if firms_dir.exists() else 0
    archive_files = (
        len([p for p in archive_dir.rglob("*.csv")]) if archive_dir.exists() else 0
    )
    archive_bytes = (
        sum(p.stat().st_size for p in archive_dir.rglob("*.csv"))
        if archive_dir.exists()
        else 0
    )
    return {
        "firms": {
            "files_on_disk": firms_files,
            "unique_files_expected": total_unique,
            "acquired_entries": _count_status("downloaded"),
            "already_present_entries": _count_status("already_present"),
            "deferred_entries": _count_status("deferred"),
            "error_entries": _count_status("http_error") + _count_status("error"),
            "pct": round(100 * min(firms_files, total_unique) / total_unique, 1)
            if total_unique else None,
        },
        "archive": {
            "files": archive_files,
            "mb": round(archive_bytes / 1e6, 1),
        },
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


@router.post(
    "/chat",
    summary="Assistant — réponses factuelles sur l'application",
    description=(
        "Assistant déterministe (pas de LLM) : intentions métier sur les "
        "données, le pipeline, les vues, le modèle de risque, les jobs et les "
        "limites scientifiques. Chaque réponse s'appuie sur les artefacts "
        "réels et l'état des jobs — jamais de contenu inventé."
    ),
)
def chat(request: Request, body: dict) -> dict:
    from api.services.chat import answer

    store = get_store(request)
    jobs = get_jobs(request).list()[:10]
    firms = store.get_json("firms.json") or {}
    downloads = {}
    dl_path = Path(__file__).resolve().parents[2] / "data" / "manifests" / "downloads.json"
    try:
        if dl_path.exists():
            downloads = {"manifest_entries": len(json.loads(dl_path.read_text(encoding="utf-8")).get("entries", []))}
    except Exception:  # noqa: BLE001
        pass
    messages = body.get("messages") or []
    last = str(messages[-1].get("content", "")) if messages else ""
    ctx = {
        "risk": store.get_json("fire_risk.json") or {},
        "meta": store.get_json("meta.json") or firms,
        "jobs": [j.view() for j in jobs],
        "downloads": downloads,
    }
    return {"reply": answer(last, ctx)}


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
