"""Tests unitaires du moteur de détection d'anomalies (pyrolens.anomaly_detection).

Jeux de données synthétiques contrôlés : activité normale, pic, données éparses,
baseline nulle, historique insuffisant, persistance, classification de sévérité,
entrées invalides.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

import pytest

from pyrolens.anomaly_detection import (
    DEFAULT_THRESHOLDS,
    CellBaseline,
    CellDailySeries,
    _sensor_label,
    anomaly_score,
    classify_severity,
    compute_baselines,
    compute_persistence,
    load_daily_counts,
    run_anomaly_detection,
    source_digest,
)
from pyrolens.grids import cell_id, epoch_days

EPOCH = date(1970, 1, 1)


def _d(epoch_day: int) -> str:
    return (EPOCH + timedelta(days=epoch_day)).isoformat()


def _write_csv(path: Path, rows: list[tuple[float, float, str, float]]) -> Path:
    """Écrit un CSV FIRMS minimal (latitude, longitude, acq_date, frp)."""
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["latitude", "longitude", "acq_date", "frp"])
        for lat, lon, d, frp in rows:
            writer.writerow([lat, lon, d, frp])
    return path


def _cell_rows(ci: int, cj: int, days: list[int], count_per_day: int = 1,
               grid_deg: float = 0.25) -> list[tuple[float, float, str, float]]:
    """Lignes CSV pour une cellule donnée (centre de cellule)."""
    from pyrolens.grids import cell_center

    lon, lat = cell_center(ci, cj, grid_deg)
    rows = []
    for d in days:
        for _ in range(count_per_day):
            rows.append((lat, lon, _d(d), 10.0))
    return rows


# ------------------------------------------------------------------ load_daily_counts
def test_load_daily_counts_aggregates_by_cell_and_day(tmp_path):
    ci, cj = 720, 360  # centre ≈ (0, 0)
    days = [epoch_days(date(2020, 1, 1)) + i for i in range(5)]
    rows = _cell_rows(ci, cj, days, count_per_day=2)
    csv_path = _write_csv(tmp_path / "a.csv", rows)

    series = load_daily_counts([csv_path], grid_deg=0.25)
    assert (ci, cj) in series
    cell = series[(ci, cj)]
    assert cell.counts[days[0]] == 2
    assert cell.counts[days[4]] == 2
    assert len(cell.counts) == 5


def test_load_daily_counts_ignores_invalid_rows(tmp_path):
    rows = [
        (0.0, 0.0, "2020-01-01", 5.0),          # valide
        (999.0, 0.0, "2020-01-01", 5.0),        # lat invalide → ignorée par NaN ? non, 999 est numérique
        (0.0, 0.0, "not-a-date", 5.0),          # date invalide
    ]
    # lat=999 passe le filtre numérique mais tombera dans une cellule valide ;
    # on teste surtout que la date invalide est ignorée.
    csv_path = _write_csv(tmp_path / "b.csv", rows)
    series = load_daily_counts([csv_path])
    total = sum(sum(c.counts.values()) for c in series.values())
    assert total == 2  # 1 valide + 1 lat=999 (date ok) ; la date invalide est exclue


def test_load_daily_counts_empty_source(tmp_path):
    csv_path = _write_csv(tmp_path / "empty.csv", [])
    assert load_daily_counts([csv_path]) == {}
    assert load_daily_counts([]) == {}


def test_source_digest_deterministic(tmp_path):
    p1 = _write_csv(tmp_path / "x.csv", [(0.0, 0.0, "2020-01-01", 1.0)])
    p2 = _write_csv(tmp_path / "y.csv", [(1.0, 1.0, "2020-01-02", 2.0)])
    assert source_digest([p1, p2]) == source_digest([p2, p1])
    assert source_digest([p1]) != source_digest([p1, p2])


# ------------------------------------------------------------------ compute_baselines
def test_baseline_cell_level_when_sufficient_history():
    ci, cj = 720, 360
    # 100 jours avec détection régulière → baseline « cell » suffisante
    days = list(range(epoch_days(date(2019, 1, 1)), epoch_days(date(2019, 4, 10))))
    cell = CellDailySeries(ci=ci, cj=cj)
    for d in days:
        cell.counts[d] = 2
    series = {(ci, cj): cell}
    ref_end = days[-1]
    baselines = compute_baselines(series, ref_end, baseline_days=400,
                                  min_baseline_days=30, min_cell_days=30)
    b = baselines[(ci, cj)]
    assert b.level == "cell"
    assert b.sufficient is True
    assert b.median_daily == 2.0


def test_baseline_region_fallback_for_sparse_cell():
    # Une cellule avec très peu de jours de détection → niveau « region »
    ci, cj = 720, 360
    cell = CellDailySeries(ci=ci, cj=cj)
    cell.counts[epoch_days(date(2019, 6, 1))] = 5  # 1 seul jour
    series = {(ci, cj): cell}
    baselines = compute_baselines(series, epoch_days(date(2019, 12, 31)),
                                  baseline_days=365, min_baseline_days=30,
                                  min_cell_days=30)
    b = baselines[(ci, cj)]
    assert b.sufficient is False
    assert b.level in ("region", "global")


def test_baseline_empty_series_returns_empty():
    assert compute_baselines({}, 100) == {}


# ------------------------------------------------------------------ anomaly_score
def _baseline(median: float, q90: float = 0.0, sufficient: bool = True) -> CellBaseline:
    return CellBaseline(
        ci=0, cj=0, n_days_observed=365, n_days_with_detection=100,
        median_daily=median, q90_daily=q90, mean_daily=median,
        max_daily=10, total_detections=1000, level="cell", sufficient=sufficient,
    )


def test_score_zero_activity_zero_baseline():
    score, ratio, reasons = anomaly_score([0] * 14, _baseline(0.0), 14)
    assert score == 0.0
    assert ratio is None


def test_score_spike_vs_baseline():
    # baseline ~1/jour, récent 10/jour → score élevé
    score, ratio, reasons = anomaly_score([10] * 14, _baseline(1.0, q90=3.0), 14)
    assert score > 0.7
    assert ratio is not None and ratio > 5.0


def test_score_normal_activity():
    score, ratio, _ = anomaly_score([1] * 14, _baseline(1.0, q90=2.0), 14)
    assert score < 0.5


def test_score_zero_baseline_with_activity():
    score, ratio, reasons = anomaly_score([5] * 14, _baseline(0.0), 14)
    assert score > 0.5
    assert "baseline_nulle_activite_nouvelle" in reasons


def test_score_insufficient_baseline_penalized():
    score_full, _, _ = anomaly_score([10] * 14, _baseline(1.0, sufficient=True), 14)
    score_low, _, reasons = anomaly_score([10] * 14, _baseline(1.0, sufficient=False), 14)
    assert score_low < score_full
    assert "baseline_insuffisante" in reasons


# ------------------------------------------------------------------ classify_severity
def test_severity_normal_below_watch():
    assert classify_severity(0.3, 10) == "NORMAL"


def test_severity_watch_requires_score_and_floor():
    assert classify_severity(0.6, 5) == "WATCH"
    # score suffisant mais activité insuffisante → NORMAL
    assert classify_severity(0.6, 1) == "NORMAL"


def test_severity_high_requires_highest_floor():
    assert classify_severity(0.9, 15) == "HIGH"
    assert classify_severity(0.9, 8) == "MODERATE"
    assert classify_severity(0.75, 8) == "MODERATE"
    assert classify_severity(0.75, 4) == "WATCH"


def test_severity_custom_thresholds():
    th = {"watch": 0.3, "moderate": 0.5, "high": 0.7}
    md = {"watch": 1, "moderate": 2, "high": 3}
    assert classify_severity(0.4, 1, thresholds=th, min_detections=md) == "WATCH"
    assert classify_severity(0.6, 2, thresholds=th, min_detections=md) == "MODERATE"
    assert classify_severity(0.8, 3, thresholds=th, min_detections=md) == "HIGH"


# ------------------------------------------------------------------ run_anomaly_detection
def test_run_detects_spike_cell(tmp_path):
    """Une cellule avec un pic récent doit ressortir au-dessus de la baseline."""
    ci, cj = 720, 360
    ref = date(2020, 6, 30)
    ref_d = epoch_days(ref)
    rows = []
    # baseline : ~1 détection/jour pendant 300 jours
    for d in range(ref_d - 300, ref_d - 14):
        rows.extend(_cell_rows(ci, cj, [d], count_per_day=1))
    # pic : 8/jour pendant les 14 derniers jours
    for d in range(ref_d - 13, ref_d + 1):
        rows.extend(_cell_rows(ci, cj, [d], count_per_day=8))
    # cellule témoin : activité stable
    ci2, cj2 = 730, 360
    for d in range(ref_d - 300, ref_d + 1):
        rows.extend(_cell_rows(ci2, cj2, [d], count_per_day=1))

    csv_path = _write_csv(tmp_path / "fires.csv", rows)
    payload = run_anomaly_detection([csv_path], grid_deg=0.25, recent_days=14,
                                    baseline_days=400, reference_date=ref)

    assert payload["estimate_kind"] == "historical_backtest"
    assert payload["summary"]["n_cells_total"] >= 2
    by_id = {a["cell_id"]: a for a in payload["alerts"]}
    spike = by_id[f"{ci}:{cj}"]
    assert spike["recent"]["detections"] == 14 * 8
    assert spike["score"] > by_id[f"{ci2}:{cj2}"]["score"]
    assert spike["severity"] in ("WATCH", "MODERATE", "HIGH")


def test_run_persistence_same_input_same_output(tmp_path):
    ci, cj = 720, 360
    ref = date(2020, 6, 30)
    ref_d = epoch_days(ref)
    rows = []
    for d in range(ref_d - 100, ref_d + 1):
        rows.extend(_cell_rows(ci, cj, [d], count_per_day=2))
    csv_path = _write_csv(tmp_path / "fires.csv", rows)

    p1 = run_anomaly_detection([csv_path], grid_deg=0.25, recent_days=14,
                               baseline_days=200, reference_date=ref)
    p2 = run_anomaly_detection([csv_path], grid_deg=0.25, recent_days=14,
                               baseline_days=200, reference_date=ref)
    # generated_at peut différer ; on compare le contenu scientifique
    for key in ("summary", "period", "params"):
        assert p1[key] == p2[key]
    assert [a["cell_id"] for a in p1["alerts"]] == [a["cell_id"] for a in p2["alerts"]]
    assert [a["score"] for a in p1["alerts"]] == [a["score"] for a in p2["alerts"]]


def test_run_empty_source_raises(tmp_path):
    csv_path = _write_csv(tmp_path / "empty.csv", [])
    with pytest.raises(ValueError, match="Aucun événement"):
        run_anomaly_detection([csv_path])


def test_run_no_recent_activity_still_evaluates_baseline_cells(tmp_path):
    """Une cellule avec baseline mais zéro détection récente → NORMAL, pas d'alerte."""
    ci, cj = 720, 360
    ref = date(2020, 6, 30)
    ref_d = epoch_days(ref)
    rows = []
    # cellule témoin : active jusqu'à la fin → fixe data_max = ref_d
    ci2, cj2 = 730, 360
    for d in range(ref_d - 100, ref_d + 1):
        rows.extend(_cell_rows(ci2, cj2, [d], count_per_day=1))
    # cellule test : active seulement dans la baseline, silencieuse sur les 14 derniers jours
    for d in range(ref_d - 200, ref_d - 14):
        rows.extend(_cell_rows(ci, cj, [d], count_per_day=3))
    csv_path = _write_csv(tmp_path / "fires.csv", rows)
    payload = run_anomaly_detection([csv_path], grid_deg=0.25, recent_days=14,
                                    baseline_days=400, reference_date=ref)
    by_id = {a["cell_id"]: a for a in payload["alerts"]}
    assert f"{ci}:{cj}" in by_id
    assert by_id[f"{ci}:{cj}"]["severity"] == "NORMAL"
    assert by_id[f"{ci}:{cj}"]["recent"]["detections"] == 0
    assert by_id[f"{ci}:{cj}"]["baseline"]["median_daily"] > 0


