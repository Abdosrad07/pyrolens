"""Exécution d'une expérience d'harmonisation (paire × grille × fenêtre).

L'expérience reproduit **exactement** les définitions d'ensembles du pipeline
(`pyrolens.grids` / `pyrolens.baselines`) sur la source configurée : données
réelles normalisées (``data/raw/firms``) ou échantillon synthétique
(``data/fixture``). Le résultat porte sa provenance complète : paramètres,
origine des données, empreinte de la source, version logicielle, horodatages.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pyrolens import __version__ as PYROLENS_VERSION
from pyrolens.audit import audit_file
from pyrolens.baselines import _monthly_divergence, _spatial, compare_sets, select_rows
from pyrolens.config import Config, PROJECT_ROOT
from pyrolens.grids import build_set

from api.errors import ApiError
from api.settings import Settings
from api.services.validation import _load_geometry


def resolve_source_dir(cfg: Config, settings: Settings, requested: str) -> Path:
    """Répertoire source effectif : fixture, raw, ou choix automatique du pipeline."""
    raw_firms = cfg.path_of("raw") / "firms"
    fixture = cfg.path_of("fixture")
    if requested == "fixture":
        if not fixture.exists() or not list(fixture.glob("*.csv")):
            raise ApiError(409, "Échantillon synthétique indisponible : exécuter `pyrolens fixture`.")
        return fixture
    if requested == "raw":
        if not raw_firms.exists() or not list(raw_firms.glob("*.csv")):
            raise ApiError(409, "Données FIRMS indisponibles : exécuter `pyrolens download` puis `normalize`.")
        return raw_firms
    if settings.source_dir is not None:
        return settings.source_dir
    if raw_firms.exists() and list(raw_firms.glob("*.csv")):
        return raw_firms
    if fixture.exists() and list(fixture.glob("*.csv")):
        return fixture
    raise ApiError(409, "Aucune source disponible : exécuter `pyrolens download` ou `pyrolens fixture`.")


def data_origin_of(source_dir: Path) -> str:
    resolved = source_dir.resolve()
    try:
        relative = resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        relative = resolved
    parts = relative.parts
    if "fixture" in parts or "fixture" in resolved.name:
        return "synthetic_fixture"
    if "raw" in parts:
        return "nasa_firms"
    return "custom_source"


def _source_digest(paths: list[Path]) -> str:
    """Empreinte déterministe de la source (noms + tailles), sans lire les données."""
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(f"{path.name}:{path.stat().st_size}\n".encode())
    return digest.hexdigest()


def run_harmonization_experiment(
    params: dict[str, Any], cfg: Config, settings: Settings
) -> dict[str, Any]:
    """Calcule une comparaison Terra↔Aqua ou Aqua↔VIIRS sur la source configurée."""
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    t0 = time.monotonic()

    pair = params["pair"]
    grid = float(params["grid_deg"])
    window = int(params["window_days"])
    a_key, b_key = pair.split("__")

    source_dir = resolve_source_dir(cfg, settings, params.get("source", "auto"))
    csv_paths = sorted(source_dir.glob("*.csv"))
    if not csv_paths:
        raise ApiError(409, "Source vide : aucun CSV à analyser.")

    geometry = _load_geometry(cfg)
    rows: list[dict[str, Any]] = []
    for path in csv_paths:
        file_audit = audit_file(
            path,
            bbox=cfg.get("region.bbox"),
            iso3=cfg.get("region.iso3", "CMR"),
            geometry=geometry,
            n_regions=int(cfg.get("analysis.n_regions", 3)),
        )
        rows.extend(file_audit.rows)

    rows_a = select_rows(rows, cfg, a_key)
    rows_b = select_rows(rows, cfg, b_key)
    keys_a = build_set(rows_a, grid, window)
    keys_b = build_set(rows_b, grid, window)
    comparison = compare_sets(pair, keys_a, keys_b, grid, window)

    monthly = _monthly_divergence(keys_a, keys_b, window)
    for row in monthly:
        total = row["a_only"] + row["b_only"] + row["both"]
        row["jaccard"] = round(row["both"] / total, 6) if total else 0.0

    spatial = _spatial(keys_a, keys_b, grid)
    spatial.sort(key=lambda r: -(r["a_count"] + r["b_count"]))
    top_n = settings.max_spatial_top

    elapsed = round(time.monotonic() - t0, 3)
    return {
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elapsed_s": elapsed,
        "params": {
            "pair": pair,
            "grid_deg": grid,
            "window_days": window,
            "key_definition": "(cellule,date)" if window == 1 else "(cellule,fenêtre)",
        },
        "data_origin": data_origin_of(source_dir),
        "source": {
            "n_files": len(csv_paths),
            "n_rows_loaded": len(rows),
            "n_rows_sensor_a": len(rows_a),
            "n_rows_sensor_b": len(rows_b),
            "digest_sha256": _source_digest(csv_paths),
            "note": "Empreinte = sha256 des noms et tailles des fichiers source (liste reproductible).",
        },
        "result": {
            "n_a": comparison.a_size,
            "n_b": comparison.b_size,
            "intersection": comparison.intersection,
            "union": comparison.union,
            "jaccard": round(comparison.jaccard, 6),
            "monthly": monthly,
            "spatial_cells_total": len(spatial),
            "spatial_top": spatial[:top_n],
            "spatial_top_note": f"Top {top_n} cellules par détections ; distribution complète publiée via baselines (configuration primaire).",
        },
        "software": {"pipeline": f"pyrolens {PYROLENS_VERSION}", "api": "pyrolens-api 0.1.0"},
        "warning": (
            "Le Jaccard mesure un recouvrement d'ensembles, pas une précision : "
            "aucune référence indépendante n'est mobilisée (H4/H6 non exécutés)."
        ),
    }
