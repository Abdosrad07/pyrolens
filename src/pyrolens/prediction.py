"""Prédiction du risque d'activité de feu **détectée** (module batch).

Étude : ``docs/FIRE_RISK_PREDICTION_FEASIBILITY.md`` — GO WITH LIMITATIONS.

Problème : pour une cellule de la grille PyroLens et une date de référence t,
estimer P(≥1 détection FIRMS dans la cellule sur [t+1, t+horizon]).

Garde-fous scientifiques (non négociables) :
* le label est une **détection ultérieure**, jamais un incendie réel — une
  absence de détection ne prouve pas l'absence de feu ;
* toutes les features n'utilisent que des observations ≤ t (fenêtres
  trailing) ;
* séparation chronologique train/val/test avec purge temporelle — le jeu
  de test ne sert ni à l'entraînement, ni à la calibration, ni au seuil ;
* les classes de confiance natives des capteurs ne sont jamais comparées
  entre elles : features séparées par capteur ;
* les probabilités sont calibrées (isotonic/sigmoid sur la validation).

Le module ne modifie rien au moteur d'harmonisation : il consomme les mêmes
CSV FIRMS et réutilise ``grids.cell_id`` pour rester cohérent avec les clés
de cellules des baselines.
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from . import __version__
from .grids import ORIGIN_LAT, ORIGIN_LON, cell_center, epoch_days, parse_date

logger = logging.getLogger("pyrolens.prediction")

# ------------------------------------------------------------------ constantes
SENSOR_KEYS = ("terra", "aqua", "viirs_snpp")
FEATURE_WINDOWS = (8, 16, 32)
FRP_WINDOW = 16
CONF_WINDOW = 16
DAYS_ACTIVE_WINDOW = 32
DEFAULT_GRID_DEG = 0.25
DEFAULT_HORIZON_DAYS = 8
DEFAULT_STRIDE_DAYS = 7
DEFAULT_PURGE_DAYS = 16
SPLIT_YEARS = {"train": (2013, 2016), "validation": (2017, 2018), "test": (2019, 2020)}
VIIRS_CONF_CLASSES = ("low", "nominal", "high")
LEVEL_HIGH_FRAC = 1.0
LEVEL_MODERATE_FRAC = 0.5
MODEL_DIRNAME = "models"

_EPOCH = date(1970, 1, 1)


# ------------------------------------------------------------------ chargement
def _sensor_of(filename: str, satellite: str) -> str:
    """Capteur d'une détection : colonne `satellite` d'abord, nom de fichier ensuite."""
    sat = (satellite or "").lower()
    name = filename.lower()
    if "terra" in sat or name.startswith("terra_"):
        return "terra"
    if "aqua" in sat or name.startswith("aqua_"):
        return "aqua"
    if "npp" in sat or "snpp" in sat or "noaa" in sat or "viirs" in name:
        return "viirs_snpp"
    return "unknown"


def _conf_class(confidence: Any, sensor: str) -> str:
    """Classe de confiance **native** du capteur — jamais fusionnée entre capteurs."""
    c = str(confidence or "").strip().lower()
    if sensor == "viirs_snpp":
        return c if c in VIIRS_CONF_CLASSES else "unknown"
    return "modis_numeric"


def load_events(csv_paths: Iterable[str | Path], grid_deg: float = DEFAULT_GRID_DEG) -> pd.DataFrame:
    """Charge les CSV FIRMS en un tableau d'événements normalisé.

    Colonnes produites : ``ci, cj, d, sensor, frp, conf_class, conf_num,
    is_day``. ``d`` = jour epoch. Les lignes non interprétables sont ignorées
    (cohérent avec l'audit : jamais de conversion silencieuse).
    """
    usecols = {
        "latitude", "longitude", "acq_date", "satellite", "confidence",
        "frp", "daynight",
    }
    frames: list[pd.DataFrame] = []
    for path in sorted(csv_paths):
        path = Path(path)
        try:
            df = pd.read_csv(path, usecols=lambda c: c in usecols, dtype=str)
        except Exception as exc:  # noqa: BLE001 — un CSV illisible n'arrête pas le lot
            logger.warning("CSV illisible ignoré : %s (%s)", path.name, exc)
            continue
        if df.empty:
            continue
        sats = df.get("satellite", pd.Series([""] * len(df))).fillna("")
        sensors = [_sensor_of(path.name, s) for s in sats]
        frames.append(
            pd.DataFrame(
                {
                    "lat": pd.to_numeric(df.get("latitude"), errors="coerce"),
                    "lon": pd.to_numeric(df.get("longitude"), errors="coerce"),
                    "d_str": df.get("acq_date", pd.Series([""] * len(df)))
                    .astype(str)
                    .str[:10],
                    "sensor": sensors,
                    "frp": pd.to_numeric(df.get("frp"), errors="coerce"),
                    "conf": df.get("confidence", pd.Series([""] * len(df)))
                    .fillna("")
                    .astype(str),
                    "dn": df.get("daynight", pd.Series([""] * len(df)))
                    .fillna("")
                    .astype(str)
                    .str.upper(),
                }
            )
        )
    cols = ["ci", "cj", "d", "sensor", "frp", "conf_class", "conf_num", "is_day"]
    if not frames:
        return pd.DataFrame(columns=cols)
    ev = pd.concat(frames, ignore_index=True).dropna(subset=["lat", "lon", "d_str"])
    valid_date = ev["d_str"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
    ev = ev[valid_date]
    ev["d"] = ev["d_str"].map(lambda s: epoch_days(parse_date(s)))
    # FRP manquant → 0 pour les sommes, mais la détection compte toujours
    # (ne jamais confondre « pas de FRP » et « pas de détection »).
    ev["frp"] = pd.to_numeric(ev["frp"], errors="coerce").fillna(0.0).astype(float)
    # cell_id vectorisé via la même convention que grids.py (origine -180/-90)
    ev["ci"] = np.floor(np.round((ev["lon"].to_numpy() - ORIGIN_LON) / grid_deg, 9)).astype(int)
    ev["cj"] = np.floor(np.round((ev["lat"].to_numpy() - ORIGIN_LAT) / grid_deg, 9)).astype(int)
    ev["is_day"] = (ev["dn"] == "D").astype(np.int8)
    ev["conf_class"] = [
        _conf_class(c, s) for c, s in zip(ev["conf"], ev["sensor"], strict=False)
    ]
    ev["conf_num"] = pd.to_numeric(ev["conf"], errors="coerce")
    return ev[cols].reset_index(drop=True)


# ------------------------------------------------------------------ index cellule
def _sorted(arr: np.ndarray) -> np.ndarray:
    return np.sort(arr) if arr.size else arr


def _count_in(sorted_dates: np.ndarray, t: int, w: int) -> int:
    """Événements dans [t-w+1, t] — fenêtre trailing incluant le jour t."""
    if sorted_dates.size == 0:
        return 0
    lo = np.searchsorted(sorted_dates, t - w + 1, side="left")
    hi = np.searchsorted(sorted_dates, t + 1, side="left")
    return int(hi - lo)


def _sum_in(dates: np.ndarray, cumsum: np.ndarray, t: int, w: int) -> tuple[float, int]:
    """Somme et effectif dans [t-w+1, t]."""
    if dates.size == 0:
        return 0.0, 0
    lo = np.searchsorted(dates, t - w + 1, side="left")
    hi = np.searchsorted(dates, t + 1, side="left")
    if hi <= lo:
        return 0.0, 0
    total = float(cumsum[hi - 1] - (cumsum[lo - 1] if lo > 0 else 0.0))
    return total, int(hi - lo)


def _max_in(dates: np.ndarray, vals: np.ndarray, t: int, w: int) -> float:
    if dates.size == 0:
        return 0.0
    lo = np.searchsorted(dates, t - w + 1, side="left")
    hi = np.searchsorted(dates, t + 1, side="left")
    if hi <= lo:
        return 0.0
    return float(np.max(vals[lo:hi]))


def _mean_in(dates: np.ndarray, vals: np.ndarray, t: int, w: int) -> float:
    if dates.size == 0:
        return np.nan
    lo = np.searchsorted(dates, t - w + 1, side="left")
    hi = np.searchsorted(dates, t + 1, side="left")
    if hi <= lo:
        return np.nan
    return float(np.mean(vals[lo:hi]))


def _label(sorted_dates: np.ndarray, t: int, horizon: int) -> int:
    """≥1 détection dans ]t, t+horizon] → jours t+1 … t+horizon."""
    if sorted_dates.size == 0:
        return 0
    lo = np.searchsorted(sorted_dates, t + 1, side="left")
    hi = np.searchsorted(sorted_dates, t + horizon + 1, side="left")
    return int(hi > lo)


@dataclass
class CellIndex:
    """Index trié par date d'une cellule — base des features trailing."""

    ci: int
    cj: int
    union_dates: np.ndarray                 # dates de détection (trié)
    union_event_dates: np.ndarray           # dates des événements (trié)
    union_frp_vals: np.ndarray              # FRP aligné sur union_event_dates
    union_frp_cum: np.ndarray               # cumul FRP
    day_dates: np.ndarray                   # dates avec ≥1 détection de jour
    night_dates: np.ndarray
    sensor_dates: dict[str, np.ndarray] = field(default_factory=dict)
    sensor_frp: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = field(
        default_factory=dict
    )  # sensor -> (dates, frp_vals, frp_cum)
    viirs_conf_dates: dict[str, np.ndarray] = field(default_factory=dict)
    modis_conf_dates: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))
    modis_conf_vals: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))


