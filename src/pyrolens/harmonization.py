"""Catalogue des approches d'harmonisation candidates (POSTERIEUR aux audits et baselines).

Aucune approche n'est déclarée validée : chaque entrée porte ses conditions
d'échec et les tests qui restent à exécuter.
"""

from __future__ import annotations

from typing import Any

CANDIDATES: list[dict[str, Any]] = [
    {
        "id": "H1-representation",
        "category": "harmonisation de la représentation des données",
        "title": "Schéma commun de colonnes normalisées (sans conversion de sens)",
        "hypothesis": (
            "Une partie des écarts observés provient de différences de nommage, de formats "
            "de date/heure et d'unités explicites, pas de différences physiques."
        ),
        "inputs": "CSV FIRMS bruts des trois capteurs, en-têtes et métadonnées de version.",
        "method": (
            "Normalisation des noms de colonnes, formatage AAAA-MM-JJ + HHMM UTC, "
            "conservation des valeurs brutes de confiance et de FRP dans des colonnes distinctes."
        ),
        "criteria": (
            "Taux de lignes analysables avant/après ; zéro perte non expliquée ; "
            "aucune colonne de confiance fusionnée."
        ),
        "validation_data": "Échantillon de fichiers réels par capteur et par année.",
        "bias_risks": "Cacher des différences réelles derrière une normalisation trop agressive.",
        "failure_conditions": "Perte de lignes ou modification des valeurs brutes.",
        "tests_status": (
            "EXÉCUTÉ sur données réelles (audit du 18/10/2026, data_origin=nasa_firms) : "
            "4 460 288 lignes bien formées, 0 ligne malformée, 0 perte non expliquée, "
            "0 colonne de confiance fusionnée (audit.json)."
        ),
    },
    {
        "id": "H2-spatial",
        "category": "harmonisation spatiale",
        "title": "Agrégation sur grille commune avec aire de cellule explicite",
        "hypothesis": (
            "Le recouvrement mesuré dépend fortement de la taille de cellule ; une grille "
            "commune avec aire documentée rend les comparaisons interpretables."
        ),
        "inputs": "Détections lat/lon, grilles 0,10 / 0,25 / 0,50°, emprise polygonale.",
        "method": (
            "Appartenance de cellule par index entier d'origine -180/-90 ; publication de "
            "l'aire des cellules et de la densité de détections par aire."
        ),
        "criteria": (
            "Sensibilité du Jaccard à la maille ; stabilité des divergences régionales ; "
            "distribution spatiale des cellules actives."
        ),
        "validation_data": "Baselines Terra-Aqua et Aqua-VIIRS sur la période complète.",
        "bias_risks": "L'agrégation grossière augmente artificiellement le recouvrement.",
        "failure_conditions": "Écarts qui disparaissent avec la maille sans explication géophysique.",
        "tests_status": (
            "EXÉCUTÉ sur données réelles (baselines du 18/10/2026) : 24 configurations "
            "publiées intégralement, sensibilité de 0,102715 à 0,658829 selon la maille et "
            "la fenêtre (baselines/summary.csv)."
        ),
    },
    {
        "id": "H3-temporal",
        "category": "harmonisation temporelle",
        "title": "Fenêtres alignées (cellule, fenêtre) avec fenêtres multiples",
        "hypothesis": (
            "Les heures de passage différentes (Terra ~10h30, Aqua/S-NPP ~13h30 locales) "
            "rendent la simultanéité journalière trop stricte."
        ),
        "inputs": "Dates d'acquisition UTC, fenêtres 1 / 4 / 8 / 16 jours alignées sur l'epoch.",
        "method": (
            "Clés (cellule, fenêtre) ; comparaison des séries de Jaccard par fenêtre ; "
            "aucune fenêtre horaire tant que la documentation ne permet pas de l'interpréter."
        ),
        "criteria": (
            "Décroissance attendue des divergences avec l'agrégation, quantifiée, sans "
            "sélection de la configuration maximisant le Jaccard."
        ),
        "validation_data": "Séries journalière/mensuelle par paire et par configuration.",
        "bias_risks": "Masker des divergences réelles par agrégation temporelle.",
        "failure_conditions": "Écart qui croît avec la fenêtre (signe d'un biais de couverture).",
        "tests_status": (
            "EXÉCUTÉ sur données réelles (18/10/2026) : séries journalière et mensuelle "
            "par paire et par configuration (jaccard_monthly.csv, monthly_divergence.csv, "
            "daily_divergence.csv) ; croissance mécanique du recouvrement avec W quantifiée."
        ),
    },
    {
        "id": "H4-confidence",
        "category": "harmonisation de la confiance",
        "title": "Règles de sélection par classe, SANS échelle numérique commune",
        "hypothesis": (
            "Des seuils de sélection par classe (MODIS 0-100 / VIIRS low-nominal-high) "
            "produisent des ensembles comparables sans conversion numérique."
        ),
        "inputs": "Colonnes confidence brutes par capteur, FRP brut, daynight.",
        "method": (
            "Définition de sous-ensembles par classe native de chaque capteur, comparaison "
            "des métriques d'ensemble pour chaque combinaison de seuils."
        ),
        "criteria": "Stabilité du Jaccard entre combinaisons de seuils ; interprétabilité.",
        "validation_data": "Fichiers réels avec confiance complète ; idéalement références indépendantes.",
        "bias_risks": "Étalonner les seuils sur la métrique elle-même (sur-ajustement).",
        "failure_conditions": "Toute table de conversion numérique confiance→confiance.",
        "tests_status": (
            "NON EXÉCUTÉ — les confiances réelles des trois capteurs sont disponibles, mais "
            "aucune table de conversion n'est implémentée (par conception) et aucun jeu de "
            "référence indépendant n'est disponible (voir docs/phase2/decisions_to_validate.md, D5)."
        ),
    },
    {
        "id": "H5-frp",
        "category": "calibration éventuelle du FRP",
        "title": "Calibration du FRP conditionnée par la géométrie d'observation",
        "hypothesis": (
            "Les écarts de FRP MODIS-VIIRS dépendent de l'angle de vue, de la taille de "
            "pixel et de l'échelle d'agrégation (Li et al., 2018), pas d'un facteur constant."
        ),
        "inputs": "FRP brut, scan/track, angles de vue si disponibles, taille de pixel, échelle.",
        "method": (
            "Modèle de régression avec covariables géométriques, entraîné sur une période "
            "et évalué sur une période distincte (séparation temporelle stricte)."
        ),
        "criteria": "Erreur hors échantillon ; comparaison à la ligne de base constante (attendu : meilleure).",
        "validation_data": "FRP + géométrie d'observation ; idéalement référence indépendante (pyrométrie, GT).",
        "bias_risks": "Confoundement entre taille de feu et géométrie ; saturation I4 (VIIRS).",
        "failure_conditions": "Gain non significatif hors échantillon ou biais résiduel par angle de vue.",
        "tests_status": (
            "NON EXÉCUTÉ — le FRP réel est acquis, mais la géométrie d'observation "
            "(MOD03/MYD03) ne l'est pas : blocage Earthdata persistent "
            "(voir docs/phase2/decisions_to_validate.md, D4)."
        ),
    },
    {
        "id": "H6-external-validation",
        "category": "validation contre références indépendantes",
        "title": "Validation croisée par séparation géographique et temporelle",
        "hypothesis": (
            "Une méthode d'harmonisation n'est crédible que si elle est évaluée sur des "
            "observations non utilisées pour l'ajustement."
        ),
        "inputs": "Jeu de développement (années ou sous-régions) vs jeu d'évaluation.",
        "method": (
            "Split temporel (ex. 2013-2016 développement / 2017-2020 évaluation) et split "
            "sud/nord de l'emprise ; rapport des métriques sur les deux jeux."
        ),
        "criteria": "Écart développement/évaluation < seuil défini avant tout test.",
        "validation_data": "Données réelles multiannuelles ; références indépendantes si disponibles.",
        "bias_risks": "Fuite d'information entre jeux ; saisonnalité non représentée.",
        "failure_conditions": "Écart important entre jeux = méthode non généralisable.",
        "tests_status": (
            "NON EXÉCUTÉ — les données réelles multiannuelles sont acquises depuis le "
            "18/10/2026 ; le split développement/évaluation reste à exécuter "
            "(voir docs/phase2/implementation_plan.md, lot S4)."
        ),
    },
]


def render_markdown() -> str:
    # Le titre de section (## 9) est fourni par report.py pour garder une
    # numérotation unique dans le rapport ; ce module ne rend que le contenu.
    lines = [
        "> Statut : **aucune méthode n'est annoncée comme validée**. H1-H3 sont exécutés sur "
        "données réelles (18/10/2026) ; H4-H6 restent non exécutés (prérequis manquants, §10) — "
        "« exécuté » ≠ « validé » (docs/phase2/scientific_method.md §6).",
        "",
    ]
    for cand in CANDIDATES:
        lines.append(f"### {cand['id']} — {cand['title']}")
        lines.append(f"- **Catégorie** : {cand['category']}")
        for label, key in (
            ("Hypothèse", "hypothesis"),
            ("Variables d'entrée", "inputs"),
            ("Méthode", "method"),
            ("Critères d'évaluation", "criteria"),
            ("Données de validation nécessaires", "validation_data"),
            ("Risques de biais", "bias_risks"),
            ("Conditions d'échec", "failure_conditions"),
            ("Statut des tests", "tests_status"),
        ):
            lines.append(f"- **{label}** : {cand[key]}")
        lines.append("")
    return "\n".join(lines)
