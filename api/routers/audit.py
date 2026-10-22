"""Routes audit qualité (comptabilité des lignes, anomalies, distributions)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response

from api.routers.deps import apply_cache_headers, cache_guard, get_store
from api.services.queries import reject_unknown_params
from api.store import ArtifactStore

router = APIRouter()


@router.get(
    "/audit/summary",
    summary="Synthèse de l'audit qualité",
    description=(
        "Comptabilité des lignes, anomalies par catégorie, distributions (FRP, confiance, volumes "
        "mensuels), trous temporels. Les entrées détaillées des trous (200 max) ne sont incluses "
        "qu'avec detail=1."
    ),
    dependencies=[Depends(reject_unknown_params({"detail"}))],
)
def audit_summary(
    request: Request,
    response: Response,
    detail: int = Query(
        default=0,
        ge=0,
        le=1,
        description="1 = inclure le détail des trous temporels (200 max).",
    ),
) -> dict:
    guard = cache_guard(request, "audit.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    audit = store.require_json("audit.json")
    gaps = audit.get("temporal_gaps", {})
    payload = {
        "generated_at": audit.get("generated_at"),
        "data_origin": audit.get("data_origin"),
        "n_files": audit.get("n_files"),
        "row_accounting": audit.get("row_accounting"),
        "rows_by_classification": audit.get("rows_by_classification"),
        "anomalies_by_category": audit.get("anomalies_by_category"),
        "missing_values_by_column": audit.get("missing_values_by_column"),
        "frp_stats": audit.get("frp_stats"),
        "confidence_distribution_by_sensor": audit.get("confidence_distribution_by_sensor"),
        "volumes_by_month": audit.get("volumes_by_month"),
        "n_distinct_days_with_records": audit.get("n_distinct_days_with_records"),
        "temporal_gaps": {
            "n_entries": gaps.get("n_entries", 0),
            "entries": gaps.get("entries", []) if int(detail) == 1 else [],
        },
        "interpretation_warning": audit.get("interpretation_warning"),
        "note": (
            "Les jours sans enregistrement sont libellés « aucun_enregistrement » côté pipeline : "
            "une absence de détection n'est jamais présentée comme une absence de feu."
        ),
    }
    apply_cache_headers(request, response, "audit.json")
    return payload