def build_cell_index(events: pd.DataFrame, grid_deg: float) -> dict[tuple[int, int], CellIndex]:
    """Construit l'index par cellule à partir du tableau d'événements."""
    index: dict[tuple[int, int], CellIndex] = {}
    if events.empty:
        return index
    # Pré-tri global pour des groupby rapides
    ev = events.sort_values(["ci", "cj", "d"]).reset_index(drop=True)
    for (ci, cj), g in ev.groupby(["ci", "cj"], sort=False):
        d = g["d"].to_numpy(dtype=np.int64)
        frp = g["frp"].to_numpy(dtype=float)
        order = np.argsort(d, kind="stable")
        d, frp = d[order], frp[order]
        sensor = g["sensor"].to_numpy()[order]
        is_day = g["is_day"].to_numpy()[order]
        conf_class = g["conf_class"].to_numpy()[order]
        conf_num = g["conf_num"].to_numpy(dtype=float)[order]

        cell = CellIndex(ci=int(ci), cj=int(cj), union_dates=np.array([], dtype=int),
                         union_event_dates=d, union_frp_vals=frp,
                         union_frp_cum=np.cumsum(frp),
                         day_dates=np.array([], dtype=int),
                         night_dates=np.array([], dtype=int))
        cell.union_dates = _sorted(np.unique(d))
        day_mask = is_day == 1
        cell.day_dates = _sorted(np.unique(d[day_mask]))
        cell.night_dates = _sorted(np.unique(d[~day_mask]))

        for s in SENSOR_KEYS:
            m = sensor == s
            if not m.any():
                cell.sensor_dates[s] = np.array([], dtype=int)
                cell.sensor_frp[s] = (np.array([], dtype=int), np.array([], dtype=float),
                                      np.array([], dtype=float))
                continue
            sub = g.loc[m, ["d", "frp"]].sort_values("d", kind="stable")
            ds = sub["d"].to_numpy(dtype=np.int64)
            fs = sub["frp"].to_numpy(dtype=float)
            cell.sensor_dates[s] = ds
            cell.sensor_frp[s] = (ds, fs, np.cumsum(fs))

        # confiance VIIRS par classe native
        for cls in VIIRS_CONF_CLASSES:
            m = (sensor == "viirs_snpp") & (conf_class == cls)
            cell.viirs_conf_dates[cls] = _sorted(d[m]) if m.any() else np.array([], dtype=int)
        # confiance MODIS numérique (terra + aqua, même échelle native)
        m = np.isin(sensor, ["terra", "aqua"]) & ~np.isnan(conf_num)
        if m.any():
            sub = pd.DataFrame({"d": d[m], "c": conf_num[m]}).sort_values("d")
            cell.modis_conf_dates = sub["d"].to_numpy(dtype=np.int64)
            cell.modis_conf_vals = sub["c"].to_numpy(dtype=float)
        index[(int(ci), int(cj))] = cell
    return index


