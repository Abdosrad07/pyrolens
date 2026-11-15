<div align="center">

# PyroLens

**Reproducible comparison, harmonization and risk modeling of MODIS and VIIRS thermal anomaly detections**

*NASA Space Apps Challenge 2026*

---

### Important Note

PyroLens does **not** predict wildfires. It predicts the probability that a satellite will *detect* at least one fire hotspot in a grid cell — and it says so, everywhere, with full provenance.

---

[![tests](https://img.shields.io/badge/tests-119%20passing-brightgreen)]()
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![data](https://img.shields.io/badge/data-NASA%20FIRMS%20%C2%B7%20GIBS%20%C2%B7%20CMR-orange)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![React](https://img.shields.io/badge/react-18%2B-blue)]()

</div>

---

## What It Does

PyroLens answers three questions about satellite fire detections over Cameroon and West Africa:

### 1. Do the sensors agree?

VIIRS vs MODIS are compared on a common 0.25° grid with canonical time windows, measured by **Jaccard set overlap** (never called "accuracy").

### 2. What happened in this area?

On-demand zone analysis from the map: near-real-time (~5 days) **or** multi-year history from yearly FIRMS country archives (2013 → today, no API key needed).

### 3. Where will detected activity continue?

A calibrated **RandomForest** estimates `P(≥1 FIRMS detection within 8 days)` per cell — a documented *historical backtest*, not an operational forecast.

## The Golden Rule

> A satellite detection is an **observation**, not a wildfire.
> An empty cell **never** means "no fire" — clouds, night, viewing angles and overpass times create blind spots. Every output carries `data_origin` (`nasa_firms` / `firms_archive_sp` / `synthetic_fixture`) and `estimate_kind` (`historical_backtest`).

---

## Quickstart

Three processes are enough to run everything locally:

```powershell
# 1) Keys (once): copy the template, then fill in
Copy-Item env.example .env.local   # FIRMS_MAP_KEY, EARTHDATA_*, PYROLENS_API_TOKEN…
#    .env.local is gitignored — NEVER put a key in env.example (versioned)

# 2) Backend API (FastAPI) — port 8010
$env:PYTHONPATH='src'
python -m uvicorn api.index:app --host 127.0.0.1 --port 8010

# 3) Frontend (React + Vite) — port 5174, proxies /api → 8010
cd frontend; npm install; npm run dev   # → http://localhost:5174
```

| Interface | URL | Content |
| --- | --- | --- |
| **React app** (main) | `http://localhost:5174` | Map + risk layer, Overview, Calendar, Jobs, Data Quality, bilingual FR/EN AI assistant |
| **Fire Monitor** (standalone) | `web/public/fire-monitor.html` | Zero-build vanilla JS version, same features |
| **API docs** | `http://127.0.0.1:8010/api/v1/docs` | Interactive OpenAPI |

**Without the backend**: artifact views still work in static mode; job-based
features show an "API required" message.

### Environment variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `FIRMS_MAP_KEY` | pipeline + `/firms/analyze` | FIRMS NRT API key (free, email signup) |
| `EARTHDATA_USER` / `EARTHDATA_PASSWORD` / `EARTHDATA_TOKEN` | pipeline | Standard granules (currently credential-blocked, documented) |
| `PYROLENS_API_TOKEN` | API | Protects POST endpoints (`Authorization: Bearer`) |
| `PYROLENS_ALLOWED_POSTS` | API | Public-demo whitelist, e.g. `chat,firms/analyze,firms/history` |
| `PYROLENS_CORS_ORIGINS` | API | Allowed origins (comma-separated) |
| `PYROLENS_SOURCE_DIR` / `PYROLENS_ARCHIVE_DIR` / `PYROLENS_ARTIFACTS_DIR` | API | Data locations |

---

## Data

| Source | Content | Access |
| --- | --- | --- |
| **NASA FIRMS NRT API** | Last ~5 days of detections per bbox | `FIRMS_MAP_KEY` required |
| **NASA FIRMS country archives** | Full years per country, standard processing | **open, no key** |
| **Natural Earth 110m** | Country polygons → bbox intersection | local |
| **`data/fixture/`** | Deterministic synthetic CSVs (seeded) | tests/demo only, `data_origin` marked |

**Real volumes acquired**: 1,171 canonical 5-day CSV windows
(2013-01 → 2020-12, ~1.8 M detections) + West Africa archive bulk download
(18 countries × 2 sensors × 2013–2025) + a validated 2019–2020 zone comparison
(410k VIIRS + 80k MODIS detections, Jaccard 0.335).

---

## The Risk Model — In Short

Module: `src/pyrolens/prediction.py` · CLI: `pyrolens predict`

- **Label**: `y=1` if ≥1 FIRMS detection (any sensor) in the cell within
  `]t, t+8 days]` — a *detection* probability, not a fire probability.
- **Features**: 24 trailing-only features (per-sensor detection counts over
  8/16/32-day windows, FRP stats, active-day fraction, native confidence
  classes, seasonality, position) — nothing after `t` is ever used.
- **Split**: chronological train 2013–16 / validation 2017–18 / test 2019–20
  with an 8-day purge at boundaries — the test set was never touched before
  the final report.
- **Models**: smoothed-frequency baseline vs RandomForest (200 trees,
  `class_weight="balanced_subsample"`, `random_state=42`), isotonic calibration
  on validation only. RF retained by rule (PR-AUC > baseline × 1.05).

**Real-data results** (`fire_risk.json`, reference 2020-12-31,
`estimate_kind=historical_backtest`):

| Metric | Value |
| --- | --- |
| Cells / samples | 1,215 / 489,645 (test n=122,715, prevalence 31.8%) |
| **PR-AUC test** | **0.926** (baseline val 0.875 → RF val 0.928) |
| F1 / recall / precision | 0.841 / 0.844 / 0.837 |
| Brier score | 0.072 |

Full documentation: [`docs/FIRE_RISK_PREDICTION.md`](docs/FIRE_RISK_PREDICTION.md)
(FR) · [`docs/en/FIRE_RISK_PREDICTION.md`](docs/en/FIRE_RISK_PREDICTION.md) (EN).

---

## Repository Layout

```
api/                  FastAPI — routers, services, async JobManager, ETag store
src/pyrolens/         pipeline CLI: ingest, audit, baselines, normalize,
                      observability, archive, prediction, report
frontend/             React 18 + Vite + Leaflet + Recharts (main UI, port 5174)
web/                  legacy React app + standalone fire-monitor.html
prototypes/           original HTML design prototypes (reference only)
scripts/              one-off utilities (archive bulk downloader, …)
data/                 raw FIRMS CSVs (gitignored), geo, fixture, manifests
docs/                 documentation (FR) + docs/en/ (EN translations)
tests/                119 pytest tests — pipeline, API, prediction, archive
models/               serialized model (~300 MB, gitignored, regenerable)
```

---

## Documentation

- 🇫🇷 French (primary): [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md),
  [`docs/README.md`](docs/README.md) (full index)
- 🇬🇧 English: [`docs/en/PROJECT_OVERVIEW.md`](docs/en/PROJECT_OVERVIEW.md),
  [`docs/en/FIRE_RISK_PREDICTION.md`](docs/en/FIRE_RISK_PREDICTION.md)
- NASA submission audit: [`docs/NASA_SUBMISSION_AUDIT.md`](docs/NASA_SUBMISSION_AUDIT.md)

## AI-Assisted Development

This project was built with AI coding assistants, used as follows:

| Tool | Role |
|------|------|
| **Freebuff** | Backend scaffolding and initial infrastructure pieces |
| **Claude** | UI/UX refinement of the frontend |
| **ChatGPT** | Brainstorming and project supervision |
| **Devin (Cognition)** | Backend improvements and the fire-risk prediction model |

The delivered product contains **no generative AI component**: the in-app assistant is a deterministic, rules-based responder built from project artifacts (FR/EN).

## Scientific Honesty

- Detection ≠ wildfire; empty cell ≠ absence of fire
- Jaccard = set overlap between sensors, not an accuracy score
- All model figures are **backtests** on historical data — never presented as
  operational forecasts
- Provenance (`data_origin`, `generated_at`, SHA-256 manifests) is propagated
  into every artifact and visible in the UI

## License

MIT — see [LICENSE](LICENSE).
