# Methodology — PyroLens Phase 2

This document defines **how** figures are produced, before interpreting them.
It is authoritative for reviewing outputs from `baselines/`, `reports/` and
`figures/`.

---

## 1. Research Question and Non-Objectives

**Question**: to what extent do MODIS Terra, MODIS Aqua, and VIIRS Suomi-NPP 375m
hotspot detections overlap spatially and temporally over Cameroon 2013-2020,
and how does this overlap depend on analysis parameters?

**Non-objectives (prohibited by design)**:
- demonstrate physical equivalence of sensors;
- validate a harmonization algorithm (no method is announced as validated);
- conclude "no fire" from a lack of detection;
- choose the configuration that maximizes Jaccard;
- convert MODIS and VIIRS confidence levels to a common numeric scale;
- apply a constant FRP correction factor;
- naively compare individual rows as simultaneous observations of the same fire.

## 2. Set Keys (Exact Definitions)

Implementation: `src/pyrolens/grids.py`.

- **Cell**: integer index `i = floor(round((lon + 180)/g, 9))`,
  `j = floor(round((lat + 90)/g, 9))`, origin `(-180, -90)`, grid `g ∈ {0.10° ; 0.25° ; 0.50°}`.
  Rounding to 1e-9 neutralizes binary error: without it, a point exactly on a
  cell boundary would change cell depending on representation.
  Key representation: `i:j`.
- **1-day window** → key = **`(cell, date)`**, format `i:j|YYYY-MM-DD`.
- **W-day window (W ∈ {4, 8, 16})** → key = **`(cell, window)`**, format `i:j|wK`,
  with `K = days_since_1970 // W` (alignment on epoch, **not** on month).
  Alignment is explicit because it shifts window bounds relative to calendar
  months; `window_start()` reverses the key to date for display.
- **Sensor set** = **duplicate-free** set of keys for which the sensor has at
  least one detection in the footprint.

Consequence: same cell and two dates of same window produce a unique key;
overlap therefore mechanically increases with W — this is **exactly** the effect
to quantify (and not to mistake for measurement improvement).

## 3. Analysis Order (Imposed)

1. **A. Terra – Aqua**: same instrument, same nominal resolution (1 km), same
   product families; documented pass time divergences (~10:30 vs ~13:30 local).
2. **B. Aqua – VIIRS S-NPP**: adds resolution differences (1 km vs 375 m),
   scan geometry (variable scan/track), field definition, and confidence semantics.
3. **C. Parameter Sensitivity**: grids × windows, fully published.

Pairs defined in `config/pipeline.yaml` (`analysis.pairs`), row selector:
`kind` (`modis`/`viirs`) **and** `satellite` (`Terra` / `Aqua` / `N` — pilot
excludes NOAA-20 `1` and NOAA-21 `2`, explicitly).

## 4. Calculated Metrics

For each pair and each configuration `(g, W)` — implementation
`src/pyrolens/baselines.py`:

| Metric | Definition |
|---|---|
| `n_a`, `n_b` | sizes of sets A and B |
| `intersection` | `|A ∩ B|` |
| `union` | `|A ∪ B|` |
| `jaccard` | `|A ∩ B| / |A ∪ B|`, 0 if union empty |
| monthly divergence | A-only, B-only, common keys grouped by month (via `window_start` for W > 1) |
| daily divergence | same in `(cell, date)` (1-day window) |
| spatial distribution | A/B counts per cell (cell centers provided) |
| regional divergence | latitude tertiles of bbox: south / center / north |

Outputs: `baselines/summary.csv` (24 configurations = 2 pairs × 3 grids × 4 windows),
`jaccard_monthly.csv`, `daily_divergence.csv`, `monthly_divergence.csv`,
`spatial_distribution.csv`, `regional_divergence.csv`, `baselines.json`.

**Regions**: latitude tertiles of bbox are a **documented proxy**, not administrative
boundaries. They serve to locate divergences, not to explain them.

**Selection**: no configuration is retained based on Jaccard value. The figure
`figures/jaccard_sensitivity.png` and `baselines/summary.csv` publish all
combinations, increases included.

**Hourly windows**: **not analyzed**. Available fields (`acq_date`, `acq_time`
in UTC per detection) do not document hourly coverage per cell: comparing pass
times would amount to comparing different overpass instants without coverage info.
Such analysis requires observation products first (MOD09GA/MOD03).

## 5. Observability: 4-State Strategy

Implementation `src/pyrolens/observability.py`.