# ------------------------------------------------------------------ features
FEATURE_NAMES = (
    [f"n_{s}_{w}" for s in SENSOR_KEYS for w in FEATURE_WINDOWS]
    + [f"n_all_{w}" for w in FEATURE_WINDOWS]
    + ["frp_mean_16", "frp_max_16", "days_active_32", "day_frac_32"]
    + [f"viirs_conf_{c}_16" for c in VIIRS_CONF_CLASSES]
    + ["modis_conf_mean_16", "month_sin", "month_cos", "lat", "lon"]
)


def _features_at(cell: CellIndex, t: int, grid_deg: float) -> list[float]:
    """Vecteur de features à la date t — 100 % trailing (≤ t)."""
    feats: list[float] = []
    # comptes par capteur et fenêtre
    for s in SENSOR_KEYS:
        ds = cell.sensor_dates.get(s, np.array([], dtype=int))
        for w in FEATURE_WINDOWS:
            feats.append(float(_count_in(ds, t, w)))
    # union tous capteurs
    for w in FEATURE_WINDOWS:
        feats.append(float(_count_in(cell.union_dates, t, w)))
    # FRP union sur 16 j
    total, n = _sum_in(cell.union_event_dates, cell.union_frp_cum, t, FRP_WINDOW)
    feats.append(total / n if n else 0.0)                      # frp_mean_16
    feats.append(_max_in(cell.union_event_dates, cell.union_frp_vals, t, FRP_WINDOW))  # frp_max_16
    # jours actifs sur 32 j
    feats.append(float(_count_in(cell.union_dates, t, DAYS_ACTIVE_WINDOW)))  # days_active_32
    # fraction jour/nuit sur 32 j
    nd = _count_in(cell.day_dates, t, DAYS_ACTIVE_WINDOW)
    nn = _count_in(cell.night_dates, t, DAYS_ACTIVE_WINDOW)
    feats.append(nd / (nd + nn) if (nd + nn) else 0.5)         # day_frac_32
    # confiance VIIRS par classe native sur 16 j
    for cls in VIIRS_CONF_CLASSES:
        feats.append(float(_count_in(cell.viirs_conf_dates.get(cls, np.array([], dtype=int)), t, CONF_WINDOW)))
    # confiance MODIS moyenne sur 16 j (échelle native, non convertie)
    feats.append(_mean_in(cell.modis_conf_dates, cell.modis_conf_vals, t, CONF_WINDOW) or 0.0)
    # saisonnalité + position
    d = _EPOCH + timedelta(days=int(t))
    ang = 2 * math.pi * (d.timetuple().tm_yday - 1) / 365.25
    feats.extend([math.sin(ang), math.cos(ang)])
    lon, lat = cell_center(cell.ci, cell.cj, grid_deg)
    feats.extend([lat, lon])
    return feats


