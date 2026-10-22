"""Routes des comparaisons inter-capteurs : summary, séries, spatial, export."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import Response as RawResponse

from api.routers.deps import apply_cache_headers, cache_guard, get_store
from api.schemas import Meta, RowsResponse
from api.services import queries
from api.store import ArtifactStore

router = APIRouter()

_EXPORT_DATASETS = {
    "summary": "summary.csv",
    "jaccard_monthly": "jaccard_monthly.csv",
    "daily": "daily_divergence.csv",
    "monthly": "monthly_divergence.csv",
    "regions": "regional_divergence.csv",
    "spatial": "spatial_distribution.csv",
}


def _meta(baselines: dict, artifact: str, **filters) -> Meta:
    return Meta(
        generated_at=baselines.get("generated_at"),
        data_origin=baselines.get("data_origin"),
        artifact=artifact,
        filters={k: v for k, v in filters.items() if v is not None},
    )


@router.get(
    "/summary",
    response_model=RowsResponse,
    summary="Configurations de comparaison (Jaccard, tailles d'ensembles)",
    description=(
        "24 configurations publiées intégralement (2 paires × 3 grilles × 4 fenêtres). "
        "Filtres facultatifs ; une configuration inexistante renvoie 404."
    ),
    dependencies=[Depends(queries.reject_unknown_params({"pair", "grid_deg", "window_days"}))],
)
def summary(
    request: Request,
    response: Response,
    pair: str | None = Query(default=None, description="terra__aqua | aqua__viirs_snpp"),
    grid_deg: float | None = Query(default=None, description="0.1 | 0.25 | 0.5"),
    window_days: int | None = Query(default=None, ge=1, description="1 | 4 | 8 | 16"),
) -> RowsResponse:
    guard = cache_guard(request, "baselines.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    rows = queries.filter_summary(baselines, pair=pair, grid_deg=grid_deg, window_days=window_days)
    apply_cache_headers(request, response, "baselines.json")
    return RowsResponse(meta=_meta(baselines, "baselines.json", pair=pair, grid_deg=grid_deg, window_days=window_days), rows=rows)


@router.get(
    "/series/jaccard",
    response_model=RowsResponse,
    summary="Série mensuelle de recouvrement",
    description="Jaccard et comptes de divergence par mois pour une configuration donnée (pair requis).",
    dependencies=[Depends(queries.reject_unknown_params({"pair", "grid_deg", "window_days"}))],
)
def series_jaccard(
    request: Request,
    response: Response,
    pair: str = Query(description="terra__aqua | aqua__viirs_snpp"),
    grid_deg: float | None = Query(default=None),
    window_days: int | None = Query(default=None, ge=1),
) -> RowsResponse:
    guard = cache_guard(request, "baselines.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    rows = queries.jaccard_series(baselines, pair, grid_deg, window_days)
    apply_cache_headers(request, response, "baselines.json")
    return RowsResponse(meta=_meta(baselines, "baselines.json", pair=pair, grid_deg=grid_deg, window_days=window_days), rows=rows)


@router.get(
    "/series/divergence",
    response_model=RowsResponse,
    summary="Séries de divergence jour / mois / région",
    description=(
        "Publiées pour la configuration primaire uniquement (24 configurations × jour/mois/région "
        "ne sont pas toutes persistées dans l'artefact). Une résolution invalide renvoie 400."
    ),
    dependencies=[Depends(queries.reject_unknown_params({"pair", "resolution"}))],
)
def series_divergence(
    request: Request,
    response: Response,
    pair: str = Query(description="terra__aqua | aqua__viirs_snpp"),
    resolution: Literal["day", "month", "region"] = Query(description="day | month | region"),
) -> RowsResponse:
    guard = cache_guard(request, "baselines.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    rows = queries.divergence_series(baselines, pair, resolution)
    apply_cache_headers(request, response, "baselines.json")
    return RowsResponse(meta=_meta(baselines, "baselines.json", pair=pair, resolution=resolution), rows=rows)


@router.get(
    "/spatial",
    response_model=None,
    summary="Distribution spatiale par cellule (configuration primaire)",
    description="Cellules (i,j) avec comptages par capteur ; pagination limit/offset. Configuration primaire uniquement.",
    dependencies=[Depends(queries.reject_unknown_params({"pair", "grid_deg", "window_days", "limit", "offset"}))],
)
def spatial(
    request: Request,
    response: Response,
    pair: str = Query(description="terra__aqua | aqua__viirs_snpp"),
    grid_deg: float | None = Query(default=None),
    window_days: int | None = Query(default=None, ge=1),
    limit: int = Query(default=1000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
):
    guard = cache_guard(request, "baselines.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    page = queries.spatial_rows(baselines, pair, grid_deg, window_days, limit, offset)
    apply_cache_headers(request, response, "baselines.json")
    return {
        "meta": _meta(baselines, "baselines.json", pair=pair, grid_deg=grid_deg, window_days=window_days),
        "total": page["total"],
        "offset": page["offset"],
        "limit": page["limit"],
        "rows": page["rows"],
    }


@router.get(
    "/observability",
    summary="États d'observabilité par capteur",
    description=(
        "4 états du pipeline (détection observée, conditions plausibles sans détection, "
        "observabilité inconnue, indéterminé). Aucun état n'affirme une absence de feu."
    ),
    dependencies=[Depends(queries.reject_unknown_params({"grid_deg"}))],
)
def observability(
    request: Request,
    response: Response,
    grid_deg: float | None = Query(default=None, description="Maille publiée (configuration primaire)."),
) -> dict:
    guard = cache_guard(request, "observability.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    payload = store.require_json("observability.json")
    if grid_deg is not None and round(float(grid_deg) - float(payload.get("grid_deg", 0)), 6) != 0.0:
        from api.errors import ApiError

        raise ApiError(
            404,
            f"Observabilité publiée pour la maille {payload.get('grid_deg')}° uniquement.",
        )
    apply_cache_headers(request, response, "observability.json")
    return payload


@router.get(
    "/export",
    summary="Export des séries publiées (CSV ou JSON)",
    description=(
        "Exporte les lignes d'une table de comparaison. Les en-têtes CSV reprennent exactement "
        "les champs de l'artefact (reproductibilité). Le pair est requis hors `summary`."
    ),
    dependencies=[Depends(queries.reject_unknown_params({"dataset", "pair", "grid_deg", "window_days", "format"}))],
)
def export(
    request: Request,
    dataset: str = Query(description="summary | jaccard_monthly | daily | monthly | regions | spatial"),
    pair: str | None = Query(default=None),
    grid_deg: float | None = Query(default=None),
    window_days: int | None = Query(default=None, ge=1),
    format: Literal["csv", "json"] = Query(default="csv"),
):
    store: ArtifactStore = get_store(request)
    baselines = store.require_json("baselines.json")
    if dataset not in _EXPORT_DATASETS:
        from api.errors import ApiError

        raise ApiError(404, f"Export inconnu : {dataset}. Disponibles : {', '.join(sorted(_EXPORT_DATASETS))}.")

    if dataset == "summary":
        rows = queries.filter_summary(baselines, pair=pair, grid_deg=grid_deg, window_days=window_days)
    else:
        if pair is None:
            from api.errors import ApiError

            raise ApiError(400, "Le paramètre pair est requis pour cet export.")
        if dataset == "jaccard_monthly":
            rows = queries.jaccard_series(baselines, pair, grid_deg, window_days)
        else:
            resolution = {"daily": "day", "monthly": "month", "regions": "region"}[dataset]
            rows = queries.divergence_series(baselines, pair, resolution)

    filename = f"pyrolens_{_EXPORT_DATASETS[dataset]}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if format == "json":
        import json

        content = json.dumps(
            {
                "generated_at": baselines.get("generated_at"),
                "data_origin": baselines.get("data_origin"),
                "dataset": dataset,
                "rows": rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        return RawResponse(content=content, media_type="application/json; charset=utf-8", headers=headers)
    content = queries.rows_to_csv(rows)
    return RawResponse(content=content, media_type="text/csv; charset=utf-8", headers=headers)
