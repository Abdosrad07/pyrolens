"""Fire Calendar — agrégations temporelles quotidiennes, hebdomadaires et mensuelles.

Endpoints :
- GET /api/v1/fire-calendar/daily
- GET /api/v1/fire-calendar/weekly
- GET /api/v1/fire-calendar/monthly
- GET /api/v1/fire-calendar/timeseries

Toutes les séries sont calculées à partir des artefacts ``baselines.json`` et
``inventory.json`` produits par le pipeline. Les périodes de date/temps sont
toujours UTC (``YYYY-MM-DD`` / ``YYYY-MM``).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request

from api.routers.deps import apply_cache_headers, cache_guard, get_store
from api.store import ArtifactStore

router = APIRouter(prefix="/api/v1/fire-calendar", tags=["Fire Calendar"])

# ---------- aide -----------------------------------------------------------

def _safe_int(value: Any | None, default: int) -> int:
    try:
        if value is None:
            return default
        ivalue = int(value)
        return ivalue if ivalue >= 1 else default
    except (TypeError, ValueError):
        return default


# ---------- daily ----------------------------------------------------------

@router.get(
    "/daily",
    summary="Série quotidienne (observations, FRP, comptages) par capteur et paire",
    description=(
        "Retourne une série quotidienne agrégée par capteur et paire pour la "
        "configuration primaire. Chaque point contient le nombre d'observations et "
        "la somme de la FRP. Les dates sont en UTC (``YYYY-MM-DD``)."
    ),
    responses={
        200: {"description": "Série quotidienne (jours avec données fixe)."},
        404: {"description": "Artefact `baselines.json` absent (pipeline non exécuté)."},
    },
)
def daily(
    request: Request,
    sensor: str | None = Query(
        default=None,
        description="Capteur à filtrer : terra | aqua | viirs_snpp. Aucun filtre = toutes.",
    ),
    pair: str | None = Query(
        default=None,
# ---------- weekly ----------------------------------------------------------

@router.get(
    "/weekly",
    summary="Série hebdomadaire (observations, FRP) par capteur et paire",
    description=(
        "Agrège les observations quotidiennes en semaines selon l'epoch. "
        "Retourne une série par semaine (1..n) avec le nombre d'observations et "
        "la somme de la FRP."
    ),
    responses={
        200: {"description": "Série hebdomadaire."},
        404: {"description": "Artefact `baselines.json` absent."},
    },
)
def weekly(
    request: Request,
    sensor: str | None = Query(
        default=None,
        description="Capteur à filtrer : terra | aqua | viirs_snpp.",
    ),
    pair: str | None = Query(
        default=None,
        description="Paire de capteurs : terra__aqua | aqua__viirs_snpp.",
    ),
    limit: int = Query(
        default=90,
        ge=1,
        le=365,
        description="Nombre maximum de semaines retournées.",
    ),
):
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    inv = store.get_json("inventory") or {}

    rows = []
    for item in (baselines.get("weekly", []) or []):
        if pair and item.get("pair") != pair:
            continue
        if sensor:
            s = (inv.get("sensors", {}) or {}).get(sensor)
            if not s:
                continue
        rows.append(
            {
                "sensor": item.get("sensor", ""),
                "week": item.get("week", ""),
                "obs_a_only": item.get("a_only", 0),
                "obs_b_only": item.get("b_only", 0),
                "obs_both": item.get("both", 0),
                "count": item.get("a_only", 0) + item.get("b_only", 0),
                "frp": item.get("frp", 0),
            }
        )
# ---------- monthly ---------------------------------------------------------

@router.get(
    "/monthly",
    summary="Série mensuelle (observations, FRP, séries de divergence)",
    description=(
        "Retourne les agrégations mensuelles : observations par capteur, "
        "séries de divergence (a_only / b_only / both), et jaccard mensuel. "
        "Les dates sont en UTC (``YYYY-MM``)."
    ),
    responses={
        200: {"description": "Série mensuelle et divergences."},
        404: {"description": "Artefact `baselines.json` absent."},
    },
)
def monthly(
    request: Request,
    sensor: str | None = Query(
        default=None,
        description="Capteur à filtrer : terra | aqua | viirs_snpp.",
    ),
    pair: str | None = Query(
        default=None,
        description="Paire de capteurs : terra__aqua | aqua__viirs_snpp.",
    ),
    limit: int = Query(
        default=24,
        ge=1,
        le=36,
        description="Nombre maximum de mois retournés.",
    ),
):
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    inv = store.get_json("inventory") or {}

    monthly_rows = (baselines.get("monthly", []) or [])
    monthly_jaccard = (baselines.get("jaccard_monthly", []) or [])
    regions = (baselines.get("regions", []) or [])
    daily = (baselines.get("daily", []) or [])

    rows = []
    jaccard_rows = []

    for item in monthly_rows:
        if pair and item.get("pair") != pair:
            continue
        if sensor:
            s = (inv.get("sensors", {}) or {}).get(sensor)
            if not s:
                continue
        rows.append(
            {
                "sensor": item.get("sensor", ""),
                "month": item.get("month", ""),
# ---------- timeseries -----------------------------------------------------

@router.get(
    "/timeseries",
    summary="Série temporelle multi-dimensionnelle (FRP, comptages, jaccard)",
    description=(
        "Retourne les données de séries temporelles nécessaires au graphique du "
        "calendrier : observations, FRP, jaccard et divergences, filtrables par "
        "période, capteur et configuration primaire."
    ),
    responses={
        200: {"description": "Série temporelle complète."},
        404: {"description": "Artefact `baselines.json` absent."},
    },
)
def timeseries(
    request: Request,
    start: str | None = Query(
        default=None,
        description="Date de début (ISO-8601 UTC, YYYY-MM-DD ou YYYY-MM).",
    ),
    end: str | None = Query(
        default=None,
        description="Date de fin (ISO-8601 UTC, YYYY-MM-DD ou YYYY-MM).",
    ),
    sensor: str | None = Query(
        default=None,
        description="Capteur : terra | aqua | viirs_snpp.",
    ),
    pair: str | None = Query(
        default=None,
        description="Paire : terra__aqua | aqua__viirs_snpp.",
    ),
    metric: str | None = Query(
        default="observation",
        description="Métrique : observation | jaccard | frp | divergence.",
    ),
):
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    inv = store.get_json("inventory") or {}

    daily_rows = (baselines.get("daily", []) or [])
    monthly_rows = (baselines.get("monthly", []) or [])
    jaccard_rows = (baselines.get("jaccard_monthly", []) or [])

    sensor = sensor or (list(inv.get("sensors", {}) or {}).keys())[0] if inv.get("sensors") else None
    pair = pair or (list((baselines.get("primary", {}) or {}).get("pairs", {}) or {}).keys())[0]

    # tolerance de date (YYYY-MM renvoie à tous les JJ du mois)
    def _in_range(date: str) -> bool:
        if not start and not end:
            return True
        try:
            y, m, d = date.split("-")
        except ValueError:
            return False
        if start and (y, m) < (start[:4], start[5:7]):
            return False
        if end and (y, m) > (end[:4], end[5:7]):
            return False
        return True

    rows = []

    # observations, grâce à `daily`
    if metric in ("observation", "frp"):
        for item in daily_rows:
            if pair and item.get("pair") != pair:
                continue
            if sensor and item.get("sensor") != sensor:
                continue
            if not _in_range(item.get("date", "")):
                continue
            rows.append(
                {
                    "sensor": item.get("sensor", ""),
                    "date": item.get("date", ""),
                    "metric": "observation",
                    "count": item.get("a_only", 0) + item.get("b_only", 0),
                    "frp": item.get("frp", 0),
                    "a_only": item.get("a_only", 0),
                    "b_only": item.get("b_only", 0),
                    "both": item.get("both", 0),
                }
            )

    # jaccard
    if metric in ("jaccard", "observation"):
        for item in jaccard_rows:
            if pair and item.get("pair") != pair:
                continue
            if sensor and item.get("sensor") != sensor:
                continue
            if not _in_range(item.get("month", "")):
                continue
            rows.append(
                {
                    "sensor": item.get("sensor", ""),
                    "month": item.get("month", ""),
                    "metric": "jaccard",
                    "jaccard": item.get("jaccard"),
                    "a_only": item.get("a_only", 0),
                    "b_only": item.get("b_only", 0),
                    "both": item.get("both", 0),
                    "total_jaccard": item.get("total_jaccard"),
                }
            )

    return {
        "generated_at": (baselines.get("generated_at") or ""),
        "data_origin": (baselines.get("data_origin") or "unknown"),
        "start": start or "",
        "end": end or "",
        "sensor": sensor,
        "pair": pair,
        "metric": metric,
        "rows": rows[:250],
    }
                "a_only": item.get("a_only", 0),
                "b_only": item.get("b_only", 0),
                "both": item.get("both", 0),
                "total": item.get("a_only", 0)
                + item.get("b_only", 0)
                + item.get("both", 0),
            }
        )

    for item in monthly_jaccard:
        if pair and item.get("pair") != pair:
            continue
        jaccard_rows.append(
            {
                "sensor": item.get("sensor", ""),
                "month": item.get("month", ""),
                "jaccard": item.get("jaccard"),
                "a_only": item.get("a_only", 0),
                "b_only": item.get("b_only", 0),
                "both": item.get("both", 0),
                "total_jaccard": item.get("total_jaccard"),
            }
        )

    return {
        "generated_at": (baselines.get("generated_at") or ""),
        "data_origin": (baselines.get("data_origin") or "unknown"),
        "grid_deg": baselines.get("primary", {}).get("grid_deg", 0.25),
        "window_days": baselines.get("primary", {}).get("window_days", 8),
        "monthly": rows[:limit],
        "jaccard_monthly": jaccard_rows[:limit],
    }


    return {
        "generated_at": (baselines.get("generated_at") or ""),
        "data_origin": (baselines.get("data_origin") or "unknown"),
        "grid_deg": baselines.get("primary", {}).get("grid_deg", 0.25),
        "window_days": baselines.get("primary", {}).get("window_days", 8),
        "rows": rows[:limit],
    }

# ---------- weekly ----------------------------------------------------------

@router.get(
    "/weekly",
    summary="Série hebdomadaire (observations, FRP) par capteur et paire",
    description=(
        "Agrège les observations quotidiennes en semaines selon l'epoch. "
        "Retourne une série par semaine (1..n) avec le nombre d'observations et "
        "la somme de la FRP."
    ),
    responses={
        200: {"description": "Série hebdomadaire."},
        404: {"description": "Artefact `baselines.json` absent."},
    },
)
def weekly(
    request: Request,
    sensor: str | None = Query(
        default=None,
        description="Capteur à filtrer : terra | aqua | viirs_snpp.",
    ),
    pair: str | None = Query(
        default=None,
        description="Paire de capteurs : terra__aqua | aqua__viirs_snpp.",
    ),
    limit: int = Query(
        default=90,
        ge=1,
        le=365,
        description="Nombre maximum de semaines retournées.",
    ),
):
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    inv = store.get_json("inventory") or {}

    rows = []
    for item in (baselines.get("weekly", []) or []):
        if pair and item.get("pair") != pair:
            continue
        if sensor:
            s = (inv.get("sensors", {}) or {}).get(sensor)
            if not s:
                continue
        rows.append(
            {
                "sensor": item.get("sensor", ""),
                "week": item.get("week", ""),
                "obs_a_only": item.get("a_only", 0),
                "obs_b_only": item.get("b_only", 0),
                "obs_both": item.get("both", 0),
                "count": item.get("a_only", 0) + item.get("b_only", 0),
                "frp": item.get("frp", 0),
            }
        )

    return {
        "generated_at": (baselines.get("generated_at") or ""),
        "data_origin": (baselines.get("data_origin") or "unknown"),
        "grid_deg": baselines.get("primary", {}).get("grid_deg", 0.25),
        "window_days": baselines.get("primary", {}).get("window_days", 8),
        "rows": rows[:limit],
    }

        description="Paire de capteurs : terra__aqua | aqua__viirs_snpp.",
    ),
    limit: int = Query(
        default=90,
        ge=1,
        le=365,
        description="Nombre maximum de jours retournés (décroissant).",
    ),
):
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    inv = store.get_json("inventory") or {}
    primary = baselines.get("primary", {}) or {}
    grid_deg = primary.get("grid_deg", 0.25)
    window_days = primary.get("window_days", 8)

    rows = []
    for item in (baselines.get("daily", []) or []):
        if pair and item.get("pair") != pair:
            continue
        if sensor:
            s = (inv.get("sensors", {}) or {}).get(sensor)
            if not s:
                continue
        rows.append(
            {
                "sensor": (inv.get("sensors", {}) or {}).get(item.get("pair", ""), {}).get(
                    "label", item.get("pair", "")
                ),
                "date": item.get("date", ""),
                "obs_a_only": item.get("a_only", 0),
                "obs_b_only": item.get("b_only", 0),
                "obs_both": item.get("both", 0),
                "count": item.get("a_only", 0) + item.get("b_only", 0),
                "frp": item.get("frp", 0),
                "grid_deg": grid_deg,
                "window_days": window_days,
            }
        )

    return {
        "generated_at": (baselines.get("generated_at") or ""),
        "data_origin": (baselines.get("data_origin") or "unknown"),
        "period": f"{primary.get('start', '')} → {primary.get('end', '')}",
        "grid_deg": grid_deg,
        "window_days": window_days,
        "rows": rows[:limit],
    }