def test_run_reference_date_controls_window(tmp_path):
    """La fenêtre récente se termine à reference_date, pas à la fin des données."""
    ci, cj = 720, 360
    ref = date(2020, 3, 31)
    ref_d = epoch_days(ref)
    rows = []
    for d in range(ref_d - 100, ref_d + 1):
        rows.extend(_cell_rows(ci, cj, [d], count_per_day=2))
    # données après la date de référence : ne doivent pas influencer le récent
    for d in range(ref_d + 1, ref_d + 60):
        rows.extend(_cell_rows(ci, cj, [d], count_per_day=50))
    csv_path = _write_csv(tmp_path / "fires.csv", rows)
    payload = run_anomaly_detection([csv_path], grid_deg=0.25, recent_days=14,
                                    baseline_days=200, reference_date=ref)
    assert payload["period"]["recent_end"] == ref.isoformat()
    by_id = {a["cell_id"]: a for a in payload["alerts"]}
    assert by_id[f"{ci}:{cj}"]["recent"]["detections"] == 14 * 2


# ------------------------------------------------------------------ capteurs
def test_sensor_label_modis():
    assert _sensor_label("MODIS", "Terra") == "modis"
    assert _sensor_label("", "Aqua") == "modis"
    assert _sensor_label("MODIS", "") == "modis"


