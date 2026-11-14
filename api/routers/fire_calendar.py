"""Fire Calendar — agrégations temporelles quotidiennes, hebdomadaires et mensuelles.

Endpoints (montés sous ``/api/v1``) :
- GET /fire-calendar/daily
- GET /fire-calendar/weekly
- GET /fire-calendar/monthly
- GET /fire-calendar/timeseries

Les séries sont calculées à partir de l'artefact ``baselines.json`` (configuration
primaire : ``primary.grid_deg`` / ``primary.window_days``). Les lignes quotidiennes
et mensuelles sont publiées **par paire** (``terra__aqua``, ``aqua__viirs_snpp``) ;
il n'existe pas de découpage par capteur individuel dans l'artefact. Les périodes
sont en UTC (``YYYY-MM-DD`` / ``YYYY-MM`` / ``YYYY-Www``).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, Response

from api.routers.deps import (
    apply_cache_headers,
    cache_guard,
    get_store,
    reject_unknown_params,
)
from api.store import ArtifactStore

router = APIRouter(tags=["Fire Calendar"])


# ---------- aide -----------------------------------------------------------


def _in_range(day: str, start: str | None, end: str | None) -> bool:
    """Filtre de période tolérant : ``start``/``end`` en YYYY-MM-DD ou YYYY-MM."""
    if not start and not end:
        return True
    if start:
        lo = start if len(start) == 10 else f"{start}-01"
        if day < lo:
            return False
    if end:
        hi = end if len(end) == 10 else f"{end}-31"
        if day > hi:
            return False
    return True


def _iso_week(day: str) -> str | None:
    """Semaine ISO ``YYYY-Www`` d'une date ``YYYY-MM-DD`` (None si invalide)."""
    try:
        y, w, _ = date.fromisoformat(day).isocalendar()
    except ValueError:
        return None
    return f"{y}-W{w:02d}"


