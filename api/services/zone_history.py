"""Historique FIRMS par zone : archive annuelle par pays (2019 → aujourd'hui).

Flux : bbox → pays intersectés (Natural Earth) → CSV annuels
``/data/country/{sensor}/{year}/…`` (ouverts, sans clé) → filtre bbox →
agrégation cellule/jour par capteur → série journalière + Jaccard.

Le résultat réutilise exactement le format de ``firms_analysis``
(``daily[]``, ``counts``, ``points``) pour alimenter le calendrier « zone »
du frontend sans adaptation.

Garde-fous :
* ``data_origin = firms_archive_sp`` — qualité standard processing, pas NRT ;
* les fichiers pays sont mis en cache sous ``data/raw/archive/`` — jamais
  re-téléchargés ;
* un pays non résolu (404 sur toutes les variantes de nom) est rapporté
  explicitement dans ``unresolved_countries``, pas ignoré silencieusement ;
* Jaccard = recouvrement de cellules/date — pas une précision ;
* les points retournés sont un échantillon plafonné.
"""

from __future__ import annotations

import logging
import math
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from api.errors import ApiError
from api.settings import Settings
from pyrolens.archive import ARCHIVE_SENSORS, DEFAULT_ARCHIVE_DIR, countries_for_bbox, ensure_country_file
from pyrolens.grids import ORIGIN_LAT, ORIGIN_LON

logger = logging.getLogger("pyrolens.api.zone_history")

Report = Callable[[str, float, str | None], None]
GEOJSON = "data/raw/geo/ne_110m_admin_0_countries.geojson"
MAX_POINTS_PER_SENSOR = 4000
FIRST_YEAR = 2000
LAST_YEAR = date.today().year


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cell_indices(lon: np.ndarray, lat: np.ndarray, grid_deg: float) -> tuple[np.ndarray, np.ndarray]:
    ci = np.floor(np.round((lon - ORIGIN_LON) / grid_deg, 9)).astype(np.int64)
    cj = np.floor(np.round((lat - ORIGIN_LAT) / grid_deg, 9)).astype(np.int64)
    return ci, cj


def _load_country_year(path: Path, bbox: list[float], grid_deg: float,
                       sensor_group: str) -> tuple[pd.DataFrame, int]:
    """Lit un CSV annuel pays, filtre la bbox, agrège cellule/jour.

    Retourne (cell-day frame, nb lignes brutes lues).
    """
    w, s, e, n = bbox
    usecols = {"latitude", "longitude", "acq_date", "frp", "confidence", "daynight"}
    df = pd.read_csv(path, usecols=lambda c: c in usecols, dtype=str)
    n_raw = len(df)
    lat = pd.to_numeric(df.get("latitude"), errors="coerce")
    lon = pd.to_numeric(df.get("longitude"), errors="coerce")
    mask = lat.notna() & lon.notna() & (lat >= s) & (lat <= n) & (lon >= w) & (lon <= e)
    df = df[mask]
    if df.empty:
        return pd.DataFrame(), n_raw
    lat_v = lat[mask].to_numpy()
    lon_v = lon[mask].to_numpy()
    ci, cj = _cell_indices(lon_v, lat_v, grid_deg)
    d = df["acq_date"].astype(str).str[:10]
    return pd.DataFrame({
        "ci": ci, "cj": cj, "date": d.to_numpy(),
        "frp": pd.to_numeric(df.get("frp"), errors="coerce").fillna(0.0).to_numpy(),
        "sensor": sensor_group,
    }), n_raw


