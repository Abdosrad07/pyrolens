# Technical Documentation — PyroLens

Architecture, installation, deployment, error and log management, security.
Known limits have their own document: `docs/limitations.md`.
The interface contract is in `docs/api.md` (+ `docs/openapi.json`).

---

## 1. Architecture

### 1.1 Overview

```
┌──────────────────── Python pipeline (src/pyrolens) ─────────────────────┐
│ download/geo/inventory → normalize → audit → baselines → observability │
│ → figures → report → web-artifacts                                     │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ writes (timestamped, reproducible)
                               ▼
                 web/public/artifacts/*.json|md|png   ← source of truth
                 baselines/*.csv                      ← figure reference (D1)
                               │
          ┌────────────────────┴────────────────────┐
          ▼                                         ▼
   web/ (Vite + React)                     api/ (FastAPI, read-only)
   data.js loads artifacts                serves same artifacts in JSON,
   6 views, no scientific calculation    + exports, + experiment jobs
```

Two consumers, **one single source**: artifacts written by the pipeline.
Neither the front nor the API recalculates published figures; only experiments
(`POST /api/v1/experiments`) execute computation, with the same library
`pyrolens.grids`/`pyrolens.baselines` and complete provenance.

### 1.2 API Structure (`api/`)

| File | Role |
|---|---|
| `api/app.py` | `create_app()`: FastAPI, lifespan, optional CORS, mounting routers under `/api/v1` |
| `api/index.py` | production entry point (`uvicorn api.index:app`) |
| `api/settings.py` | frozen `Settings` read from environment (`.env.example`); never reads `FIRMS_MAP_KEY`/`EARTHDATA_*` |
| `api/store.py` | `ArtifactStore`: artifact reading, memory cache by fingerprint (mtime+size), weak ETags |
| `api/errors.py` | envelope `{"error": {code, message}}`, handlers 400/401/403/404/405/409/413/415/500 |
| `api/security.py` | optional Bearer on POSTs (`PYROLENS_API_TOKEN`) |
| `api/jobs.py` | in-memory queue, 1 thread, JSON result persistence |
| `api/schemas.py` | response models (compatible by field addition) |
| `api/services/` | business logic: `catalog`, `queries`, `validation`, `experiments` |
| `api/routers/` | HTTP only: `system`, `catalog`, `audit`, `baselines`, `validation`, `experiments` |

Rule: HTTP layer contains **no** business logic; all computation lives in
`src/pyrolens/` (shared with CLI).

### 1.3 Frontend (`web/`)

Vite + React + Recharts, pure CSS (`web/src/index.css`), HMR disabled by platform
(`vite.config.js`: do not touch). All artifact accesses go through `web/src/data.js`.
Complete handoff: `frontend-handoff/`.

---

## 2. Installation and Startup

```bash
# Python 3.10+ (observed: 3.10.12)
pip install -r requirements.txt        # pipeline + API (fastapi, uvicorn, polars, …)

# Frontend
npm --prefix web ci                    # or npm --prefix web install

# Checks
PYTHONPATH=src python3 -m pyrolens.cli doctor   # key names only, never values
python3 -m pytest                               # pipeline + API
npm --prefix web run build                      # static build → web/dist
```

Configuration: `cp env.example .env.local` then fill in. All variables are
documented in `env.example`; `.env.local` overrides `.env`.

### Local Startup

```bash
# API (port 8000 by default)
PYTHONPATH=src uvicorn api.index:app --host 0.0.0.0 --port 8000
# or
PYTHONPATH=src python3 -m api.index

# Front (via platform)
freebuff-preview set "npm --prefix web run dev" 5173   # already registered
freebuff-preview start
```

Regenerate artifacts after pipeline change:

```bash
PYTHONPATH=src python3 -m pyrolens.cli run          # full sequence
PYTHONPATH=src python3 -m pyrolens.cli web-artifacts
```

---

## 3. Deployment (Freebuff)

- **Front**: build command `vite build` (see `web/package.json`) →
  `web/dist/` static; install is `npm ci`. No Python step in install/build
  (hosting image is Node.js only).
- **API**: `api/*.py` + `requirements.txt` at root — host installs Python
  dependencies itself; entry is `api/index.py` (`app`).
- Verify what host will actually execute:

