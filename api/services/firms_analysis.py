"""Analyse de zone à la demande : détections FIRMS VIIRS vs MODIS + harmonisation.

Flux : bbox arbitraire → API FIRMS ``area/csv`` (sources SP, fenêtre récente)
→ normalisation → appariement par cellule/grille/date → Jaccard.

Garde-fous :
* la clé ``FIRMS_MAP_KEY`` reste côté serveur (jamais dans les URLs journalisées
  ni dans les réponses — seuls les noms de sources sont conservés) ;
* les points retournés sont un échantillon plafonné (visualisation carte) ;
* le Jaccard mesure le recouvrement des cellules — pas une précision ;
* « archive » n'est pas supporté pour une zone arbitraire (fichiers FIRMS
  annuels mondiaux) : la tâche échoue avec une explication explicite.
"""

from __future__ import annotations

import csv
import io
import logging
import math
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from api.errors import ApiError
from api.settings import Settings

logger = logging.getLogger("pyrolens.api.firms")

FIRMS_API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
# Sources NRT (near real-time) — seules sources avec des données récentes via
# l'API area : les sources SP (qualité science, utilisées par le pipeline pour
# 2013-2020) ne couvrent pas les derniers jours, et VIIRS_SNPP est vide
# actuellement. NOAA-20 et NOAA-21 sont fusionnées côté « VIIRS ».
SOURCES = {
    "viirs": ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"],
    "modis": ["MODIS_NRT"],
}
WINDOWS = {"nrt", "archive"}
MAX_POINTS_PER_SENSOR = 3000
MAX_DAY_RANGE = 5  # borne documentée de l'API area/csv
FETCH_TIMEOUT_S = 60.0

Report = Callable[[str, float, str | None], None]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fetch_csv(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "PyroLens/0.2 (+api)"})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_S) as resp:  # noqa: S310 — URL API publique
        return resp.status, resp.read()


def _download_sensor(source: str, key: str, bbox: list[float], start: date, day_range: int) -> list[dict[str, Any]]:
    """Télécharge un CSV FIRMS pour une source/bbox/fenêtre. Renvoie les lignes brutes."""
    bbox_s = ",".join(f"{v:g}" for v in bbox)
    url = f"{FIRMS_API}/{key}/{source}/{bbox_s}/{day_range}/{start.isoformat()}"
    rows: list[dict[str, Any]] = []
    attempts = 0
    while attempts < 3:
        attempts += 1
        try:
            status, body = _fetch_csv(url)
        except Exception as exc:  # noqa: BLE001
            if attempts < 3:
                time.sleep(3 * attempts)
                continue
            raise ApiError(502, f"FIRMS injoignable pour {source} : {type(exc).__name__}.") from exc
        if status == 200 and b"latitude" in body[:300].lower():
            text = body.decode("utf-8", errors="replace")
            for row in csv.DictReader(io.StringIO(text)):
                rows.append(row)
            return rows
        if status in (429, 500, 502, 503, 504):
            time.sleep(5 * attempts)
            continue
        raise ApiError(502, f"FIRMS a répondu HTTP {status} pour {source}.")
    raise ApiError(502, f"FIRMS : trop de tentatives pour {source}.")