def test_sensor_label_viirs():
    assert _sensor_label("VIIRS", "N") == "viirs-snpp"
    assert _sensor_label("", "Suomi NPP") == "viirs-snpp"
    assert _sensor_label("VIIRS", "NOAA-20") == "viirs-snpp"  # instrument prioritaire
    assert _sensor_label("", "NOAA-21") == "viirs-noaa"


def test_sensor_label_unknown():
    assert _sensor_label("", "") == "unknown"
    assert _sensor_label("OTHER", "X") == "other"


def _write_csv_with_satellite(path: Path, rows: list[tuple[float, float, str, float, str]]) -> Path:
    """CSV FIRMS avec colonne satellite (latitude, longitude, acq_date, frp, satellite)."""
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["latitude", "longitude", "acq_date", "frp", "satellite"])
        for lat, lon, d, frp, sat in rows:
            writer.writerow([lat, lon, d, frp, sat])
    return path


def test_load_daily_counts_tracks_sensors(tmp_path):
    ci, cj = 720, 360
    from pyrolens.grids import cell_center

    lon, lat = cell_center(ci, cj, 0.25)
    d1 = _d(epoch_days(date(2020, 1, 1)))
    d2 = _d(epoch_days(date(2020, 1, 2)))
    rows = [
        (lat, lon, d1, 10.0, "Terra"),   # modis
        (lat, lon, d1, 10.0, "Aqua"),    # modis
        (lat, lon, d2, 10.0, "N"),       # viirs-snpp
    ]
    csv_path = _write_csv_with_satellite(tmp_path / "s.csv", rows)
    series = load_daily_counts([csv_path], grid_deg=0.25)
    cell = series[(ci, cj)]
    d1_int = epoch_days(date(2020, 1, 1))
    d2_int = epoch_days(date(2020, 1, 2))
    assert cell.sensors_by_day[d1_int] == {"modis"}
    assert cell.sensors_by_day[d2_int] == {"viirs-snpp"}


