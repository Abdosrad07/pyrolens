"""Assistant conversationnel déterministe — aucune LLM, réponses factuelles.

Couvre les questions métier sur PyroLens : données, pipeline, vues de
l'interface, analyse de zone, modèle de risque, jobs, qualité, limites
scientifiques. Réponses en français ET en anglais (détection automatique
de la langue du message). Chaque réponse cite sa source (artefact ou
endpoint) pour rester vérifiable — jamais de contenu inventé.
"""

from __future__ import annotations

import re
from typing import Any

# ── intentions (mots-clés minuscules, FR + EN) ─────────────────────────
# L'ordre compte : les intentions les plus spécifiques passent en premier
# (« risk levels » ne doit pas tomber dans « prediction » à cause de « risk »).
_INTENTS: list[tuple[str, tuple[str, ...]]] = [
    ("resume", (
        "summar", "summary", "overview", "résum", "resume", "résumé", "resumé",
        "résumer", "resumer", "synthèse", "synthese", "aperçu", "apercu",
        "highlight", "key figures", "chiffres clés", "result", "results",
    )),
    ("levels", (
        "level", "levels", "colour", "color", "colors", "colours", "legend",
        "meaning", "niveaux", "couleur", "couleurs", "légende", "legende",
        "que signifient",
    )),
    ("capteurs", (
        "difference", "différence", "différence entre", "versus", " vs ",
        "sensor", "capteur", "terra", "aqua", "snpp", "375", "1 km",
        "modis et viirs", "viirs et modis", "compare", "jaccard",
    )),
    ("prediction", (
        "risque", "prédict", "prediction", "forecast", "probabilité", "probabilite",
        "random forest", "modèle", "modele", "predict", "probability", "chance",
        "risk",
    )),
    ("zone", (
        "zone", "région", "region", "bbox", "périmètre", "perimetre", "clic",
        "carte", "secteur", "area", "map", "click", "analyse", "analysis",
        "analyze",
    )),
    ("historique", (
        "historique", "archive", "année", "annee", "2019", "depuis", "longue",
        "history", "past", "since", "long-term", "year",
    )),
    ("qualite", (
        "qualité", "qualite", "anomalie", "audit", "dq", "propre", "propreté",
        "proprete", "manquant", "manquante", "quality", "anomal", "missing",
        "clean",
    )),
    ("donnees", (
        "donnée", "donnee", "source", "firms", "nasa", "satellite", "modis",
        "viirs", "période", "periode", "couverture", "combien", "data",
        "dataset", "coverage", "how many",
    )),
    ("calendrier", (
        "calendrier", "jour", "date", "mensuel", "quotidien", "saison",
        "calendar", "day", "daily", "monthly", "season", "timeline",
    )),
    ("jobs", (
        "job", "jobs", "tâche", "taches", "traitement", "background", "arrière",
        "arriere", "progression", "statut", "task", "tasks", "processing",
        "progress", "status", "running",
    )),
    ("aide", (
        "aide", "help", "utiliser", "comment", "fonctionne", "faire", "où", "ou ",
        "endpoint", "api", "how", "use", "work", "where", "guide", "start",
        "what can you",
    )),
]

_EN_MARKERS = (
    " the ", " is ", " are ", " what", " how", " does", " do ", "difference",
    " show", " map", " when", " where", " can ", " please", " hello", " hi ",
    " thanks", " yes", " summarize", " risk level", " color", " colour",
    " run ", " view", " i ", " me ", " my ", " you", " your", " data ",
    " report", " results", " jobs", " quality", " please",
)
_FR_MARKERS = (
    " le ", " la ", " les ", " des ", " une ", " est ", " sont ", "comment",
    " quelle", " qu'", " bonjour", " merci", " données", " fonctionn",
    " pouvez", " je ", " vous",
)


def _detect_lang(text: str) -> str:
    t = f" {text.lower()} "
    en = sum(1 for m in _EN_MARKERS if m in t)
    fr = sum(1 for m in _FR_MARKERS if m in t)
    return "en" if en > fr else "fr"


def _match_intent(text: str) -> str:
    """Premier intent dont un mot-clé correspond comme MOT ENTIER.

    Les frontières \b évitent les faux positifs de sous-chaîne
    (« bonjour » ne doit pas matcher « jour »).
    """
    t = text.lower()
    for name, keywords in _INTENTS:
        for k in keywords:
            if re.search(rf"(?<!\w){re.escape(k.strip())}(?!\w)", t):
                return name
    return "general"


def _fmt_metrics(m: dict, lang: str) -> str:
    if not m:
        return ""
    labels = {
        "pr_auc": "PR-AUC",
        "f1": "F1",
        "recall": "rappel" if lang == "fr" else "recall",
        "brier": "Brier",
    }
    parts = []
    for k, label in labels.items():
        if m.get(k) is not None:
            parts.append(f"{label}={m[k]:.3f}" if isinstance(m[k], float) else f"{label}={m[k]}")
    return " · ".join(parts)


