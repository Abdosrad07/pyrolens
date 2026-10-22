"""Tests des expériences asynchrones : file, statuts, provenance, erreurs, jeton."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.settings import Settings

VALID_BODY = {"pair": "terra__aqua", "grid_deg": 0.25, "window_days": 8, "source": "fixture"}


def test_experiment_rejects_unknown_pair(fixture_client):
    response = fixture_client.post("/api/v1/experiments", json={"pair": "terra__viirs", "grid_deg": 0.25, "window_days": 8})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "400"


def test_experiment_rejects_unknown_grid(fixture_client):
    response = fixture_client.post("/api/v1/experiments", json={"pair": "terra__aqua", "grid_deg": 0.33, "window_days": 8})
    assert response.status_code == 400


def test_experiment_rejects_unknown_window(fixture_client):
    response = fixture_client.post("/api/v1/experiments", json={"pair": "terra__aqua", "grid_deg": 0.25, "window_days": 7})
    assert response.status_code == 400


def test_experiment_rejects_extra_field(fixture_client):
    response = fixture_client.post(
        "/api/v1/experiments",
        json={**VALID_BODY, "note": "interdit"},
    )
    assert response.status_code == 400


def test_experiment_runs_and_reports_provenance(fixture_client, fixture_dir, wait_job):
    create = fixture_client.post("/api/v1/experiments", json=VALID_BODY)
    assert create.status_code == 202
    assert create.headers["location"].startswith("/api/v1/experiments/")
    job_id = create.json()["job_id"]

    view = wait_job(fixture_client, job_id)
    assert view["status"] == "succeeded", view.get("error")
    assert view["params"] == VALID_BODY

    result = fixture_client.get(f"/api/v1/experiments/{job_id}/result").json()
    payload = result["result"]
    # Provenance complète et chaînable
    assert result["params"] == VALID_BODY
    assert payload["data_origin"] == "synthetic_fixture"
    assert payload["source"]["n_files"] > 0
    assert len(payload["source"]["digest_sha256"]) == 64
    assert payload["software"]["pipeline"].startswith("pyrolens")
    assert payload["started_at"] and payload["finished_at"]
    # Équation Jaccard et bornes
    assert payload["result"]["union"] == (
        payload["result"]["n_a"] + payload["result"]["n_b"] - payload["result"]["intersection"]
    )
    assert 0.0 <= payload["result"]["jaccard"] <= 1.0
    assert payload["result"]["monthly"]
    assert all(0.0 <= m["jaccard"] <= 1.0 for m in payload["result"]["monthly"])
    # Avertissement d'interprétation porté par le résultat
    assert "précision" in payload["warning"]


def test_experiment_result_persisted_on_disk(fixture_client, wait_job):
    create = fixture_client.post("/api/v1/experiments", json=VALID_BODY)
    job_id = create.json()["job_id"]
    wait_job(fixture_client, job_id)
    # Le gestionnaire persiste dans PYROLENS_EXPERIMENTS_DIR
    experiments_dir = Path(fixture_client.app.state.settings.experiments_dir)
    saved = experiments_dir / f"{job_id}.json"
    assert saved.exists()
    payload = json.loads(saved.read_text(encoding="utf-8"))
    assert payload["status"] == "succeeded"
    assert payload["job_id"] == job_id


def test_unknown_job_is_404(fixture_client):
    assert fixture_client.get("/api/v1/experiments/deadbeef0000").status_code == 404
    assert fixture_client.get("/api/v1/experiments/../../etc/passwd").status_code == 404


def test_list_experiments_contains_created_job(fixture_client, wait_job):
    create = fixture_client.post("/api/v1/experiments", json=VALID_BODY)
    job_id = create.json()["job_id"]
    wait_job(fixture_client, job_id)
    listing = fixture_client.get("/api/v1/experiments").json()
    assert listing["count"] >= 1
    assert job_id in {item["job_id"] for item in listing["items"]}


def test_result_before_completion_is_409_or_absent(fixture_client):
    """Une tâche inconnue est 404 ; l'endpoint résultat n'expose jamais de pile."""
    response = fixture_client.get("/api/v1/experiments/000000000000/result")
    assert response.status_code == 404
    assert "Traceback" not in response.text


def test_failed_job_returns_clean_error(fixture_client, monkeypatch, wait_job):
    import api.routers.experiments as experiments_module

    def _boom(*args, **kwargs):
        raise RuntimeError("détail interne ne doit pas fuiter")

    monkeypatch.setattr(experiments_module, "run_harmonization_experiment", _boom)
    create = fixture_client.post("/api/v1/experiments", json=VALID_BODY)
    job_id = create.json()["job_id"]
    view = wait_job(fixture_client, job_id)
    assert view["status"] == "failed"
    assert "ne doit pas fuiter" not in (view["error"] or "")
    assert "Traceback" not in json.dumps(view)


def test_jobs_disabled_returns_403(fixture_dir):
    app = create_app(Settings(source_dir=fixture_dir, jobs_enabled=False))
    with TestClient(app) as disabled:
        response = disabled.post("/api/v1/experiments", json=VALID_BODY)
        assert response.status_code == 403


def test_api_token_protects_write_endpoints(fixture_dir):
    app = create_app(Settings(source_dir=fixture_dir, api_token="jeton-de-test"))
    with TestClient(app) as guarded:
        # Lecture libre
        assert guarded.get("/api/v1/health").status_code == 200
        # Écriture refusée sans jeton
        denied = guarded.post("/api/v1/experiments", json=VALID_BODY)
        assert denied.status_code == 401
        # Écriture acceptée avec le bon jeton
        allowed = guarded.post(
            "/api/v1/experiments", json=VALID_BODY, headers={"Authorization": "Bearer jeton-de-test"}
        )
        assert allowed.status_code == 202
        # Mauvais jeton
        wrong = guarded.post(
            "/api/v1/experiments", json=VALID_BODY, headers={"Authorization": "Bearer faux"}
        )
        assert wrong.status_code == 401
