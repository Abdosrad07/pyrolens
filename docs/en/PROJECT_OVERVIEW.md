# PyroLens — Complete project documentation (English)

> NASA Space Apps Challenge 2026 feasibility study: comparison and
> harmonization of **MODIS** and **VIIRS** thermal detections (NASA FIRMS),
> historical zone analysis, and a detected-activity risk prediction model
> over Cameroon and West Africa.
>
> *French version: [`../PROJECT_OVERVIEW.md`](../PROJECT_OVERVIEW.md)*

---

## 1. Overview

PyroLens answers three questions:

1. **Do the sensors behave the same?** — VIIRS/MODIS comparison on a common
   grid and canonical windows, measured by **Jaccard** (set overlap,
   never an accuracy).
2. **What happened in a given area?** — On-demand analysis of a map-clicked
   perimeter: NRT (~5 days) or **yearly archive history** (2013→today,
   per-country yearly files).
3. **Where will detected activity continue?** — Calibrated **RandomForest**
   risk model: P(≥1 FIRMS detection within 8 days) per cell.

### Guiding scientific principle

> A satellite detection is an **observation**, not a wildfire.
> An empty cell **never** means "no fire": clouds, night, viewing angles and
> satellite overpasses create blind spots. Every output carries
> `data_origin` (nasa_firms / synthetic_fixture / firms_archive_sp) and
> `estimate_kind` (historical_backtest) so the interface cannot oversell
> results.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA                                                           │
│  data/raw/firms/        1,171 canonical CSVs (2013-2020, 344 MB) │
│  data/raw/archive/      yearly per-country CSVs (2013-2025)     │
│  data/fixture/          synthetic fixtures (tests/demo)         │
│  data/raw/geo/          Natural Earth 110m (country → bbox)     │
└──────────────┬──────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────┐
│  PIPELINE  src/pyrolens/  (CLI `pyrolens …`)                     │
│  ingest → audit → baselines → observability → normalize →       │
│  figures → report → predict (risk model)                        │
└──────────────┬──────────────────────────────────────────────────┘
               │ writes timestamped JSON artifacts
┌──────────────▼──────────────────────────────────────────────────┐
│  FastAPI  api/  →  http://127.0.0.1:8010/api/v1                 │
│  Artifact reads (ETag) · async jobs (1 worker) · POST           │
│  protected by PYROLENS_API_TOKEN                                │
└───────┬───────────────────────────────┬─────────────────────────┘
        │ /api proxy                     │ /artifacts statics
┌───────▼──────────┐          ┌──────────▼────────────────────────┐
│ frontend/ React  │          │ web/public/fire-monitor.html     │
│ Vite, port 5174  │          │ standalone vanilla JS monitor    │
│ (main UI)        │          │ + web/ legacy React app 5173     │
└──────────────────┘          └───────────────────────────────────┘
```

**API golden rule**: read-only artifact access + bounded job execution. No
scientific computation happens "on the fly" in a GET request; POSTs
(analyze, history, predict, chat, experiments) submit jobs to the
`JobManager` (single worker, real progress, disk resume for large jobs).

---

## 3. Data

### 3.1 Sources

| Source | Content | Access |
|---|---|---|
| FIRMS NRT API (`firms.modaps…/api/area/csv`) | Last ~5 days of detections per bbox | `FIRMS_MAP_KEY` required |
| FIRMS **country archive** (`/data/country/{sensor}/{year}/{file}.csv`) | Full years per country, standard processing | **open, no key** |
| Natural Earth 110m GeoJSON | Country polygons → bbox intersection | local |
| `data/fixture/` | Reproducible synthetic CSVs (fixed seed) | local, tests/demo |

### 3.2 Real volumes acquired

- **Pipeline**: 1,171 canonical files (5-day windows, 2013-01 → 2020-12)
  — ~1.8 M detections, 344 MB
- **Zone archive**: 12 files (Chad/Nigeria/Cameroon 2019-2020) —
  410,370 VIIRS + 79,666 MODIS detections on the test bbox
- **West Africa archive** (in progress): 18 countries × 2 sensors ×
  13 years (2013-2025) ≈ 468 files — script
  `scripts/download_west_africa_archive.py`, manifest
  `data/manifests/archive_bulk_west_africa.jsonl`

### 3.3 Normalization

`pyrolens normalize` merges 5-day slices into **canonical windows**
[date, date+5d[ with strict deduplication by `(cell, date, sensor)`.
A date belongs to exactly one window → no double counting.

---

## 4. The pipeline (`src/pyrolens/`)

| CLI step | Role | Output artifact |
|---|---|---|
| `download` | Acquires FIRMS NRT + Earthdata probe | `data/manifests/downloads.json` |
| `audit` | Quality: anomalies, temporal gaps, missing values | `artifacts/audit.json` |
| `baselines` | Comparison A (Terra-Aqua), B (Aqua-VIIRS), C (sensitivity) | `artifacts/baselines.json` |
| `observability` | 4 observability states — **never** "no fire" | `artifacts/observability.json` |
| `normalize` | Canonical 5-day windows | normalized CSVs |
| `figures` / `report` | Charts + Markdown/DOCX report | `figures/`, `reports/` |
| `predict` | **Risk model** (see §7) | `artifacts/fire_risk.json` + `models/` |

Key point: every artifact carries `generated_at`, `data_origin`,
`project_version` — provenance lives in the data, not in a README.

---

## 5. The API (`api/`)

Base: `http://127.0.0.1:8010/api/v1` — interactive docs at `/api/v1/docs`.