```bash
freebuff-deploy check      # commands + potential issues, without spending a build
freebuff-deploy status     # state, framework, build time
freebuff-deploy logs       # build errors from a deployment
freebuff-deploy start      # redeploy after fix
```

- **Production variables**: `freebuff-deploy env list` / `freebuff-deploy
  env set '{"KEY":"value"}'` — `.env` values from sandbox are dev values.
  In production, define if needed `PYROLENS_API_TOKEN`,
  `PYROLENS_CORS_ORIGINS`; **never** provide `FIRMS_MAP_KEY`/`EARTHDATA_*`
  to production API (acquisition = local pipeline).
- After command changes: go through `freebuff-preview set-install`
  / `set-build` then `freebuff-deploy check`.

---

## 4. Errors and Logs

### 4.1 Error Envelope

Any non-2xx response is JSON UTF-8:

```json
{ "error": { "code": "404", "message": "Route unknown." } }
```

| Code | Meaning |
|---|---|
| 400 | invalid parameter/file (request validation, missing columns, empty file, name ≠ .csv) |
| 401 | `Authorization: Bearer` expected (`PYROLENS_API_TOKEN` defined) |
| 403 | experiments disabled (`PYROLENS_JOBS_ENABLED=0`) |
| 404 | unknown resource (artifact-filter, job, dataset) |
| 405 | unauthorized method |
| 409 | source unavailable / job not finished or failed |
| 413 | upload too large (`PYROLENS_MAX_UPLOAD_BYTES`) |
| 415 | refused upload content type |
| 500 | artifact unavailable/unreadable or internal error (detail only server-side) |

No message contains exception stack nor server path.

### 4.2 Logging

- Root logger `pyrolens.api` (+ `pyrolens.api.jobs` for tasks):
  internal errors with stack (`logger.exception`), experiment failures,
  startup (directories, jobs enabled or not).
- Default level `WARNING`; make visible with `LOG_LEVEL=INFO`/`DEBUG`
  if needed (`logging.basicConfig` server-side).
- Reading logs:
  - local preview: `freebuff-preview logs`
  - production: `freebuff-deploy logs`
- Pipeline side: `reports/logs/` (execution log of `pyrolens run`).

---

## 5. Security

1. **Read-only**: only `POST /api/v1/experiments` and
   `POST /api/v1/datasets/validate` modify state (job queue, temporary files).
   No writes to `data/raw`.
2. **Optional auth**: the 2 POSTs require `Authorization: Bearer
   $PYROLENS_API_TOKEN` if variable defined; without it, API open
   (choice D6: public MVP). Token compared in simple constant time, never stored.
3. **Strict CORS**: disabled by default; `PYROLENS_CORS_ORIGINS` (CSV)
   and methods limited to `GET`.
4. **Secrets**: API never reads `FIRMS_MAP_KEY` nor `EARTHDATA_*`;
   no keys in `web/`, artifacts, or responses; `.env*` gitignored,
   `env.example` contains only empty values. Verification:
   `grep -rniE "(map_key|earthdata_token|bearer [A-Za-z0-9])" web/dist docs/openapi.json`.
5. **Upload**: streaming by 1 MB chunks with ceiling, written to system temp
   directory (`pyrolens-upload-*`) deleted after analysis;
   filename reduced to basename only; no path exposed in response.
6. **Resource limiting**: 1 compute thread, `PYROLENS_MAX_JOBS` results kept
   (FIFO eviction), memory cache capped by file fingerprint, negative TTL 30s
   for absent artifacts.
7. **Transparency**: each response carries `data_origin`/`generated_at`;
   nothing claims fire absence (editorial contract, `CONTRIBUTING.md` §3).

---

## 6. Service Continuity and Reproducibility

- Artifacts are written in **atomically-compatible** way (reading by
  mtime+size fingerprint): regeneration during request only serves complete
  versions; ETag changes as soon as artifact changes.
- `Cache-Control: public, max-age=60` + `ETag` weak; `If-None-Match` → 304.
- Experiment results are persisted in `PYROLENS_EXPERIMENTS_DIR`:
  they survive restart (disk re-read), not in-progress tasks
  (see `docs/limitations.md`).
- Full figure reproduction: `pyrolens run` + `pytest`, same inputs → same
  artifacts (timestamp `generated_at` updated).
