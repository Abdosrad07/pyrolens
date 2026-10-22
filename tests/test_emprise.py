"""Tests de l'emprise documentée (polygone vs bbox) et du découpage régional."""

from __future__ import annotations

from pathlib import Path

import pytest
from shapely.geometry import box, Point

from pyrolens.emprise import bbox_polygon, inside_mask, region_of

BBOX = [8.4, 4.1, 16.4, 13.2]
GEO = Path(__file__).resolve().parents[1] / "data" / "raw" / "geo" / "ne_110m_admin_0_countries.geojson"


def test_bbox_polygon_matches_config():
    geom = bbox_polygon(BBOX)
    west, south, east, north = geom.bounds
    assert (west, south, east, north) == tuple(BBOX)


def test_inside_mask_distinguishes_bbox_and_polygon():
    geom = box(*BBOX)
    assert inside_mask(geom, [12.0], [6.0]) == [True]
    assert inside_mask(geom, [20.0], [6.0]) == [False]
    assert inside_mask(geom, [], []) == []


@pytest.mark.skipif(not GEO.exists(), reason="géométrie Natural Earth non téléchargée")
def test_real_polygon_is_stricter_than_bbox():
    from pyrolens.emprise import load_region_polygon

    poly = load_region_polygon(GEO, "CMR")
    # Point dans la bbox englobante mais hors Cameroun (ouest : Nigeria, ~10,5°N)
    assert inside_mask(poly, [9.0], [10.5])[0] is False
    # Un point au centre du Cameroun
    assert inside_mask(poly, [12.5], [5.5])[0] is True
    # la bbox englobante accepte bien ce point hors pays : elle n'est pas le pays
    assert box(*BBOX).contains(Point(9.0, 10.5))


def test_region_terciles_documented():
    _w, south, _e, north = BBOX
    assert region_of(12.0, south + 0.1, BBOX) == "sud"
    assert region_of(12.0, (south + north) / 2, BBOX) == "centre"
    assert region_of(12.0, north - 0.1, BBOX) == "nord"
    # hors bbox : signalé, jamais intégré silencieusement
    assert region_of(12.0, 40.0, BBOX) == "hors_emprise"
