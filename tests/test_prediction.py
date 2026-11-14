"""Tests du module de prédiction Fire Risk (src/pyrolens/prediction.py).

Ces tests utilisent des événements synthétiques multi-années pour couvrir
le split chronologique — ils ne valident PAS le modèle sur données réelles
(voir docs/FIRE_RISK_PREDICTION.md §limites).
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pyrolens.grids import epoch_days
from pyrolens.prediction import (
    FEATURE_NAMES,
    _best_f1_threshold,
    _label,
    build_cell_index,
    build_dataset,
    calibration_bins,
    data_origin_of_source,
    export_artifact,
    fit_frequency_baseline,
    load_events,
    run_prediction,
    split_mask,
)


def _events_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _mk_events(seed: int = 0, years=(2015, 2016, 2017, 2018, 2019, 2020)) -> pd.DataFrame:
    """Événements synthétiques : 2 cellules, activité saisonnière simple."""
    rng = np.random.default_rng(seed)
    rows = []
    # cellule chaude : détections fréquentes en saison sèche (jan-fév)
    for year in years:
        for month in range(1, 13):
            for _ in range(3 if month in (1, 2, 12) else 1):
                day = int(rng.integers(1, 28))
                rows.append({
                    "ci": 10, "cj": 10, "d": epoch_days(date(year, month, day)),
                    "sensor": "viirs_snpp", "frp": float(rng.uniform(5, 50)),
                    "conf_class": "high", "conf_num": np.nan, "is_day": 1,
                })
            # cellule froide : rare
            if month in (6, 7) and rng.random() < 0.3:
                rows.append({
                    "ci": 11, "cj": 11, "d": epoch_days(date(year, month, 15)),
                    "sensor": "terra", "frp": 10.0,
                    "conf_class": "modis_numeric", "conf_num": 80.0, "is_day": 1,
                })
    return pd.DataFrame(rows)


class TestLoadEvents:
    def test_load_fixture_csvs(self):
        paths = sorted(Path("data/fixture").glob("*.csv"))
        if not paths:
            pytest.skip("fixtures absentes")
        ev = load_events(paths, 0.25)
        assert len(ev) > 0
        assert {"ci", "cj", "d", "sensor", "frp", "conf_class", "conf_num", "is_day"} <= set(ev.columns)
        assert ev["sensor"].isin(["terra", "aqua", "viirs_snpp", "unknown"]).all()
        assert ev["d"].between(epoch_days(date(2019, 1, 1)), epoch_days(date(2019, 12, 31))).all()

    def test_load_missing_dir_empty(self, tmp_path):
        ev = load_events([], 0.25)
        assert ev.empty


class TestCellIndex:
    def test_index_sorted_and_label(self):
        ev = _mk_events()
        idx = build_cell_index(ev, 0.25)
        assert (10, 10) in idx
        cell = idx[(10, 10)]
        assert cell.union_dates.size > 0
        # label : détection dans les 8 j suivant un jour creux
        t = int(cell.union_dates[0]) - 20
        assert _label(cell.union_dates, t, 8) == 0
        t2 = int(cell.union_dates[0]) - 3
        assert _label(cell.union_dates, t2, 8) == 1

    def test_features_are_trailing_only(self):
        """Aucune feature ne doit voir une observation postérieure à t."""
        ev = _mk_events()
        idx = build_cell_index(ev, 0.25)
        cell = idx[(10, 10)]
        t = int(cell.union_dates[len(cell.union_dates) // 2])
        f1 = None
        # compter les détections avant/après t
        before = int((cell.union_dates <= t).sum())
        after = int((cell.union_dates > t).sum())
        assert before > 0 and after > 0
        # n_all_8 à t ne doit compter que [t-7, t]
        from pyrolens.prediction import _count_in
        n8 = _count_in(cell.union_dates, t, 8)
        expected = int(((cell.union_dates >= t - 7) & (cell.union_dates <= t)).sum())
        assert n8 == expected


class TestDatasetAndSplit:
    def test_dataset_shapes_and_labels(self):
        ev = _mk_events()
        idx = build_cell_index(ev, 0.25)
        X, y, meta = build_dataset(idx, 0.25, 8, 7)
        assert X.shape[1] == len(FEATURE_NAMES)
        assert len(X) == len(y) == len(meta)
        assert set(y.unique()) <= {0, 1}

    def test_split_purge_no_overlap(self):
        ev = _mk_events()
        idx = build_cell_index(ev, 0.25)
        X, y, meta = build_dataset(idx, 0.25, 8, 7)
        masks = split_mask(meta, purge_days=16)
        d = meta["d"].to_numpy()
        b1 = epoch_days(date(2017, 1, 1))
        b2 = epoch_days(date(2019, 1, 1))
        # train strictement avant b1-16, val entre b1+16 et b2-16, test après b2+16
        assert d[masks["train"]].max() < b1 - 16
        assert d[masks["validation"]].min() > b1 + 16
        assert d[masks["validation"]].max() < b2 - 16
        assert d[masks["test"]].min() > b2 + 16
        # pas de chevauchement
        assert not (masks["train"] & masks["validation"]).any()
        assert not (masks["validation"] & masks["test"]).any()

    def test_split_covers_all_years(self):
        ev = _mk_events()
        idx = build_cell_index(ev, 0.25)
        X, y, meta = build_dataset(idx, 0.25, 8, 7)
        masks = split_mask(meta)
        assert masks["train"].sum() > 0
        assert masks["validation"].sum() > 0
        assert masks["test"].sum() > 0


class TestBaseline:
    def test_baseline_bounded_and_sensible(self):
        ev = _mk_events()
        idx = build_cell_index(ev, 0.25)
        X, y, meta = build_dataset(idx, 0.25, 8, 7)
        masks = split_mask(meta)
        p = fit_frequency_baseline(
            y[masks["train"]].to_numpy(),
            meta[masks["train"]].reset_index(drop=True),
            meta[masks["validation"]].reset_index(drop=True),
        )
        assert p.min() >= 0.0 and p.max() <= 1.0
        assert len(p) == int(masks["validation"].sum())
        # la cellule chaude doit avoir une probabilité > cellule froide en moyenne
        hot = meta[masks["validation"]].reset_index(drop=True)
        hot_p = p[(hot["ci"] == 10) & (hot["cj"] == 10)]
        cold_p = p[(hot["ci"] == 11) & (hot["cj"] == 11)]
        if len(hot_p) and len(cold_p):
            assert hot_p.mean() > cold_p.mean()


class TestCalibrationAndMetrics:
    def test_best_f1_threshold_in_range(self):
        y = np.array([0, 0, 1, 1, 0, 1, 0, 1])
        p = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.4, 0.6])
        t = _best_f1_threshold(y, p)
        assert 0.05 <= t <= 0.95

    def test_calibration_bins_cover(self):
        y = np.random.default_rng(0).integers(0, 2, 200)
        p = np.random.default_rng(1).random(200)
        bins = calibration_bins(y, p)
        assert bins
        assert all(0 <= b["mean_pred"] <= 1 for b in bins)


class TestExport:
    def test_export_contract(self, tmp_path):
        ev = _mk_events(years=(2019,))
        idx = build_cell_index(ev, 0.25)
        ref = date(2019, 12, 31)
        payload = export_artifact(
            tmp_path / "fire_risk.json", idx, 0.25, 8, ref,
            "synthetic_fixture", "frequency_baseline",
            lambda f, ci, cj: 0.42,
            {"pr_auc": 0.5, "threshold": 0.5},
            {"start": "2019-01-01", "end": "2019-12-31"},
        )
        for key in ("generated_at", "reference_date", "prediction_horizon_days",
                    "data_origin", "model", "metrics", "cells"):
            assert key in payload
        assert payload["data_origin"] == "synthetic_fixture"
        assert payload["estimate_kind"] == "historical_backtest"
        cell = payload["cells"][0]
        for key in ("cell_i", "cell_j", "lat", "lon", "prob", "level"):
            assert key in cell
        assert 0.0 <= cell["prob"] <= 1.0
        assert cell["level"] in ("low", "moderate", "high")
        # le fichier est bien écrit
        assert (tmp_path / "fire_risk.json").exists()


class TestDataOrigin:
    def test_origin_raw_vs_fixture(self, tmp_path):
        raw = tmp_path / "data" / "raw" / "firms" / "a.csv"
        fix = tmp_path / "data" / "fixture" / "b.csv"
        assert data_origin_of_source([raw]) == "nasa_firms"
        assert data_origin_of_source([fix]) == "synthetic_fixture"


class TestRunPredictionSmoke:
    def test_run_on_synthetic_years(self, tmp_path):
        """run_prediction de bout en bout sur événements synthétiques 2015-2020."""
        # il faut des CSV — on écrit des CSV synthétiques multi-années
        import csv
        src = tmp_path / "src"
        src.mkdir()
        ev = _mk_events()
        # reconstruire des lignes CSV depuis les événements
        inv_sensor = {"viirs_snpp": "NPP", "terra": "Terra", "aqua": "Aqua"}
        rows = []
        for _, r in ev.iterrows():
            d = _EPOCH_DATE(r["d"])
            rows.append({
                "latitude": 5.0 + r["cj"] * 0.25, "longitude": 10.0 + r["ci"] * 0.25,
                "acq_date": d.isoformat(), "satellite": inv_sensor.get(r["sensor"], "X"),
                "confidence": r["conf_class"] if r["sensor"] == "viirs_snpp" else "80",
                "frp": r["frp"], "daynight": "D" if r["is_day"] else "N",
            })
        df = pd.DataFrame(rows)
        for sensor_name, sub in df.groupby(df["satellite"].map(
                {"NPP": "viirs", "Terra": "terra", "Aqua": "aqua"})):
            fname = {"viirs": "viirs_snpp", "terra": "terra", "aqua": "aqua"}[sensor_name]
            sub.to_csv(src / f"{fname}_synthetic.csv", index=False)
        out = tmp_path / "fire_risk.json"
        payload = run_prediction(
            sorted(src.glob("*.csv")), grid_deg=0.25, horizon=8, stride=14,
            out_path=out, model_dir=tmp_path / "models",
        )
        assert payload["data_origin"] == "synthetic_fixture"
        assert payload["estimate_kind"] == "historical_backtest"
        assert len(payload["cells"]) > 0
        assert "metrics" in payload
        # le modèle choisi est documenté
        assert payload["model"]["type"] in ("random_forest", "frequency_baseline")


def _EPOCH_DATE(d: int) -> date:
    return date(1970, 1, 1) + timedelta(days=int(d))
