"""Service « early warning » : détection d'anomalies d'activité de feu.

Enveloppe ``pyrolens.anomaly_detection`` pour l'API : résolution de la source
CSV (fixture / raw / source_dir), calcul protégé par un cache indexé sur
l'empreinte de la source et les paramètres, et payload JSON propagant la
provenance complète.

Aucune affirmation temps réel : le payload porte ``estimate_kind =
"historical_backtest"`` et les données FIRMS sont des archives/NRT avec
latence documentée.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from pyrolens.anomaly_detection import (
    DEFAULT_BASELINE_DAYS,
    DEFAULT_GRID_DEG,
    DEFAULT_MIN_RECENT_DETECTIONS,
    DEFAULT_RECENT_DAYS,
    DEFAULT_THRESHOLDS,
    run_anomaly_detection,
    source_digest,
)
from pyrolens.config import Config

from api.errors import ApiError
from api.services.experiments import data_origin_of, resolve_source_dir
from api.settings import Settings

_CACHE_ATTR = "early_warning_cache"


def _cache_store(app_state: Any) -> dict[str, Any]:
    cache = getattr(app_state, _CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(app_state, _CACHE_ATTR, cache)
    return cache


def _resolve_csvs(cfg: Config, settings: Settings, source: str) -> tuple[Path, list[Path]]:
    source_dir = resolve_source_dir(cfg, settings, source)
    csv_paths = sorted(source_dir.glob("*.csv"))
    if not csv_paths:
        raise ApiError(409, "Source vide : aucun CSV à analyser.")
    return source_dir, csv_paths


def compute_early_warning(
    cfg: Config,
    settings: Settings,
    app_state: Any,
    *,
    source: str = "auto",
    grid_deg: float = DEFAULT_GRID_DEG,
    recent_days: int = DEFAULT_RECENT_DAYS,
    baseline_days: int = DEFAULT_BASELINE_DAYS,
    reference_date: str | None = None,
    severity: str | None = None,
    min_score: float | None = None,
    limit: int | None = None,
    cell_id: str | None = None,
) -> dict[str, Any]:
    """Calcule (ou sert depuis le cache) la détection d'anomalies complète."""
    source_dir, csv_paths = _resolve_csvs(cfg, settings, source)

    ref_date = None
    if reference_date:
        from datetime import date

        try:
            ref_date = date.fromisoformat(reference_date)
        except ValueError:
            raise ApiError(400, "reference_date invalide : format AAAA-MM-JJ attendu.")

    # Clé de cache : source (digest) + paramètres de calcul (pas les filtres
    # de présentation, qui sont appliqués après coup sur le payload complet).
    cache_key = hashlib.sha256(
        "|".join(
            [
                str(source_dir.resolve()),
                source_digest(csv_paths),
                f"{grid_deg}",
                f"{recent_days}",
                f"{baseline_days}",
                reference_date or "",
            ]
        ).encode()
    ).hexdigest()

    cache = _cache_store(app_state)
    payload = cache.get(cache_key)
    if payload is None:
        payload = run_anomaly_detection(
            csv_paths,
            grid_deg=grid_deg,
            recent_days=recent_days,
            baseline_days=baseline_days,
            reference_date=ref_date,
        )
        # La provenance « source » est celle du pipeline (raw vs fixture),
        # pas dérivée du seul nom de dossier.
        payload["data_origin"] = data_origin_of(source_dir)
        payload["source"]["source_dir_kind"] = (
            "fixture" if "fixture" in source_dir.resolve().parts else "raw"
        )
        cache[cache_key] = payload
        # borne le cache : 8 configurations max (les plus récentes)
        if len(cache) > 8:
            for old_key in list(cache.keys())[: len(cache) - 8]:
                cache.pop(old_key, None)

    return _apply_filters(payload, severity=severity, min_score=min_score,
                          limit=limit, cell_id=cell_id)


def _apply_filters(
    payload: dict[str, Any],
    *,
    severity: str | None,
    min_score: float | None,
    limit: int | None,
    cell_id: str | None,
) -> dict[str, Any]:
    """Filtres de présentation : ne modifient jamais les métriques du payload."""
    alerts = payload.get("alerts", [])
    if cell_id is not None:
        alerts = [a for a in alerts if a.get("cell_id") == cell_id]
    if severity is not None:
        alerts = [a for a in alerts if a.get("severity") == severity.upper()]
    if min_score is not None:
        alerts = [a for a in alerts if float(a.get("score", 0.0)) >= min_score]
    total = len(alerts)
    if limit is not None:
        alerts = alerts[:limit]

    out = dict(payload)
    out["alerts"] = alerts
    out["filters"] = {
        "severity": severity,
        "min_score": min_score,
        "limit": limit,
        "cell_id": cell_id,
        "matched": total,
    }
    return out


def summary_view(payload: dict[str, Any]) -> dict[str, Any]:
    """Vue « summary » : compteurs par sévérité + métadonnées, sans la liste."""
    return {
        "generated_at": payload.get("generated_at"),
        "estimate_kind": payload.get("estimate_kind"),
        "data_origin": payload.get("data_origin"),
        "params": payload.get("params"),
        "period": payload.get("period"),
        "summary": payload.get("summary"),
        "source": payload.get("source"),
        "notes": payload.get("notes"),
        "elapsed_s": payload.get("elapsed_s"),
    }


def alerts_view(payload: dict[str, Any]) -> dict[str, Any]:
    """Vue « alerts » : la liste filtrée + métadonnées de pagination."""
    return {
        "generated_at": payload.get("generated_at"),
        "estimate_kind": payload.get("estimate_kind"),
        "data_origin": payload.get("data_origin"),
        "params": payload.get("params"),
        "period": payload.get("period"),
        "summary": payload.get("summary"),
        "filters": payload.get("filters"),
        "alerts": payload.get("alerts", []),
        "notes": payload.get("notes"),
    }


def cell_view(payload: dict[str, Any], cell_id: str) -> dict[str, Any]:
    """Vue « cell » : détail d'une cellule + sa baseline et son score."""
    for alert in payload.get("alerts", []):
        if alert.get("cell_id") == cell_id:
            return {
                "generated_at": payload.get("generated_at"),
                "estimate_kind": payload.get("estimate_kind"),
                "data_origin": payload.get("data_origin"),
                "params": payload.get("params"),
                "period": payload.get("period"),
                "cell": alert,
                "notes": payload.get("notes"),
            }
    raise ApiError(404, f"Cellule inconnue ou sans activité récente : {cell_id}.")