def build_dataset(
    index: dict[tuple[int, int], CellIndex],
    grid_deg: float,
    horizon: int,
    stride: int,
    min_date: int | None = None,
    max_date: int | None = None,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Échantillons (features, label) pour toutes les cellules actives.

    Fenêtre de dates : [min_date + max_feature_window, max_date - horizon],
    pas = ``stride`` jours. Retourne (X DataFrame, y Series aligné).
    """
    max_feat = max(FEATURE_WINDOWS)
    rows_x: list[list[float]] = []
    rows_y: list[int] = []
    rows_meta: list[tuple[int, int, int]] = []
    dates = sorted({d for cell in index.values() for d in cell.union_dates})
    if not dates:
        return pd.DataFrame(columns=FEATURE_NAMES), pd.Series(dtype=int)
    lo = min_date if min_date is not None else dates[0] + max_feat
    hi = max_date if max_date is not None else dates[-1] - horizon
    t = lo
    while t <= hi:
        for (ci, cj), cell in index.items():
            # ne produire un échantillon que si la cellule a une chance d'être
            # positive ou une activité récente — toutes les cellules actives
            # sont conservées (le négatif est une information, pas du bruit)
            rows_x.append(_features_at(cell, t, grid_deg))
            rows_y.append(_label(cell.union_dates, t, horizon))
            rows_meta.append((ci, cj, t))
        t += stride
    X = pd.DataFrame(rows_x, columns=FEATURE_NAMES)
    meta = pd.DataFrame(rows_meta, columns=["ci", "cj", "d"])
    meta["year"] = [(_EPOCH + timedelta(days=int(d))).year for d in meta["d"]]
    return X, pd.Series(rows_y, name="y"), meta


# ------------------------------------------------------------------ découpages
def split_mask(meta: pd.DataFrame, purge_days: int = DEFAULT_PURGE_DAYS) -> dict[str, np.ndarray]:
    """Masques chronologiques train/validation/test avec purge autour des frontières.

    Les dates sont des jours epoch. Frontières : 2017-01-01 et 2019-01-01.
    Un échantillon à moins de ``purge_days`` d'une frontière est exclu des
    deux côtés — garantit qu'aucun label train ne chevauche une feature val.
    """
    b1 = epoch_days(date(2017, 1, 1))
    b2 = epoch_days(date(2019, 1, 1))
    d = meta["d"].to_numpy()
    y = meta["year"].to_numpy()
    train = (y <= SPLIT_YEARS["train"][1]) & (d < b1 - purge_days)
    val = ((y == SPLIT_YEARS["validation"][0]) | (y == SPLIT_YEARS["validation"][1])) & (
        d > b1 + purge_days
    ) & (d < b2 - purge_days)
    test = (y >= SPLIT_YEARS["test"][0]) & (d > b2 + purge_days)
    return {"train": train, "validation": val, "test": test}


# ------------------------------------------------------------------ modèles
def fit_frequency_baseline(y_train: np.ndarray, meta_train: pd.DataFrame,
                           meta_pred: pd.DataFrame) -> np.ndarray:
    """Baseline : taux historique lissé par (cellule, mois) avec repli cellule.

    Lissage bêta à deux niveaux (comptages pseudo-observations) — stable même
    quand une cellule n'a presque jamais de détection.
    """
    global_rate = float(np.mean(y_train)) if len(y_train) else 0.0
    df = meta_train.assign(y=y_train)
    df["month"] = [(_EPOCH + timedelta(days=int(d))).month for d in df["d"]]
    # niveau 1 : taux global ; niveau 2 : taux cellule lissé vers global ;
    # niveau 3 : taux (cellule, mois) lissé vers taux cellule
    ALPHA_CELL, ALPHA_MONTH = 30.0, 15.0
    cell_stats = df.groupby(["ci", "cj"])["y"].agg(["sum", "count"])
    cell_rate = {
        k: (r["sum"] + ALPHA_CELL * global_rate) / (r["count"] + ALPHA_CELL)
        for k, r in cell_stats.iterrows()
    }
    cm_stats = df.groupby(["ci", "cj", "month"])["y"].agg(["sum", "count"])
    cm_rate = {
        k: (r["sum"] + ALPHA_MONTH * cell_rate.get(k[:2], global_rate))
        / (r["count"] + ALPHA_MONTH)
        for k, r in cm_stats.iterrows()
    }
    out = np.empty(len(meta_pred), dtype=float)
    months = [(_EPOCH + timedelta(days=int(d))).month for d in meta_pred["d"]]
    for i, ((ci, cj), m) in enumerate(zip(meta_pred[["ci", "cj"]].itertuples(index=False), months, strict=False)):
        out[i] = cm_rate.get((ci, cj, m), cell_rate.get((ci, cj), global_rate))
    return out


def fit_models(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
    meta_train: pd.DataFrame,
    meta_val: pd.DataFrame,
):
    """Entraîne baseline + RF, calibre sur la validation, choisit le seuil F1.

    Retourne un dict avec les deux pipelines et les métriques de validation.
    Le jeu de test n'intervient jamais ici.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.isotonic import IsotonicRegression

    result: dict[str, Any] = {}

    # --- baseline fréquence
    result["baseline_val_pred"] = fit_frequency_baseline(y_train, meta_train, meta_val)

    # --- Random Forest
    rf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=5,
    )
    rf.fit(X_train, y_train)
    p_val_rf = rf.predict_proba(X_val)[:, 1]

    # calibration : isotonic si volume suffisant, sinon sigmoid (Platt)
    if len(np.unique(y_val)) < 2 or len(y_val) < 500:
        method = "sigmoid"
    else:
        method = "isotonic"
    if method == "isotonic":
        cal = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        cal.fit(p_val_rf, y_val)
        p_val_rf_cal = cal.predict(p_val_rf)
    else:
        # Platt scaling simple via régression logistique sur le logit
        from sklearn.linear_model import LogisticRegression
        eps = 1e-6
        logit = np.log(np.clip(p_val_rf, eps, 1 - eps) / (1 - np.clip(p_val_rf, eps, 1 - eps)))
        lr = LogisticRegression()
        lr.fit(logit.reshape(-1, 1), y_val)
        p_val_rf_cal = lr.predict_proba(logit.reshape(-1, 1))[:, 1]
    result["rf"] = rf
    result["calibrator"] = cal if method == "isotonic" else lr
    result["calibration_method"] = method
    result["rf_val_pred"] = p_val_rf_cal

    # seuil F1 sur la validation (jamais sur le test)
    result["threshold"] = _best_f1_threshold(y_val, p_val_rf_cal)
    return result


