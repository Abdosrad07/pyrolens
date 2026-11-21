"""
Mode démo PyroLens — données réalistes pour démonstration client.

Activer avec : PYROLENS_DEMO=1 uvicorn api.index:app --reload

Toutes les réponses sont des fixtures statiques réalistes (Afrique de l'Ouest,
MODIS + VIIRS, grille 0.25°, saison sèche). Aucun calcul, aucune dépendance
aux données FIRMS téléchargées.
"""

from __future__ import annotations

import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _seed(seed: str = "pyrolens-demo-2025") -> random.Random:
    """Seed reproductible pour des données stables entre les runs."""
    h = hashlib.md5(seed.encode()).hexdigest()
    return random.Random(int(h, 16))


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


_rng = _seed()

# ──────────────────────────────────────────────────────────────────────────────
# Fire risk
# ──────────────────────────────────────────────────────────────────────────────

def _fire_risk() -> dict:
    """Probabilités de risque d'activité de feu par cellule (Afrique de l'Ouest)."""
    now = datetime.now(timezone.utc)
    # Grille 0.25° sur la zone Afrique de l'Ouest (~25×20 cellules)
    cells = []
    for i in range(25):
        for j in range(20):
            lat = 4.0 + i * 0.25
            lon = -18.0 + j * 0.25
            # Zone sahélienne : risque plus élevé entre 10°N et 15°N
            center_lat = 12.5
            dist = abs(lat - center_lat)
            if dist < 3:
                base = 0.7 + _rng.uniform(-0.15, 0.3)
            elif dist < 6:
                base = 0.4 + _rng.uniform(-0.1, 0.2)
            else:
                base = 0.1 + _rng.uniform(-0.05, 0.1)
            prob = max(0.01, min(0.99, base))
            if prob > 0.7:
                level = "critical"
            elif prob > 0.5:
                level = "high"
            elif prob > 0.3:
                level = "medium"
            else:
                level = "low"
            cells.append({
                "i": i, "j": j,
                "lat": round(lat, 4), "lon": round(lon, 4),
                "prob": round(prob, 4),
                "risk_level": level,
                "n_detections": int(prob * 50),
                "frp_mean": round(prob * 80 + _rng.uniform(0, 20), 1),
                "sensors_active": random.sample(["viirs-snpp", "modis"], k=_rng.randint(1, 2)),
            })
    return {
        "generated_at": _iso(now),
        "reference_date": _date(now - timedelta(days=8)),
        "prediction_horizon_days": 8,
        "estimate_kind": "historical_backtest",
        "data_origin": "nasa_firms",
        "model": {
            "type": "random_forest",
            "version": "0.2.0",
            "pipeline": "pyrolens.prediction",
            "features": ["n_terra_8", "n_aqua_8", "n_viirs_snpp_8"],
            "calibration": "isotonic",
            "threshold": 0.42,
        },
        "metrics": {
            "pr_auc": 0.926,
            "roc_auc": 0.956,
            "recall": 0.844,
            "precision": 0.837,
            "f1": 0.841,
            "brier": 0.072,
            "threshold": 0.42,
            "n": 122715,
            "n_positive": 38964,
            "confusion_matrix": [[77362, 6389], [6074, 32890]],
        },
        "cells": cells,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Fire calendar daily
# ──────────────────────────────────────────────────────────────────────────────

def _fire_calendar(pair: str = "viirs__modis", start: str | None = None, end: str | None = None) -> dict:
    """Série quotidienne de détections pour la paire de capteurs."""
    start_dt = datetime.strptime(start or "2019-01-01", "%Y-%m-%d")
    end_dt = datetime.strptime(end or "2024-12-31", "%Y-%m-%d")
    rows = []
    current = start_dt
    while current <= end_dt:
        # Saisonnalité : pics en saison sèche (nov-mars)
        month = current.month
        seasonal = 1.5 if month in (11, 12, 1, 2, 3) else 0.6
        total = max(0, int(_rng.gauss(seasonal * 15, 8)))
        rows.append({
            "date": _date(current),
            "pair": pair,
            "total": total,
            "a_only": int(total * 0.55),
            "b_only": int(total * 0.35),
        })
        current += timedelta(days=1)
    return {"rows": rows}


# ──────────────────────────────────────────────────────────────────────────────
# Early warning
# ──────────────────────────────────────────────────────────────────────────────

def _early_warning_summary() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "n_cells_monitored": 248,
        "n_anomalies": 17,
        "n_high_priority": 5,
        "n_increasing_zones": 9,
        "data_period": {"start": "2019-01-01", "end": "2024-12-31", "days": 2191},
        "recent_window": {"start": _date(now - timedelta(days=61)), "end": _date(now), "days": 61},
        "historical_backtest": True,
        "data_origin": "nasa_firms",
        "generated_at": _iso(now),
    }


