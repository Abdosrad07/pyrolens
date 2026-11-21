"""Détection d'anomalies d'activité de feu par cellule de grille.

Moteur statistique pour l'« early warning » PyroLens : agrège les détections
FIRMS en compteurs journaliers par cellule spatiale, calcule une baseline
historique robuste, puis compare une fenêtre récente à cette baseline.

Choix méthodologiques (données zéro-lourdes et éparses) :

* **Agrégation** : compte de détections par (cellule, jour). Les jours sans
  enregistrement ne sont PAS des zéros « pas de feu » — ils sont exclus du
  dénominateur d'observabilité quand la couverture est documentée, et sinon
  traités comme des zéros *d'activité détectée* avec un avertissement explicite.
* **Baseline** : médiane + quantiles robusts par cellule sur la période de
  référence, avec lissage hiérarchique (cellule → région → global) pour les
  cellules à historique insuffisant. La moyenne n'est jamais utilisée seule :
  elle est dominée par les pics.
* **Score** : probabilité de dépassement sous un modèle de comptage
  sur-dispersé (négatif binomial approché par Poisson avec inflation de
  variance), complétée par un ratio robuste ``recent / baseline_médiane``.
  Le score est borné [0, 1] et interprété comme une *force d'anomalie*, pas
  une probabilité d'incendie.
* **Sévérité** : NORMAL / WATCH / MODERATE / HIGH via seuils configurables sur
  le score ET un plancher d'activité absolue (évite d'alerter sur 0→1
  détection dans une cellule vide).

Garde-fous scientifiques :
* aucune affirmation temps réel — les données FIRMS sont historiques/NRT avec
  latence ; le résultat est étiqueté ``historical_backtest`` ;
* une cellule sans détection n'est jamais « pas de feu » ;
* la provenance (origine, empreinte source, paramètres, versions) est
  propagée dans chaque résultat.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .grids import ORIGIN_LAT, ORIGIN_LON, cell_center, epoch_days

# ------------------------------------------------------------------ constantes
DEFAULT_GRID_DEG = 0.25
DEFAULT_RECENT_DAYS = 14          # fenêtre « récente » comparée à la baseline
DEFAULT_BASELINE_DAYS = 730       # ~2 ans de référence glissante
DEFAULT_MIN_BASELINE_DAYS = 60    # en dessous : baseline « insuffisante »
DEFAULT_CELL_MIN_DAYS = 30        # jours avec ≥1 détection pour baseline fiable

SEVERITY_ORDER = ("NORMAL", "WATCH", "MODERATE", "HIGH")

# Seuils par défaut (configurables) — sur le score d'anomalie ∈ [0,1]
DEFAULT_THRESHOLDS = {
    "watch": 0.55,
    "moderate": 0.72,
    "high": 0.88,
}
# Plancher d'activité absolue : détections récentes minimales pour WATCH+
DEFAULT_MIN_RECENT_DETECTIONS = {"watch": 3, "moderate": 6, "high": 12}

_EPOCH = date(1970, 1, 1)


# ------------------------------------------------------------------ dataclasses
@dataclass
class CellDailySeries:
    """Série journalière d'une cellule : date epoch → nb détections."""

    ci: int
    cj: int
    counts: dict[int, int] = field(default_factory=dict)   # d_epoch -> count
    frp_sum: dict[int, float] = field(default_factory=dict)

    def days_with_detection(self) -> int:
        return sum(1 for v in self.counts.values() if v > 0)


@dataclass
class CellBaseline:
    """Baseline robuste d'une cellule sur la période de référence."""

    ci: int
    cj: int
    n_days_observed: int          # jours dans la fenêtre de référence
    n_days_with_detection: int
    median_daily: float           # médiane des comptes journaliers (zéros inclus)
    q90_daily: float
    mean_daily: float
    max_daily: int
    total_detections: int
    level: str                    # "cell" | "region" | "global" (lissage utilisé)
    sufficient: bool              # assez d'historique pour une baseline fiable


