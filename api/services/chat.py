"""Assistant conversationnel déterministe — aucune LLM, réponses factuelles.

Couvre les questions métier sur PyroLens : données, pipeline, vues de
l'interface, analyse de zone, modèle de risque, jobs, qualité, limites
scientifiques. Chaque réponse cite sa source (artefact ou endpoint) pour
rester vérifiable — jamais de contenu inventé.
"""

from __future__ import annotations

import re
from typing import Any

# ── intentions (mots-clés FR, minuscules) ──────────────────────────────
_INTENTS: list[tuple[str, tuple[str, ...]]] = [
    ("prediction", ("risque", "prédict", "prediction", "forecast", "probabilité", "probabilite", "random forest", "modèle", "modele")),
    ("zone", ("zone", "région", "region", "bbox", "périmètre", "perimetre", "clic", "carte", "secteur")),
    ("historique", ("historique", "archive", "année", "annee", "2019", "depuis", "longue")),
    ("donnees", ("donnée", "donnee", "source", "firms", "nasa", "satellite", "modis", "viirs", "période", "periode", "couverture", "combien")),
    ("calendrier", ("calendrier", "jour", "date", "mensuel", "quotidien", "saison")),
    ("jobs", ("job", "tâche", "tache", "traitement", "background", "arrière", "arriere", "progression", "statut")),
    ("qualite", ("qualité", "qualite", "anomalie", "audit", "dq", "propre", "propreté", "proprete", "manquant", "manquante")),
    ("aide", ("aide", "help", "utiliser", "comment", "fonctionne", "faire", "où", "ou ", "endpoint", "api")),
]


def _match_intent(text: str) -> str:
    t = text.lower()
    for name, keywords in _INTENTS:
        if any(k in t for k in keywords):
            return name
    return "general"


def _fmt_metrics(m: dict) -> str:
    if not m:
        return ""
    parts = []
    for k, label in (("pr_auc", "PR-AUC"), ("f1", "F1"), ("recall", "rappel"), ("brier", "Brier")):
        if m.get(k) is not None:
            parts.append(f"{label}={m[k]:.3f}" if isinstance(m[k], float) else f"{label}={m[k]}")
    return " · ".join(parts)