def _early_warning_alerts() -> dict:
    now = datetime.now(timezone.utc)
    items = [
        {
            "cell_id": "47_12", "cell_i": 47, "cell_j": 12,
            "lat": 7.95, "lon": 12.25,
            "severity": "critical", "recent_detections": 142, "historical_baseline": 31,
            "activity_change": 358, "persistence": 23,
            "sensors": ["viirs-snpp", "modis"],
            "observation_period": {"start": _date(now - timedelta(days=23)), "end": _date(now)},
            "anomaly_score": 0.94,
            "reason": "Pic de détections 4.6× au-dessus de la médiane historique glissante (fenêtre 8 j), persistant sur 23 jours consécutifs. Cohérent avec un épisode de décharge à sec en saison sèche.",
            "limitations": ["Zone à faible densité de capteurs — l'estimation peut sous-estimer l'activité réelle.", "Données VIIRS uniquement la nuit."],
        },
        {
            "cell_id": "49_8", "cell_i": 49, "cell_j": 8,
            "lat": 8.45, "lon": 10.75,
            "severity": "critical", "recent_detections": 98, "historical_baseline": 22,
            "activity_change": 345, "persistence": 18,
            "sensors": ["viirs-snpp"],
            "observation_period": {"start": _date(now - timedelta(days=18)), "end": _date(now)},
            "anomaly_score": 0.89,
            "reason": "Activité 4.5× la médiane, concentrée sur VIIRS. MODIS absent — possible diurne.",
            "limitations": ["Capteur unique — risque de faux positif diurne."],
        },
        {
            "cell_id": "35_15", "cell_i": 35, "cell_j": 15,
            "lat": 5.25, "lon": 13.75,
            "severity": "high", "recent_detections": 67, "historical_baseline": 18,
            "activity_change": 272, "persistence": 15,
            "sensors": ["viirs-snpp", "modis"],
            "observation_period": {"start": _date(now - timedelta(days=15)), "end": _date(now)},
            "anomaly_score": 0.81,
            "reason": "Double capteur confirme l'anomalie. Croissance continue depuis 15 jours.",
            "limitations": [],
        },
        {
            "cell_id": "52_5", "cell_i": 52, "cell_j": 5,
            "lat": 9.0, "lon": 8.75,
            "severity": "high", "recent_detections": 55, "historical_baseline": 20,
            "activity_change": 175, "persistence": 12,
            "sensors": ["viirs-snpp", "modis"],
            "observation_period": {"start": _date(now - timedelta(days=12)), "end": _date(now)},
            "anomaly_score": 0.76,
            "reason": "Activité modérément élevée, corroborée par les deux capteurs.",
            "limitations": ["Proximité avec la cellule 47_12 — possible corrélation spatiale."],
        },
        {
            "cell_id": "28_18", "cell_i": 28, "cell_j": 18,
            "lat": 3.0, "lon": 16.5,
            "severity": "high", "recent_detections": 44, "historical_baseline": 15,
            "activity_change": 193, "persistence": 10,
            "sensors": ["modis"],
            "observation_period": {"start": _date(now - timedelta(days=10)), "end": _date(now)},
            "anomaly_score": 0.72,
            "reason": "Signal MODIS uniquement, mais persistant sur 10 jours.",
            "limitations": ["MODIS uniquement — confirmation VIIRS souhaitable."],
        },
        {
            "cell_id": "42_20", "cell_i": 42, "cell_j": 20,
            "lat": 6.75, "lon": 17.75,
            "severity": "moderate", "recent_detections": 38, "historical_baseline": 14,
            "activity_change": 171, "persistence": 8,
            "sensors": ["viirs-snpp", "modis"],
            "observation_period": {"start": _date(now - timedelta(days=8)), "end": _date(now)},
            "anomaly_score": 0.65,
            "reason": "Croissance récente, double confirmation capteurs.",
            "limitations": ["Courte persistance — à surveiller."],
        },
        {
            "cell_id": "55_3", "cell_i": 55, "cell_j": 3,
            "lat": 9.75, "lon": 7.25,
            "severity": "moderate", "recent_detections": 31, "historical_baseline": 12,
            "activity_change": 158, "persistence": 7,
            "sensors": ["viirs-snpp"],
            "observation_period": {"start": _date(now - timedelta(days=7)), "end": _date(now)},
            "anomaly_score": 0.61,
            "reason": "Signal VIIRS isolé mais au-dessus de la baseline.",
            "limitations": ["Capteur unique."],
        },
        {
            "cell_id": "31_10", "cell_i": 31, "cell_j": 10,
            "lat": 4.25, "lon": 12.25,
            "severity": "moderate", "recent_detections": 28, "historical_baseline": 11,
            "activity_change": 155, "persistence": 6,
            "sensors": ["viirs-snpp", "modis"],
            "observation_period": {"start": _date(now - timedelta(days=6)), "end": _date(now)},
            "anomaly_score": 0.58,
            "reason": "Détections croissantes, double capteur.",
            "limitations": ["Faible effectif."],
        },
        {
            "cell_id": "45_7", "cell_i": 45, "cell_j": 7,
            "lat": 7.25, "lon": 9.75,
            "severity": "moderate", "recent_detections": 25, "historical_baseline": 10,
            "activity_change": 150, "persistence": 5,
            "sensors": ["viirs-snpp", "modis"],
            "observation_period": {"start": _date(now - timedelta(days=5)), "end": _date(now)},
            "anomaly_score": 0.55,
            "reason": "Légère élévation confirmée par les deux capteurs.",
            "limitations": [],
        },
        {
            "cell_id": "22_14", "cell_i": 22, "cell_j": 14,
            "lat": 1.5, "lon": 14.5,
            "severity": "low", "recent_detections": 15, "historical_baseline": 8,
            "activity_change": 88, "persistence": 4,
            "sensors": ["viirs-snpp"],
            "observation_period": {"start": _date(now - timedelta(days=4)), "end": _date(now)},
            "anomaly_score": 0.42,
            "reason": "Légère augmentation sur VIIRS uniquement.",
            "limitations": ["Niveau bas, à confirmer."],
        },
        {
            "cell_id": "38_2", "cell_i": 38, "cell_j": 2,
            "lat": 5.75, "lon": 6.25,
            "severity": "low", "recent_detections": 12, "historical_baseline": 7,
            "activity_change": 71, "persistence": 3,
            "sensors": ["viirs-snpp", "modis"],
            "observation_period": {"start": _date(now - timedelta(days=3)), "end": _date(now)},
            "anomaly_score": 0.38,
            "reason": "Écart modéré, double confirmation.",
            "limitations": ["Très courte persistance."],
        },
        {
            "cell_id": "60_12", "cell_i": 60, "cell_j": 12,
            "lat": 11.0, "lon": 13.0,
            "severity": "low", "recent_detections": 10, "historical_baseline": 6,
            "activity_change": 67, "persistence": 3,
            "sensors": ["modis"],
            "observation_period": {"start": _date(now - timedelta(days=3)), "end": _date(now)},
            "anomaly_score": 0.35,
            "reason": "Signal MODIS isolé, tendance à surveiller.",
            "limitations": ["Capteur unique, faible effectif."],
        },
        {
            "cell_id": "25_22", "cell_i": 25, "cell_j": 22,
            "lat": 2.25, "lon": 19.25,
            "severity": "low", "recent_detections": 8, "historical_baseline": 5,
            "activity_change": 60, "persistence": 2,
            "sensors": ["viirs-snpp"],
            "observation_period": {"start": _date(now - timedelta(days=2)), "end": _date(now)},
            "anomaly_score": 0.30,
            "reason": "Écart léger, début de tendance.",
            "limitations": ["Données insuffisantes pour conclure."],
        },
        {
            "cell_id": "40_25", "cell_i": 40, "cell_j": 25,
            "lat": 6.25, "lon": 21.25,
            "severity": "low", "recent_detections": 7, "historical_baseline": 4,
            "activity_change": 75, "persistence": 2,
            "sensors": ["viirs-snpp", "modis"],
            "observation_period": {"start": _date(now - timedelta(days=2)), "end": _date(now)},
            "anomaly_score": 0.33,
            "reason": "Double confirmation malgré l'effectif réduit.",
            "limitations": [],
        },
    ]
    return {"items": items, "meta": _early_warning_summary()}


