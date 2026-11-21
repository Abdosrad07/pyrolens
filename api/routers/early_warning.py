"""Early Warning — détection d'anomalies d'activité de feu par cellule.

Endpoints (montés sous ``/api/v1``) :
- GET /early-warning/summary          → compteurs par sévérité + métadonnées
- GET /early-warning/alerts           → liste des cellules évaluées/alertées
- GET /early-warning/alerts/{cell_id} → détail d'une cellule (score, baseline)

Le calcul est protégé par un cache indexé sur l'empreinte de la source et les
paramètres ; les filtres (severity, min_score, limit) sont appliqués après le
calcul et ne modifient jamais les métriques. Toutes les réponses portent
``estimate_kind = "historical_backtest"`` : les données FIRMS sont des
archives/NRT avec latence — aucune affirmation temps réel.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from api.errors import ApiError
from api.routers.deps import get_cfg, get_settings, reject_unknown_params
from api.services import early_warning as ew
from api.settings import Settings
from pyrolens.anomaly_detection import (
    DEFAULT_BASELINE_DAYS,
    DEFAULT_GRID_DEG,
    DEFAULT_RECENT_DAYS,
    SEVERITY_ORDER,
)
from pyrolens.config import Config

router = APIRouter(tags=["Early Warning"])

_SOURCE_DESC = "auto (réel sinon fixture) | fixture (synthétique) | raw (FIRMS normalisées)"


def _validate_params(
    grid_deg: float,
    recent_days: int,
    baseline_days: int,
    severity: str | None,
    min_score: float | None,
) -> None:
    if grid_deg <= 0 or grid_deg > 2.0:
        raise ApiError(400, "grid_deg invalide : valeur dans (0, 2.0] attendue.")
    if recent_days < 1 or recent_days > 365:
        raise ApiError(400, "recent_days invalide : entier dans [1, 365] attendu.")
    if baseline_days < recent_days or baseline_days > 3650:
        raise ApiError(400, "baseline_days invalide : >= recent_days et <= 3650 attendu.")
    if severity is not None and severity.upper() not in SEVERITY_ORDER:
        raise ApiError(
            400,
            f"severity invalide : une de {', '.join(SEVERITY_ORDER)} attendue.",
        )
    if min_score is not None and not (0.0 <= min_score <= 1.0):
        raise ApiError(400, "min_score invalide : valeur dans [0, 1] attendue.")


def _compute(
    request: Request,
    cfg: Config,
    settings: Settings,
    *,
    source: str,
    grid_deg: float,
    recent_days: int,
    baseline_days: int,
    reference_date: str | None,
    severity: str | None,
    min_score: float | None,
    limit: int | None,
    cell_id: str | None = None,
) -> dict[str, Any]:
    _validate_params(grid_deg, recent_days, baseline_days, severity, min_score)
    return ew.compute_early_warning(
        cfg,
        settings,
        request.app.state,
        source=source,
        grid_deg=grid_deg,
        recent_days=recent_days,
        baseline_days=baseline_days,
        reference_date=reference_date,
        severity=severity,
        min_score=min_score,
        limit=limit,
        cell_id=cell_id,
    )


@router.get(
    "/early-warning/summary",
    summary="Résumé des alertes d'anomalie par sévérité",
    description=(
        "Compteurs NORMAL/WATCH/MODERATE/HIGH sur la fenêtre récente, avec "
        "paramètres, période et provenance. `estimate_kind=historical_backtest` : "
        "pas une alerte temps réel."
    ),
    dependencies=[
        Depends(
            reject_unknown_params(
                {"source", "grid_deg", "recent_days", "baseline_days",
                 "reference_date", "severity", "min_score", "limit"}
            )
        )
    ],
)
def summary(
    request: Request,
    cfg: Config = Depends(get_cfg),
    settings: Settings = Depends(get_settings),
    source: str = Query(default="auto", description=_SOURCE_DESC),
    grid_deg: float = Query(default=DEFAULT_GRID_DEG, gt=0.0, le=2.0),
    recent_days: int = Query(default=DEFAULT_RECENT_DAYS, ge=1, le=365),
    baseline_days: int = Query(default=DEFAULT_BASELINE_DAYS, ge=1, le=3650),
    reference_date: str | None = Query(default=None, description="AAAA-MM-JJ (défaut : max des données)."),
    severity: str | None = Query(default=None, description="Filtre : NORMAL | WATCH | MODERATE | HIGH."),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int | None = Query(default=None, ge=1, le=5000),
) -> dict:
    payload = _compute(
        request, cfg, settings,
        source=source, grid_deg=grid_deg, recent_days=recent_days,
        baseline_days=baseline_days, reference_date=reference_date,
        severity=severity, min_score=min_score, limit=limit,
    )
    return ew.summary_view(payload)


@router.get(
    "/early-warning/alerts",
    summary="Liste des cellules évaluées avec leur sévérité",
    description=(
        "Chaque alerte porte cell_id, coordonnées, severity, score, ratio, "
        "compteurs récents et baseline (niveau de lissage, suffisance). "
        "Tri : sévérité décroissante puis score décroissant."
    ),
    dependencies=[
        Depends(
            reject_unknown_params(
                {"source", "grid_deg", "recent_days", "baseline_days",
                 "reference_date", "severity", "min_score", "limit"}
            )
        )
    ],
)
def alerts(
    request: Request,
    cfg: Config = Depends(get_cfg),
    settings: Settings = Depends(get_settings),
    source: str = Query(default="auto", description=_SOURCE_DESC),
    grid_deg: float = Query(default=DEFAULT_GRID_DEG, gt=0.0, le=2.0),
    recent_days: int = Query(default=DEFAULT_RECENT_DAYS, ge=1, le=365),
    baseline_days: int = Query(default=DEFAULT_BASELINE_DAYS, ge=1, le=3650),
    reference_date: str | None = Query(default=None, description="AAAA-MM-JJ (défaut : max des données)."),
    severity: str | None = Query(default=None, description="Filtre : NORMAL | WATCH | MODERATE | HIGH."),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int | None = Query(default=None, ge=1, le=5000),
) -> dict:
    payload = _compute(
        request, cfg, settings,
        source=source, grid_deg=grid_deg, recent_days=recent_days,
        baseline_days=baseline_days, reference_date=reference_date,
        severity=severity, min_score=min_score, limit=limit,
    )
    return ew.alerts_view(payload)


@router.get(
    "/early-warning/alerts/{cell_id}",
    summary="Détail d'une cellule (score, baseline, raisons)",
    description=(
        "cell_id au format `ci:cj` ou `ci_cj` (index de grille, origine "
        "-180/-90). 404 si la cellule n'a pas été évaluée (aucune activité "
        "récente ni baseline non nulle)."
    ),
    dependencies=[
        Depends(
            reject_unknown_params(
                {"source", "grid_deg", "recent_days", "baseline_days",
                 "reference_date"}
            )
        )
    ],
)
def alert_cell(
    request: Request,
    cell_id: str,
    cfg: Config = Depends(get_cfg),
    settings: Settings = Depends(get_settings),
    source: str = Query(default="auto", description=_SOURCE_DESC),
    grid_deg: float = Query(default=DEFAULT_GRID_DEG, gt=0.0, le=2.0),
    recent_days: int = Query(default=DEFAULT_RECENT_DAYS, ge=1, le=365),
    baseline_days: int = Query(default=DEFAULT_BASELINE_DAYS, ge=1, le=3650),
    reference_date: str | None = Query(default=None, description="AAAA-MM-JJ (défaut : max des données)."),
) -> dict:
    if ":" not in cell_id and "_" not in cell_id:
        raise ApiError(400, "cell_id invalide : format `ci:cj` ou `ci_cj` attendu (ex. 720:360).")
    # Le front utilise `ci_cj` ; le contrat canonique `ci:cj`. On normalise.
    if ":" not in cell_id:
        cell_id = cell_id.replace("_", ":", 1)
    payload = _compute(
        request, cfg, settings,
        source=source, grid_deg=grid_deg, recent_days=recent_days,
        baseline_days=baseline_days, reference_date=reference_date,
        severity=None, min_score=None, limit=None, cell_id=cell_id,
    )
    return ew.cell_view(payload, cell_id)
