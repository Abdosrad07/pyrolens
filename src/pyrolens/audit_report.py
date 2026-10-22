"""Rendu du rapport d'audit (Markdown + JSON d'artefact pour le web)."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import FileAudit


def build_audit_summary(audits: list[FileAudit], data_origin: str,
                        gaps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cat_counts: Counter = Counter()
    class_counts: Counter = Counter()
    files = []
    satellites: set[str] = set()
    versions: set[str] = set()
    frp_all: list[float] = []
    confidence: Counter = Counter()
    volumes_month: Counter = Counter()
    volumes_day: Counter = Counter()
    missing_by_column: Counter = Counter()

    for a in audits:
        for an in a.anomalies:
            cat_counts[an.category] += 1
            class_counts[an.classification] += 1
            if an.category == "missing_value":
                missing_by_column[an.column] += 1
        satellites |= a.satellites
        versions |= a.versions
        frp_all.extend(a.frp_values)
        confidence.update(a.confidence_values)
        volumes_month.update(a.volumes_by_month)
        volumes_day.update(a.volumes_by_day)
        files.append(
            {
                "file": a.path.name,
                "sensor": a.sensor,
                "header": a.header,
                "n_records": a.n_records,
                "n_rows_analysable": a.counts["rows_analysable"],
                "n_rows_excluded": a.counts["rows_excluded"],
                "n_rows_outside_emprise": a.counts["rows_outside_emprise"],
                "n_anomalies": len(a.anomalies),
                "n_duplicate_rows": a.counts["duplicate_rows"],
                "n_duplicate_keys": a.counts["duplicate_keys"],
                "date_min": min(a.dates).isoformat() if a.dates else None,
                "date_max": max(a.dates).isoformat() if a.dates else None,
            }
        )

    row_accounting = {
        "lignes_bien_formees": sum(a.n_records for a in audits),
        "valides_analysables": sum(a.counts["rows_analysable"] for a in audits),
        "hors_emprise_conservées": sum(a.counts["rows_outside_emprise"] for a in audits),
        "exclues_non_interprétables": sum(a.counts["rows_excluded"] for a in audits),
        "lignes_mal_formées": sum(
            1 for a in audits for an in a.anomalies if an.category == "malformed_row"
        ),
    }

    frp_stats = None
    if frp_all:
        frp_stats = {
            "n": len(frp_all),
            "min": round(min(frp_all), 3),
            "max": round(max(frp_all), 3),
            "mean": round(sum(frp_all) / len(frp_all), 3),
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_origin": data_origin,
        "n_files": len(audits),
        "files": files,
        "anomalies_by_category": dict(cat_counts.most_common()),
        "rows_by_classification": dict(class_counts),
        "row_accounting": row_accounting,
        "missing_values_by_column": dict(missing_by_column.most_common()),
        "satellites": sorted(satellites),
        "versions": sorted(versions),
        "frp_stats": frp_stats,
        "confidence_distribution_by_sensor": dict(confidence.most_common()),
        "volumes_by_month": dict(sorted(volumes_month.items())),
        "n_distinct_days_with_records": len(volumes_day),
        "temporal_gaps": {
            "n_entries": len(gaps or []),
            "entries": (gaps or [])[:200],
        },
        "interpretation_warning": (
            "Les trous temporels listent des jours SANS ENREGISTREMENT pour un capteur. "
            "Ils ne signifient pas absence de feu, et sans produit de couverture/nuages "
            "l'observabilité reste inconnue."
        ),
    }


def write_audit_markdown(summary: dict[str, Any], out_path: Path) -> Path:
    lines: list[str] = []
    add = lines.append
    add("# Rapport d'audit des données — PyroLens phase 2")
    add("")
    add(f"- Généré le : {summary['generated_at']}")
    add(f"- **Origine des données** : `{summary['data_origin']}`")
    if summary["data_origin"] == "synthetic_fixture":
        add("")
        add("> **AVERTISSEMENT** — fichiers d'exécution **synthétiques de démonstration**.")
        add("> Les données NASA réelles sont bloquées (Earthdata Login / FIRMS MAP_KEY absents) ;")
        add("> aucun de ces chiffres ne constitue une mesure du Cameroun.")
    add(f"- Fichiers audités : {summary['n_files']}")
    add(f"- Satellites présents : {', '.join(summary['satellites']) or 'aucun'}")
    add(f"- Versions de traitement présentes : {', '.join(summary['versions']) or 'aucune'}")
    add("")
    add("## 1. Fichiers et structure")
    add("")
    add("| fichier | capteur | lignes | analysables | exclues | hors emprise | anomalies | période |")
    add("|---|---|---:|---:|---:|---:|---:|---|")
    for f in summary["files"]:
        period = f"{f['date_min']} → {f['date_max']}" if f["date_min"] else "—"
        add(
            f"| {f['file']} | {f['sensor']} | {f['n_records']} | {f['n_rows_analysable']} | "
            f"{f['n_rows_excluded']} | {f['n_rows_outside_emprise']} | {f['n_anomalies']} | {period} |"
        )
    add("")
    add("## 2. Anomalies par catégorie")
    add("")
    add("| catégorie | occurrences | interprétation |")
    add("|---|---:|---|")
    interpretations = {
        "malformed_row": "nombre de champs ≠ nombre de colonnes (ligne conservée brute)",
        "invalid_latitude": "latitude non numérique ou hors plage — **jamais corrigée**",
        "invalid_longitude": "longitude non numérique ou hors plage — **jamais corrigée**",
        "invalid_date": "date d'acquisition non interprétable",
        "invalid_time": "heure HHMM invalide",
        "invalid_frp": "FRP non numérique ou négative",
        "invalid_confidence": "confiance hors sémantique du capteur (aucune conversion d'échelle)",
        "missing_value": "valeur obligatoire manquante",
        "outside_emprise": "hors emprise documentée (bbox/polygone) — ligne valide, hors zone d'étude",
        "duplicate_row": "ligne strictement identique",
        "duplicate_key": "même clé (lat, lon, date, heure, satellite)",
        "missing_required_column": "colonne obligatoire absente de l'en-tête",
        "duplicate_column": "colonnes dupliquées après normalisation",
    }
    for cat, count in summary["anomalies_by_category"].items():
        add(f"| `{cat}` | {count} | {interpretations.get(cat, '—')} |")
    if not summary["anomalies_by_category"]:
        add("| — | 0 | aucune anomalie détectée |")
    add("")
    add("## 3. Classification des lignes")
    add("")
    add("Comptage des lignes (aucune ligne n'est réécrite) :")
    add("")
    add("| rubrique | nombre |")
    add("|---|---:|")
    for label, key in (
        ("lignes bien formées (lues)", "lignes_bien_formées"),
        ("**valides — analysables** (dans l'emprise, sans anomalie bloquante)", "valides_analysables"),
        ("hors emprise — conservées, hors périmètre d'étude", "hors_emprise_conservées"),
        ("exclues — valeurs non interprétables (non corrigées)", "exclues_non_interprétables"),
        ("lignes mal formées (champs ≠ colonnes)", "lignes_mal_formées"),
    ):
        add(f"| {label} | {summary.get('row_accounting', {}).get(key, 0)} |")
    add("")
    add("Classification des **anomalies enregistrées** (fichiers CSV détaillés) :")
    add("")
    add("| classe | anomalies |")
    add("|---|---:|")
    for cls in ("valid", "ambiguous", "reconstructed", "excluded"):
        add(f"| {cls} | {summary['rows_by_classification'].get(cls, 0)} |")
    add("")
    add("Les lignes hors emprise sont comptées comme anomalies *ambiguës* : elles sont "
        "conservées et tracées (numéro de ligne + motif) mais exclues des ensembles de "
        "comparaison par conception, car l'étude porte sur le polygon du pays.")
    add("")
    add("Aucune reconstruction automatique n'a été appliquée : la table de règles de "
        "reconstruction est vide dans `config/pipeline.yaml` (toute reconstruction doit "
        "être démontrable et déclarée).")
    add("")
    add("## 4. Valeurs manquantes par colonne")
    add("")
    if summary["missing_values_by_column"]:
        add("| colonne | occurrences |")
        add("|---|---:|")
        for col, count in summary["missing_values_by_column"].items():
            add(f"| `{col}` | {count} |")
    else:
        add("Aucune valeur manquante détectée sur les colonnes obligatoires.")
    add("")
    add("## 5. FRP et confiance")
    add("")
    if summary["frp_stats"]:
        s = summary["frp_stats"]
        add(f"- FRP (MW) sur {s['n']} valeurs : min={s['min']}, max={s['max']}, moyenne={s['mean']}.")
    else:
        add("- FRP : aucune valeur exploitable.")
    add("- Distribution de confiance **par capteur, sans mise en commun des échelles** :")
    for key, count in summary["confidence_distribution_by_sensor"].items():
        add(f"  - `{key}` : {count}")
    add("")
    add("## 6. Volumes et trous temporels")
    add("")
    add(f"- Jours avec au moins un enregistrement : {summary['n_distinct_days_with_records']}")
    add(f"- Entrées de trous temporels : {summary['temporal_gaps']['n_entries']}")
    add("")
    add("> " + summary["interpretation_warning"])
    add("")
    if summary["temporal_gaps"]["entries"]:
        add("<details><summary>Jours sans enregistrement (extrait, 200 premières entrées)</summary>")
        add("")
        add("| capteur | date | interprétation |")
        add("|---|---|---|")
        for g in summary["temporal_gaps"]["entries"][:60]:
            add(f"| {g['sensor']} | {g['date']} | {g['interpretation']} |")
        add("")
        add("</details>")
        add("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def write_audit_artifact(summary: dict[str, Any], artifacts_dir: Path) -> Path:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    target = artifacts_dir / "audit.json"
    target.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return target
