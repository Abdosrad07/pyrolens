"""Observabilité : classification en 4 états.

États :
  1. no_detection_plausible_conditions : absence de détection alors que la
     couverture d'observation documente une observation plausible ;
  2. unknown_observability             : absence d'observation ou observabilité
     inconnue (état PAR DÉFAUT tant qu'aucun produit de couverture/nuages n'est acquis) ;
  3. detection_observed                : détection observée ;
  4. indeterminate                     : situation indéterminée (couverture
     présente mais état d'observation ambigu).

Aucune absence de détection n'est convertie en "pas de feu".
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .grids import cell_key, cell_id

STATE_DETECTED = "detection_observed"
STATE_NO_DET = "no_detection_plausible_conditions"
STATE_UNKNOWN = "unknown_observability"
STATE_INDETERMINATE = "indeterminate"

STATE_LABELS_FR = {
    STATE_DETECTED: "détection observée",
    STATE_NO_DET: "absence de détection en conditions d'observation plausibles",
    STATE_UNKNOWN: "absence d'observation ou observabilité inconnue",
    STATE_INDETERMINATE: "situation indéterminée",
}


def classify_states(
    rows_by_sensor: dict[str, list[dict[str, Any]]],
    grid_deg: float,
    coverage_available: bool = False,
    coverage: dict[tuple[str, str], str] | None = None,
) -> dict[str, Counter]:
    """Retourne {capteur: Counter(état -> effectif)} pour la grille et la période données."""
    coverage = coverage or {}
    states: dict[str, Counter] = {}

    for sensor, rows in rows_by_sensor.items():
        counter: Counter = Counter()
        by_cell_day: dict[tuple[str, str], int] = defaultdict(int)
        all_cells_days: set[tuple[str, str]] = set()
        for row in rows:
            i, j = cell_id(row["longitude"], row["latitude"], grid_deg)
            ck = cell_key(i, j)
            day = row["acq_date"].isoformat()
            by_cell_day[(ck, day)] += 1
            all_cells_days.add((ck, day))
        # État 3 pour les cellules/jours avec détection
        for key in all_cells_days:
            if by_cell_day[key] > 0:
                counter[STATE_DETECTED] += 1
                continue
        # Pour les cellules observées par un AUTRE capteur le même jour, l'absence
        # de détection de ce capteur est classée selon la disponibilité de la couverture.
        if coverage_available and coverage:
            for key, status in coverage.items():
                if key in all_cells_days:
                    continue
                if status == "clear_observed":
                    counter[STATE_NO_DET] += 1
                elif status == "not_observed":
                    counter[STATE_UNKNOWN] += 1
                else:
                    counter[STATE_INDETERMINATE] += 1
        states[sensor] = counter
    return states


def coverage_absent_states(
    rows_by_sensor: dict[str, list[dict[str, Any]]],
    grid_deg: float,
    observed_cells_days: dict[str, set[tuple[str, str]]] | None = None,
) -> dict[str, Counter]:
    """État réel sans produit de couverture : détection ou observabilité inconnue.

    `observed_cells_days` modélise une couverture d'observation future ; sans lui,
    toute cellule/jour sans détection pour un capteur est "observabilité inconnue".
    """
    observed_cells_days = observed_cells_days or {}
    states: dict[str, Counter] = {}
    universe: set[tuple[str, str]] = set()
    per_sensor: dict[str, set[tuple[str, str]]] = {}

    for sensor, rows in rows_by_sensor.items():
        keys = set()
        for row in rows:
            i, j = cell_id(row["longitude"], row["latitude"], grid_deg)
            keys.add((cell_key(i, j), row["acq_date"].isoformat()))
        per_sensor[sensor] = keys
        universe |= keys

    for sensor, keys in per_sensor.items():
        counter: Counter = Counter()
        observed = observed_cells_days.get(sensor, set())
        for key in universe:
            if key in keys:
                counter[STATE_DETECTED] += 1
            elif key in observed:
                counter[STATE_INDETERMINATE] += 1  # observée mais sans info nuage exploitable
            else:
                counter[STATE_UNKNOWN] += 1
        states[sensor] = counter
    return states


def run_observability(
    rows_by_sensor: dict[str, list[dict[str, Any]]],
    cfg,
    out_dir: Path,
    artifacts_dir: Path,
    data_origin: str,
) -> dict[str, Any]:
    grid = float(cfg.get("analysis.primary_grid_deg", 0.25))
    coverage_acquired = bool(cfg.get("observability.coverage_products_acquired", False))
    states = coverage_absent_states(rows_by_sensor, grid) if not coverage_acquired else classify_states(
        rows_by_sensor, grid, coverage_available=True
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    csv_rows = []
    for sensor, counter in states.items():
        for state, count in counter.items():
            csv_rows.append(
                {
                    "sensor": sensor,
                    "state": state,
                    "label_fr": STATE_LABELS_FR[state],
                    "cell_date_count": count,
                    "coverage_products_acquired": str(coverage_acquired).lower(),
                }
            )
    target = out_dir / "observability_states.csv"
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["sensor", "state", "label_fr", "cell_date_count", "coverage_products_acquired"]
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_origin": data_origin,
        "grid_deg": grid,
        "coverage_products_acquired": coverage_acquired,
        "states": {s: dict(c) for s, c in states.items()},
        "state_labels": STATE_LABELS_FR,
        "note": (
            "Sans produit de couverture/nuages acquis, une cellule/jour sans détection "
            "est classée 'observabilité inconnue' et jamais 'pas de feu'."
        ),
    }
    (artifacts_dir / "observability.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "observability.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return payload
