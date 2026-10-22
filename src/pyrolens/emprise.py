"""Emprise géographique documentée (polygone administratif Natural Earth).

La bbox de configuration est une boîte englobante utilisée pour les requêtes ;
le polygon est la géométrie de référence pour filtrer les détections.
"""

from __future__ import annotations

from pathlib import Path

import shapely
from shapely.geometry import box, shape
from shapely.geometry.base import BaseGeometry


def load_region_polygon(geojson_path: Path, iso3: str) -> BaseGeometry:
    """Charge le polygone d'un pays depuis un GeoJSON d'administration (Natural Earth)."""
    import json

    data = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    for feat in data["features"]:
        props = feat.get("properties", {})
        code = props.get("ADM0_A3") or props.get("ISO_A3") or props.get("iso_a3")
        if code == iso3:
            return shape(feat["geometry"])
    raise KeyError(f"Pays {iso3} introuvable dans {geojson_path}")


def bbox_polygon(bbox: list[float]) -> BaseGeometry:
    west, south, east, north = bbox
    return box(west, south, east, north)


def inside_mask(geometry: BaseGeometry, lons: list[float], lats: list[float]) -> list[bool]:
    """Test vectorisé point-in-polygon (aucune correction de coordonnées)."""
    if not lons:
        return []
    return [bool(flag) for flag in shapely.contains_xy(geometry, lons, lats)]


def region_of(lon: float, lat: float, bbox: list[float], n_regions: int = 3) -> str:
    """Découpage régional explicite : terciles de latitude de la bbox (proxy documenté)."""
    _west, south, east, north = bbox
    if not (south <= lat <= north):
        return "hors_emprise"
    step = (north - south) / n_regions
    idx = int((lat - south) / step) if step > 0 else 0
    idx = min(idx, n_regions - 1)
    labels = ["sud", "centre", "nord"]
    if n_regions == 3:
        return labels[idx]
    return f"bande_{idx + 1}"
