"""Rapport scientifique (Markdown + DOCX) : chiffres calculés vs références v0.3."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_artifacts(artifacts_dir: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, key in (
        ("audit.json", "audit"),
        ("baselines.json", "baselines"),
        ("observability.json", "observability"),
        ("inventory.json", "inventory"),
        ("execution.json", "execution"),
    ):
        path = artifacts_dir / name
        if path.exists():
            try:
                out[key] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                out[key] = None
    return out


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def build_report_md(artifacts: dict[str, Any], refs_present: bool, inv_present: bool) -> str:
    audit = artifacts.get("audit") or {}
    baselines = artifacts.get("baselines") or {}
    obs = artifacts.get("observability") or {}
    execution = artifacts.get("execution") or {}
    origin = audit.get("data_origin") or execution.get("data_origin") or "non déterminé"

    lines: list[str] = []
    add = lines.append
    add("# PyroLens — Rapport scientifique de la phase 2")
    add("")
    add(f"- Généré le : {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    add(f"- Origine des données analysées : `{origin}`")
    add(f"- Période cible : {execution.get('period_start', '2013-01-01')} → {execution.get('period_end', '2020-12-31')}")
    add("")
    if origin == "synthetic_fixture":
        add("## 0. Avertissement d'origine des données")
        add("")
        add("Les données NASA réelles (Earthdata Login et FIRMS MAP_KEY) **n'ont pas pu être "
            "acquises dans cet environnement** (blocages HTTP documentés §10). Les métriques de "
            "ce rapport sont calculées sur un **échantillon synthétique de démonstration** "
            "(`data_origin = synthetic_fixture`) : elles valident le pipeline, elles **ne sont "
            "pas des mesures du Cameroun**.")
        add("")
    add("## 1. Statut des étapes")
    add("")
    add("| étape | statut | preuve |")
    add("|---|---|---|")
    for row in execution.get("steps", []):
        add(f"| {row['step']} | {row['status']} | {row['detail']} |")
    add("")
    add("## 2. Origine et provenance")
    add("")
    add(f"- Inventaire produit/période : {'voir docs/data_inventory.md' if inv_present else 'non généré'}")
    add(f"- Références bibliographiques consultées : {'voir docs/references.md' if refs_present else 'non générées'}")
    if execution.get("manifest"):
        add(f"- Manifest de téléchargement/provenance : `{execution['manifest']}`")
    add("- Sommes de contrôle SHA-256 : enregistrées dans `data/manifests/` pour tout fichier acquis.")
    add("")

    add("## 3. Audit des données")
    add("")
    if audit:
        add(f"- Fichiers audités : {audit.get('n_files')}")
        add(f"- Satellites : {', '.join(audit.get('satellites', []))}")
        add(f"- Anomalies totales : {sum(audit.get('anomalies_by_category', {}).values())}")
        add(f"- Jours avec enregistrements : {audit.get('n_distinct_days_with_records')}")
        add("")
        add("| catégorie | occurrences |")
        add("|---|---:|")
        for cat, count in list(audit.get("anomalies_by_category", {}).items())[:15]:
            add(f"| {cat} | {count} |")
        add("")
        add("> " + str(audit.get("interpretation_warning", "")))
    else:
        add("_Audit non exécuté._")
    add("")

    add("## 4. Baselines calculées")
    add("")
    if baselines:
        add(f"- Définition des clés : `{baselines.get('key_definitions', {}).get('window_1')}` "
            f"(fenêtre 1 j) ; `{baselines.get('key_definitions', {}).get('window_gt1')}` (W > 1)")
        add(f"- Configurations testées : grilles {baselines.get('grids_deg')}° × fenêtres "
            f"{baselines.get('window_days')} jours")
        add(f"- Configuration primaire affichée : {baselines.get('primary')}")
        add("")
        add("| paire | grille | fenêtre | \\|A\\| | \\|B\\| | intersection | union | Jaccard |")
        add("|---|---:|---:|---:|---:|---:|---:|---:|")
        for row in baselines.get("summary", []):
            add(
                f"| {row['pair']} | {row['grid_deg']} | {row['window_days']} j | {row['n_a']} | "
                f"{row['n_b']} | {row['intersection']} | {row['union']} | {row['jaccard']:.4f} |"
            )
        add("")
        add("> La configuration au Jaccard maximal **n'est pas** retenue : l'agrégation "
            "grossière augmente le recouvrement tout en masquant les divergences. "
            "Toutes les configurations sont publiées (`baselines/summary.csv`).")
        add("")
        add("### Divergences mensuelles (configuration primaire)")
        add("")
        add("| paire | mois | A seul | B seul | commune |")
        add("|---|---|---:|---:|---:|")
        for row in baselines.get("monthly", [])[:40]:
            add(f"| {row['pair']} | {row['month']} | {row['a_only']} | {row['b_only']} | {row['both']} |")
        add("")
        add("### Divergences régionales (terciles de latitude de la bbox — proxy documenté)")
        add("")
        add("| paire | région | A seul | B seul | commune |")
        add("|---|---|---:|---:|---:|")
        for row in baselines.get("regions", []):
            add(f"| {row['pair']} | {row['region']} | {row['a_only']} | {row['b_only']} | {row['both']} |")
    else:
        add("_Baselines non exécutées._")
    add("")

    add("## 5. Observabilité")
    add("")
    if obs:
        add(f"- Grille : {obs.get('grid_deg')}°")
        add(f"- Produits de couverture/nuages acquis : **{obs.get('coverage_products_acquired')}**")
        add("")
        for sensor, counter in obs.get("states", {}).items():
            parts = ", ".join(
                f"{obs.get('state_labels', {}).get(state, state)} = {count}"
                for state, count in counter.items()
            )
            add(f"- **{sensor}** : {parts}")
        add("")
        add("> " + str(obs.get("note", "")))
        add(">")
        add("> **Rappel d'interprétation** : une cellule/jour sans détection n'implique "
            "jamais l'absence de feu — seule une couverture d'observation documentée "
            "permettrait d'évoquer des conditions d'observation plausibles.")
    else:
        add("_Analyse d'observabilité non exécutée._")
    add("")

    add("## 6. Comparaison A — Terra / Aqua")
    add("")
    add("Voir tableau §4 (paire `terra__aqua`). Les deux capteurs partagent l'instrument, "
        "la résolution nominale 1 km et la famille de produit, mais diffèrent par l'heure "
        "de passage (~10 h 30 vs ~13 h 30 locales) : la comparaison journalière n'est donc "
        "pas une observation simultanée.")
    add("")
    add("## 7. Comparaison B — Aqua / VIIRS Suomi-NPP 375 m")
    add("")
    add("Voir tableau §4 (paire `aqua__viirs_snpp`). Différences à documenter avec les "
        "chiffres : résolution 1 km vs 375 m, géométrie de balayage (pixel scan/track "
        "variable), définition de champ (un pixel VIIRS ≠ un pixel MODIS), sémantique de "
        "confiance distincte (numérique 0-100 vs catégories low/nominal/high — non "
        "converties ici).")
    add("")
    add("## 8. Sensibilité des paramètres")
    add("")
    add("Grilles 0,10 / 0,25 / 0,50° et fenêtres 1 / 4 / 8 / 16 jours : intégralement "
        "publiées dans `baselines/summary.csv` et `baselines/jaccard_monthly.csv`, et "
        "visualisées dans `figures/jaccard_sensitivity.png`. Aucune fenêtre horaire n'est "
        "analysée : les champs disponibles (date + heure d'acquisition UTC par détection) "
        "ne documentent pas une couverture horaire interprétable par cellule.")
    add("")

    add("## 9. Approches d'harmonisation candidates")
    add("")
    from .harmonization import render_markdown

    lines.extend(render_markdown().splitlines())
    add("")

    add("## 10. Blocages et accès aux données")
    add("")
    for blocker in execution.get("blockers", []):
        add(f"- **{blocker['what']}** — {blocker['detail']} (statut HTTP {blocker.get('http_status')}, "
            f"action attendue : {blocker['action']})")
    if not execution.get("blockers"):
        add("- Aucun blocage enregistré.")
    add("")
    add("## 11. Valeurs de référence v0.3 (non recalculées)")
    add("")
    add("- Les statistiques de concordance de l'exploratoire v0.3 (grille 0,25°, fenêtres "
        "1 j / 8 j / 1 mois) **ne sont pas fournies dans cet environnement** : le dépôt est "
        "vide de résultats antérieurs. Elles ne sont donc **ni reprises ni recalculées** ici ; "
        "pour les comparer, fournir les CSV v0.3 (voir README §« Comparer avec v0.3 »).")
    add("- La tendance annoncée (recouvrement spatial croissant avec l'agrégation "
        "temporelle) reste **une observation exploratoire**, non une démonstration "
        "d'équivalence physique des capteurs ni la validation d'un algorithme "
        "d'harmonisation.")
    add("")
    add("## 12. Limites")
    add("")
    add("- Données d'exécution non réelles tant que les credentials ne sont pas fournis.")
    add("- Aucun produit de couverture/nuages acquis : l'état « absence de détection en "
        "conditions d'observation plausibles » n'est **jamais** attribué.")
    add("- Aucune conversion de confiance MODIS↔VIIRS, aucune calibration FRP constante.")
    add("- Découpage régional = terciles de latitude de la bbox (proxy), pas des "
        "limites administratives.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- DOCX
def md_to_docx(md_path: Path, docx_path: Path) -> Path:
    """Convertit le Markdown du rapport en DOCX (python-docx disponible)."""
    from docx import Document

    doc = Document()
    lines = Path(md_path).read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").replace(" ", "")) <= {"-", ":"}:
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            rows = [[c.strip() for c in row.strip("|").split("|")] for row in block]
            rows = [r for r in rows if not all(set(c) <= {"-", ":"} for c in r)]
            if rows:
                table = doc.add_table(rows=len(rows), cols=len(rows[0]))
                for ri, row in enumerate(rows):
                    for ci, cell in enumerate(row):
                        if ci < len(rows[ri]):
                            table.rows[ri].cells[ci].text = cell.replace("**", "").replace("\\", "")
            continue
        if stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)
        elif stripped.startswith("> "):
            p = doc.add_paragraph(stripped[2:].replace("**", ""))
            p.paragraph_format.left_indent = 24
        elif stripped.startswith(("- ", "* ")):
            doc.add_paragraph(stripped[2:].replace("**", ""), style="List Bullet")
        elif stripped.startswith("<") or stripped == "---":
            pass
        elif stripped:
            doc.add_paragraph(stripped.replace("**", "").replace("`", ""))
        i += 1
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx_path))
    return docx_path


def write_report(artifacts: dict[str, Any], reports_dir: Path,
                 refs_present: bool, inv_present: bool) -> dict[str, Any]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    md_path = reports_dir / "scientific_report.md"
    md_path.write_text(build_report_md(artifacts, refs_present, inv_present), encoding="utf-8")
    out: dict[str, Any] = {"markdown": str(md_path), "docx": None}
    try:
        docx_path = md_to_docx(md_path, reports_dir / "scientific_report.docx")
        out["docx"] = str(docx_path)
    except Exception as exc:  # noqa: BLE001
        out["docx_error"] = str(exc)

    # copie web
    artifacts_dir = reports_dir.parent / "web" / "public" / "artifacts"
    if artifacts_dir.exists():
        (artifacts_dir / "scientific_report.md").write_text(
            md_path.read_text(encoding="utf-8"), encoding="utf-8"
        )
    return out