### Reads (GET, no token)

| Endpoint | Content |
|---|---|
| `/health` `/meta` | Health, period, primary config, pairs |
| `/catalog`, `/catalog/{id}` | Datasets and variables |
| `/audit/summary` | Audit summary |
| `/baselines*` `/fire-calendar/{daily,weekly,monthly,timeseries}` | Comparisons + time series |
| `/methodology*` `/validation*` | Methodology and decisions |
| `/fire-risk` | **Risk model artifact** |
| `/report` | Scientific Markdown report |
| `/downloads/status` | Pipeline + archive progress (disk only) |

### Writes (POST, `PYROLENS_API_TOKEN` if configured)

| Endpoint | Effect |
|---|---|
| `/experiments` | Parameterizable harmonization job |
| `/firms/analyze` | NRT zone analysis (bbox + radius + grid) |
| `/firms/history` | Archive history by zone (years + grid) |
| `/predict` | (Re)train the risk model — ~10 min job |
| `/chat` | Deterministic assistant (see §9) |
| `/datasets/validate` | CSV file validation |

Each job exposes `GET …/{id}` (status + `progress{step,pct,detail}`) and
`GET …/{id}/result`. `GET /experiments` lists **all** jobs.

---

## 6. The interfaces

### `frontend/` — React (main, port 5174)

Vite + React 18 + react-leaflet + recharts, `fr`/`en` i18n. `/api` proxy →
`VITE_API_ORIGIN` (8010). Views: **Map** (GIBS tiles + risk GeoJSON layer),
**Overview** (pipeline artifacts + mini-map), **Calendar** (real daily
divergence), **Jobs** (real API jobs), **Data Quality** (audit.json),
**Risk** (config panel + "Run prediction" → `POST /predict` + polling).
The floating AI sphere and bottom dock are available on every view; the
assistant answers in the language of the question (FR/EN).

```bash
cd frontend && npm install && npm run dev   # http://localhost:5174
```

### `web/public/fire-monitor.html` — standalone Fire Monitor

Same design, zero build: served by any static server or the `web/` dev
server (5173). Adds: map click → zone analysis NRT/history, multi-year
calendar, live downloads gauge.

### `web/` — legacy React app

Kept for the pipeline views (baselines, observability, methodology).

---

## 7. The fire-risk prediction model — in detail

Module: `src/pyrolens/prediction.py` — function `run_prediction()`.

### 7.1 The problem

For each **0.25° grid cell** and each **date t**:

```
label(t) = 1  if ≥ 1 FIRMS detection in ]t, t+8 days]
         = 0  otherwise
```

The model estimates `P(label = 1 | features(t))` — the probability that a
cell records at least one detection within 8 days. **This is not a fire
probability**: it is a detection probability.

### 7.2 Training data

- 1,170 canonical FIRMS CSVs → ~1.8 M detections → (i, j) cells on the
  0.25° grid + acquisition day
- Sampling window: `[min_date + 32 d, max_date − 8 d]`,
  **7-day stride** per cell
- 1,215 "active" cells (≥ 1 detection over the period) →
  **489,645 samples**

### 7.3 Features — 100% "trailing"

Absolute rule: at date `t`, only observations `≤ t` are used. Per cell:

| Feature | Description |
|---|---|
| `n_{terra,aqua,viirs}_8/16/32` | detections per sensor over rolling 8/16/32 d |
| `n_all_*` | all sensors combined |
| `frp_mean_16`, `frp_max_16` | mean/max radiative power (16 d) |
| `days_active_32`, `day_frac_32` | days with ≥1 detection / fraction (32 d) |
| `viirs_conf_{low,nominal,high}_16` | VIIRS confidence-class detections |
| `modis_conf_mean_16` | mean MODIS confidence |
| `month_sin`, `month_cos` | seasonality (dry season) |
| `lat`, `lon` | cell position |

Implementation: `CellIndex` sorts dates per cell;
`_count_in/_sum_in/_max_in/_mean_in` use `np.searchsorted` →
features in O(log n) per cell-date.

### 7.4 The split — chronological, never random

```
train      : 2013 → 2016   (245,430 samples)
validation : 2017 → 2018   (121,500)
test       : 2019 → 2020   (122,715)   ← never touched before the report
```

**8-day purge** at boundaries: a train label cannot overlap a
validation/test feature (leakage through the window). This is what makes
the test metrics honest — a random split would have inflated scores.

### 7.5 The two competing models

**"Frequency" baseline** (reference): per cell, probability =
detection-day frequency smoothed over train history + monthly seasonal
adjustment. No ML — pure statistics. Validation: **PR-AUC = 0.875**.