| State | Condition | Available today? |
|---|---|---|
| `detection_observed` | ≥ 1 detection from sensor for (cell, day) | yes |
| `no_detection_plausible_conditions` | no detection **and** coverage product documenting observation with clear sky | **no** (no coverage product acquired) |
| `unknown_observability` | no detection **and** no coverage information → **default state** | yes (default) |
| `indeterminate` | coverage present but observation state ambiguous (cloud/uncertainty) | no |

Rules:
- default state is `unknown_observability` as long as
  `observability.coverage_products_acquired = false` in configuration;
- no state, label, or output text contains "no fire" (test
  `tests/test_observability.py`);
- the report repeats the memorandum: *a cell/day without detection never implies
  absence of fire*.

## 6. Coverage Product Acquisition Plan (Not Yet Acquired)

By tiles/periods, to limit size, with same SHA-256 manifests:

1. **Observation geometry**: `MOD03` / `MYD03` (sun/satellite angles, geolocation)
   — restricted period first (e.g., one-year pilot), as it conditions FRP interpretation.
2. **Observation coverage**: `MOD09GA` (observation coverage/number, QA) per day,
   extracted on bbox only.
3. **Clouds**: `MOD35_L2` / `MYD35_L2` (clear sky confidence).
4. **VIIRS side**: VIIRS masks/quality come from a **different product**
   (VIIRS bands, distinct definitions): they are **not interchangeable** with
   `MOD35_L2`; both must be carried as separate variables with their own semantics,
   never merged into a "single cloud mask".

Until (1)-(3) are acquired, the coverage column remains empty and the default
state remains `unknown_observability`.

## 7. Data Audit Policies

Implementations `src/pyrolens/ingest.py`, `src/pyrolens/audit.py`.

- **Preserve raw**: rows are never rewritten; each anomaly preserves file,
  physical line number, column, raw value, category, reason, classification.
- **Coordinates**: non-numeric or out-of-range latitude/longitude is **excluded**,
  never "corrected" because another value might seem more plausible.
  A valid but out-of-footprint point is classified *ambiguous*: preserved, plotted,
  excluded from sets.
- **Reconstruction**: empty rule table by default (`config/pipeline.yaml → reconstruction.rules`).
  Any reconstruction must be demonstrable (file, column, pattern, justification);
  at this stage, **0 rows reconstructed**.
- **Deduplication**: for sets only, keeping first occurrence;
  duplicates remain traced (`duplicate_row`, `duplicate_key`).
- **FRP**: negative or non-numeric value → anomaly, `frp = None` (never replaced).
- **Confidence**: validated by sensor semantics (MODIS 0-100 or legacy classes;
  VIIRS low/nominal/high), **never converted**.
- **Temporal gaps**: days with no record in sensor's covered range,
  labeled `no_record`, never "no fire".
- **Immutability of `data/raw`**: verified by test (SHA-256 before/after full execution,
  `tests/test_reproducibility.py`).

## 8. Development / Evaluation Separation (for Harmonization Phase)

To apply **before** adjusting any candidate method:

- **temporal split**: development 2013-2016, evaluation 2017-2020;
- **complementary geographic split**: south vs north of polygon (latitude tertiles),
  to detect regional bias;
- evaluation metrics are calculated on evaluation set **only**, and development
  set serves only to tune parameters;
- any significant gap between the two sets = declared failure condition (see
  `harmonization.py`, entries H4-H6).

## 9. Reproducibility

- versioned configuration: `config/pipeline.yaml` (no secrets);
- deterministic fixture seed: `20260101` (tested: identical bits);
- commands: see `README.md`;
- logs: `reports/logs/*.log`; execution history:
  `web/public/artifacts/execution.json` (steps, statuses, blocks, HTTP codes);
- provenance: `data/manifests/*.json` (URL, HTTP code, bytes, SHA-256, timestamp);
- tests: `python3 -m pytest` (31 tests);
- environment: `requirements.txt`, Python 3.10.12 observed (target 3.10+).

## 10. Current Methodological Limits

1. Real FIRMS detections acquired (2013-2020, `data_origin = nasa_firms`);
   demo outputs remain identifiable by `data_origin = synthetic_fixture`.
2. No coverage products → impossibility to assign state
   "no detection under plausible observation conditions".
3. 110m footprint (simplified boundaries).
4. Set/key comparisons: no event-to-event matching (not requested at this stage,
   and not justifiable without observation geometry).
5. No independent reference (ground records, other sensors) in environment:
   external validation (H6) remains conditioned on acquiring such data.