def _early_warning_alert_detail(cell_id: str) -> dict | None:
    alerts = _early_warning_alerts()["items"]
    for a in alerts:
        if a["cell_id"] == cell_id:
            return a
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Baselines
# ──────────────────────────────────────────────────────────────────────────────

def _baselines_summary(pair: str = "viirs__modis", grid_deg: float = 0.25, window_days: int = 8) -> dict:
    """Résumé des baselines pour les paires de capteurs."""
    pairs = [
        ("viirs-snpp", "modis"),
        ("viirs-snpp", "viirs-noaa20"),
        ("modis__aqua", "modis__terra"),
    ]
    rows = []
    for sa, sb in pairs:
        n_a = _rng.randint(50000, 200000)
        n_b = _rng.randint(50000, 200000)
        inter = int(n_a * _rng.uniform(0.4, 0.7))
        union = n_a + n_b - inter
        rows.append({
            "pair": f"{sa}__{sb}",
            "sensor_a": sa,
            "sensor_b": sb,
            "grid_deg": grid_deg,
            "window_days": window_days,
            "key_definition": "intersection_over_union",
            "n_a": n_a,
            "n_b": n_b,
            "intersection": inter,
            "union": union,
            "jaccard": round(inter / union, 4) if union else 0,
        })
    return {"rows": rows}


