# PyroLens API Contract — v1

Base URL: `/api/v1`. JSON UTF-8 responses (`application/json; charset=utf-8`),
except `/report` (`text/markdown`) and `/export` (`text/csv` or JSON download).
Machine specification: `docs/openapi.json` (export from `/api/v1/openapi.json`),
interactive at `/api/v1/docs` (Swagger) and `/api/v1/redoc`.

> **Read-only**: only `POST /api/v1/experiments` and
> `POST /api/v1/datasets/validate` are write operations (see §6).
> **D1 — single source of figures**: any published Jaccard value comes
> from `baselines/summary.csv` (`/api/v1/summary`, `dataset=summary` of
> `/export`), timestamped and reproducible; the API never recalculates these
> values.

---

## 1. Envelopes and Headers

Success response: the business object itself (no wrapper), with provenance
fields `generated_at` and/or `data_origin` depending on routes.

Error response:

```json
{ "error": { "code": "404", "message": "Unknown dataset: xyz." } }
```

| Code | When |
|---|---|
| 400 | unknown/invalid parameter, missing required columns, empty file, name ≠ `.csv` |
| 401 | `Authorization: Bearer <token>` expected (token configured) |
| 403 | experiments disabled (`PYROLENS_JOBS_ENABLED=0`) |
| 404 | route, filter, dataset, job, or export unknown |
| 405 | unauthorized method |
| 409 | source unavailable, job not finished/failed |
| 413 | upload > `PYROLENS_MAX_UPLOAD_BYTES` (10 MB) |
| 415 | refused upload content type |
| 500 | artifact unavailable/unreadable ("run pipeline") or internal error |

**Unknown parameters**: any undocumented query parameter → 400 (never silent ignore).

**HTTP cache**: weak `ETag` (artifact fingerprint) +
`Cache-Control: public, max-age=60`; send `If-None-Match` → `304` without body.
ETag changes as soon as artifact is regenerated.

**Pagination**: only `/spatial` (`limit` ≤ 5000, `offset`); other routes return
all published lines.

---

## 2. System

### `GET /health`

Immediate response, without artifact reading:

```json
{ "status": "ok", "generated_at": "2026-10-18T12:00:00+00:00",
  "data_origin": "nasa_firms", "project_version": "0.2.0" }
```

### `GET /meta`

Period, primary configuration, published grids/windows/pairs, key definitions,
observability state, interpretation note (Jaccard ≠ accuracy).

### `GET /report`

Timestamped scientific report Markdown (`Content-Type: text/markdown;
charset=utf-8`), same content as `reports/scientific_report.md`.

---

## 3. Catalog and Quality

### `GET /catalog`

```bash
curl -s https://<host>/api/v1/catalog
```

- `datasets[]`: **source** datasets (`firms_modis`, `firms_viirs` — files,
  records, analysable rows, out-of-footprint, anomalies, period) and
  **derived** datasets (`audit`, `baselines`, `observability`, `scientific_report`
  with `artifact`, `generated_at`, `data_origin`, `available`).
- `provenance`: acquisition manifest (`downloads.json`, aggregated statuses;
  URL in template `<FIRMS_MAP_KEY>`, never the key).
- Relative filenames only — no local paths.

### `GET /catalog/{dataset_id}`

Per-file for sources (`files[]` with counts, anomalies,
`date_min`/`date_max`); metadata for derived. 404 if unknown.

### `GET /audit/summary?detail=0|1`

Row accounting (`row_accounting`, `rows_by_classification`),
anomalies by category, FRP/confidence/monthly volume distributions, temporal gaps.
`detail=1` includes gap `entries` (200 max); `detail=0`
(`default`) returns `n_entries` without entries.

> Days without record are labeled `no_record` by pipeline — never "no fire".

---

## 4. Inter-Sensor Comparisons (D1 Figures)

All these routes read `baselines.json` and return `{"meta", "rows"}`;
`meta` carries `generated_at`, `data_origin`, `artifact`, `filters`.

### `GET /summary`

24 configurations (2 pairs × 3 grids × 4 windows), optional filters
`pair`, `grid_deg`, `window_days` (non-existent combination → 404).

Row fields: `pair`, `sensor_a`, `sensor_b`, `grid_deg`,
`window_days`, `key_definition`, `n_a`, `n_b`, `intersection`, `union`,
`jaccard`.

```bash
curl -s 'https://<host>/api/v1/summary?pair=terra__aqua&grid_deg=0.25&window_days=8'
# verifiable equation: union == n_a + n_b - intersection
```

### `GET /series/jaccard?pair=…[&grid_deg][&window_days]`

Monthly series: `month`, `a_only`, `b_only`, `both`, `jaccard`.
`pair` required; non-existent configuration → 404.

### `GET /series/divergence?pair=…&resolution=day|month|region`

**Primary configuration only** (0.25° / 8 days): `day` → `date`,
`month` → `month`, `region` → `region` (documented latitude tertiles),
with `a_only`, `b_only`, `both`.

### `GET /spatial?pair=…[&grid_deg][&window_days][&limit][&offset]`

