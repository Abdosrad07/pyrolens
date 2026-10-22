"""Baselines de concordance entre capteurs.

Chaque comparaison travaille sur des ENSEMBLES de clés, jamais sur des lignes
individuelles supposées simultanées :
  - clé (cellule, date)          pour la fenêtre 1 jour
  - clé (cellule, fenêtre W)     pour W > 1
Aucune configuration n'est sélectionnée parce qu'elle maximise le Jaccard :
la sensibilité est publiée intégralement (0,10 / 0,25 / 0,50° x 1 / 4 / 8 / 16 j).
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .grids import build_set, cell_id, make_key, parse_date, window_start, window_index

SENSORS_CFG_DEFAULT = {
    "terra": {"kind": "modis", "satellites": ["Terra"]},
    "aqua": {"kind": "modis", "satellites": ["Aqua"]},
    "viirs_snpp": {"kind": "viirs", "satellites": ["N"]},
}


def sensor_spec(cfg, key: str) -> dict[str, Any]:
    spec = dict(cfg.get(f"sensors.{key}", {}) or {})
    defaults = SENSORS_CFG_DEFAULT.get(key, {})
    spec.setdefault("kind", defaults.get("kind", "unknown"))
    spec.setdefault("satellites", defaults.get("satellites", []))
    spec.setdefault("label", key)
    return spec


def select_rows(rows: Iterable[dict[str, Any]], cfg, sensor_key: str) -> list[dict[str, Any]]:
    spec = sensor_spec(cfg, sensor_key)
    kind = spec["kind"]
    allowed = set(spec["satellites"])
    out = []
    for row in rows:
        if kind != "unknown" and row.get("sensor") != kind:
            continue
        if allowed and row.get("satellite") not in allowed:
            continue
        out.append(row)
    return out


@dataclass
class Comparison:
    pair: str
    grid_deg: float
    window_days: int
    a_size: int
    b_size: int
    intersection: int
    union: int

    @property
    def jaccard(self) -> float:
        return (self.intersection / self.union) if self.union else 0.0


def compare_sets(pair: str, a: set[str], b: set[str], grid: float, window: int) -> Comparison:
    inter = len(a & b)
    union = len(a | b)
    return Comparison(pair, grid, window, len(a), len(b), inter, union)


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def _monthly_divergence(keys_a: set[str], keys_b: set[str], window: int) -> list[dict[str, Any]]:
    """Divergences par mois sur la fenêtre primaire (clés (cellule, fenêtre))."""
    def month_of(key: str) -> str:
        tail = key.split("|", 1)[1]
        if tail.startswith("w"):
            d = window_start(int(tail[1:]), window)
            return d.strftime("%Y-%m")
        return tail[:7]

    a_only: Counter = Counter()
    b_only: Counter = Counter()
    both: Counter = Counter()
    for k in keys_a - keys_b:
        a_only[month_of(k)] += 1
    for k in keys_b - keys_a:
        b_only[month_of(k)] += 1
    for k in keys_a & keys_b:
        both[month_of(k)] += 1
    months = sorted(set(a_only) | set(b_only) | set(both))
    return [
        {
            "month": m,
            "a_only": a_only.get(m, 0),
            "b_only": b_only.get(m, 0),
            "both": both.get(m, 0),
        }
        for m in months
    ]


def _daily_divergence(keys_a: set[str], keys_b: set[str]) -> list[dict[str, Any]]:
    def day_of(key: str) -> str:
        return key.split("|", 1)[1]

    a_only: Counter = Counter()
    b_only: Counter = Counter()
    both: Counter = Counter()
    for k in keys_a - keys_b:
        a_only[day_of(k)] += 1
    for k in keys_b - keys_a:
        b_only[day_of(k)] += 1
    for k in keys_a & keys_b:
        both[day_of(k)] += 1
    days = sorted(set(a_only) | set(b_only) | set(both))
    return [
        {"date": d, "a_only": a_only.get(d, 0), "b_only": b_only.get(d, 0), "both": both.get(d, 0)}
        for d in days
    ]


def _region_divergence(rows_a: list[dict], rows_b: list[dict], grid: float, window: int,
                       regions_of_b: dict[str, str]) -> list[dict[str, Any]]:
    """Divergences par région (terciles de latitude de la bbox, documentés)."""
    keys_a = {make_key(r["longitude"], r["latitude"], r["acq_date"].isoformat(), grid, window) for r in rows_a}
    keys_b = {make_key(r["longitude"], r["latitude"], r["acq_date"].isoformat(), grid, window) for r in rows_b}
    region_by_key_a: dict[str, str] = {
        make_key(r["longitude"], r["latitude"], r["acq_date"].isoformat(), grid, window): r["region"]
        for r in rows_a
    }
    a_only: Counter = Counter()
    b_only: Counter = Counter()
    both: Counter = Counter()
    for k in keys_a - keys_b:
        a_only[region_by_key_a.get(k, "inconnu")] += 1
    for k in keys_b - keys_a:
        b_only[regions_of_b.get(k, "inconnu")] += 1
    for k in keys_a & keys_b:
        both[region_by_key_a.get(k, regions_of_b.get(k, "inconnu"))] += 1
    out = []
    for region in sorted(set(a_only) | set(b_only) | set(both)):
        out.append({"region": region, "a_only": a_only[region], "b_only": b_only[region], "both": both[region]})
    return out


def _spatial(keys_a: set[str], keys_b: set[str], grid: float) -> list[dict[str, Any]]:
    a_count: Counter = Counter()
    b_count: Counter = Counter()
    for k in keys_a:
        a_count[k.split("|", 1)[0]] += 1
    for k in keys_b:
        b_count[k.split("|", 1)[0]] += 1
    out = []
    for cell in sorted(set(a_count) | set(b_count)):
        i, j = (int(x) for x in cell.split(":"))
        out.append(
            {
                "cell_i": i,
                "cell_j": j,
                "lon": i * grid + grid / 2,
                "lat": j * grid + grid / 2,
                "a_count": a_count.get(cell, 0),
                "b_count": b_count.get(cell, 0),
            }
        )
    return out


def run_baselines(
    all_rows: list[dict[str, Any]],
    cfg,
    out_dir: Path,
    artifacts_dir: Path,
    data_origin: str,
) -> dict[str, Any]:
    """Exécute les comparaisons A (Terra-Aqua) puis B (Aqua-VIIRS) puis C (sensibilité)."""
    grids: list[float] = [float(g) for g in cfg.get("analysis.grid_sizes_deg", [0.25])]
    windows: list[int] = [int(w) for w in cfg.get("analysis.window_days", [1, 8])]
    primary_grid = float(cfg.get("analysis.primary_grid_deg", 0.25))
    primary_window = int(cfg.get("analysis.primary_window_days", 8))
    pairs = [tuple(p) for p in cfg.get("analysis.pairs", [["terra", "aqua"], ["aqua", "viirs_snpp"]])]

    selected: dict[str, list[dict[str, Any]]] = {}
    for key in {k for pair in pairs for k in pair}:
        selected[key] = select_rows(all_rows, cfg, key)

    summary_rows: list[dict[str, Any]] = []
    timeseries_rows: list[dict[str, Any]] = []
    daily_rows: list[dict[str, Any]] = []
    monthly_rows: list[dict[str, Any]] = []
    spatial_rows: list[dict[str, Any]] = []
    region_rows: list[dict[str, Any]] = []

    computed: dict[tuple[str, float, int], dict[str, Any]] = {}

    for pair in pairs:
        a_key, b_key = pair
        pair_name = f"{a_key}__{b_key}"
        rows_a, rows_b = selected[a_key], selected[b_key]
        for grid in grids:
            for window in windows:
                keys_a = build_set(rows_a, grid, window)
                keys_b = build_set(rows_b, grid, window)
                cmp = compare_sets(pair_name, keys_a, keys_b, grid, window)
                summary_rows.append(
                    {
                        "pair": pair_name,
                        "sensor_a": a_key,
                        "sensor_b": b_key,
                        "grid_deg": grid,
                        "window_days": window,
                        "key_definition": "(cellule,date)" if window == 1 else "(cellule,fenêtre)",
                        "n_a": cmp.a_size,
                        "n_b": cmp.b_size,
                        "intersection": cmp.intersection,
                        "union": cmp.union,
                        "jaccard": round(cmp.jaccard, 6),
                    }
                )
                computed[(pair_name, grid, window)] = {"a": keys_a, "b": keys_b, "cmp": cmp}

                # série temporelle mensuelle (toutes configurations)
                for m in _monthly_divergence(keys_a, keys_b, window):
                    total = m["a_only"] + m["b_only"] + m["both"]
                    timeseries_rows.append(
                        {
                            "pair": pair_name,
                            "grid_deg": grid,
                            "window_days": window,
                            "month": m["month"],
                            "a_only": m["a_only"],
                            "b_only": m["b_only"],
                            "both": m["both"],
                            "jaccard": round(m["both"] / total, 6) if total else 0.0,
                        }
                    )
                # divergence spatiale
                for s in _spatial(keys_a, keys_b, grid):
                    spatial_rows.append({"pair": pair_name, "grid_deg": grid, "window_days": window, **s})

    # Détails journaliers / région sur la configuration primaire uniquement
    primary_pairs = []
    for pair in pairs:
        pair_name = f"{pair[0]}__{pair[1]}"
        keys_a = build_set(selected[pair[0]], primary_grid, primary_window)
        keys_b = build_set(selected[pair[1]], primary_grid, primary_window)
        primary_pairs.append(pair_name)
        if primary_window == 1:
            for d in _daily_divergence(keys_a, keys_b):
                daily_rows.append({"pair": pair_name, **d})
        else:
            # agrégation journalière indirecte via les clés (cellule,date)
            ka = build_set(selected[pair[0]], primary_grid, 1)
            kb = build_set(selected[pair[1]], primary_grid, 1)
            for d in _daily_divergence(ka, kb):
                daily_rows.append({"pair": pair_name, **d})
        for m in _monthly_divergence(keys_a, keys_b, primary_window):
            monthly_rows.append({"pair": pair_name, **m})
        region_by_key_b = {
            make_key(r["longitude"], r["latitude"], r["acq_date"].isoformat(), primary_grid, primary_window): r["region"]
            for r in selected[pair[1]]
        }
        for r in _region_divergence(
            selected[pair[0]], selected[pair[1]], primary_grid, primary_window, region_by_key_b
        ):
            region_rows.append({"pair": pair_name, **r})

    # Écritures disque
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "summary.csv",
               ["pair", "sensor_a", "sensor_b", "grid_deg", "window_days", "key_definition",
                "n_a", "n_b", "intersection", "union", "jaccard"], summary_rows)
    _write_csv(out_dir / "jaccard_monthly.csv",
               ["pair", "grid_deg", "window_days", "month", "a_only", "b_only", "both", "jaccard"],
               timeseries_rows)
    _write_csv(out_dir / "daily_divergence.csv", ["pair", "date", "a_only", "b_only", "both"], daily_rows)
    _write_csv(out_dir / "monthly_divergence.csv", ["pair", "month", "a_only", "b_only", "both"], monthly_rows)
    _write_csv(out_dir / "spatial_distribution.csv",
               ["pair", "grid_deg", "window_days", "cell_i", "cell_j", "lon", "lat", "a_count", "b_count"],
               spatial_rows)
    _write_csv(out_dir / "regional_divergence.csv", ["pair", "region", "a_only", "b_only", "both"], region_rows)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_origin": data_origin,
        "key_definitions": {
            "window_1": "(cellule, date)",
            "window_gt1": "(cellule, fenêtre) avec fenêtre = jours_depuis_1970 // W",
        },
        "grids_deg": grids,
        "window_days": windows,
        "primary": {"grid_deg": primary_grid, "window_days": primary_window},
        "sensor_sizes": {k: len(v) for k, v in selected.items()},
        "summary": summary_rows,
        "monthly": monthly_rows,
        "daily": daily_rows,
        "regions": region_rows,
        "jaccard_monthly": timeseries_rows,
        "spatial": [
            r for r in spatial_rows
            if float(r["grid_deg"]) == primary_grid and int(r["window_days"]) == primary_window
        ],
    }
    (artifacts_dir / "baselines.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "baselines.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
