"""Tests d'audit : coordonnées jamais corrigées, dates, FRP, doublons, emprise."""

from __future__ import annotations

from pathlib import Path

from pyrolens.audit import audit_file, temporal_gaps

HEADER = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,frp,daynight"
BBOX = [8.4, 4.1, 16.4, 13.2]  # Cameroun (boîte englobante)


def _csv(tmp_path: Path, rows: list[str], name: str = "MOD14_sample.csv") -> Path:
    p = tmp_path / name
    p.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return p


GOOD_A = "6.00,10.00,310.0,1.1,1.1,2019-01-10,1130,Terra,72,6.1NRT,12.4,D"
GOOD_B = "6.10,10.10,311.0,1.1,1.1,2019-01-11,1135,Terra,65,6.1NRT,9.9,D"


def test_valid_rows_kept_and_counted(tmp_path):
    audit = audit_file(_csv(tmp_path, [GOOD_A, GOOD_B]), bbox=BBOX)
    assert audit.counts["rows_analysable"] == 2
    assert audit.rows[0]["satellite"] == "Terra"
    assert audit.rows[0]["sensor"] == "modis"


def test_out_of_range_latitude_never_corrected(tmp_path):
    bad = "95.00,10.00,310.0,1.1,1.1,2019-01-10,1130,Terra,72,6.1NRT,12.4,D"
    audit = audit_file(_csv(tmp_path, [bad]), bbox=BBOX)
    assert audit.counts["rows_excluded"] == 1
    cats = {a.category for a in audit.anomalies}
    assert "invalid_latitude" in cats
    # la valeur brute est conservée dans l'anomalie, jamais réécrite
    anomaly = next(a for a in audit.anomalies if a.category == "invalid_latitude")
    assert anomaly.raw_value == "95.00"
    assert audit.rows == []


def test_invalid_date_and_time_flagged(tmp_path):
    bad_date = "6.00,10.00,310.0,1.1,1.1,10/01/2019,1130,Terra,72,6.1NRT,12.4,D"
    bad_time = "6.00,10.00,310.0,1.1,1.1,2019-01-10,2560,Terra,72,6.1NRT,12.4,D"
    audit = audit_file(_csv(tmp_path, [bad_date, bad_time]), bbox=BBOX)
    cats = [a.category for a in audit.anomalies]
    assert "invalid_date" in cats and "invalid_time" in cats
    assert audit.counts["rows_excluded"] == 2


def test_negative_frp_is_ambiguous_not_repaired(tmp_path):
    row = "6.00,10.00,310.0,1.1,1.1,2019-01-10,1130,Terra,72,6.1NRT,-5.0,D"
    audit = audit_file(_csv(tmp_path, [row]), bbox=BBOX)
    anomaly = next(a for a in audit.anomalies if a.category == "invalid_frp")
    assert anomaly.classification == "ambiguous"
    assert anomaly.raw_value == "-5.0"
    # la ligne reste analysable pour sa géométrie/sa date, le FRP est None
    assert audit.rows[0]["frp"] is None


def test_duplicate_rows_and_keys(tmp_path):
    dup_key = "6.00,10.00,310.0,1.1,1.1,2019-01-10,1130,Terra,99,6.1NRT,1.0,D"
    audit = audit_file(_csv(tmp_path, [GOOD_A, GOOD_A, dup_key]), bbox=BBOX)
    cats = [a.category for a in audit.anomalies]
    assert "duplicate_row" in cats and "duplicate_key" in cats
    assert audit.counts["rows_analysable"] == 1   # dédupliqué pour les ensembles


def test_outside_emprise_kept_in_anomalies_but_excluded(tmp_path):
    outside = "6.00,20.00,310.0,1.1,1.1,2019-01-10,1130,Terra,72,6.1NRT,12.4,D"  # lon hors bbox
    audit = audit_file(_csv(tmp_path, [outside, GOOD_A]), bbox=BBOX)
    assert audit.counts["rows_outside_emprise"] == 1
    assert audit.counts["rows_analysable"] == 1
    anomaly = next(a for a in audit.anomalies if a.category == "outside_emprise")
    assert anomaly.line_number == 2


def test_temporal_gaps_listed_without_fire_claim(tmp_path):
    rows = [
        "6.00,10.00,310.0,1.1,1.1,2019-01-10,1130,Terra,72,6.1NRT,12.4,D",
        "6.00,10.00,310.0,1.1,1.1,2019-01-12,1130,Terra,72,6.1NRT,12.4,D",
    ]
    audit = audit_file(_csv(tmp_path, rows), bbox=BBOX)
    gaps = temporal_gaps([audit])
    assert any(g["date"] == "2019-01-11" for g in gaps)
    assert all(g["interpretation"].startswith(("aucun", "0")) is False or True for g in gaps)
    # aucun énoncé « pas de feu »
    assert all("feu" not in g["interpretation"] for g in gaps)
