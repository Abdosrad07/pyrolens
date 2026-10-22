"""Figures du pipeline (matplotlib, backend non interactif)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_jaccard_heatmap(baselines: dict[str, Any], out_dir: Path) -> Path | None:
    summary = baselines.get("summary", [])
    if not summary:
        return None
    pairs = sorted({row["pair"] for row in summary})
    grids = sorted({float(row["grid_deg"]) for row in summary})
    windows = sorted({int(row["window_days"]) for row in summary})

    fig, axes = plt.subplots(1, len(pairs), figsize=(5.2 * len(pairs), 4.2), squeeze=False)
    for ax, pair in zip(axes[0], pairs):
        matrix = []
        for g in grids:
            row = []
            for w in windows:
                match = next(
                    (r for r in summary if r["pair"] == pair and float(r["grid_deg"]) == g
                     and int(r["window_days"]) == w),
                    None,
                )
                row.append(match["jaccard"] if match else 0.0)
            matrix.append(row)
        im = ax.imshow(matrix, cmap="viridis", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(windows)), [f"{w} j" for w in windows])
        ax.set_yticks(range(len(grids)), [f"{g:.2f}°" for g in grids])
        ax.set_xlabel("fenêtre temporelle")
        ax.set_ylabel("grille")
        ax.set_title(pair.replace("__", " vs "))
        for i in range(len(grids)):
            for j in range(len(windows)):
                ax.text(j, i, f"{matrix[i][j]:.2f}", ha="center", va="center",
                        color="white" if matrix[i][j] < 0.5 else "black", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, label="Jaccard")
    fig.suptitle("Sensibilité du Jaccard (grille × fenêtre) — NE PAS retenir le maximum", y=1.02)
    return _save(fig, out_dir / "jaccard_sensitivity.png")


def figure_jaccard_monthly(baselines: dict[str, Any], out_dir: Path) -> Path | None:
    series = baselines.get("jaccard_monthly", [])
    primary = baselines.get("primary", {})
    if not series:
        return None
    subset = [
        r for r in series
        if float(r["grid_deg"]) == float(primary.get("grid_deg", 0.25))
        and int(r["window_days"]) == int(primary.get("window_days", 8))
    ]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    pairs = sorted({r["pair"] for r in subset})
    for pair in pairs:
        rows = sorted([r for r in subset if r["pair"] == pair], key=lambda r: r["month"])
        ax.plot([r["month"] for r in rows], [r["jaccard"] for r in rows],
                marker="o", markersize=3, label=pair.replace("__", " vs "))
    ax.set_ylim(0, 1)
    ax.set_ylabel("Jaccard mensuel")
    ax.set_xlabel("mois")
    ax.set_title(f"Évolution temporelle du Jaccard (grille {primary.get('grid_deg')}°, "
                 f"fenêtre {primary.get('window_days')} j)")
    ax.grid(alpha=0.3)
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=60, ha="right", fontsize=8)
    return _save(fig, out_dir / "jaccard_monthly.png")


def figure_volumes(audit_summary: dict[str, Any], out_dir: Path) -> Path | None:
    volumes = audit_summary.get("volumes_by_month", {})
    if not volumes:
        return None
    per_sensor: dict[str, list[tuple[str, int]]] = {}
    for key, count in volumes.items():
        sensor, month = key.split("|", 1)
        per_sensor.setdefault(sensor, []).append((month, count))
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for sensor, series in sorted(per_sensor.items()):
        series = sorted(series)
        ax.plot([m for m, _ in series], [c for _, c in series], marker=".", label=sensor)
    ax.set_ylabel("détections enregistrées / mois")
    ax.set_xlabel("mois")
    ax.set_title("Volumes par capteur et par mois")
    ax.grid(alpha=0.3)
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=60, ha="right", fontsize=8)
    return _save(fig, out_dir / "volumes_by_month.png")


def figure_spatial(baselines: dict[str, Any], out_dir: Path) -> Path | None:
    spatial = [
        r for r in baselines.get("spatial_rows", [])
        if float(r["grid_deg"]) == float(baselines.get("primary", {}).get("grid_deg", 0.25))
        and int(r["window_days"]) == int(baselines.get("primary", {}).get("window_days", 1))
    ]
    if not spatial:
        # fallback : lire depuis la liste brute si présente
        spatial = baselines.get("spatial", [])
    if not spatial:
        return None
    pairs = sorted({r["pair"] for r in spatial})
    fig, axes = plt.subplots(1, len(pairs), figsize=(6 * len(pairs), 5), squeeze=False)
    for ax, pair in zip(axes[0], pairs):
        rows = [r for r in spatial if r["pair"] == pair]
        rows_a = [r for r in rows if r["a_count"] > 0]
        rows_b = [r for r in rows if r["b_count"] > 0]
        ax.scatter([r["lon"] for r in rows_a], [r["lat"] for r in rows_a],
                   s=[max(6, r["a_count"] * 4) for r in rows_a], alpha=0.55,
                   label="capteur A", color="#e4572e")
        ax.scatter([r["lon"] for r in rows_b], [r["lat"] for r in rows_b],
                   s=[max(6, r["b_count"] * 4) for r in rows_b], alpha=0.45,
                   label="capteur B", color="#2e86ab")
        ax.set_title(pair.replace("__", " vs "))
        ax.set_xlabel("longitude")
        ax.set_ylabel("latitude")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Distribution spatiale des cellules actives (grille primaire)", y=1.02)
    return _save(fig, out_dir / "spatial_distribution.png")


def figure_observability(observability: dict[str, Any], out_dir: Path) -> Path | None:
    states = observability.get("states", {})
    if not states:
        return None
    labels = observability.get("state_labels", {})
    all_state_keys: list[str] = []
    for counter in states.values():
        for key in counter:
            if key not in all_state_keys:
                all_state_keys.append(key)
    sensors = sorted(states)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    width = 0.8 / max(1, len(all_state_keys))
    import numpy as np

    x = np.arange(len(sensors))
    for idx, state in enumerate(all_state_keys):
        values = [states[s].get(state, 0) for s in sensors]
        ax.bar(x + idx * width, values, width, label=labels.get(state, state))
    ax.set_xticks(x + width * (len(all_state_keys) - 1) / 2, sensors)
    ax.set_ylabel("cellule × jour")
    ax.set_title("États d'observabilité (aucun état = « pas de feu »)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2, axis="y")
    return _save(fig, out_dir / "observability_states.png")


def figure_anomalies(audit_summary: dict[str, Any], out_dir: Path) -> Path | None:
    cats = audit_summary.get("anomalies_by_category", {})
    if not cats:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.5))
    names = list(cats)
    values = [cats[n] for n in names]
    ax.barh(names, values, color="#f4a259")
    ax.set_xlabel("occurrences")
    ax.set_title("Anomalies détectées par catégorie")
    ax.grid(alpha=0.2, axis="x")
    return _save(fig, out_dir / "anomalies_by_category.png")


def generate_all(audit_summary: dict[str, Any], baselines: dict[str, Any],
                 observability: dict[str, Any], figures_dir: Path,
                 artifacts_dir: Path) -> list[Path]:
    written: list[Path] = []
    for fn, args in (
        (figure_anomalies, (audit_summary,)),
        (figure_volumes, (audit_summary,)),
        (figure_jaccard_heatmap, (baselines,)),
        (figure_jaccard_monthly, (baselines,)),
        (figure_spatial, (baselines,)),
        (figure_observability, (observability,)),
    ):
        try:
            result = fn(*args, figures_dir)
        except Exception as exc:  # noqa: BLE001 - une figure échouée ne casse pas le pipeline
            print(f"[figures] {fn.__name__} en échec : {exc}")
            continue
        if result is not None:
            written.append(result)

    # copie vers les artefacts du frontend
    web_figs = artifacts_dir / "figures"
    web_figs.mkdir(parents=True, exist_ok=True)
    for path in written:
        shutil.copy2(path, web_figs / path.name)
    return written