def _baselines_jaccard_series(pair: str = "viirs__modis", grid_deg: float = 0.25, window_days: int = 8) -> dict:
    """Série mensuelle de Jaccard."""
    rows = []
    base = datetime(2019, 1, 1)
    for m in range(72):  # 6 ans
        dt = base + timedelta(days=m * 30)
        month_str = dt.strftime("%Y-%m")
        seasonal = 1.3 if dt.month in (1, 2, 12) else 0.8 if dt.month in (6, 7, 8) else 1.0
        jaccard = max(0.2, min(0.9, 0.55 + _rng.gauss(0, 0.08) * seasonal))
        both = int(15000 * jaccard + _rng.gauss(0, 2000))
        a_only = int(8000 + _rng.gauss(0, 1500))
        b_only = int(6000 + _rng.gauss(0, 1200))
        rows.append({
            "month": month_str,
            "jaccard": round(jaccard, 4),
            "both": max(0, both),
            "a_only": max(0, a_only),
            "b_only": max(0, b_only),
        })
    return {"rows": rows}


def _baselines_spatial(pair: str = "viirs__modis", grid_deg: float = 0.25, window_days: int = 8, limit: int = 50) -> dict:
    """Distribution spatiale du Jaccard par cellule."""
    rows = []
    for i in range(20):
        for j in range(20):
            if len(rows) >= limit:
                break
            rows.append({
                "cell_i": i,
                "cell_j": j,
                "a_count": _rng.randint(100, 5000),
                "b_count": _rng.randint(100, 5000),
            })
    return {"rows": rows}


# ──────────────────────────────────────────────────────────────────────────────
# Experiments / Jobs
# ──────────────────────────────────────────────────────────────────────────────