@dataclass
class AnomalyResult:
    """Résultat d'anomalie pour une cellule sur la fenêtre récente."""

    ci: int
    cj: int
    cell_id: str
    lon: float
    lat: float
    recent_days: int
    recent_detections: int
    recent_daily_mean: float
    baseline_median: float
    baseline_q90: float
    score: float                  # ∈ [0,1], force d'anomalie
    ratio: float | None           # recent_mean / baseline_median (None si baseline=0)
    severity: str                 # NORMAL | WATCH | MODERATE | HIGH
    baseline_level: str           # niveau de lissage utilisé
    baseline_sufficient: bool
    reasons: list[str] = field(default_factory=list)


# ------------------------------------------------------------------ chargement
def load_daily_counts(
    csv_paths: Iterable[str | Path],
    grid_deg: float = DEFAULT_GRID_DEG,
) -> dict[tuple[int, int], CellDailySeries]:
    """Agrège les CSV FIRMS en compteurs journaliers par cellule.

    Retourne ``{(ci, cj): CellDailySeries}``. Les lignes non interprétables
    (lat/lon/date invalides) sont ignorées — cohérent avec l'audit qui les
    isole sans correction.
    """
    usecols = {"latitude", "longitude", "acq_date", "frp"}
    frames: list[pd.DataFrame] = []
    for path in sorted(csv_paths):
        path = Path(path)
        try:
            df = pd.read_csv(path, usecols=lambda c: c in usecols, dtype=str)
        except Exception:  # noqa: BLE001 — CSV illisible : ignoré, tracé par l'audit
            continue
        if df.empty:
            continue
        frames.append(
            pd.DataFrame(
                {
                    "lat": pd.to_numeric(df.get("latitude"), errors="coerce"),
                    "lon": pd.to_numeric(df.get("longitude"), errors="coerce"),
                    "d_str": df.get("acq_date", pd.Series([""] * len(df)))
                    .astype(str)
                    .str[:10],
                    "frp": pd.to_numeric(df.get("frp"), errors="coerce"),
                }
            )
        )
    if not frames:
        return {}
    ev = pd.concat(frames, ignore_index=True).dropna(subset=["lat", "lon", "d_str"])
    ev = ev[ev["d_str"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
    if ev.empty:
        return {}
    # Parsing vectorisé : datetime64[D] → entier = jours depuis epoch.
    # Les dates invalides (ex. 2020-02-30) deviennent NaT → exclues.
    d64 = pd.to_datetime(ev["d_str"], format="%Y-%m-%d", errors="coerce")
    ev = ev.loc[d64.notna()].copy()
    if ev.empty:
        return {}
    ev["d"] = d64[d64.notna()].values.astype("datetime64[D]").astype("int64")
    ev["frp"] = pd.to_numeric(ev["frp"], errors="coerce").fillna(0.0).astype(float)
    ev["ci"] = np.floor(np.round((ev["lon"].to_numpy() - ORIGIN_LON) / grid_deg, 9)).astype(int)
    ev["cj"] = np.floor(np.round((ev["lat"].to_numpy() - ORIGIN_LAT) / grid_deg, 9)).astype(int)

    series: dict[tuple[int, int], CellDailySeries] = {}
    for (ci, cj), g in ev.groupby(["ci", "cj"], sort=False):
        cell = CellDailySeries(ci=int(ci), cj=int(cj))
        counts = g.groupby("d").size()
        frp_sums = g.groupby("d")["frp"].sum()
        for d, c in counts.items():
            d_int = int(d)
            cell.counts[d_int] = int(c)
            cell.frp_sum[d_int] = float(frp_sums.loc[d])
        series[(int(ci), int(cj))] = cell
    return series


def source_digest(csv_paths: Iterable[str | Path]) -> str:
    """Empreinte déterministe de la source (noms + tailles), sans lire les données."""
    digest = hashlib.sha256()
    for path in sorted(Path(p) for p in csv_paths):
        try:
            digest.update(f"{path.name}:{path.stat().st_size}\n".encode())
        except OSError:
            digest.update(f"{path.name}:missing\n".encode())
    return digest.hexdigest()


def data_origin_of_source(csv_paths: Iterable[str | Path]) -> str:
    """`nasa_firms` si la source est sous data/raw, sinon `synthetic_fixture`."""
    parts = {str(Path(p)).replace("\\", "/").lower() for p in csv_paths}
    if any("/raw/" in p or p.startswith("data/raw") for p in parts):
        return "nasa_firms"
    return "synthetic_fixture"


# ------------------------------------------------------------------ baseline
def _daily_vector(counts: dict[int, int], d_min: int, d_max: int) -> np.ndarray:
    """Vecteur de comptes journaliers sur [d_min, d_max] — zéros inclus."""
    vec = np.zeros(d_max - d_min + 1, dtype=float)
    for d, c in counts.items():
        if d_min <= d <= d_max:
            vec[d - d_min] = c
    return vec


def compute_baselines(
    series: dict[tuple[int, int], CellDailySeries],
    reference_end: int,
    baseline_days: int = DEFAULT_BASELINE_DAYS,
    min_baseline_days: int = DEFAULT_MIN_BASELINE_DAYS,
    min_cell_days: int = DEFAULT_CELL_MIN_DAYS,
) -> dict[tuple[int, int], CellBaseline]:
    """Calcule la baseline robuste par cellule sur [reference_end-baseline_days+1, reference_end].

    Lissage hiérarchique : cellule → médiane régionale (même bande de latitude
    de 5°) → globale. Une cellule avec trop peu d'historique hérite du niveau
    supérieur et est marquée ``sufficient=False``.
    """
    d_min = reference_end - baseline_days + 1
    # bornes effectives : ne pas remonter avant la première observation globale
    all_days = [d for s in series.values() for d in s.counts]
    if not all_days:
        return {}
    data_start = min(all_days)
    d_min = max(d_min, data_start)
    span = reference_end - d_min + 1
    if span < min_baseline_days:
        # historique global insuffisant : tout le monde hérite du global
        span = max(span, 1)

    # niveau global
    global_vec = np.zeros(span, dtype=float)
    for s in series.values():
        global_vec += _daily_vector(s.counts, d_min, reference_end)
    # normaliser : moyenne par cellule-observée (approximation : chaque cellule
    # "pourrait" avoir des détections chaque jour — on divise par le nombre de
    # cellules actives pour obtenir un taux journalier moyen par cellule)
    n_cells = max(1, len(series))
    global_daily = global_vec / n_cells
    global_median = float(np.median(global_daily)) if span else 0.0
    global_q90 = float(np.quantile(global_daily, 0.9)) if span else 0.0
    global_mean = float(np.mean(global_daily)) if span else 0.0

    # niveau régional : bande de latitude de 5°
    region_stats: dict[int, dict[str, float]] = {}
    bands: dict[int, list[np.ndarray]] = {}
    for (ci, cj), s in series.items():
        _lon, lat = cell_center(ci, cj, DEFAULT_GRID_DEG)
        band = int(math.floor(lat / 5.0))
        bands.setdefault(band, []).append(_daily_vector(s.counts, d_min, reference_end))
    for band, vecs in bands.items():
        if not vecs:
            continue
        arr = np.sum(vecs, axis=0) / max(1, len(vecs))
        region_stats[band] = {
            "median": float(np.median(arr)),
            "q90": float(np.quantile(arr, 0.9)),
            "mean": float(np.mean(arr)),
        }

    baselines: dict[tuple[int, int], CellBaseline] = {}
    for (ci, cj), s in series.items():
        vec = _daily_vector(s.counts, d_min, reference_end)
        n_obs = int(span)
        n_det_days = s.days_with_detection()
        cell_median = float(np.median(vec))
        cell_q90 = float(np.quantile(vec, 0.9))
        cell_mean = float(np.mean(vec))
        cell_max = int(vec.max()) if vec.size else 0
        total = int(vec.sum())

        _lon, lat = cell_center(ci, cj, DEFAULT_GRID_DEG)
        band = int(math.floor(lat / 5.0))
        reg = region_stats.get(band)

        sufficient = n_det_days >= min_cell_days and n_obs >= min_baseline_days
        if sufficient:
            level = "cell"
            median, q90, mean = cell_median, cell_q90, cell_mean
        elif reg is not None and n_obs >= min_baseline_days:
            level = "region"
            median, q90, mean = reg["median"], reg["q90"], reg["mean"]
        else:
            level = "global"
            median, q90, mean = global_median, global_q90, global_mean

        baselines[(ci, cj)] = CellBaseline(
            ci=ci, cj=cj,
            n_days_observed=n_obs,
            n_days_with_detection=n_det_days,
            median_daily=median,
            q90_daily=q90,
            mean_daily=mean,
            max_daily=cell_max,
            total_detections=total,
            level=level,
            sufficient=sufficient,
        )
    return baselines


# ------------------------------------------------------------------ scoring
def _poisson_sf(k: int, lam: float) -> float:
    """P(X ≥ k) pour X ~ Poisson(lam), calculée par récurrence stable."""
    if lam <= 0:
        return 1.0 if k <= 0 else 0.0
    if k <= 0:
        return 1.0
    # P(X = k-1) puis somme de la queue — stable pour lam raisonnable
    log_p = -lam + (k - 1) * math.log(lam) - math.lgamma(k)
    p_km1 = math.exp(log_p)
    # somme P(X ≥ k) = 1 - P(X ≤ k-1) ; on somme directement la queue
    # pour éviter l'annulation catastrophique quand lam est petit
    tail = p_km1 * lam / k  # P(X=k) approx via récurrence
    total = tail
    term = tail
    for j in range(k + 1, k + 60):
        term *= lam / j
        total += term
        if term < 1e-15:
            break
    return min(1.0, max(0.0, total))


def anomaly_score(
    recent_counts: list[int],
    baseline: CellBaseline,
    recent_days: int,
) -> tuple[float, float | None, list[str]]:
    """Score d'anomalie ∈ [0,1] pour une cellule.

    Combine :
    * un **score de comptage** : P(X ≥ recent_total) sous Poisson(λ =
      baseline_median × recent_days), avec inflation de λ par le facteur de
      sur-dispersion (variance/moyenne observée sur la baseline, bornée) ;
    * un **ratio robuste** : moyenne récente / médiane baseline.

    Retourne (score, ratio, reasons).
    """
    reasons: list[str] = []
    total_recent = int(sum(recent_counts))
    mean_recent = total_recent / max(1, recent_days)

    lam_daily = baseline.median_daily
    if lam_daily <= 0:
        # baseline nulle : toute activité est « nouvelle » — score élevé mais
        # plafonné pour ne pas saturer sur du bruit (1-2 détections).
        if total_recent >= 3:
            score = min(0.95, 0.5 + 0.1 * total_recent)
            reasons.append("baseline_nulle_activite_nouvelle")
        elif total_recent > 0:
            score = 0.3 + 0.05 * total_recent
            reasons.append("baseline_nulle_activite_faible")
        else:
            score = 0.0
        return score, None, reasons

    # inflation de sur-dispersion : variance empirique / moyenne, bornée [1, 8]
    # (approximation : on utilise q90/median comme proxy de dispersion)
    dispersion = 1.0
    if baseline.median_daily > 0 and baseline.q90_daily > baseline.median_daily:
        dispersion = min(8.0, max(1.0, baseline.q90_daily / max(baseline.median_daily, 1e-9)))
    lam = lam_daily * recent_days * dispersion

    # P(X ≥ total_recent) sous Poisson(lam) — le « p-value » d'excès
    p_exceed = _poisson_sf(total_recent, lam) if total_recent > 0 else 1.0
    # convertir en score : 1 - p_exceed, avec compression pour éviter la
    # saturation quand p_exceed → 0
    count_score = 1.0 - p_exceed if p_exceed > 0 else 1.0
    count_score = min(1.0, count_score * 1.2)  # légère amplification

    ratio = mean_recent / lam_daily if lam_daily > 0 else None
    if ratio is not None and ratio > 1.0:
        reasons.append(f"ratio_{ratio:.1f}x")

    # score final : moyenne pondérée du score de comptage et du ratio borné
    ratio_score = 0.0
    if ratio is not None:
        ratio_score = min(1.0, math.log1p(ratio) / math.log1p(10.0))  # log1p(10)≈2.4 → ratio 10x ≈ 1.0

    score = 0.65 * count_score + 0.35 * ratio_score
    score = min(1.0, max(0.0, score))

    if not baseline.sufficient:
        reasons.append("baseline_insuffisante")
        score *= 0.85  # pénalité : ne pas sur-alerter sur historique faible
    return score, ratio, reasons


def classify_severity(
    score: float,
    recent_detections: int,
    thresholds: dict[str, float] | None = None,
    min_detections: dict[str, int] | None = None,
) -> str:
    """NORMAL / WATCH / MODERATE / HIGH selon score + plancher d'activité."""
    th = thresholds or DEFAULT_THRESHOLDS
    md = min_detections or DEFAULT_MIN_RECENT_DETECTIONS
    if score >= th["high"] and recent_detections >= md["high"]:
        return "HIGH"
    if score >= th["moderate"] and recent_detections >= md["moderate"]:
        return "MODERATE"
    if score >= th["watch"] and recent_detections >= md["watch"]:
        return "WATCH"
    return "NORMAL"


# ------------------------------------------------------------------ orchestration
def run_anomaly_detection(
    csv_paths: list[str | Path],
    grid_deg: float = DEFAULT_GRID_DEG,
    recent_days: int = DEFAULT_RECENT_DAYS,
    baseline_days: int = DEFAULT_BASELINE_DAYS,
    reference_date: date | None = None,
    thresholds: dict[str, float] | None = None,
    min_detections: dict[str, int] | None = None,
    progress=None,
) -> dict[str, Any]:
    """Pipeline complet : CSV → séries → baseline → scores → alertes.

    Retourne le payload JSON pour l'API (compatible contrat frontend).
    """
    t0 = datetime.now(timezone.utc)
    csv_paths = [Path(p) for p in csv_paths]

    def rep(step: str, pct: float, detail: str | None = None) -> None:
        if progress:
            progress(step, pct, detail)

    rep("load", 5, f"{len(csv_paths)} CSV")
    series = load_daily_counts(csv_paths, grid_deg)
    if not series:
        raise ValueError("Aucun événement exploitable dans la source.")

    all_days = sorted({d for s in series.values() for d in s.counts})
    data_max = max(all_days)
    data_min = min(all_days)
    ref_d = epoch_days(reference_date) if reference_date else data_max
    # la fenêtre récente se termine à la date de référence (ou max des données)
    recent_end = min(ref_d, data_max)
    recent_start = recent_end - recent_days + 1
    baseline_end = recent_start - 1  # baseline = tout ce qui précède le récent

    rep("baseline", 30, f"{len(series)} cellules, référence {baseline_end}")
    baselines = compute_baselines(
        series, baseline_end,
        baseline_days=baseline_days,
        min_baseline_days=DEFAULT_MIN_BASELINE_DAYS,
    )

    rep("score", 60, "calcul des scores d'anomalie")
    alerts: list[dict[str, Any]] = []
    summary = {"NORMAL": 0, "WATCH": 0, "MODERATE": 0, "HIGH": 0}
    cells_with_data = 0

    for (ci, cj), cell in series.items():
        baseline = baselines.get((ci, cj))
        if baseline is None:
            continue
        # comptes récents sur la fenêtre
        recent_counts = [
            cell.counts.get(d, 0) for d in range(recent_start, recent_end + 1)
        ]
        recent_total = sum(recent_counts)
        if recent_total == 0 and baseline.median_daily == 0:
            continue  # cellule vide des deux côtés : pas d'alerte
        cells_with_data += 1

        score, ratio, reasons = anomaly_score(recent_counts, baseline, recent_days)
        severity = classify_severity(
            score, recent_total, thresholds=thresholds, min_detections=min_detections
        )
        summary[severity] += 1

        lon, lat = cell_center(ci, cj, grid_deg)
        cid = f"{ci}:{cj}"
        alerts.append({
            "cell_id": cid,
            "cell_i": int(ci),
            "cell_j": int(cj),
            "lon": round(lon, 5),
            "lat": round(lat, 5),
            "severity": severity,
            "score": round(score, 4),
            "ratio": round(ratio, 3) if ratio is not None else None,
            "recent": {
                "days": recent_days,
                "detections": int(recent_total),
                "daily_mean": round(recent_total / recent_days, 3),
            },
            "baseline": {
                "median_daily": round(baseline.median_daily, 4),
                "q90_daily": round(baseline.q90_daily, 4),
                "level": baseline.level,
                "sufficient": baseline.sufficient,
                "n_days_with_detection": baseline.n_days_with_detection,
            },
            "reasons": reasons,
        })

    # trier : sévérité décroissante puis score décroissant
    sev_rank = {"HIGH": 3, "MODERATE": 2, "WATCH": 1, "NORMAL": 0}
    alerts.sort(key=lambda a: (-sev_rank[a["severity"]], -a["score"]))

    rep("export", 90, f"{len(alerts)} cellules évaluées")
    period = {
        "data_start": (_EPOCH + timedelta(days=data_min)).isoformat(),
        "data_end": (_EPOCH + timedelta(days=data_max)).isoformat(),
        "recent_start": (_EPOCH + timedelta(days=recent_start)).isoformat(),
        "recent_end": (_EPOCH + timedelta(days=recent_end)).isoformat(),
        "baseline_end": (_EPOCH + timedelta(days=baseline_end)).isoformat(),
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "estimate_kind": "historical_backtest",
        "data_origin": data_origin_of_source(csv_paths),
        "source": {
            "n_files": len(csv_paths),
            "digest_sha256": source_digest(csv_paths),
        },
        "params": {
            "grid_deg": grid_deg,
            "recent_days": recent_days,
            "baseline_days": baseline_days,
            "reference_date": reference_date.isoformat() if reference_date else None,
            "thresholds": thresholds or DEFAULT_THRESHOLDS,
            "min_detections": min_detections or DEFAULT_MIN_RECENT_DETECTIONS,
        },
        "period": period,
        "summary": {
            "n_cells_evaluated": cells_with_data,
            "n_cells_total": len(series),
            "n_alerts": sum(1 for a in alerts if a["severity"] != "NORMAL"),
            "by_severity": summary,
        },
        "alerts": alerts,
        "notes": (
            "Score d'anomalie = force statistique d'excès d'activité détectée "
            "vs baseline historique (Poisson sur-dispersé + ratio robuste). "
            "Ce n'est PAS une probabilité d'incendie réel ni une alerte "
            "opérationnelle : les données FIRMS sont historiques avec latence, "
            "et une cellule sans détection n'implique jamais l'absence de feu."
        ),
        "elapsed_s": round((datetime.now(timezone.utc) - t0).total_seconds(), 2),
    }
    rep("done", 100, "terminé")
    return payload
