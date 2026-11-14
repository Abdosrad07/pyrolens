"""Tests du module archive FIRMS par pays et de l'agrégation zone_history."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from api.services.zone_history import _aggregate
from pyrolens.archive import (
    ARCHIVE_SENSORS,
    archive_path,
    countries_for_bbox,
    ensure_country_file,
)

GEOJSON = Path("data/raw/geo/ne_110m_admin_0_countries.geojson")


class TestCountriesForBbox:
    @pytest.mark.skipif(not GEOJSON.exists(), reason="geojson absent")
    def test_cameroon_bbox_finds_cameroon(self):
        # bbox typique emprise projet
        hits = countries_for_bbox([8.4, 4.1, 16.4, 13.2], GEOJSON)
        names = {h.name for h in hits}
        assert "Cameroon" in names
        assert all(h.variants for h in hits)

    @pytest.mark.skipif(not GEOJSON.exists(), reason="geojson absent")
    def test_ocean_bbox_finds_nothing(self):
        hits = countries_for_bbox([-30.0, -30.0, -20.0, -20.0], GEOJSON)
        assert hits == []

    def test_name_variants_cover_aliases(self):
        hits = countries_for_bbox([8.4, 4.1, 16.4, 13.2], GEOJSON) if GEOJSON.exists() else []
        for h in hits:
            assert h.iso3 != "???" or h.name


class TestArchivePath:
    def test_path_layout(self, tmp_path):
        p = archive_path(tmp_path, "viirs", 2019, "Cameroon")
        assert p == tmp_path / "viirs-snpp" / "2019_Cameroon.csv"
        assert ARCHIVE_SENSORS["modis"] == "modis"


class TestEnsureCountryFile:
    def test_unresolved_country_reported(self, tmp_path):
        """Un pays aux variantes inexistantes → status unresolved, pas d'exception."""
        from pyrolens.archive import CountryHit

        hit = CountryHit(iso3="XXX", name="Atlantis", variants=["Atlantis", "Atlantis_Island"])
        meta = ensure_country_file("viirs", 2019, hit, tmp_path)
        assert meta["status"] == "unresolved"
        assert meta["path"] is None

    @pytest.mark.skipif(not GEOJSON.exists(), reason="geojson absent")
    def test_cached_file_not_redownloaded(self, tmp_path):
        """Un fichier déjà présent → status cached sans réseau."""
        from pyrolens.archive import CountryHit

        hit = CountryHit(iso3="CMR", name="Cameroon", variants=["Cameroon"])
        # pré-créer le fichier cible
        target = archive_path(tmp_path, "viirs", 2019, "Cameroon")
        target.parent.mkdir(parents=True)
        target.write_text("latitude,longitude\n", encoding="utf-8")
        meta = ensure_country_file("viirs", 2019, hit, tmp_path)
        assert meta["status"] == "cached"
        assert meta["bytes"] > 0


class TestAggregate:
    def _frame(self, rows):
        return pd.DataFrame(rows, columns=["ci", "cj", "date", "frp", "sensor"])

    def test_daily_jaccard_and_counts(self):
        viirs = self._frame([
            {"ci": 1, "cj": 1, "date": "2019-01-01", "frp": 10.0, "sensor": "viirs"},
            {"ci": 2, "cj": 2, "date": "2019-01-01", "frp": 20.0, "sensor": "viirs"},
        ])
        modis = self._frame([
            {"ci": 1, "cj": 1, "date": "2019-01-01", "frp": 15.0, "sensor": "modis"},
            {"ci": 3, "cj": 3, "date": "2019-01-02", "frp": 5.0, "sensor": "modis"},
        ])
        agg = _aggregate([(viirs, "viirs"), (modis, "modis")], 0.25)
        assert agg["counts"]["viirs_cells"] == 2
        assert agg["counts"]["modis_cells"] == 2
        assert agg["counts"]["common_cells"] == 1
        assert agg["counts"]["union_cells"] == 3
        assert len(agg["daily"]) == 2
        day1 = next(d for d in agg["daily"] if d["date"] == "2019-01-01")
        # jour 1 : VIIRS {(1,1),(2,2)} vs MODIS {(1,1)} → 1/2
        assert day1["jaccard"] == pytest.approx(0.5, abs=1e-3)

    def test_empty_input(self):
        agg = _aggregate([(pd.DataFrame(), "viirs")], 0.25)
        assert agg["daily"] == []
        assert agg["counts"] == {}

    def test_points_sample_bounded(self):
        rows = [{"ci": i % 10, "cj": i // 10, "date": "2019-01-01",
                 "frp": 1.0, "sensor": "viirs"} for i in range(5000)]
        agg = _aggregate([(self._frame(rows), "viirs")], 0.25)
        assert len(agg["points"]["viirs"]) <= 4000
