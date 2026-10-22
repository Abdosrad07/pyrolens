"""Parcours de vérification de bout en bout sur un jeu de données explicitement identifié.

Jeu identifié n°1 — **échantillon synthétique** (`synthetic_fixture`, graine 20260101,
2019-01-01 → 2019-03-31, généré dans le test) : téléversement → validation → expérience →
comparaison avec un calcul indépendant du pipeline.
Jeu identifié n°2 — **artefacts réels** (`nasa_firms`, artefacts du dépôt) : catalogue →
summary → séries → spatial → export, avec équations vérifiées.
"""

from __future__ import annotations

from pathlib import Path

from pyrolens.audit import audit_file
from pyrolens.baselines import compare_sets, select_rows
from pyrolens.config import load_config
from pyrolens.grids import build_set


def test_e2e_fixture_upload_experiment(fixture_client, fixture_dir, wait_job):
    cfg = load_config()
    csvs = sorted(Path(fixture_dir).glob("*.csv"))
    assert csvs, "aucun CSV synthétique généré"

    # 1) Chaque fichier synthétique est téléversé et audité via l'API
    for csv_path in csvs:
        response = fixture_client.post(
            "/api/v1/datasets/validate",
            files={"file": (csv_path.name, csv_path.read_bytes(), "text/csv")},
        )
        assert response.status_code == 200, csv_path.name
        payload = response.json()
        assert payload["data_origin"] == "uploaded_file"
        assert payload["dataset"]["sensor"] in ("modis", "viirs")

    # 2) Expérience Terra↔Aqua sur la même source
    # source=auto : le client de test épingle source_dir sur l'échantillon généré ici
    body = {"pair": "terra__aqua", "grid_deg": 0.25, "window_days": 8, "source": "auto"}
    create = fixture_client.post("/api/v1/experiments", json=body)
    assert create.status_code == 202
    job_id = create.json()["job_id"]
    view = wait_job(fixture_client, job_id)
    assert view["status"] == "succeeded", view.get("error")
    full = fixture_client.get(f"/api/v1/experiments/{job_id}/result").json()["result"]
    result = full["result"]  # métriques ; la provenance reste sur le enveloppe complète

    # 3) Calcul indépendant (mêmes fonctions de bas du pipeline, hors API)
    geometry = None
    geo_file = cfg.path_of("raw") / "geo" / "ne_110m_admin_0_countries.geojson"
    if geo_file.exists():
        from pyrolens.emprise import load_region_polygon

        geometry = load_region_polygon(geo_file, "CMR")
    rows = []
    for csv_path in csvs:
        rows.extend(audit_file(csv_path, bbox=cfg.get("region.bbox"), geometry=geometry).rows)
    keys_a = build_set(select_rows(rows, cfg, "terra"), 0.25, 8)
    keys_b = build_set(select_rows(rows, cfg, "aqua"), 0.25, 8)
    expected = compare_sets("terra__aqua", keys_a, keys_b, 0.25, 8)

    assert result["n_a"] == expected.a_size
    assert result["n_b"] == expected.b_size
    assert result["intersection"] == expected.intersection
    assert result["union"] == expected.union
    assert result["jaccard"] == round(expected.jaccard, 6)
    assert full["data_origin"] == "synthetic_fixture"


def test_e2e_real_artifacts_full_walk(client):
    meta = client.get("/api/v1/meta").json()
    assert meta["data_origin"] == "nasa_firms"
    primary = meta["primary"]

    # Catalogue cohérent avec l'audit
    catalog = client.get("/api/v1/catalog").json()
    assert any(d["id"] == "firms_modis" and d["kind"] == "source" for d in catalog["datasets"])

    # Toutes les configurations publiées, équation Jaccard vérifiée sur chacune
    summary = client.get("/api/v1/summary").json()["rows"]
    assert len(summary) == 24
    for row in summary:
        assert row["union"] == row["n_a"] + row["n_b"] - row["intersection"]
        assert row["jaccard"] == round(row["intersection"] / row["union"], 6)

    # Séries mensuelles de la configuration primaire : bornes et tri
    series = client.get(
        "/api/v1/series/jaccard",
        params={"pair": "terra__aqua", "grid_deg": primary["grid_deg"], "window_days": primary["window_days"]},
    ).json()["rows"]
    assert series == sorted(series, key=lambda r: r["month"])
    assert all(0.0 <= r["jaccard"] <= 1.0 for r in series)

    # Spatial : compteurs cohérents avec la configuration primaire
    spatial = client.get(
        "/api/v1/spatial",
        params={"pair": "terra__aqua", "grid_deg": primary["grid_deg"], "window_days": primary["window_days"], "limit": 5000},
    ).json()
    assert spatial["total"] == len(spatial["rows"])
    assert all(row["a_count"] >= 0 and row["b_count"] >= 0 for row in spatial["rows"])

    # Export CSV : mêmes lignes que l'artefact
    csv_text = client.get("/api/v1/export", params={"dataset": "summary"}).text
    assert len(csv_text.strip().splitlines()) == 1 + 24
