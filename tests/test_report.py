"""Tests du rapport scientifique (Markdown + DOCX) et séparation calculé / référence."""

from __future__ import annotations

from pathlib import Path

from pyrolens.report import build_report_md, md_to_docx

ARTIFACTS = {
    "audit": {
        "generated_at": "2026-10-16T00:00:00+00:00",
        "data_origin": "synthetic_fixture",
        "n_files": 3,
        "satellites": ["Aqua", "N", "Terra"],
        "anomalies_by_category": {"outside_emprise": 5, "invalid_latitude": 1},
        "n_distinct_days_with_records": 120,
        "interpretation_warning": "warning textuelle",
        "row_accounting": {
            "lignes_bien_formees": 1000,
            "valides_analysables": 900,
            "hors_emprise_conservées": 90,
            "exclues_non_interprétables": 6,
            "lignes_mal_formées": 4,
        },
        "rows_by_classification": {"ambiguous": 95, "excluded": 6},
        "files": [],
        "missing_values_by_column": {},
        "frp_stats": {"n": 900, "min": 0.1, "max": 100.0, "mean": 12.5},
        "confidence_distribution_by_sensor": {"modis:72": 10, "viirs:high": 20},
        "volumes_by_month": {"modis|2019-01": 50},
        "temporal_gaps": {"n_entries": 0, "entries": []},
    },
    "baselines": {
        "key_definitions": {"window_1": "(cellule, date)", "window_gt1": "(cellule, fenêtre)"},
        "grids_deg": [0.25],
        "window_days": [1, 8],
        "primary": {"grid_deg": 0.25, "window_days": 8},
        "summary": [
            {"pair": "terra__aqua", "grid_deg": 0.25, "window_days": 8, "n_a": 100, "n_b": 120,
             "intersection": 40, "union": 180, "jaccard": 0.2222}
        ],
        "monthly": [{"pair": "terra__aqua", "month": "2019-01", "a_only": 10, "b_only": 12, "both": 20}],
        "regions": [{"pair": "terra__aqua", "region": "sud", "a_only": 5, "b_only": 6, "both": 10}],
        "daily": [],
        "jaccard_monthly": [],
    },
    "observability": {
        "grid_deg": 0.25,
        "coverage_products_acquired": False,
        "states": {"terra": {"detection_observed": 10, "unknown_observability": 20}},
        "state_labels": {
            "detection_observed": "détection observée",
            "unknown_observability": "absence d'observation ou observabilité inconnue",
        },
        "note": "note d'observabilité",
    },
    "execution": {
        "period_start": "2013-01-01",
        "period_end": "2020-12-31",
        "data_origin": "synthetic_fixture",
        "manifest": "data/manifests/downloads.json",
        "steps": [{"step": "audit", "status": "ok", "detail": "3 fichiers"}],
        "blockers": [
            {"what": "Archives standard", "detail": "redirection URS", "http_status": 302,
             "action": "fournir EARTHDATA_USER"}
        ],
    },
}


def test_report_distinguishes_computed_vs_reference():
    md = build_report_md(dict(ARTIFACTS), refs_present=True, inv_present=True)
    assert "synthetic_fixture" in md
    assert "Valeurs de référence v0.3" in md
    assert "non recalculées" in md or "non recalculée" in md
    assert "0.2222" in md                     # chiffre réellement calculé présent
    assert "Earthdata" in md                  # blocage documenté
    assert "absence de feu" in md            # mémorandum d'interprétation
    assert "terra__aqua" in md


def test_report_without_artifacts_does_not_crash():
    md = build_report_md({}, refs_present=False, inv_present=False)
    assert "_Audit non exécuté._" in md
    assert "_Baselines non exécutées._" in md


def test_docx_generated(tmp_path):
    md_path = tmp_path / "report.md"
    md_path.write_text(
        "# Titre\n\n## Section\n\n- puce 1\n- puce 2\n\n> note\n\n"
        "| a | b |\n|---|---|\n| 1 | 2 |\n",
        encoding="utf-8",
    )
    docx_path = md_to_docx(md_path, tmp_path / "report.docx")
    assert docx_path.exists() and docx_path.stat().st_size > 0
    from docx import Document

    doc = Document(str(docx_path))
    assert doc.paragraphs[0].text == "Titre"
    assert any(p.style.name.startswith("List") for p in doc.paragraphs)
    assert len(doc.tables) == 1
