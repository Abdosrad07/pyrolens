# Fire Risk Prediction — Technical documentation (English)

> Backend module predicting the risk of **detected** fire activity.
> Feasibility study: `docs/FIRE_RISK_PREDICTION_FEASIBILITY.md` (GO WITH LIMITATIONS).
> Work split: `docs/FIRE_RISK_PREDICTION_SPLIT.md`.
>
> *French version: [`../FIRE_RISK_PREDICTION.md`](../FIRE_RISK_PREDICTION.md)*

---

## 1. What the model predicts — and what it does not

For a grid cell `(i,j)` of the PyroLens grid and a reference date `t`,
the model estimates:

```
P( ≥1 FIRMS detection in the cell over the `horizon` days after t )
```

**Locked formulation**: "risk of fire activity **detected** by satellites"
— never "wildfire risk", never "alert". A missing detection does not prove
the absence of fire (clouds, overpass time, resolution); under-covered
periods produce noisy labels — a limitation assumed and documented in the
artifact (`notes`).

## 2. Architecture

```
data/raw/firms/*.csv  (or data/fixture/)
        │  pyrolens predict
        ▼
src/pyrolens/prediction.py
  ├─ load_events()        CSV → events (ci, cj, d, sensor, frp, conf)
  ├─ build_cell_index()   date-sorted index per cell (numpy/searchsorted)
  ├─ build_dataset()      trailing features + label J+horizon, stride step
  ├─ split_mask()         train 2013-16 / val 2017-18 / test 2019-20 + purge
  ├─ fit_models()         frequency baseline + RandomForest + calibration
  └─ export_artifact()    web/public/artifacts/fire_risk.json
        │
        ▼  (optional)
GET /api/v1/fire-risk     serves the artifact, ETag, clean 404 if absent
```

The serialized model goes into `models/` (project root) — **never** into
`web/public/`: `fire_risk_model.joblib` or `fire_risk_baseline.json`.

## 3. Data

- **Real**: `data/raw/firms/` — 1,170 canonical 5-day windows,
  2013-01 → 2020-12, ~1.83 M analyzable detections (audit.json).
  `data_origin = nasa_firms`.
- **Fixture**: `data/fixture/` — 3 synthetic 2019 CSVs.
  `data_origin = synthetic_fixture` — propagated to the JSON and the UI.
- Columns used: `latitude, longitude, acq_date, satellite,
  confidence, frp, daynight`. **Not available**: weather, vegetation,
  wind — unused (external collection out of scope).

## 4. Features (24)

Trailing windows `[t-w+1, t]` — never after `t`:

| Group | Features |
| --- | --- |
| Per-sensor counts | `n_{terra,aqua,viirs_snpp}_{8,16,32}` (9) |
| Union | `n_all_{8,16,32}` (3) |
| FRP | `frp_mean_16`, `frp_max_16` (union) |
| Activity | `days_active_32`, `day_frac_32` (day/night) |
| Native confidence | `viirs_conf_{low,nominal,high}_16` + `modis_conf_mean_16` — **scales never merged** |
| Context | `month_sin`, `month_cos`, `lat`, `lon` (cell centroid) |

## 5. Label

`y=1` if ≥1 detection **all sensors combined** in `]t, t+horizon]`
(horizon = 8 d by default). The union maximizes label sensitivity.

## 6. Models and selection

| Model | Role |
| --- | --- |
| **Frequency baseline** | (cell, month) rate smoothed with two-level beta (pseudo-counts α=30 cell, α=15 month) — stable on rare cells |
| **RandomForest** | `n_estimators=200, class_weight="balanced_subsample", min_samples_leaf=5, random_state=42` |
| **Calibration** | Isotonic if val ≥ 500 samples, else Platt (logit + logistic) — raw RF probabilities are never published |

**Selection rule** (on **validation** only): the RF is retained only if
`PR-AUC_RF > PR-AUC_baseline × 1.05` (**relative**, not absolute).
Otherwise the baseline is the final model — a defensible feature.

## 7. Evaluation protocol

| Split | Period | Usage |
| --- | --- | --- |
| train | 2013–2016 | baseline + RF training |
| validation | 2017–2018 | calibration, F1 threshold choice, model choice |
| test | 2019–2020 | final evaluation — never touched before |