def _f(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _normalize(rows: list[dict[str, Any]], bbox: list[float], grid_deg: float,
               sensor_label: str) -> tuple[list[dict[str, Any]], set[tuple[int, int, str]]]:
    """Filtre dans la bbox, parse date/heure, affecte la cellule de la grille."""
    w, s, e, n = bbox
    pts: list[dict[str, Any]] = []
    cells: set[tuple[int, int, str]] = set()
    for r in rows:
        lat, lon = _f(r.get("latitude")), _f(r.get("longitude"))
        if lat is None or lon is None or not (s <= lat <= n and w <= lon <= e):
            continue
        d = str(r.get("acq_date") or "")[:10]
        if len(d) != 10:
            continue
        ci = math.floor(lon / grid_deg)
        cj = math.floor(lat / grid_deg)
        cells.add((ci, cj, d))
        pts.append({
            "lat": round(lat, 5), "lon": round(lon, 5),
            "date": d, "time": str(r.get("acq_time") or "")[:4],
            "satellite": str(r.get("satellite") or "")[:12],
            "frp": _f(r.get("frp")),
            "sensor": sensor_label,
        })
    return pts, cells


def _sample(points: list[dict[str, Any]], cap: int = MAX_POINTS_PER_SENSOR) -> list[list[Any]]:
    if len(points) <= cap:
        return [[p["lat"], p["lon"], p["date"], p["time"], p["satellite"], p["frp"]] for p in points]
    step = len(points) / cap
    return [[p["lat"], p["lon"], p["date"], p["time"], p["satellite"], p["frp"]]
            for p in (points[int(i * step)] for i in range(cap))]


def run_zone_analysis(params: dict[str, Any], settings: Settings, report: Report) -> dict[str, Any]:
    """Corps du job : retourne le dict de résultat persisté par JobManager."""
    t0 = time.monotonic()
    bbox = [float(v) for v in params["bbox"]]
    window = params.get("window", "nrt")
    grid_deg = float(params.get("grid_deg", 0.05))

    if window == "archive":
        raise ApiError(
            400,
            "L'archive FIRMS par zone arbitraire n'est pas disponible : les archives "
            "sont des fichiers annuels mondiaux. Utilisez la fenêtre récente (NRT/SP) "
            "ou le pipeline complet pour l'historique 2013-2020.",
        )
    if not settings.firms_map_key:
        raise ApiError(503, "FIRMS_MAP_KEY absente du serveur — configurez-la dans .env.local.")

    # Fenêtre NRT : 5 derniers jours glissants incluant aujourd'hui (les sources
    # NRT couvrent ~24-72 h ; au-delà l'API renvoie des fichiers vides).
    end = date.today()
    start = end - timedelta(days=MAX_DAY_RANGE - 1)
    day_range = MAX_DAY_RANGE

    report("fetch_viirs", 5, f"VIIRS NRT (NOAA-20+21) — {start} → {end}")
    viirs_rows: list[dict[str, Any]] = []
    for src in SOURCES["viirs"]:
        viirs_rows.extend(_download_sensor(src, settings.firms_map_key, bbox, start, day_range))
    report("fetch_viirs", 35, f"{len(viirs_rows)} lignes brutes")

    report("fetch_modis", 40, f"MODIS NRT — {start} → {end}")
    modis_rows: list[dict[str, Any]] = []
    for src in SOURCES["modis"]:
        modis_rows.extend(_download_sensor(src, settings.firms_map_key, bbox, start, day_range))
    report("fetch_modis", 65, f"{len(modis_rows)} lignes brutes")

    report("normalize", 70, f"grille {grid_deg}° — filtre bbox + cellules")
    viirs_pts, viirs_cells = _normalize(viirs_rows, bbox, grid_deg, "viirs")
    modis_pts, modis_cells = _normalize(modis_rows, bbox, grid_deg, "modis")
    report("normalize", 82, f"{len(viirs_pts)} pts VIIRS · {len(modis_pts)} pts MODIS")

    report("match", 86, "appariement cellules (cellule, date)")
    inter = viirs_cells & modis_cells
    union = viirs_cells | modis_cells
    jaccard = (len(inter) / len(union)) if union else None

    # Série quotidienne : pour chaque date, Jaccard des cellules du jour.
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
            "date": d, "viirs_cells": len(a), "modis_cells": len(b),
            "common": len(a & b), "jaccard": round(len(a & b) / len(u), 4) if u else None,
        })

    report("metrics", 96, "agrégation des métriques")
    result = {
        "params": dict(params),
        "data_origin": "firms_api_nrt",
        "generated_at": _now(),
        "window": {"requested": window, "start": start.isoformat(), "end": end.isoformat(), "day_range": day_range},
        "sources": {k: (v if isinstance(v, list) else [v]) for k, v in SOURCES.items()},
        "counts": {
            "viirs_rows": len(viirs_rows), "modis_rows": len(modis_rows),
            "viirs_points": len(viirs_pts), "modis_points": len(modis_pts),
            "viirs_cells": len(viirs_cells), "modis_cells": len(modis_cells),
            "common_cells": len(inter), "union_cells": len(union),
        },
        "jaccard": round(jaccard, 4) if jaccard is not None else None,
        "grid_deg": grid_deg,
        "key_definition": f"(cellule {grid_deg}°, date)",
        "daily": daily,
        "points": {"viirs": _sample(viirs_pts), "modis": _sample(modis_pts)},
        "elapsed_s": round(time.monotonic() - t0, 2),
        "note": (
            "Données FIRMS NRT (near real-time, fenêtre ~5 jours) pour la bbox demandée — "
            "VIIRS NOAA-20/21 vs MODIS Terra/Aqua. Qualité préliminaire, non validée. "
            "Jaccard = |cellules VIIRS ∩ MODIS| / |union| — recouvrement des détections, pas une précision. "
            "Une cellule vide signifie « aucun enregistrement », pas « aucun feu »."
        ),
    }
    report("metrics", 100, "terminé")
    return result
