"""Inventaire des produits via l'API CMR (NASA Earthdata) - accès public, sans clé.

La recherche CMR est ouverte : elle permet de vérifier RÉELLEMENT quelles
collections/granules existent pour l'emprise et la période cibles, avant tout
téléchargement massif. Le téléchargement des granules reste protégé
(Earthdata Login) : voir download.py.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

CMR_SEARCH = "https://cmr.earthdata.nasa.gov/search"


def _get(url: str, params: dict[str, Any], timeout: float = 30.0) -> httpx.Response:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        return client.get(url, params=params)


def collection_versions(short_name: str) -> list[dict[str, Any]]:
    """Versions de collection disponibles pour un short_name (statut, couverture)."""
    resp = _get(
        f"{CMR_SEARCH}/collections.json",
        {"short_name": short_name, "page_size": 20},
    )
    resp.raise_for_status()
    entries = resp.json().get("feed", {}).get("entry", [])
    out = []
    for e in entries:
        out.append(
            {
                "short_name": e.get("short_name"),
                "version_id": e.get("version_id"),
                "title": e.get("title"),
                "time_start": e.get("time_start"),
                "time_end": e.get("time_end"),
                "data_center": e.get("data_center"),
                "summary": (e.get("summary") or "")[:400],
            }
        )
    return out


def granule_count(short_name: str, version: str, bbox: list[float], temporal: str) -> int:
    """Nombre de granules pour emprise + période (en-tête CMR-Hits)."""
    resp = _get(
        f"{CMR_SEARCH}/granules.json",
        {
            "short_name": short_name,
            "version": version,
            "bounding_box": ",".join(str(v) for v in bbox),
            "temporal": temporal,
            "page_size": 0,
        },
    )
    resp.raise_for_status()
    hits = resp.headers.get("cmr-hits", "0")
    return int(hits)


def sample_granules(short_name: str, version: str, bbox: list[float], temporal: str, n: int = 3) -> list[dict[str, Any]]:
    resp = _get(
        f"{CMR_SEARCH}/granules.json",
        {
            "short_name": short_name,
            "version": version,
            "bounding_box": ",".join(str(v) for v in bbox),
            "temporal": temporal,
            "page_size": n,
        },
    )
    resp.raise_for_status()
    out = []
    for g in resp.json().get("feed", {}).get("entry", []):
        links = [
            l.get("href")
            for l in g.get("links", [])
            if l.get("href", "").startswith("https://") and l.get("href", "").endswith((".hdf", ".nc", ".tif"))
        ]
        out.append({"title": g.get("title"), "id": g.get("id"), "download_links": links[:2]})
    return out


def run_inventory(cfg, raw_dir: Path) -> dict[str, Any]:
    """Inventaire réel (exécuté) : versions de collection + granules par année et capteur."""
    bbox = cfg.get("region.bbox")
    start_year = int(str(cfg.get("period.start"))[:4])
    end_year = int(str(cfg.get("period.end"))[:4])

    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "NASA CMR Search API (accès public, sans clé)",
        "base_url": CMR_SEARCH,
        "bbox_note": "bounding_box CMR = boîte englobante [west,south,east,north], pas la frontière",
        "period": {"start": cfg.get("period.start"), "end": cfg.get("period.end")},
        "sensors": {},
    }

    for key, spec in (cfg.get("sensors") or {}).items():
        short_name = spec.get("cmr_short_name")
        configured_version = str(spec.get("cmr_version"))
        if not short_name:
            continue
        versions = collection_versions(short_name)
        chosen = next(
            (v for v in versions if str(v.get("version_id")) == configured_version),
            versions[0] if versions else None,
        )
        entry: dict[str, Any] = {
            "label": spec.get("label"),
            "short_name": short_name,
            "configured_version": configured_version,
            "versions_found": [
                {"version_id": v.get("version_id"), "time_start": v.get("time_start"), "title": v.get("title")}
                for v in versions
            ],
            "version_used": chosen.get("version_id") if chosen else None,
            "years": {},
        }
        if chosen:
            version = str(chosen.get("version_id"))
            for year in range(start_year, end_year + 1):
                temporal = f"{year}-01-01T00:00:00Z,{year}-12-31T23:59:59Z"
                try:
                    count = granule_count(short_name, version, bbox, temporal)
                    entry["years"][str(year)] = {"granules_in_bbox": count, "temporal": temporal}
                except Exception as exc:  # noqa: BLE001 - enregistré, jamais masqué
                    entry["years"][str(year)] = {"error": str(exc), "temporal": temporal}
            try:
                entry["sample_granules_2019"] = sample_granules(
                    short_name, version, bbox, "2019-01-01T00:00:00Z,2019-02-01T00:00:00Z"
                )
            except Exception as exc:  # noqa: BLE001
                entry["sample_granules_2019"] = {"error": str(exc)}
        payload["sensors"][key] = entry

    raw_cmr = raw_dir / "cmr"
    raw_cmr.mkdir(parents=True, exist_ok=True)
    (raw_cmr / "inventory.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