```json
{ "meta": {…}, "total": 1523, "offset": 0, "limit": 1000,
  "rows": [ { "cell_i": 780, "cell_j": 300, "lon": 195.125, "lat": 75.125,
              "a_count": 4, "b_count": 3 } ] }
```

### `GET /observability[?grid_deg=…]`

4 pipeline states per sensor (`grid_deg` must match published grid else 404).
No state claims fire absence.

### `GET /export?dataset=…[&pair][&grid_deg][&window_days][&format=csv|json]`

```bash
curl -sOJ 'https://<host>/api/v1/export?dataset=summary&format=csv'
```

`dataset` ∈ `summary` | `jaccard_monthly` | `daily` | `monthly` | `regions`
`spatial` (404 otherwise); `pair` required except `summary` (400 otherwise).
CSV headers = artifact fields (reproducibility);
`Content-Disposition: attachment` (`pyrolens_<file>`).

---

## 5. Upload (validation, never integration)

### `POST /datasets/validate`

`multipart/form-data`, field `file` (`.csv`, UTF-8); accepted `Content-Type`:
`text/csv`, `application/csv`, `text/plain`, `application/octet-stream`,
`application/vnd.ms-excel`. Required columns: `latitude`, `longitude`,
`acq_date`, `acq_time`, `satellite`.

```bash
curl -s -X POST https://<host>/api/v1/datasets/validate \
  -H 'Content-Type: multipart/form-data' -F 'file=@my_file.csv'
```

Response 200 (audited, **never integrated**, `integrated: false`,
`data_origin: "uploaded_file"`):

- `dataset`: filename, inferred sensor, observed satellites/versions;
- `counts`: `n_records`, `n_rows_analysable`, `n_anomalies`,
  `n_anomalies_sampled`;
- `period`: `acq_date` bounds of analysable rows;
- `anomalies_by_category` + `anomalies_sample[]` (`line_number`, `column`,
  `raw_value`, `category`, `reason`, `classification`): raw values traced,
  **never corrected**;
- `note`: policy (no correction, no integration, no detection ≠ no fire).

Errors: 400 (name/empty/columns), 413 (size), 415 (type), 401 (token).

---

## 6. Experiments (jobs)

### `POST /experiments` → `202`

```bash
curl -s -X POST https://<host>/api/v1/experiments \
  -H 'Content-Type: application/json' ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
  -d '{"pair":"terra__aqua","grid_deg":0.25,"window_days":8,"source":"auto"}'
# → { "job_id": "3fa4856e12ab", "status": "queued",
#     "links": { "self": "…/experiments/3fa4856e12ab", "result": "…/result" } }
```

Body: `pair` (`terra__aqua` | `aqua__viirs_snpp`), `grid_deg`
(0.1 | 0.25 | 0.5), `window_days` (1 | 4 | 8 | 16), `source`
(`auto` | `fixture` | `raw`, default `auto`). Value outside configuration → 400
listing allowed values. `Location` header = tracking URL.

### `GET /experiments/{job_id}` → tracking

`status`: `queued` → `running` → `succeeded` | `failed`; fields
`created_at`, `started_at`, `finished_at`, `error` (message, never stack),
`params`, `links`. 404 if unknown (id = 12 hex).

### `GET /experiments/{job_id}/result`

200 when `succeeded`; **409** while not finished ("Retry later")
or if failed. The `result` field contains complete provenance envelope:
`started_at`, `finished_at`, `elapsed_s`, `params`, `data_origin`,
`source` (`n_files`, `n_rows_*`, `digest_sha256`), `software`, `warning`, and
metrics under `result.result`: `n_a`, `n_b`, `intersection`, `union`,
`jaccard`, `monthly[]`, `spatial_top[]`.

```bash
curl -s https://<host>/api/v1/experiments/$JOB/result | jq '.result.result.jaccard'
```

### `GET /experiments`

List of tasks known to process (`count`, `items[]` = task views),
plus persisted results re-read from `PYROLENS_EXPERIMENTS_DIR`.

Behavior: sequential execution (1 thread), `PYROLENS_MAX_JOBS` results kept
(FIFO eviction), `PYROLENS_JOBS_ENABLED=0` → 403.
Details and limits: `docs/limitations.md` §3.

---

## 7. Authentication

Open read (choice D6: public MVP). If `PYROLENS_API_TOKEN` is defined,
the two POSTs require:

```
Authorization: Bearer <token>
```

else → 401. CORS: disabled by default; `PYROLENS_CORS_ORIGINS` (CSV)
authorizes only `GET`. No secrets stored API-side; API never reads
`FIRMS_MAP_KEY` nor `EARTHDATA_*`.

---

## 8. OpenAPI Specification

- Served at `/api/v1/openapi.json` (Swagger UI: `/api/v1/docs`, ReDoc:
  `/api/v1/redoc`).
- Versioned reference export: **`docs/openapi.json`** — to regenerate after
  any route change:

```bash
python3 -c 'import json; from api.app import app; \
  open("docs/openapi.json","w",encoding="utf-8").write( \
  json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n")'
python3 -m pytest tests/api -q   # tests verify exported document
```

- Row responses (`meta` + `rows`) and row objects are free by design
  (field addition possible): this file describes **structure**,
  `docs/api.md` describes **published fields**.