def _experiments_list() -> dict:
    now = datetime.now(timezone.utc)
    kinds = ["harmonization", "firms_analyze", "predict"]
    statuses = ["succeeded", "succeeded", "succeeded", "running", "pending"]
    items = []
    for i in range(8):
        kind = kinds[i % len(kinds)]
        status = statuses[i % len(statuses)]
        created = now - timedelta(days=i * 3, hours=i * 4)
        item = {
            "job_id": f"demo-{kind}-{i+1:03d}",
            "kind": kind,
            "status": status,
            "progress": {
                "step": "completed" if status == "succeeded" else "processing",
                "pct": 100 if status == "succeeded" else (50 if status == "running" else 0),
                "detail": "Terminé" if status == "succeeded" else ("En cours…" if status == "running" else "En attente"),
            },
            "created_at": _iso(created),
            "started_at": _iso(created + timedelta(minutes=1)) if status != "pending" else None,
            "finished_at": _iso(created + timedelta(minutes=5)) if status == "succeeded" else None,
            "params": {"grid_deg": 0.25, "window_days": 8},
            "error": None,
            "links": {"result": f"/artifacts/{kind}_demo_{i+1}.json"} if status == "succeeded" else {},
        }
        items.append(item)
    return {"items": items}


def _predict_job(job_id: str) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "job_id": job_id,
        "kind": "predict",
        "status": "succeeded",
        "progress": {"step": "completed", "pct": 100, "detail": "Terminé"},
        "created_at": _iso(now - timedelta(hours=1)),
        "started_at": _iso(now - timedelta(minutes=55)),
        "finished_at": _iso(now - timedelta(minutes=10)),
        "params": {"grid_deg": 0.25, "window": 8, "reference_date": _date(now - timedelta(days=8))},
        "error": None,
        "links": {"result": "/artifacts/fire_risk.json"},
    }


# ─��────────────────────────────────────────────────────────────────────────────
# Chat
# ──────────────────────────────────────────────────────────────────────────────

_CHAT_RESPONSES = [
    "Les données proviennent de VIIRS (Suomi NPP) et MODIS (Terra/Aqua), deux capteurs NASA complémentaires. VIIRS offre une résolution plus fine (~375 m) mais passe la nuit seulement ; MODIS couvre jour et nuit avec une résolution de 1 km.",
    "Le risque d'activité de feu est une estimation basée sur un modèle Random Forest entraîné sur 7 ans de données (2019-2025). Les probabilités sont calibrées par cellule de grille 0.25°. Ce n'est pas une alerte en temps réel.",
    "La zone d'étude couvre l'Afrique de l'Ouest et du Sud (25 pays). Les données proviennent du catalogue FIRMS open-access de la NASA.",
    "Le Jaccard mesure le recouvrement d'ensembles entre capteurs : il indique quelle fraction des détections est commune aux deux instruments. Un Jaccard de 0.5 signifie que 50 % des détections MODIS ont aussi une détection VIIRS dans la même cellule et fenêtre temporelle.",
    "Les anomalies détectées sont comparées à une baseline historique (médiane glissante 8 jours sur 6 ans). Un dépassement de 2× la baseline avec persistance ≥ 5 jours déclenche une alerte.",
    "La saison sèche sahélienne (novembre à mars) concentre la majorité des détections. L'activité diminue significativement pendant la saison des pluies (juin à septembre).",
    "Pour toute question sur les limites scientifiques : ces estimations ne remplacent pas un système d'alerte incendie opérationnel. Elles servent à la surveillance statistique et à la planification.",
]


def _chat_reply(message: str) -> str:
    msg = message.lower()
    if any(k in msg for k in ["viirs", "modis", "capteur", "sensor"]):
        return _CHAT_RESPONSES[0]
    if any(k in msg for k in ["risque", "risk", "modèle", "model", "random forest"]):
        return _CHAT_RESPONSES[1]
    if any(k in msg for k in ["zone", "couverture", "pays", "afrique", "country"]):
        return _CHAT_RESPONSES[2]
    if any(k in msg for k in ["jaccard", "harmonisation", "recouvrement", "overlap"]):
        return _CHAT_RESPONSES[3]
    if any(k in msg for k in ["anomalie", "alerte", "alert", "baseline"]):
        return _CHAT_RESPONSES[4]
    if any(k in msg for k in ["saison", "sèche", "pluie", "season"]):
        return _CHAT_RESPONSES[5]
    if any(k in msg for k in ["limite", "précaution", "validité", "limit"]):
        return _CHAT_RESPONSES[6]
    # Default
    idx = _rng.randint(0, len(_CHAT_RESPONSES) - 1)
    return _CHAT_RESPONSES[idx]


