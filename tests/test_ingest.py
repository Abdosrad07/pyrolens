"""Tests de lecture CSV : préservation du brut, lignes mal formées."""

from __future__ import annotations

from pathlib import Path

from pyrolens.ingest import parse_csv_file
from pyrolens.schema import normalize_header, spec_from_name, validate_confidence, MODIS_SPEC, VIIRS_SPEC

HEADER = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,frp,daynight"
GOOD = "5.96,10.18,309.5,1.2,1.1,2019-01-15,1130,Terra,72,6.1NRT,12.4,D"


def _write(tmp_path: Path, *lines: str) -> Path:
    p = tmp_path / "sample.csv"
    p.write_text("\n".join([HEADER, *lines]) + "\n", encoding="utf-8")
    return p


def test_parse_keeps_good_rows(tmp_path):
    parsed = parse_csv_file(_write(tmp_path, GOOD, GOOD))
    assert len(parsed.records) == 2
    assert parsed.anomalies == []
    assert parsed.header[:2] == ["latitude", "longitude"]


def test_malformed_row_recorded_with_line_number(tmp_path):
    parsed = parse_csv_file(_write(tmp_path, GOOD, "1.0,2.0,3.0"))
    assert len(parsed.records) == 1
    bad = [a for a in parsed.anomalies if a.category == "malformed_row"]
    assert len(bad) == 1
    assert bad[0].line_number == 3            # entête = ligne 1
    assert "champs" in bad[0].reason
    assert bad[0].classification == "excluded"
    # la ligne brute est conservée telle quelle
    assert bad[0].raw_value == "1.0,2.0,3.0"


def test_header_aliases_normalized():
    assert normalize_header(["Lat", " LON ", "Acq_Date", "sat"]) == [
        "latitude", "longitude", "acq_date", "satellite"
    ]


def test_sensor_detection_from_filename():
    assert spec_from_name("MOD14_A2019.csv").key == "modis"
    assert spec_from_name("MYD14_clip.csv").key == "modis"
    assert spec_from_name("VNP14IMG_2019.csv").key == "viirs"
    assert spec_from_name("unknown.bin").key == "unknown"


def test_confidence_never_converted():
    # MODIS numérique 0-100 : valide tel quel
    assert validate_confidence("72", MODIS_SPEC) == (True, None)
    # MODIS hors échelle : invalide, sans conversion
    ok, reason = validate_confidence("150", MODIS_SPEC)
    assert not ok and "0-100" in reason
    # VIIRS catégories : valide tel quel
    assert validate_confidence("nominal", VIIRS_SPEC) == (True, None)
    ok, reason = validate_confidence("fort", VIIRS_SPEC)
    assert not ok
    # aucune échelle commune : une confiance numérique VIIRS n'est pas requalifiée MODIS
    assert validate_confidence("72", VIIRS_SPEC) == (True, None)
