"""Validation d'un CSV FIRMS téléversé, sans jamais l'intégrer au pipeline.

Le fichier est traité **en mémoire de travail** (répertoire temporaire supprimé
à la fin), avec la même politique d'audit que le pipeline : aucune correction,
aucune substitution, chaque anomalie tracée avec son numéro de ligne. Rien n'est
écrit dans ``data/raw`` ; la réponse porte ``data_origin = "uploaded_file"``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pyrolens import __version__ as PYROLENS_VERSION
from pyrolens.audit import audit_file
from pyrolens.config import Config

from api.errors import ApiError
from api.settings import Settings

_MAX_RAW_VALUE = 200


def _load_geometry(cfg: Config):
    """Polygone d'emprise documenté si disponible (sinon filtre bbox seul)."""
    geo_file = cfg.path_of("raw") / "geo" / "ne_110m_admin_0_countries.geojson"
    if not geo_file.exists():
        return None
    try:
        from pyrolens.emprise import load_region_polygon

        return load_region_polygon(geo_file, cfg.get("region.iso3", "CMR"))
    except Exception:  # noqa: BLE001 — geometry indisponible : on dégrade, on ne casse pas
        return None


def validate_csv(path: Path, original_name: str, cfg: Config, settings: Settings,
                 geometry=None) -> dict[str, Any]:
    """Audite un CSV déjà écrit sur disque temporaire et retourne le résumé API."""
    try:
        file_audit = audit_file(
            path,
            bbox=cfg.get("region.bbox"),
            iso3=cfg.get("region.iso3", "CMR"),
            geometry=geometry,
            n_regions=int(cfg.get("analysis.n_regions", 3)),
        )
    except ValueError as exc:
        raise ApiError(400, f"Fichier illisible : {exc}") from exc

    if "missing_required_column" in {a.category for a in file_audit.anomalies}:
        missing = sorted({a.column for a in file_audit.anomalies if a.category == "missing_required_column"})
        raise ApiError(400, f"Colonnes obligatoires absentes : {', '.join(missing)}.")

    anomalies_by_category: dict[str, int] = {}
    for anomaly in file_audit.anomalies:
        anomalies_by_category[anomaly.category] = anomalies_by_category.get(anomaly.category, 0) + 1

    dates = [d.isoformat() for d in file_audit.dates]
    sample = [
        {
            "line_number": a.line_number,
            "column": a.column,
            "raw_value": a.raw_value[:_MAX_RAW_VALUE],
            "category": a.category,
            "reason": a.reason,
            "classification": a.classification,
        }
        for a in file_audit.anomalies[: settings.max_anomalies_sample]
    ]

    return {
        "generated_at": None,  # renseigné par le routeur (horodatage de la requête)
        "data_origin": "uploaded_file",
        "dataset": {
            "file": Path(original_name).name,  # nom seul : jamais de chemin
            "sensor": file_audit.sensor,
            "satellites_observed": sorted(file_audit.satellites),
            "versions_observed": sorted(file_audit.versions),
        },
        "counts": {
            "n_records": file_audit.n_records,
            "n_rows_analysable": len(file_audit.rows),
            "n_anomalies": len(file_audit.anomalies),
            "n_anomalies_sampled": len(sample),
        },
        "period": {"start": min(dates) if dates else None, "end": max(dates) if dates else None},
        "anomalies_by_category": dict(sorted(anomalies_by_category.items())),
        "anomalies_sample": sample,
        "software": f"pyrolens {PYROLENS_VERSION}",
        "integrated": False,
        "note": (
            "Fichier validé en mémoire, jamais intégré aux données du pipeline. "
            "Aucune correction appliquée : valeurs invalides ou hors emprise tracées, jamais réparées. "
            "Une absence de détection n'est jamais interprétée comme une absence de feu."
        ),
    }
