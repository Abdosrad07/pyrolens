"""Interrogation des artefacts de comparaison (filtres, séries, spatial, exports).

Toutes les fonctions sont pures (dicts en entrée/sortie) : testables sans HTTP.
Les configurations inconnues lèvent ``ApiError(404)`` (contrat v2 : « paire ou
configuration inexistante ») ; les grilles/fenêtres sont comparées avec une
tolérance d'arrondi à 1e-6 (JSON flottants).
"""

from __future__ import annotations

import csv
import io
from typing import Any, Iterable

from fastapi import Request

from api.errors import ApiError

PAIR_LABELS = {
    "terra__aqua": "MODIS Terra ↔ MODIS Aqua",
    "aqua__viirs_snpp": "MODIS Aqua ↔ VIIRS Suomi-NPP",
}


def reject_unknown_params(allowed: set[str]):
    """Dépendance FastAPI : 400 si un paramètre de requête n'est pas attendu.

    Contrat v2 : « 400 (paramètre inconnu) ». Empêche notamment les filtres
    implicites qui pourraient faire interpréter une absence de détection.
    """

    async def dependency(request: Request) -> None:
        unknown = sorted(set(request.query_params.keys()) - allowed)
        if unknown:
            raise ApiError(
                400,
                f"Paramètre inconnu : {unknown[0]}. Paramètres acceptés : {', '.join(sorted(allowed))}.",
            )

    return dependency


def _close(a: float, b: float) -> bool:
    return round(float(a) - float(b), 6) == 0.0


def known_pairs(baselines: dict) -> list[str]:
    return sorted({row.get("pair") for row in baselines.get("summary", []) if row.get("pair")})


def filter_summary(
    baselines: dict,
    pair: str | None = None,
    grid_deg: float | None = None,
    window_days: int | None = None,
) -> list[dict[str, Any]]:
    rows = baselines.get("summary", [])
    if pair is not None:
        if pair not in known_pairs(baselines):
            raise ApiError(404, f"Paire inconnue : {pair}. Paires disponibles : {', '.join(known_pairs(baselines))}.")
        rows = [r for r in rows if r.get("pair") == pair]
    if grid_deg is not None:
        if not any(_close(g, grid_deg) for g in baselines.get("grids_deg", [])):
            raise ApiError(404, f"Grille inexistante : {grid_deg}.")
        rows = [r for r in rows if _close(r.get("grid_deg", -1), grid_deg)]
    if window_days is not None:
        if int(window_days) not in {int(w) for w in baselines.get("window_days", [])}:
            raise ApiError(404, f"Fenêtre inexistante : {window_days} jours.")
        rows = [r for r in rows if int(r.get("window_days", -1)) == int(window_days)]
    if not rows:
        raise ApiError(404, "Aucune configuration ne correspond à ces filtres.")
    return [dict(r, pair_label=PAIR_LABELS.get(r.get("pair", ""), r.get("pair"))) for r in rows]


def primary_config(baselines: dict) -> dict[str, Any]:
    return baselines.get("primary", {}) or {}


def _require_config(baselines: dict, pair: str, grid_deg: float | None, window_days: int | None) -> tuple[float, int]:
    primary = primary_config(baselines)
    grid = float(grid_deg) if grid_deg is not None else float(primary.get("grid_deg", 0.25))
    window = int(window_days) if window_days is not None else int(primary.get("window_days", 8))
    if pair not in known_pairs(baselines):
        raise ApiError(404, f"Paire inconnue : {pair}.")
    if not any(_close(g, grid) for g in baselines.get("grids_deg", [])):
        raise ApiError(404, f"Grille inexistante : {grid}.")
    if window not in {int(w) for w in baselines.get("window_days", [])}:
        raise ApiError(404, f"Fenêtre inexistante : {window} jours.")
    return grid, window


def jaccard_series(
    baselines: dict, pair: str, grid_deg: float | None, window_days: int | None
) -> list[dict[str, Any]]:
    grid, window = _require_config(baselines, pair, grid_deg, window_days)
    rows = [
        dict(r)
        for r in baselines.get("jaccard_monthly", [])
        if r.get("pair") == pair
        and _close(r.get("grid_deg", -1), grid)
        and int(r.get("window_days", -1)) == window
    ]
    if not rows:
        raise ApiError(404, "Série mensuelle indisponible pour cette configuration.")
    return sorted(rows, key=lambda r: r.get("month", ""))


def divergence_series(baselines: dict, pair: str, resolution: str) -> list[dict[str, Any]]:
    """Divergences jour/mois/région — publiées pour la configuration primaire uniquement."""
    if pair not in known_pairs(baselines):
        raise ApiError(404, f"Paire inconnue : {pair}.")
    source = {"day": "daily", "month": "monthly", "region": "regions"}.get(resolution)
    if source is None:
        raise ApiError(400, "Résolution invalide : utiliser day, month ou region.")
    rows = [dict(r) for r in baselines.get(source, []) if r.get("pair") == pair]
    if not rows:
        raise ApiError(
            404,
            "Série indisponible : les divergences journalière/mensuelle/régionale sont publiées "
            "pour la configuration primaire uniquement.",
        )
    key = {"day": "date", "month": "month", "region": "region"}[resolution]
    return sorted(rows, key=lambda r: str(r.get(key, "")))


def spatial_rows(
    baselines: dict, pair: str, grid_deg: float | None, window_days: int | None,
    limit: int, offset: int,
) -> dict[str, Any]:
    primary = primary_config(baselines)
    grid = float(grid_deg) if grid_deg is not None else float(primary.get("grid_deg", 0.25))
    window = int(window_days) if window_days is not None else int(primary.get("window_days", 8))
    if pair not in known_pairs(baselines):
        raise ApiError(404, f"Paire inconnue : {pair}.")
    if not (_close(grid, primary.get("grid_deg", 0.25)) and window == int(primary.get("window_days", 8))):
        raise ApiError(
            404,
            "Distribution spatiale publiée pour la configuration primaire uniquement "
            f"({primary.get('grid_deg')}° / {primary.get('window_days')} j).",
        )
    rows = [dict(r) for r in baselines.get("spatial", []) if r.get("pair") == pair]
    if not rows:
        raise ApiError(404, "Distribution spatiale indisponible pour cette paire.")
    rows.sort(key=lambda r: (r.get("cell_i", 0), r.get("cell_j", 0)))
    return {"total": len(rows), "offset": offset, "limit": limit, "rows": rows[offset : offset + limit]}


def rows_to_csv(rows: Iterable[dict[str, Any]]) -> str:
    rows = list(rows)
    if not rows:
        return ""
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