def _aggregate(files: list[tuple[pd.DataFrame, str]], grid_deg: float) -> dict[str, Any]:
    """Agrège les cell-days par capteur → métriques journalières + Jaccard."""
    frames = [f for f, _ in files if not f.empty]
    if not frames:
        return {"daily": [], "counts": {}, "points": {"viirs": [], "modis": []}}
    all_df = pd.concat(frames, ignore_index=True)
    all_df = all_df[all_df["date"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
    if all_df.empty:
        return {"daily": [], "counts": {}, "points": {"viirs": [], "modis": []}}

    # ensembles (cellule, date) par capteur
    sets: dict[str, set[tuple[int, int, str]]] = {"viirs": set(), "modis": set()}
    for sensor in ("viirs", "modis"):
        sub = all_df[all_df["sensor"] == sensor]
        sets[sensor] = set(zip(sub["ci"], sub["cj"], sub["date"], strict=False))

    viirs_cells = {(c[0], c[1], c[2]) for c in sets["viirs"]}
    modis_cells = {(c[0], c[1], c[2]) for c in sets["modis"]}
    inter = viirs_cells & modis_cells
    union = viirs_cells | modis_cells

    by_date: dict[str, dict[str, set]] = {}
    for ci, cj, d in viirs_cells:
        by_date.setdefault(d, {"a": set(), "b": set()})["a"].add((ci, cj))
    for ci, cj, d in modis_cells:
        by_date.setdefault(d, {"a": set(), "b": set()})["b"].add((ci, cj))
    daily = []
    for d in sorted(by_date):
        a, b = by_date[d]["a"], by_date[d]["b"]
        u = a | b
        daily.append({
            "date": d,
            "viirs_cells": len(a), "modis_cells": len(b),
            "common": len(a & b),
            "jaccard": round(len(a & b) / len(u), 4) if u else None,
        })

    # points échantillonnés pour la carte (lat/lon centroïde de cellule)
    def _points(sensor: str) -> list[list[Any]]:
        sub = all_df[all_df["sensor"] == sensor]
        if sub.empty:
            return []
        if len(sub) > MAX_POINTS_PER_SENSOR:
            sub = sub.sample(n=MAX_POINTS_PER_SENSOR, random_state=42)
        # centroïde de la cellule (même convention que grids.cell_center)
        lons = ORIGIN_LON + (sub["ci"].to_numpy() + 0.5) * grid_deg
        lats = ORIGIN_LAT + (sub["cj"].to_numpy() + 0.5) * grid_deg
        return [[round(la, 5), round(lo, 5), d, "", "", None]
                for la, lo, d in zip(lats, lons, sub["date"], strict=False)]

    return {
        "daily": daily,
        "counts": {
            "viirs_cells": len(viirs_cells), "modis_cells": len(modis_cells),
            "common_cells": len(inter), "union_cells": len(union),
            "viirs_rows": int((all_df["sensor"] == "viirs").sum()),
            "modis_rows": int((all_df["sensor"] == "modis").sum()),
        },
        "points": {"viirs": _points("viirs"), "modis": _points("modis")},
    }


def run_zone_history(params: dict[str, Any], settings: Settings, report: Report) -> dict[str, Any]:
    """Corps du job : bbox + plage d'années → série historique par capteur."""
    t0 = time.monotonic()
    bbox = [float(v) for v in params["bbox"]]
    start_year = int(params.get("start_year", 2019))
    end_year = int(params.get("end_year", date.today().year))
    grid_deg = float(params.get("grid_deg", 0.25))
    archive_dir = Path(getattr(settings, "archive_dir", None) or DEFAULT_ARCHIVE_DIR)
    geojson = Path(getattr(settings, "geojson_path", None) or GEOJSON)

    if start_year < FIRST_YEAR or end_year > LAST_YEAR or start_year > end_year:
        raise ApiError(400, f"Plage invalide : {FIRST_YEAR} ≤ start ≤ end ≤ {LAST_YEAR}.")
    if not geojson.exists():
        raise ApiError(409, "Polygone Natural Earth absent : exécuter `pyrolens geo`.")

    # purger les téléchargements interrompus (.part*) — incomplets par définition
    for stale in archive_dir.glob("**/*.part*"):
        try:
            stale.unlink()
        except OSError:
            pass

    report("countries", 3, "résolution des pays intersectés")
    hits = countries_for_bbox(bbox, geojson)
    if not hits:
        raise ApiError(404, "Aucun pays détecté pour cette bbox (hors couverture cartographique).")
    report("countries", 8, f"{len(hits)} pays : {', '.join(h.name for h in hits[:5])}{'…' if len(hits) > 5 else ''}")

    # --- téléchargement/garantie des fichiers annuels
    files_meta: list[dict[str, Any]] = []
    total_tasks = len(ARCHIVE_SENSORS) * len(hits) * (end_year - start_year + 1)
    done = 0
    for sensor_key in ARCHIVE_SENSORS:
        for year in range(start_year, end_year + 1):
            for hit in hits:
                done += 1
                pct = 8 + 55 * done / max(1, total_tasks)
                report("fetch", pct, f"{sensor_key} {year} — {hit.name}")
                meta = ensure_country_file(sensor_key, year, hit, archive_dir)
                files_meta.append(meta)

    unresolved = [m for m in files_meta if m["status"] == "unresolved"]
    errors = [m for m in files_meta if m["status"] == "error"]
    ready = [m for m in files_meta if m.get("path")]
    if not ready:
        raise ApiError(
            502,
            "Aucun fichier archive accessible : "
            + (errors[0]["error"] if errors else "noms de pays non résolus"),
        )
    report("load", 66, f"{len(ready)} fichiers prêts ({len(unresolved)} non résolus, {len(errors)} erreurs)")

    # --- lecture + filtrage bbox + agrégation
    sensor_group = {"viirs": "viirs", "modis": "modis"}
    loaded: list[tuple[pd.DataFrame, str]] = []
    n_rows_raw = 0
    for meta in ready:
        df, n_raw = _load_country_year(Path(meta["path"]), bbox, grid_deg,
                                       sensor_group[meta["sensor"]])
        n_rows_raw += n_raw
        loaded.append((df, meta["sensor"]))
    report("aggregate", 85, f"{n_rows_raw} lignes brutes lues")

    agg = _aggregate(loaded, grid_deg)
    report("metrics", 95, f"{len(agg['daily'])} jours avec détections")

    downloaded = [m for m in files_meta if m["status"] == "downloaded"]
    cached = [m for m in files_meta if m["status"] == "cached"]
    result = {
        "params": dict(params),
        "data_origin": "firms_archive_sp",
        "generated_at": _now(),
        "window": {"requested": "archive", "start_year": start_year, "end_year": end_year},
        "grid_deg": grid_deg,
        "key_definition": f"(cellule {grid_deg}°, date)",
        "countries": [{"name": h.name, "iso3": h.iso3} for h in hits],
        "unresolved_countries": sorted({m["country"] for m in unresolved}),
        "file_errors": [{"country": m["country"], "sensor": m["sensor"],
                         "year": m["year"], "error": m.get("error")} for m in errors],
        "files": {"downloaded": len(downloaded), "cached": len(cached), "ready": len(ready)},
        "counts": agg["counts"],
        "daily": agg["daily"],
        "jaccard": (
            round(sum(d["common"] for d in agg["daily"]) /
                  max(1, sum(d["viirs_cells"] + d["modis_cells"] - d["common"] for d in agg["daily"])), 4)
            if agg["daily"] else None
        ),
        "points": agg["points"],
        "elapsed_s": round(time.monotonic() - t0, 2),
        "note": (
            f"Archive FIRMS SP {start_year}→{end_year} filtrée sur la bbox — pays : "
            f"{', '.join(h.name for h in hits)}. VIIRS-SNPP vs MODIS (Terra+Aqua). "
            "Jaccard = recouvrement cellules/date, pas une précision. "
            "Une cellule vide = aucun enregistrement, pas absence de feu."
        ),
    }
    report("metrics", 100, "terminé")
    return result
