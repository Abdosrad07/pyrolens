# Contributing to PyroLens

Thank you for joining the project! This guide summarizes setup, mandatory checks,
and **non-negotiable** editorial rules (reading contract). The code is published
under the **MIT license** (`LICENSE`), repository intended for **public visibility**.

---

## 1. Setup

```bash
# Pipeline + API (Python 3.10+)
pip install -r requirements.txt

# Frontend (Vite + React + Recharts)
npm --prefix web ci

# Verify environment (key names only, never values)
PYTHONPATH=src python3 -m pyrolens.cli doctor
```

Configuration: `cp env.example .env.local` then fill in only what you need
(`.env.local` is gitignored — never commit a key). Acquisition keys
(`FIRMS_MAP_KEY`, `EARTHDATA_*`) remain local: they are only read by the pipeline,
never by the API nor the browser.

## 2. Pre-PR Checks

```bash
python3 -m pytest                 # full suite (pipeline + API)
npm --prefix web run build        # build frontend, must exit 0
```

Attention points:

- `data/raw/firms/` (> 330 MB) is gitignored: its presence is not required for
  most of the suite, but `pyrolens download` is necessary to replay acquisition
  and for a complete `tests/test_reproducibility.py`. The footprint geometry
  (`data/raw/geo/`) and CMR inventory are versioned.
- `reports/anomalies/` (474 MB) and `reports/experiments/` are regenerable
  outputs: **never** commit them.
- After modifying a published artifact, regenerate and recouple:
  `PYTHONPATH=src python3 -m pyrolens.cli run` then
  `PYTHONPATH=src python3 -m pyrolens.cli web-artifacts`.

## 3. Editorial Rules (Reading Contract)

1. **D1 — single source of figures**: any published Jaccard/volume value comes
   from `baselines/summary.csv` (and artifacts derived from it), timestamped and
   reproducible. Old phase 1 figures are removed everywhere; do not copy them
   elsewhere (validated decision, see `docs/phase2/decisions_to_validate.md`).
2. **Never claim absence of fire**: a lack of detection displays as
   "no_record" / "unknown_observability".
   `grep -ri "pas de feu" web/src docs src` should only match explicit negations.
3. **Visible provenance**: any view or section displaying figures carries
   `data_origin` and `generated_at`.
4. **Jaccard ≠ accuracy**: preserve interpretation warnings (set overlap,
   mechanical effect of grid/window, out-of-footprint = ambiguous excluded).
5. **No client-side secrets**: no keys or acquisition URLs in `web/`, `docs/`,
   or artifacts; the API never reads `FIRMS_MAP_KEY` / `EARTHDATA_*`.

## 4. API (`api/`)

- The API is **read-only** on artifacts; only `POST /api/v1/experiments` and
  `POST /api/v1/datasets/validate` write (jobs and temporary files).
- Dedicated tests: `python3 -m pytest tests/api`.
- OpenAPI contract: after any route change, regenerate the specification
  (see `docs/api.md` §"OpenAPI Specification").
- POST endpoints require `Authorization: Bearer $PYROLENS_API_TOKEN` when the
  variable is defined.

## 5. Frontend (`web/`)

- Do not touch `web/vite.config.js` (HMR disabled by the platform).
- All artifact accesses go through `web/src/data.js`; no hardcoded values in views.
- A view displays `data.errors[]` in case of missing artifact without blocking others.
- Validity checklist: see `docs/phase2/frontend_handoff.md` §5 and
  `frontend-handoff/README.md`.

## 6. Style

- Python 3.10+, docstrings and comments in French, style compatible with
  `ruff`/`black` without exotic configuration; no dependency added without agreement.
- Functional React, hooks only from `react`; pure CSS via tokens from
  `web/src/index.css` (no Tailwind in this project).
- Commits: explicit messages in French or English, one intention per commit,
  never large data files or environment files.

## 7. PR Checklist

- [ ] `python3 -m pytest` green; `npm --prefix web run build` exit 0
- [ ] figures cross-checked with `baselines/summary.csv` (D1)
- [ ] no claim of fire absence; provenance displayed
- [ ] no secret / local path / acquisition URL committed
- [ ] artifacts and (if routes modified) `docs/openapi.json` regenerated
- [ ] documentation updated (`docs/`, `README.md`) if behavior changed