def _best_f1_threshold(y: np.ndarray, p: np.ndarray) -> float:
    from sklearn.metrics import f1_score

    best_t, best_f = 0.5, -1.0
    for t in np.linspace(0.05, 0.95, 91):
        f = f1_score(y, (p >= t).astype(int), zero_division=0)
        if f > best_f:
            best_f, best_t = f, float(t)
    return best_t


def _metrics(y: np.ndarray, p: np.ndarray, threshold: float) -> dict[str, Any]:
    from sklearn.metrics import (
        average_precision_score,
        brier_score_loss,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    pred = (p >= threshold).astype(int)
    out = {
        "pr_auc": float(average_precision_score(y, p)) if len(np.unique(y)) > 1 else None,
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) > 1 else None,
        "recall": float(recall_score(y, pred, zero_division=0)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "brier": float(brier_score_loss(y, p)),
        "threshold": float(threshold),
        "n": int(len(y)),
        "n_positive": int(y.sum()),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
    }
    return out


def calibration_bins(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> list[dict[str, float]]:
    """Table de calibration (fréquence observée vs probabilité moyenne)."""
    bins = np.linspace(0, 1, n_bins + 1)
    out = []
    for i in range(n_bins):
        m = (p >= bins[i]) & (p < bins[i + 1] if i < n_bins - 1 else p <= bins[i + 1])
        if m.sum() == 0:
            continue
        out.append({
            "bin": f"{bins[i]:.1f}-{bins[i+1]:.1f}",
            "mean_pred": float(p[m].mean()),
            "observed": float(y[m].mean()),
            "n": int(m.sum()),
        })
    return out


# ------------------------------------------------------------------ artefact
def _level(prob: float, threshold: float) -> str:
    if prob >= threshold * LEVEL_HIGH_FRAC:
        return "high"
    if prob >= threshold * LEVEL_MODERATE_FRAC:
        return "moderate"
    return "low"


def export_artifact(
    out_path: Path,
    index: dict[tuple[int, int], CellIndex],
    grid_deg: float,
    horizon: int,
    reference_date: date,
    data_origin: str,
    model_name: str,
    predict_fn,
    metrics: dict[str, Any],
    period: dict[str, str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Écrit fire_risk.json selon le contrat frontend (docs/FIRE_RISK_PREDICTION_SPLIT.md)."""
    t_ref = epoch_days(reference_date)
    cells = []
    for (ci, cj), cell in index.items():
        feats = np.array(_features_at(cell, t_ref, grid_deg), dtype=float)
        prob = float(np.clip(predict_fn(feats, ci, cj), 0.0, 1.0))
        lon, lat = cell_center(ci, cj, grid_deg)
        cells.append({
            "cell_i": int(ci), "cell_j": int(cj),
            "lat": round(lat, 5), "lon": round(lon, 5),
            "prob": round(prob, 4),
            "level": _level(prob, metrics.get("threshold", 0.5)),
        })
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reference_date": reference_date.isoformat(),
        "prediction_horizon_days": int(horizon),
        "estimate_kind": "historical_backtest",
        "data_origin": data_origin,
        "model": {
            "type": model_name,
            "version": __version__,
            "pipeline": "pyrolens.prediction",
            "features": list(FEATURE_NAMES),
            "calibration": metrics.get("calibration_method"),
            "threshold": metrics.get("threshold"),
        },
        "metrics": metrics,
        "period": period,
        "cells": cells,
        "notes": (
            "Probabilité d'observer ≥1 détection FIRMS dans la cellule sur les "
            f"{horizon} jours suivant la date de référence — estimation d'activité "
            "détectée, pas une alerte incendie. Les données s'arrêtent en 2020 : "
            "ce résultat est un backtest historique, jamais une prévision actuelle."
        ),
    }
    if extra:
        payload.update(extra)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


# ------------------------------------------------------------------ orchestration
def data_origin_of_source(csv_paths: Iterable[str | Path]) -> str:
    """`nasa_firms` si la source est sous data/raw, sinon `synthetic_fixture`."""
    parts = {str(Path(p)).replace("\\", "/").lower() for p in csv_paths}
    if any("/raw/" in p or p.startswith("data/raw") for p in parts):
        return "nasa_firms"
    return "synthetic_fixture"


def run_prediction(
    csv_paths: list[str | Path],
    grid_deg: float = DEFAULT_GRID_DEG,
    horizon: int = DEFAULT_HORIZON_DAYS,
    stride: int = DEFAULT_STRIDE_DAYS,
    purge_days: int = DEFAULT_PURGE_DAYS,
    reference_date: date | None = None,
    out_path: str | Path | None = None,
    model_dir: str | Path | None = None,
    progress=None,
) -> dict[str, Any]:
    """Pipeline complet : événements → index → dataset → split → modèles → artefact.

    ``progress(step, pct, detail)`` optionnel — même convention que les jobs API.
    Retourne le payload de l'artefact.
    """
    t0 = time.monotonic()
    csv_paths = [Path(p) for p in csv_paths]
    data_origin = data_origin_of_source(csv_paths)

    def rep(step: str, pct: float, detail: str | None = None) -> None:
        if progress:
            progress(step, pct, detail)
        logger.info("predict %s %.0f%% %s", step, pct, detail or "")

    rep("load", 5, f"{len(csv_paths)} CSV")
    events = load_events(csv_paths, grid_deg)
    if events.empty:
        raise ValueError("Aucun événement exploitable dans la source.")
    d_min, d_max = int(events["d"].min()), int(events["d"].max())
    period = {
        "start": (_EPOCH + timedelta(days=d_min)).isoformat(),
        "end": (_EPOCH + timedelta(days=d_max)).isoformat(),
    }

    rep("index", 20, "index cellule-jour")
    index = build_cell_index(events, grid_deg)
    n_cells = len(index)

    rep("features", 40, f"{n_cells} cellules actives")
    X, y, meta = build_dataset(index, grid_deg, horizon, stride)
    if len(X) == 0:
        raise ValueError("Dataset vide : période insuffisante pour features+label.")
    masks = split_mask(meta, purge_days)
    tr, va, te = masks["train"], masks["validation"], masks["test"]
    rep("split", 55, f"train={int(tr.sum())} val={int(va.sum())} test={int(te.sum())}")

    rep("train", 65, "baseline + RandomForest")
    fitted = fit_models(
        X[tr].reset_index(drop=True), y[tr].to_numpy(),
        X[va].reset_index(drop=True), y[va].to_numpy(),
        meta[tr].reset_index(drop=True), meta[va].reset_index(drop=True),
    )

    # --- comparaison sur la VALIDATION (choix du modèle, pas du test)
    rep("validate", 80, "métriques de validation")
    thr = fitted["threshold"]
    val_metrics = {
        "baseline": _metrics(y[va].to_numpy(), fitted["baseline_val_pred"], thr),
        "random_forest": _metrics(y[va].to_numpy(), fitted["rf_val_pred"], thr),
    }
    ap_base = val_metrics["baseline"]["pr_auc"] or 0.0
    ap_rf = val_metrics["random_forest"]["pr_auc"] or 0.0
    # RF retenu seulement s'il bat la baseline d'au moins 5 % **relatif** sur PR-AUC
    use_rf = ap_rf > ap_base * 1.05 if ap_base > 0 else ap_rf > 0
    model_name = "random_forest" if use_rf else "frequency_baseline"

    # --- évaluation finale sur le TEST (une seule fois, modèle choisi)
    rep("test", 88, f"modèle retenu : {model_name}")
    if use_rf:
        p_test = _predict_calibrated(fitted, X[te].reset_index(drop=True))
    else:
        p_test = fit_frequency_baseline(
            y[tr].to_numpy(), meta[tr].reset_index(drop=True), meta[te].reset_index(drop=True)
        )
    test_metrics = _metrics(y[te].to_numpy(), p_test, thr)
    test_metrics["calibration_method"] = fitted["calibration_method"] if use_rf else None
    test_metrics["threshold"] = thr
    test_metrics["validation"] = val_metrics
    test_metrics["selection_rule"] = (
        "RF retenu si PR-AUC val > baseline × 1.05 (relatif) ; sinon baseline"
    )
    test_metrics["calibration_bins_test"] = calibration_bins(y[te].to_numpy(), p_test)

    # --- date de référence : max des données (backtest) ou explicite
    ref = reference_date or (_EPOCH + timedelta(days=d_max))
    rep("export", 95, f"référence {ref.isoformat()}")

    if use_rf:
        def predict_fn(feats: np.ndarray, ci: int, cj: int) -> float:
            Xnew = pd.DataFrame([feats], columns=FEATURE_NAMES)
            return float(_predict_calibrated(fitted, Xnew)[0])
    else:
        lookup = _baseline_lookup(y[tr].to_numpy(), meta[tr].reset_index(drop=True), ref.month)

        def predict_fn(feats: np.ndarray, ci: int, cj: int) -> float:
            return float(lookup.get((ci, cj), 0.0))

    out = Path(out_path) if out_path else Path("web/public/artifacts/fire_risk.json")
    payload = export_artifact(
        out, index, grid_deg, horizon, ref, data_origin, model_name,
        predict_fn, test_metrics, period,
        extra={"elapsed_s": round(time.monotonic() - t0, 2), "n_cells": n_cells,
               "n_samples": {"train": int(tr.sum()), "validation": int(va.sum()), "test": int(te.sum())}},
    )

    # modèle sérialisé hors du dossier public (backend uniquement)
    if model_dir:
        mdir = Path(model_dir)
        mdir.mkdir(parents=True, exist_ok=True)
        if use_rf:
            import joblib
            joblib.dump({"rf": fitted["rf"], "calibrator": fitted["calibrator"],
                         "method": fitted["calibration_method"],
                         "threshold": thr, "model_name": model_name,
                         "grid_deg": grid_deg, "horizon": horizon,
                         "features": list(FEATURE_NAMES)},
                        mdir / "fire_risk_model.joblib")
        else:
            (mdir / "fire_risk_baseline.json").write_text(
                json.dumps({"model_name": model_name, "threshold": thr,
                            "month": ref.month,
                            "lookup": {f"{k[0]}:{k[1]}": v for k, v in lookup.items()}},
                           ensure_ascii=False), encoding="utf-8")

    rep("done", 100, f"{len(payload['cells'])} cellules → {out}")
    return payload


def _predict_calibrated(fitted: dict[str, Any], X: pd.DataFrame) -> np.ndarray:
    p = fitted["rf"].predict_proba(X)[:, 1]
    cal = fitted["calibrator"]
    if fitted["calibration_method"] == "isotonic":
        return cal.predict(p)
    from sklearn.linear_model import LogisticRegression  # noqa: F401 — type only
    eps = 1e-6
    logit = np.log(np.clip(p, eps, 1 - eps) / (1 - np.clip(p, eps, 1 - eps)))
    return cal.predict_proba(logit.reshape(-1, 1))[:, 1]


def _baseline_lookup(y_train: np.ndarray, meta_train: pd.DataFrame,
                     month: int) -> dict[tuple[int, int], float]:
    """Lookup (ci,cj) → prob lissée pour le mois de référence donné.

    Même lissage bêta à deux niveaux que ``fit_frequency_baseline`` mais
    restreint au mois demandé (repli : taux cellule annuel → global).
    """
    global_rate = float(np.mean(y_train)) if len(y_train) else 0.0
    df = meta_train.assign(y=y_train)
    df["month"] = [(_EPOCH + timedelta(days=int(d))).month for d in df["d"]]
    ALPHA_CELL, ALPHA_MONTH = 30.0, 15.0
    cell_stats = df.groupby(["ci", "cj"])["y"].agg(["sum", "count"])
    cell_rate = {
        k: (r["sum"] + ALPHA_CELL * global_rate) / (r["count"] + ALPHA_CELL)
        for k, r in cell_stats.iterrows()
    }
    cm_stats = df[df["month"] == month].groupby(["ci", "cj"])["y"].agg(["sum", "count"])
    lookup: dict[tuple[int, int], float] = {}
    for key in set(cell_rate) | set(cm_stats.index):
        cm = cm_stats.loc[key] if key in cm_stats.index else None
        if cm is not None:
            lookup[key] = (cm["sum"] + ALPHA_MONTH * cell_rate.get(key, global_rate)) / (
                cm["count"] + ALPHA_MONTH
            )
        else:
            lookup[key] = cell_rate.get(key, global_rate)
    return lookup