Purge: ±16 days around the 2017/2019 boundaries (8-day labels + margin).
No sampling: `stride=7` days (decorrelation). Active cells only
(≥1 detection over the period).

**Metrics** (on test): PR-AUC (primary), ROC-AUC, recall, precision,
F1, Brier, confusion matrix, calibration table (10 bins).
The threshold is the validation **F1-max**, never the test one.

## 8. `fire_risk.json` artifact

```json
{
  "generated_at": "…", "reference_date": "YYYY-MM-DD",
  "prediction_horizon_days": 8, "estimate_kind": "historical_backtest",
  "data_origin": "nasa_firms | synthetic_fixture",
  "model": {"type": "…", "version": "…", "features": […], "calibration": "…", "threshold": 0.x},
  "metrics": {"pr_auc": …, "f1": …, "recall": …, "brier": …, "confusion_matrix": [[…]], "validation": {…}},
  "period": {"start": "…", "end": "…"},
  "cells": [{"cell_i": 0, "cell_j": 0, "lat": 0.0, "lon": 0.0, "prob": 0.x, "level": "low|moderate|high"}],
  "notes": "…"
}
```

`level`: `high` if prob ≥ F1 threshold, `moderate` if ≥ threshold/2, else `low`.

## 9. Reference-date handling

- `reference_date` = data max by default → **historical backtest**.
- `estimate_kind` is **always** `historical_backtest`: data ends in 2020,
  no "current" estimate is produced.
- A real day J would require recent FIRMS observations as input
  (separate module, not implemented — the NRT zone exists via
  `/firms/analyze` but does not provide 32 days of per-cell history).

## 10. Execution

```bash
# real data (after pyrolens download) or fixture
PYTHONPATH=src python -m pyrolens.cli predict                 # defaults
PYTHONPATH=src python -m pyrolens.cli predict --grid 0.25 --window 8
PYTHONPATH=src python -m pyrolens.cli predict --source data/fixture --reference-date 2019-12-31
PYTHONPATH=src python -m pyrolens.cli predict --stride 3      # finer sampling
```
Outputs: `web/public/artifacts/fire_risk.json` + `models/fire_risk_*.joblib|json`.

API: `GET /api/v1/fire-risk` → artifact + ETag; clean 404 if absent;
no recomputation on request.

## 11. Results on real data (2026-11-14)

Run: `pyrolens predict --grid 0.25 --window 8` on the 1,170 canonical
FIRMS CSVs (2013-01 → 2020-12, `data_origin=nasa_firms`).

| Indicator | Value |
| --- | --- |
| Active cells | 1,215 |
| Samples | 489,645 (train 245,430 / val 121,500 / test 122,715) |
| Positive rate | **31.8%** (38,964 / 122,715) |
| **Selected model** | `random_forest` (val PR-AUC 0.928 > baseline 0.875 × 1.05) |
| Calibration | isotonic |
| F1 threshold (val) | 0.42 |
| **Test PR-AUC** | **0.926** |
| Test F1 / recall | 0.841 / 0.844 |
| Test Brier | 0.072 |

Interpretation: the RF exploits the strong persistence of fire activity
(recent per-sensor counts) — high PR-AUC but **not** a fire probability:
it is P(≥1 FIRMS detection within 8 d). The baseline alone already
reaches 0.875: the signal is dominated by persistence, not weather
drivers (absent from features).

## 12. Reproduction

1. `pip install -r requirements.txt` (includes `scikit-learn>=1.5`)
2. `pyrolens download` (real data) or `pyrolens fixture`
3. `pyrolens predict` → reproducible artifact (fixed seeds: RF
   `random_state=42`, deterministic sampling via date sorting)
4. `python -m pytest` → 119 tests

## 13. Scientific limits

- **Single domain** (Cameroon): no spatial generalization claimed.
- Label noisy due to coverage (clouds) — mitigated by sensor union,
  not eliminated; observability only exists at footprint level.
- Features limited to detections: no weather/vegetation/drought —
  the model captures activity **persistence**, not drivers.
- NRT window unusable for 32-day features: prediction is a backtest,
  not a real-time product.
- On fixture (1 synthetic year) the chronological split is degenerate —
  real validation requires the 2013-2020 CSVs.