def answer(message: str, ctx: dict[str, Any]) -> str:
    """Réponse déterministe à ``message`` selon le contexte réel chargé."""
    intent = _match_intent(message or "")
    risk = ctx.get("risk") or {}
    meta = ctx.get("meta") or {}
    jobs = ctx.get("jobs") or []
    downloads = ctx.get("downloads") or {}
    period = risk.get("period") or {}
    metrics = risk.get("metrics") or {}
    model = (risk.get("model") or {}).get("type", "?")
    horizon = risk.get("prediction_horizon_days") or (risk.get("model") or {}).get("horizon_days", "?")

    if intent == "prediction":
        if not risk:
            return ("Aucun modèle entraîné pour le moment : lance « pyrolens predict » "
                    "ou le bouton « Exécuter prédiction » du panneau Risque.")
        val = (metrics.get("validation") or {})
        return (
            f"Le modèle de risque ({model}) prédit la probabilité qu'une cellule 0,25° "
            f"connaisse au moins une détection FIRMS dans les {horizon} jours — c'est un "
            "backtest historique, pas une alerte incendie.\n"
            f"Données : {risk.get('data_origin', '?')}, {len(risk.get('cells', []))} cellules, "
            f"référence {risk.get('reference_date', '?')}.\n"
            f"Test : {_fmt_metrics(metrics)}.\n"
            "La baseline (fréquence lissée) atteint PR-AUC 0,875 en validation ; le "
            "RandomForest la bat avec 0,928 — la persistance de l'activité de feu domine "
            "le signal. Détail : docs/FIRE_RISK_PREDICTION.md."
        )

    if intent == "zone":
        return (
            "Analyse de zone : cliquez sur la carte (vue Carte) pour définir un "
            "périmètre, puis choisissez « Analyse NRT » (~5 derniers jours, instantané) "
            "ou « Historique » (archive annuelle FIRMS par pays, ex. 2019→aujourd'hui). "
            "Le résultat compare VIIRS et MODIS sur la même grille via le Jaccard — "
            "un recouvrement d'ensembles, pas une précision. Endpoint : "
            "POST /api/v1/firms/analyze et POST /api/v1/firms/history."
        )

    if intent == "historique":
        dl = downloads.get("archive") or {}
        return (
            "L'historique utilise les fichiers annuels FIRMS par pays "
            "(/data/country/{capteur}/{année}/), sans clé API — cache local "
            "data/raw/archive/. La couverture standard processing commence ~2012 "
            "(VIIRS) / ~2000 (MODIS) avec quelques mois de retard sur l'année "
            "courante ; le NRT complète les ~5 derniers jours. "
            f"Cache actuel : {dl.get('files', 0)} fichiers ({dl.get('mb', 0)} Mo)."
        )

    if intent == "donnees":
        d_origin = risk.get("data_origin") or meta.get("data_origin") or "?"
        p = period or {}
        return (
            f"Sources : NASA FIRMS (CSV NRT + archive annuelle par pays), jamais de "
            f"données inventées — origine propagée : {d_origin}.\n"
            f"Période pipeline : {p.get('start', meta.get('period', {}).get('start', '?'))} "
            f"→ {p.get('end', meta.get('period', {}).get('end', '?'))}.\n"
            "Capteurs : VIIRS-SNPP (375 m) et MODIS (1 km) sur la même grille 0,25°. "
            "Limite clé : une cellule sans détection ne signifie PAS absence de feu "
            "(nuages, nuit, passage satellite)."
        )

    if intent == "calendrier":
        return (
            "Le calendrier (vue Calendrier) affiche les cellules en divergence "
            "inter-capteurs par jour — /api/v1/fire-calendar/daily. Pour l'historique "
            "d'une zone précise, utilise l'analyse « Historique » depuis la carte : "
            "le calendrier zone suit alors les résultats quotidiens réels."
        )

    if intent == "jobs":
        if not jobs:
            return "Aucun job en cours ou récent. Les jobs apparaissent ici après une analyse de zone, un historique ou un entraînement predict."
        running = [j for j in jobs if j.get("status") == "running"]
        lines = [f"{len(jobs)} job(s) connu(s), {len(running)} en cours."]
        for j in jobs[:5]:
            p = j.get("progress") or {}
            pct = f" {round(p.get('pct', 0))}%" if p else ""
            lines.append(f"• {j.get('kind', '?')} — {j.get('status')}{pct}")
        return "\n".join(lines)

    if intent == "qualite":
        return (
            "Le rapport qualité (vue Qualité des données) lit audit.json : "
            "anomalies par catégorie, trous temporels capteurs, valeurs manquantes. "
            "Règle d'or du projet : les lignes malformées sont isolées, jamais "
            "corrigées silencieusement — voir interpretation_warning dans l'artefact."
        )

    if intent == "aide":
        return (
            "PyroLens compare et harmonise les détections MODIS/VIIRS (NASA FIRMS).\n"
            "• Carte : hotspots GIBS + clic = analyse de zone (NRT ou historique)\n"
            "• Aperçu : artefacts du pipeline · Calendrier : divergence quotidienne\n"
            "• Jobs : tâches réelles · Qualité : audit des données\n"
            "• Risque : modèle RandomForest (backtest) + panneau de config\n"
            "API : GET /api/v1/meta, /fire-risk, /fire-calendar/*, /audit/summary ; "
            "POST /firms/analyze, /firms/history, /predict."
        )

    # ── général ──────────────────────────────────────────────────────
    return (
        "Je suis l'assistant PyroLens — je réponds à partir des artefacts réels "
        "(pas de LLM). Pose-moi par exemple : « comment fonctionne le modèle de "
        "risque », « quelles données sont utilisées », « où voir les jobs », "
        "« comment lancer une analyse de zone »."
    )
