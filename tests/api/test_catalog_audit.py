"""Tests catalogue, audit et exports : chiffres recoupés aux artefacts, aucun chemin local."""

from __future__ import annotations

import csv
import io
import json

from pyrolens.config import PROJECT_ROOT

ARTIFACTS = PROJECT_ROOT / "web" / "public" / "artifacts"


def _assert_no_local_path(payload_text: str) -> None:
    assert str(PROJECT_ROOT) not in payload_text, "chemin absolu local exposé"
    assert "/home/" not in payload_text and "/root/" not in payload_text


# ------------------------------------------------------------------ catalogue
def test_catalog_lists_source_and_derived_datasets(client):
    payload = client.get("/api/v1/catalog").json()
    ids = {d["id"]: d for d in payload["datasets"]}
    assert {"firms_modis", "firms_viirs", "audit", "baselines", "observability", "scientific_report"} <= set(ids)
    assert ids["firms_modis"]["kind"] == "source"
    assert ids["firms_modis"]["data_origin"] == "nasa_firms"
    assert ids["firms_modis"]["n_files"] > 0
    _assert_no_local_path(client.get("/api/v1/catalog").text)


def test_catalog_detail_matches_artifact(client):
    artifact = json.loads((ARTIFACTS / "audit.json").read_text(encoding="utf-8"))
    expected_files = sum(1 for f in artifact["files"] if f["sensor"] == "modis")
    payload = client.get("/api/v1/catalog/firms_modis").json()
    assert payload["dataset"]["n_files"] == expected_files
    assert all("file" in entry and "/" not in entry["file"] for entry in payload["dataset"]["files"])


def test_catalog_unknown_dataset_is_404(client):
    assert client.get("/api/v1/catalog/inconnu").status_code == 404


# ---------------------------------------------------------------------- audit
def test_audit_summary_matches_artifact(client):
    artifact = json.loads((ARTIFACTS / "audit.json").read_text(encoding="utf-8"))
    payload = client.get("/api/v1/audit/summary").json()
    assert payload["row_accounting"] == artifact["row_accounting"]
    assert payload["anomalies_by_category"] == artifact["anomalies_by_category"]
    assert payload["temporal_gaps"]["n_entries"] == artifact["temporal_gaps"]["n_entries"]
    # Comptabilité publiée (équation de l'audit, phase 2 §7) :
    # analysables + hors emprise + doublons de clé (3) = lignes bien formées
    accounting = payload["row_accounting"]
    total = accounting["valides_analysables"] + accounting["hors_emprise_conservées"] + 3
    assert total == accounting["lignes_bien_formees"]


def test_audit_detail_flag_controls_entries(client):
    without = client.get("/api/v1/audit/summary", params={"detail": 0}).json()
    with_detail = client.get("/api/v1/audit/summary", params={"detail": 1}).json()
    assert without["temporal_gaps"]["entries"] == []
    assert len(with_detail["temporal_gaps"]["entries"]) <= 200


# --------------------------------------------------------------------- exports
def test_export_summary_csv_matches_artifact_fields(client):
    artifact = json.loads((ARTIFACTS / "baselines.json").read_text(encoding="utf-8"))
    response = client.get("/api/v1/export", params={"dataset": "summary", "format": "csv"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    reader = csv.DictReader(io.StringIO(response.text))
    for field in ("pair", "grid_deg", "window_days", "intersection", "union", "jaccard"):
        assert field in reader.fieldnames
    rows = list(reader)
    assert len(rows) == len(artifact["summary"])


def test_export_json_rows_equal_csv_rows(client):
    csv_rows = list(csv.DictReader(io.StringIO(
        client.get("/api/v1/export", params={"dataset": "monthly", "pair": "terra__aqua"}).text
    )))
    json_rows = client.get(
        "/api/v1/export", params={"dataset": "monthly", "pair": "terra__aqua", "format": "json"}
    ).json()["rows"]
    assert len(csv_rows) == len(json_rows) > 0
    assert csv_rows[0]["month"] == json_rows[0]["month"]


def test_export_unknown_dataset_is_404(client):
    assert client.get("/api/v1/export", params={"dataset": "inconnu"}).status_code == 404


def test_export_without_pair_is_400(client):
    assert client.get("/api/v1/export", params={"dataset": "monthly"}).status_code == 400