def test_run_includes_persistence_and_sensors(tmp_path):
    """Le payload d'alerte porte persistence (jours consécutifs) et sensors."""
    ci, cj = 720, 360
    ref = date(2020, 6, 30)
    ref_d = epoch_days(ref)
    rows = []
    # baseline : 1/jour pendant 300 jours
    for d in range(ref_d - 300, ref_d - 14):
        rows.extend(_cell_rows(ci, cj, [d], count_per_day=1))
    # récent : 8/jour pendant les 14 derniers jours (pics au-dessus de la baseline)
    for d in range(ref_d - 13, ref_d + 1):
        rows.extend(_cell_rows(ci, cj, [d], count_per_day=8))
    csv_path = _write_csv(tmp_path / "fires.csv", rows)
    payload = run_anomaly_detection([csv_path], grid_deg=0.25, recent_days=14,
                                    baseline_days=400, reference_date=ref)
    by_id = {a["cell_id"]: a for a in payload["alerts"]}
    spike = by_id[f"{ci}:{cj}"]
    # baseline médiane = 1/jour → chaque jour récent (8) dépasse → persistance = 14
    assert spike["persistence"] == 14
    assert isinstance(spike["sensors"], list)
    # CSV sans colonne satellite → capteur « unknown » (pas de crash)
    assert spike["sensors"] == ["unknown"]


# ------------------------------------------------------------------ compute_persistence
def test_compute_persistence_counts_consecutive_days_above_baseline():
    counts = {100: 5, 101: 5, 102: 0, 103: 5, 104: 5, 105: 5}
    # baseline médiane = 1 → jours 103,104,105 > 1 ; 102 = 0 → stop
    assert compute_persistence(counts, 100, 105, 1.0) == 3


def test_compute_persistence_zero_baseline_counts_any_detection():
    counts = {100: 0, 101: 0, 102: 1, 103: 2}
    # baseline nulle → tout jour avec ≥1 détection compte ; 101=0 → stop
    assert compute_persistence(counts, 100, 103, 0.0) == 2


def test_compute_persistence_no_activity_returns_zero():
    assert compute_persistence({}, 100, 110, 1.0) == 0
    assert compute_persistence({100: 1}, 100, 110, 1.0) == 0  # 1 > 1 est faux