def _recent(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Conserve les ``limit`` lignes les plus récentes (ordre chronologique gardé)."""
    return rows[-limit:] if len(rows) > limit else rows


def _base_payload(baselines: dict, **extra: Any) -> dict[str, Any]:
    return {
        "generated_at": baselines.get("generated_at") or "",
        "data_origin": baselines.get("data_origin") or "unknown",
        "key_definitions": baselines.get("key_definitions"),
        **extra,
    }


# ---------- daily ----------------------------------------------------------


@router.get(
    "/fire-calendar/daily",
    summary="Série quotidienne de divergence par paire",
    description=(
        "Comptages quotidiens ``a_only`` / ``b_only`` / ``both`` par paire de capteurs "
        "(configuration primaire). ``total`` = a_only + b_only ; les dates sont en UTC."
    ),
    dependencies=[Depends(reject_unknown_params({"pair", "start", "end", "limit"}))],
)
def daily(
    request: Request,
    response: Response,
    pair: str | None = Query(default=None, description="terra__aqua | aqua__viirs_snpp"),
    start: str | None = Query(default=None, description="Début YYYY-MM-DD ou YYYY-MM (UTC)."),
    end: str | None = Query(default=None, description="Fin YYYY-MM-DD ou YYYY-MM (UTC)."),
    limit: int = Query(default=4000, ge=1, le=20000, description="Jours les plus récents retournés."),
) -> dict:
    guard = cache_guard(request, "baselines.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")

    rows = []
    for item in baselines.get("daily", []) or []:
        if pair and item.get("pair") != pair:
            continue
        day = item.get("date", "")
        if not _in_range(day, start, end):
            continue
        a_only = item.get("a_only", 0)
        b_only = item.get("b_only", 0)
        rows.append(
            {
                "pair": item.get("pair", ""),
                "date": day,
                "a_only": a_only,
                "b_only": b_only,
                "both": item.get("both", 0),
                "total": a_only + b_only,
            }
        )
    rows.sort(key=lambda r: (r["date"], r["pair"]))
    apply_cache_headers(request, response, "baselines.json")
    return _base_payload(
        baselines,
        pair=pair,
        start=start or "",
        end=end or "",
        rows=_recent(rows, limit),
    )


# ---------- weekly ---------------------------------------------------------


@router.get(
    "/fire-calendar/weekly",
    summary="Série hebdomadaire (semaines ISO) par paire",
    description=(
        "Agrège les comptages quotidiens en semaines ISO ``YYYY-Www``. "
        "``total`` = a_only + b_only sur la semaine."
    ),
    dependencies=[Depends(reject_unknown_params({"pair", "start", "end", "limit"}))],
)
def weekly(
    request: Request,
    response: Response,
    pair: str | None = Query(default=None, description="terra__aqua | aqua__viirs_snpp"),
    start: str | None = Query(default=None, description="Début YYYY-MM-DD ou YYYY-MM (UTC)."),
    end: str | None = Query(default=None, description="Fin YYYY-MM-DD ou YYYY-MM (UTC)."),
    limit: int = Query(default=400, ge=1, le=2000, description="Semaines les plus récentes retournées."),
) -> dict:
    guard = cache_guard(request, "baselines.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")

    buckets: dict[tuple[str, str], dict[str, int]] = {}
    for item in baselines.get("daily", []) or []:
        if pair and item.get("pair") != pair:
            continue
        week = _iso_week(item.get("date", ""))
        if week is None or not _in_range(item.get("date", ""), start, end):
            continue
        key = (item.get("pair", ""), week)
        bucket = buckets.setdefault(key, {"a_only": 0, "b_only": 0, "both": 0})
        for field in ("a_only", "b_only", "both"):
            bucket[field] += int(item.get(field, 0) or 0)

    rows = [
        {
            "pair": p,
            "week": w,
            "a_only": b["a_only"],
            "b_only": b["b_only"],
            "both": b["both"],
            "total": b["a_only"] + b["b_only"],
        }
        for (p, w), b in buckets.items()
    ]
    rows.sort(key=lambda r: (r["week"], r["pair"]))
    apply_cache_headers(request, response, "baselines.json")
    return _base_payload(
        baselines,
        pair=pair,
        start=start or "",
        end=end or "",
        rows=_recent(rows, limit),
    )


# ---------- monthly --------------------------------------------------------


@router.get(
    "/fire-calendar/monthly",
    summary="Séries mensuelles de divergence et de Jaccard",
    description=(
        "Comptages mensuels ``a_only`` / ``b_only`` / ``both`` par paire, plus la série "
        "de Jaccard de la configuration primaire (``grid_deg`` / ``window_days``)."
    ),
    dependencies=[Depends(reject_unknown_params({"pair", "limit"}))],
)
def monthly(
    request: Request,
    response: Response,
    pair: str | None = Query(default=None, description="terra__aqua | aqua__viirs_snpp"),
    limit: int = Query(default=120, ge=1, le=600, description="Mois les plus récents retournés."),
) -> dict:
    guard = cache_guard(request, "baselines.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")

    rows = []
    for item in baselines.get("monthly", []) or []:
        if pair and item.get("pair") != pair:
            continue
        a_only = item.get("a_only", 0)
        b_only = item.get("b_only", 0)
        rows.append(
            {
                "pair": item.get("pair", ""),
                "month": item.get("month", ""),
                "a_only": a_only,
                "b_only": b_only,
                "both": item.get("both", 0),
                "total": a_only + b_only,
            }
        )
    rows.sort(key=lambda r: (r["month"], r["pair"]))

    primary = baselines.get("primary", {}) or {}
    jaccard_rows = []
    for item in baselines.get("jaccard_monthly", []) or []:
        if pair and item.get("pair") != pair:
            continue
        if item.get("grid_deg") != primary.get("grid_deg"):
            continue
        if item.get("window_days") != primary.get("window_days"):
            continue
        jaccard_rows.append(
            {
                "pair": item.get("pair", ""),
                "month": item.get("month", ""),
                "jaccard": item.get("jaccard"),
                "total_jaccard": item.get("total_jaccard"),
                "a_only": item.get("a_only", 0),
                "b_only": item.get("b_only", 0),
                "both": item.get("both", 0),
            }
        )
    jaccard_rows.sort(key=lambda r: (r["month"], r["pair"]))

    apply_cache_headers(request, response, "baselines.json")
    return _base_payload(
        baselines,
        pair=pair,
        grid_deg=primary.get("grid_deg"),
        window_days=primary.get("window_days"),
        monthly=_recent(rows, limit),
        jaccard_monthly=_recent(jaccard_rows, limit),
    )


# ---------- timeseries -----------------------------------------------------


@router.get(
    "/fire-calendar/timeseries",
    summary="Série temporelle pour graphiques (observations, Jaccard, divergence)",
    description=(
        "``metric=observation`` : séries quotidiennes par paire. "
        "``metric=jaccard`` : Jaccard mensuel de la configuration primaire. "
        "``metric=monthly`` : comptages mensuels de divergence par paire."
    ),
    dependencies=[
        Depends(
            reject_unknown_params({"start", "end", "pair", "metric", "limit"})
        )
    ],
)
def timeseries(
    request: Request,
    response: Response,
    start: str | None = Query(default=None, description="Début YYYY-MM-DD ou YYYY-MM (UTC)."),
    end: str | None = Query(default=None, description="Fin YYYY-MM-DD ou YYYY-MM (UTC)."),
    pair: str | None = Query(default=None, description="terra__aqua | aqua__viirs_snpp"),
    metric: str = Query(
        default="observation",
        description="observation | jaccard | monthly",
    ),
    limit: int = Query(default=4000, ge=1, le=20000),
) -> dict:
    guard = cache_guard(request, "baselines.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")

    if metric not in ("observation", "jaccard", "monthly"):
        from api.errors import ApiError

        raise ApiError(400, "Métrique inconnue : observation | jaccard | monthly.")

    primary = baselines.get("primary", {}) or {}
    rows: list[dict[str, Any]] = []

    if metric == "observation":
        source = baselines.get("daily", []) or []
        date_key = "date"
    elif metric == "jaccard":
        source = [
            item
            for item in (baselines.get("jaccard_monthly", []) or [])
            if item.get("grid_deg") == primary.get("grid_deg")
            and item.get("window_days") == primary.get("window_days")
        ]
        date_key = "month"
    else:
        source = baselines.get("monthly", []) or []
        date_key = "month"

    for item in source:
        if pair and item.get("pair") != pair:
            continue
        period = item.get(date_key, "")
        # les mois (YYYY-MM) sont comparés sur 7 caractères, les jours sur 10
        if not _in_range(period if len(period) == 10 else f"{period}-01", start, end):
            continue
        row = {"pair": item.get("pair", ""), date_key: period}
        for field in ("a_only", "b_only", "both", "jaccard", "total_jaccard"):
            if field in item:
                row[field] = item[field]
        row["total"] = int(item.get("a_only", 0) or 0) + int(item.get("b_only", 0) or 0)
        rows.append(row)

    rows.sort(key=lambda r: (r[date_key], r["pair"]))
    apply_cache_headers(request, response, "baselines.json")
    return _base_payload(
        baselines,
        start=start or "",
        end=end or "",
        pair=pair,
        metric=metric,
        rows=_recent(rows, limit),
    )
