"""Catalogue des jeux de données : sources FIRMS + ensembles dérivés.

Le catalogue est reconstruit à partir des artefacts horodatés (audit, inventaire,
manifestes). Seuls des **noms de fichiers relatifs** apparaissent dans les
réponses : aucun chemin absolu local, aucune clé (`api_contract.md`, invariant 6).
"""

from __future__ import annotations

from typing import Any

from pyrolens import __version__ as PYROLENS_VERSION

from api.errors import ApiError
from api.store import ArtifactStore

SENSOR_DATASETS = {
    "modis": {
        "id": "firms_modis",
        "label": "NASA FIRMS — MODIS Terra & Aqua (C6.1)",
        "sensors": ["terra", "aqua"],
    },
    "viirs": {
        "id": "firms_viirs",
        "label": "NASA FIRMS — VIIRS Suomi-NPP 375 m",
        "sensors": ["viirs_snpp"],
    },
}

DERIVED_DATASETS = {
    "audit": {"artifact": "audit.json", "label": "Audit qualité (comptabilité, anomalies, distributions)"},
    "baselines": {"artifact": "baselines.json", "label": "Comparaisons inter-capteurs (Jaccard, divergences)"},
    "observability": {"artifact": "observability.json", "label": "États d'observabilité par cellule"},
    "scientific_report": {"artifact": "scientific_report.md", "label": "Rapport scientifique (Markdown)"},
}


def _manifest_provenance(store: ArtifactStore) -> dict[str, Any]:
    """Provenance d'acquisition : manifeste d'artefact (horodaté), sans chemin local."""
    if not store.has("downloads.json"):
        return {"manifest": "downloads.json", "available": False}
    manifest = store.get_json("downloads.json") or {}
    entries = manifest.get("entries", [])
    statuses: dict[str, int] = {}
    for entry in entries:
        key = str(entry.get("status", "unknown"))
        statuses[key] = statuses.get(key, 0) + 1
    return {
        "manifest": "downloads.json",
        "available": True,
        "generated_at": manifest.get("generated_at"),
        "entry_count": manifest.get("entry_count", len(entries)),
        "statuses": statuses,
        "note": "URL FIRMS publiées en gabarit <FIRMS_MAP_KEY> ; la clé reste côté pipeline.",
    }


def build_catalog(store: ArtifactStore) -> dict[str, Any]:
    audit = store.require_json("audit.json")
    inventory = store.require_json("inventory.json")

    files = audit.get("files", [])
    datasets: list[dict[str, Any]] = []

    for kind, spec in SENSOR_DATASETS.items():
        kind_files = [f for f in files if f.get("sensor") == kind]
        if not kind_files:
            continue
        satellites = sorted(set(audit.get("satellites", [])))
        dates = [f.get("date_min") for f in kind_files if f.get("date_min")] + [
            f.get("date_max") for f in kind_files if f.get("date_max")
        ]
        versions_by_sensor = audit.get("versions", {})
        datasets.append(
            {
                "id": spec["id"],
                "label": spec["label"],
                "kind": "source",
                "data_origin": audit.get("data_origin"),
                "sensors": spec["sensors"],
                "satellites_observed": satellites,
                "n_files": len(kind_files),
                "n_records": sum(f.get("n_records", 0) for f in kind_files),
                "n_rows_analysable": sum(f.get("n_rows_analysable", 0) for f in kind_files),
                "n_rows_outside_emprise": sum(f.get("n_rows_outside_emprise", 0) for f in kind_files),
                "n_anomalies": sum(f.get("n_anomalies", 0) for f in kind_files),
                "period": {"start": min(dates) if dates else None, "end": max(dates) if dates else None},
                "versions": versions_by_sensor,
                "quality_endpoint": "/api/v1/audit/summary",
                "provenance": {
                    "source": inventory.get("source"),
                    "generated_at": audit.get("generated_at"),
                    "software": f"pyrolens {PYROLENS_VERSION}",
                },
            }
        )

    for key, spec in DERIVED_DATASETS.items():
        name = spec["artifact"]
        if not store.has(name):
            datasets.append(
                {
                    "id": key,
                    "label": spec["label"],
                    "kind": "derived",
                    "available": False,
                    "note": "Artefact absent : exécuter le pipeline (pyrolens).",
                }
            )
            continue
        generated_at = None
        data_origin = None
        if name.endswith(".json"):
            payload = store.get_json(name) or {}
            generated_at = payload.get("generated_at")
            data_origin = payload.get("data_origin")
        datasets.append(
            {
                "id": key,
                "label": spec["label"],
                "kind": "derived",
                "available": True,
                "artifact": name,
                "generated_at": generated_at,
                "data_origin": data_origin,
                "software": f"pyrolens {PYROLENS_VERSION}",
            }
        )

    return {
        "generated_at": audit.get("generated_at"),
        "data_origin": audit.get("data_origin"),
        "period": inventory.get("period"),
        "datasets": datasets,
        "provenance": _manifest_provenance(store),
        "note": (
            "Les jeux « source » sont les fenêtres canoniques issues de `pyrolens normalize` ; "
            "les jeux « dérivé » sont recalculés par le pipeline et horodatés."
        ),
    }


def dataset_detail(store: ArtifactStore, dataset_id: str) -> dict[str, Any]:
    audit = store.require_json("audit.json")
    files = audit.get("files", [])

    for kind, spec in SENSOR_DATASETS.items():
        if spec["id"] == dataset_id:
            kind_files = [f for f in files if f.get("sensor") == kind]
            if not kind_files:
                raise ApiError(404, f"Jeu de données inconnu : {dataset_id}.")
            return {
                "generated_at": audit.get("generated_at"),
                "data_origin": audit.get("data_origin"),
                "dataset": {
                    "id": spec["id"],
                    "label": spec["label"],
                    "sensors": spec["sensors"],
                    "n_files": len(kind_files),
                    "files": [
                        {
                            "file": f.get("file"),
                            "sensor": f.get("sensor"),
                            "n_records": f.get("n_records"),
                            "n_rows_analysable": f.get("n_rows_analysable"),
                            "n_rows_outside_emprise": f.get("n_rows_outside_emprise"),
                            "n_anomalies": f.get("n_anomalies"),
                            "n_duplicate_rows": f.get("n_duplicate_rows"),
                            "date_min": f.get("date_min"),
                            "date_max": f.get("date_max"),
                        }
                        for f in kind_files
                    ],
                    "provenance": _manifest_provenance(store),
                },
            }

    if dataset_id in DERIVED_DATASETS:
        spec = DERIVED_DATASETS[dataset_id]
        name = spec["artifact"]
        if not store.has(name):
            raise ApiError(404, f"Jeu de données indisponible : {dataset_id} (artefact absent).")
        payload = store.get_json(name) if name.endswith(".json") else None
        return {
            "generated_at": payload.get("generated_at") if payload else None,
            "data_origin": payload.get("data_origin") if payload else None,
            "dataset": {
                "id": dataset_id,
                "label": spec["label"],
                "kind": "derived",
                "artifact": name,
                "software": f"pyrolens {PYROLENS_VERSION}",
            },
        }

    raise ApiError(404, f"Jeu de données inconnu : {dataset_id}.")