**RandomForest** (`sklearn.ensemble.RandomForestClassifier`):
- 200 trees, `class_weight='balanced_subsample'` (31.8% positives
  on test — balanced weighting avoids bias toward the majority class)
- `min_samples_leaf=20`, free depth, `random_state=42`
- 24 features → the RF captures non-linear interactions
  ("3 detections this week" ≠ "3 weeks ago") without normalization

Validation: **PR-AUC = 0.928** → retained (rule: > baseline × 1.05).
`feature_importances_` confirms recent counts dominate —
**persistence** of fire activity is the main signal.

### 7.6 Isotonic calibration

The RF outputs scores, not reliable probabilities. An **isotonic
regression** is fitted **on validation only**: a displayed 42%
probability then corresponds to an observed ~42% frequency.
Without this step, the map percentages would be misleading.

### 7.7 Metrics (test 2019-2020, never seen in training)

| Metric | Value | Reading |
|---|---|---|
| **PR-AUC** | **0.926** | area under precision-recall curve — key metric at 31.8% positives |
| F1 | 0.841 | precision/recall compromise at optimal threshold (0.42) |
| Recall | 0.844 | 84% of detection days are covered |
| Brier | 0.072 | probabilistic quality (calibrated probabilities) |

### 7.8 Output

`fire_risk.json`: `cells[]` {cell_i, cell_j, lat, lon, prob, level},
`metrics`, `period`, `reference_date` (2020-12-31), `estimate_kind` =
`historical_backtest`, `data_origin` = `nasa_firms`. The serialized model
(`models/fire_risk_model.joblib`, ~300 MB) is **outside Git** —
regenerable via `pyrolens predict` in ~10 min.

### 7.9 Honest limits

- **Backtest only**: data ≤ 2020; the map is a historical simulation,
  not today's forecast
- Label = detection, not fire → metrics measure the ability to anticipate
  what satellites *will see*, clouds included
- No weather drivers (rainfall, wind, humidity) — the signal is dominated
  by persistence; adding ERA5 is the logical next step
- A single threshold (0.42) for all of Cameroon — spatial calibration
  would improve the map

---

## 8bis. Colleague guide — local training

`docs/MODEL_TRAINING_COLLEAGUE.md`: setup, downloads (NRT >2020,
keyless country archives), `pyrolens predict` and its options, and the
levers to make the model more performant.

---

## 9. The assistant (`/api/v1/chat`)

Deterministic, **no LLM**: `api/services/chat.py` detects 11 intents
(summary, risk levels/colors, sensor differences, prediction, zone,
history, data, calendar, jobs, quality, help) in **French and English**
(automatic language detection) and answers from real artifacts + live job
state. Every answer cites its source — consistent with the project's
rigor, and the natural injection point if an LLM is added later.

---

## 10. Running the project

```bash
# 1. Backend (prerequisite: .env.local with FIRMS_MAP_KEY, PYROLENS_API_TOKEN)
set PYTHONPATH=src
python -m uvicorn api.index:app --host 127.0.0.1 --port 8010

# 2. React frontend (main)
cd frontend && npm install && npm run dev        # → http://localhost:5174

# 3. Or standalone Fire Monitor (static)
cd web && npm install && npm run dev              # → http://localhost:5173
# or simply open web/public/fire-monitor.html

# 4. Pipeline (to regenerate artifacts)
python -m pyrolens.cli download                   # FIRMS data
python -m pyrolens.cli audit baselines observability normalize
python -m pyrolens.cli predict                    # risk model (~10 min)
python -m pyrolens.cli report                     # final report
```

### Tests

```bash
python -m pytest tests        # 119 tests (pipeline + API + predict + archive)
cd frontend && npm run build  # React build check
```

---

## 11. Scientific limits (recap)

1. Detection ≠ wildfire; empty cell ≠ absence of fire
2. Jaccard = set overlap between sensors, not an accuracy
3. Data < 2021 comes from the **pipeline** (canonical NRT);
   2019+ also comes from the **SP archive** when available —
   provenance is always displayed
4. The country archive lags a few months behind the current year;
   NRT covers the last ~5 days
5. All model figures are **backtests** on historical data — never
   presented as operational forecasts

---

## 12. Repository structure

```
pyrolens/
├── api/                  FastAPI — routers/, services/, jobs.py, store.py
├── src/pyrolens/         pipeline: ingest, audit, baselines, normalize,
│                         observability, archive, prediction, cli, report
├── frontend/             main React app (port 5174)
├── web/                  legacy React app + standalone fire-monitor.html
├── prototypes/           original HTML design prototypes (reference)
├── scripts/              download_west_africa_archive.py (bulk archive)
├── data/
│   ├── raw/firms/        pipeline CSVs (gitignored)
│   ├── raw/archive/      country archive CSVs (gitignored)
│   ├── raw/geo/          Natural Earth
│   ├── fixture/          synthetic
│   └── manifests/        downloads.json + archive_bulk_*.jsonl
├── models/               .joblib (gitignored, regenerable)
├── web/public/artifacts/ served JSON artifacts (versioned)
├── docs/                 FR docs + docs/en/ EN translations
└── tests/                pytest (pipeline, api, prediction, archive)
```