# ──────────────────────────────────────────────────────────────────────────────
# Health / meta
# ──────────────────────────────────────────────────────────────────────────────

def _health() -> dict:
    return {
        "status": "ok",
        "generated_at": _iso(datetime.now(timezone.utc)),
        "data_origin": "nasa_firms (demo mode)",
        "project_version": "0.2.0-demo",
    }


def _meta() -> dict:
    return {
        "generated_at": _iso(datetime.now(timezone.utc)),
        "data_origin": "nasa_firms",
        "project_version": "0.2.0-demo",
        "period": {"start": "2019-01-01", "end": "2024-12-31"},
        "primary": {"grid_deg": 0.25, "window_days": 8},
        "grids_deg": [0.1, 0.25, 0.5],
        "window_days": [1, 4, 8, 16],
        "pairs": [
            {"pair": "viirs-snpp__modis", "label": "VIIRS Suomi NPP + MODIS (Terra/Aqua)"},
        ],
        "key_definitions": {
            "window_1": "intersection sur 1 jour",
            "window_gt1": "intersection glissante sur N jours",
        },
        "coverage_products_acquired": 420,
        "interpretation_note": "Mode démo — données simulées.",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Module-level demo router (used by the demo patch)
# ──────────────────────────────────────────────────────────────────────────────

class DemoRouter:
    """Sert les données mock pour tous les endpoints consommés par le frontend."""

    def __init__(self):
        self._jobs_store: list[dict] = _experiments_list()["items"]

    # ── system ──

    def get_health(self) -> dict:
        return _health()

    def get_meta(self) -> dict:
        return _meta()

    # ── fire-risk ──

    def get_fire_risk(self) -> dict:
        return _fire_risk()

    # ── chat ──

    def post_chat(self, body: dict) -> dict:
        messages = body.get("messages") or []
        last = str(messages[-1].get("content", "")) if messages else ""
        return {"reply": _chat_reply(last)}

    # ── predict ──

    def post_predict(self, body: dict) -> dict:
        job_id = f"demo-predict-{_rng.randint(1000, 9999)}"
        return {
            "job_id": job_id,
            "status": "succeeded",
            "progress": {"step": "completed", "pct": 100, "detail": "Terminé (demo)"},
            "links": {"result": "/artifacts/fire_risk.json"},
        }

    def get_predict_job(self, job_id: str) -> dict:
        return _predict_job(job_id)

    def get_predict_list(self) -> dict:
        return {"items": [_predict_job(f"demo-predict-{i}") for i in range(1, 4)]}

    # ── experiments ──

    def get_experiments(self) -> dict:
        return {"items": self._jobs_store}

    # ── fire-calendar ──

    def get_fire_calendar_daily(self, params: dict) -> dict:
        return _fire_calendar(
            pair=params.get("pair", "viirs__modis"),
            start=params.get("start"),
            end=params.get("end"),
        )

    # ── early-warning ──

    def get_early_warning_summary(self) -> dict:
        return _early_warning_summary()

    def get_early_warning_alerts(self) -> dict:
        return _early_warning_alerts()

    def get_early_warning_alert_detail(self, cell_id: str) -> dict | None:
        return _early_warning_alert_detail(cell_id)

    # ── baselines ──

    def get_baselines_summary(self, params: dict) -> dict:
        return _baselines_summary(
            pair=params.get("pair", "viirs__modis"),
            grid_deg=params.get("grid_deg", 0.25),
            window_days=params.get("window_days", 8),
        )

    def get_baselines_jaccard_series(self, params: dict) -> dict:
        return _baselines_jaccard_series(
            pair=params.get("pair", "viirs__modis"),
            grid_deg=params.get("grid_deg", 0.25),
            window_days=params.get("window_days", 8),
        )

    def get_baselines_spatial(self, params: dict) -> dict:
        return _baselines_spatial(
            pair=params.get("pair", "viirs__modis"),
            grid_deg=params.get("grid_deg", 0.25),
            window_days=params.get("window_days", 8),
            limit=int(params.get("limit", 50)),
        )


# Singleton
_demo = None

def get_demo_router() -> DemoRouter:
    global _demo
    if _demo is None:
        _demo = DemoRouter()
    return _demo