def _ctx(ctx: dict[str, Any]) -> dict[str, Any]:
    risk = ctx.get("risk") or {}
    meta = ctx.get("meta") or {}
    return {
        "risk": risk,
        "meta": meta,
        "jobs": ctx.get("jobs") or [],
        "downloads": ctx.get("downloads") or {},
        "period": risk.get("period") or {},
        "metrics": risk.get("metrics") or {},
        "model": (risk.get("model") or {}).get("type", "?"),
        "horizon": risk.get("prediction_horizon_days")
        or (risk.get("model") or {}).get("horizon_days", "?"),
    }


def _answer_fr(intent: str, v: dict[str, Any]) -> str:
    risk, metrics, model, horizon = v["risk"], v["metrics"], v["model"], v["horizon"]
    period, jobs, downloads = v["period"], v["jobs"], v["downloads"]

    if intent == "resume":
        if not risk:
            return ("Aucun modèle entraîné pour le moment : lance « pyrolens predict » "
                    "ou le bouton « Exécuter prédiction » du panneau Risque.")
        return (
            f"En bref : PyroLens compare MODIS et VIIRS sur une grille 0,25° et "
            f"prédit la probabilité d'au moins une détection FIRMS dans les "
            f"{horizon} jours (backtest, pas une alerte). "
            f"Modèle {model} — {len(risk.get('cells', []))} cellules, référence "
            f"{risk.get('reference_date', '?')}, test : {_fmt_metrics(metrics, 'fr')}. "
            "La baseline fréquence est battue par le RandomForest (PR-AUC 0,928 vs "
            "0,875 en validation)."
        )

    if intent == "levels":
        return (
            "Les couleurs de la carte encodent la probabilité calibrée d'observer "
            "≥1 détection FIRMS dans la cellule sur 8 jours : <30 % jaune « Faible », "
            "30–60 % orange « Modéré », 60–80 % rouge-orangé « Élevé », ≥80 % bordeaux "
            "« Critique ». Ce n'est PAS une probabilité d'incendie réel — une cellule "
            "« Faible » peut quand même avoir du feu non détecté (nuages, nuit)."
        )

    if intent == "capteurs":
        return (
            "MODIS Terra et Aqua : capteurs 1 km, passages ~10h30 et ~13h30 locales. "
            "VIIRS-SNPP : 375 m, passage ~13h30 — plus fin et plus récent. "
            "Ils ne voient pas les feux de la même façon (résolution, angle, heure) : "
            "le projet les harmonise sur une grille commune 0,25° et mesure le "
            "recouvrement par Jaccard — jamais une « précision »."
        )

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
            f"Test : {_fmt_metrics(metrics, 'fr')}.\n"
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
        d_origin = risk.get("data_origin") or v["meta"].get("data_origin") or "?"
        p = period or {}
        return (
            f"Sources : NASA FIRMS (CSV NRT + archive annuelle par pays), jamais de "
            f"données inventées — origine propagée : {d_origin}.\n"
            f"Période pipeline : {p.get('start', v['meta'].get('period', {}).get('start', '?'))} "
            f"→ {p.get('end', v['meta'].get('period', {}).get('end', '?'))}.\n"
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

    return (
        "Je suis l'assistant PyroLens — je réponds à partir des artefacts réels "
        "(pas de LLM). Pose-moi par exemple : « comment fonctionne le modèle de "
        "risque », « quelles données sont utilisées », « où voir les jobs », "
        "« comment lancer une analyse de zone »."
    )


def _answer_en(intent: str, v: dict[str, Any]) -> str:
    risk, metrics, model, horizon = v["risk"], v["metrics"], v["model"], v["horizon"]
    period, jobs, downloads = v["period"], v["jobs"], v["downloads"]

    if intent == "resume":
        if not risk:
            return ("No model trained yet: run \"pyrolens predict\" or the "
                    "\"Run prediction\" button in the Risk panel.")
        return (
            f"In short: PyroLens compares MODIS and VIIRS on a 0.25° grid and "
            f"predicts the probability of at least one FIRMS detection within "
            f"{horizon} days (a backtest, not an alert). "
            f"{model} model — {len(risk.get('cells', []))} cells, reference "
            f"{risk.get('reference_date', '?')}, test: {_fmt_metrics(metrics, 'en')}. "
            "The frequency baseline is beaten by the RandomForest (PR-AUC 0.928 vs "
            "0.875 on validation)."
        )

    if intent == "levels":
        return (
            "Map colors encode the calibrated probability of observing ≥1 FIRMS "
            "detection in the cell over 8 days: <30% yellow \"Low\", 30–60% orange "
            "\"Moderate\", 60–80% red-orange \"High\", ≥80% maroon \"Critical\". "
            "This is NOT a real-fire probability — a \"Low\" cell can still have "
            "undetected fire (clouds, night, satellite overpass)."
        )

    if intent == "capteurs":
        return (
            "MODIS Terra and Aqua: 1 km sensors, overpasses ~10:30 and ~13:30 local. "
            "VIIRS-SNPP: 375 m, ~13:30 overpass — finer and more recent. "
            "They do not see fires the same way (resolution, viewing angle, time): "
            "the project harmonizes them on a common 0.25° grid and measures "
            "overlap with Jaccard — never an \"accuracy\"."
        )

    if intent == "prediction":
        if not risk:
            return ("No model trained yet: run \"pyrolens predict\" or the "
                    "\"Run prediction\" button in the Risk panel.")
        return (
            f"The risk model ({model}) predicts the probability that a 0.25° cell "
            f"records at least one FIRMS detection within {horizon} days — this is a "
            "historical backtest, not a fire alert.\n"
            f"Data: {risk.get('data_origin', '?')}, {len(risk.get('cells', []))} cells, "
            f"reference {risk.get('reference_date', '?')}.\n"
            f"Test: {_fmt_metrics(metrics, 'en')}.\n"
            "The baseline (smoothed frequency) reaches PR-AUC 0.875 on validation; "
            "the RandomForest beats it with 0.928 — fire-activity persistence "
            "dominates the signal. Details: docs/FIRE_RISK_PREDICTION.md."
        )

    if intent == "zone":
        return (
            "Zone analysis: click on the map (Map view) to draw an area, then pick "
            "\"NRT analysis\" (~last 5 days, snapshot) or \"History\" (yearly FIRMS "
            "country archives, e.g. 2019→today). The result compares VIIRS and MODIS "
            "on the same grid via Jaccard — a set overlap, not an accuracy. "
            "Endpoints: POST /api/v1/firms/analyze and POST /api/v1/firms/history."
        )

    if intent == "historique":
        dl = downloads.get("archive") or {}
        return (
            "History uses yearly FIRMS country files (/data/country/{sensor}/{year}/), "
            "no API key needed — local cache data/raw/archive/. Standard processing "
            "coverage starts ~2012 (VIIRS) / ~2000 (MODIS) with a few months lag on "
            "the current year; NRT fills the last ~5 days. "
            f"Current cache: {dl.get('files', 0)} files ({dl.get('mb', 0)} MB)."
        )

    if intent == "donnees":
        d_origin = risk.get("data_origin") or v["meta"].get("data_origin") or "?"
        p = period or {}
        return (
            f"Sources: NASA FIRMS (NRT CSV + yearly country archives), never "
            f"invented data — propagated origin: {d_origin}.\n"
            f"Pipeline period: {p.get('start', v['meta'].get('period', {}).get('start', '?'))} "
            f"→ {p.get('end', v['meta'].get('period', {}).get('end', '?'))}.\n"
            "Sensors: VIIRS-SNPP (375 m) and MODIS (1 km) on the same 0.25° grid. "
            "Key limit: a cell without detection does NOT mean no fire "
            "(clouds, night, satellite overpass)."
        )

    if intent == "calendrier":
        return (
            "The calendar (Calendar view) shows inter-sensor divergent cells per day "
            "— /api/v1/fire-calendar/daily. For a specific area's history, use the "
            "\"History\" analysis from the map: the zone calendar then follows real "
            "daily results."
        )

    if intent == "jobs":
        if not jobs:
            return "No running or recent jobs. Jobs appear here after a zone analysis, a history run or a predict training."
        running = [j for j in jobs if j.get("status") == "running"]
        lines = [f"{len(jobs)} known job(s), {len(running)} running."]
        for j in jobs[:5]:
            p = j.get("progress") or {}
            pct = f" {round(p.get('pct', 0))}%" if p else ""
            lines.append(f"• {j.get('kind', '?')} — {j.get('status')}{pct}")
        return "\n".join(lines)

    if intent == "qualite":
        return (
            "The quality report (Data quality view) reads audit.json: anomalies by "
            "category, sensor temporal gaps, missing values. Golden rule: malformed "
            "rows are isolated, never silently fixed — see interpretation_warning "
            "in the artifact."
        )

    if intent == "aide":
        return (
            "PyroLens compares and harmonizes MODIS/VIIRS detections (NASA FIRMS).\n"
            "• Map: GIBS hotspots + click = zone analysis (NRT or history)\n"
            "• Overview: pipeline artifacts · Calendar: daily divergence\n"
            "• Jobs: real tasks · Quality: data audit\n"
            "• Risk: RandomForest model (backtest) + config panel\n"
            "API: GET /api/v1/meta, /fire-risk, /fire-calendar/*, /audit/summary; "
            "POST /firms/analyze, /firms/history, /predict."
        )

    return (
        "I'm the PyroLens assistant — I answer from real artifacts (no LLM). "
        "Try asking: \"how does the risk model work\", \"what data is used\", "
        "\"where are the jobs\", \"how to run a zone analysis\"."
    )


def answer(message: str, ctx: dict[str, Any]) -> str:
    """Réponse déterministe à ``message`` selon le contexte réel chargé."""
    v = _ctx(ctx)
    intent = _match_intent(message or "")
    lang = _detect_lang(message or "")
    return _answer_en(intent, v) if lang == "en" else _answer_fr(intent, v)
