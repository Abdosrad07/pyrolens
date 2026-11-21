"""Tests d'intégration des endpoints /api/v1/early-warning/*.

Utilise ``fixture_client`` (source_dir = data/fixture du dépôt, origine
``synthetic_fixture``) : les trois endpoints doivent retourner des payloads
cohérents, filtrables et sans chemin local exposé.
"""

from __future__ import annotations

from pyrolens.config import PROJECT_ROOT


def _assert_no_local_path(text: str) -> None:
    assert str(PROJECT_ROOT) not in text, "chemin absolu local exposé"
    assert "/home/" not in text and "/root/" not in text


def test_summary_returns_counts_and_provenance(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["estimate_kind"] == "historical_backtest"
    assert payload["data_origin"] == "synthetic_fixture"
    assert payload["summary"]["n_cells_evaluated"] > 0
    assert set(payload["summary"]["by_severity"]) == {"NORMAL", "WATCH", "MODERATE", "HIGH"}
    assert payload["params"]["grid_deg"] == 0.25
    assert payload["period"]["recent_start"] <= payload["period"]["recent_end"]
    assert payload["source"]["n_files"] > 0
    assert len(payload["source"]["digest_sha256"]) == 64
    assert "historical" in payload["notes"] or "backtest" in payload["estimate_kind"]
    _assert_no_local_path(response.text)


def test_alerts_returns_sorted_list_with_required_fields(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/alerts")
    assert response.status_code == 200
    payload = response.json()
    alerts = payload["alerts"]
    assert len(alerts) == payload["summary"]["n_cells_evaluated"]
    for alert in alerts[:5]:
        for field in ("cell_id", "lon", "lat", "severity", "score", "recent", "baseline"):
            assert field in alert, field
        assert alert["severity"] in ("NORMAL", "WATCH", "MODERATE", "HIGH")
        assert 0.0 <= alert["score"] <= 1.0
        assert ":" in alert["cell_id"]
    # tri : sévérité décroissante puis score décroissant
    sev_rank = {"HIGH": 3, "MODERATE": 2, "WATCH": 1, "NORMAL": 0}
    keys = [(-sev_rank[a["severity"]], -a["score"]) for a in alerts]
    assert keys == sorted(keys)
    _assert_no_local_path(response.text)


def test_alerts_severity_filter(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/alerts", params={"severity": "WATCH"})
    assert response.status_code == 200
    payload = response.json()
    assert all(a["severity"] == "WATCH" for a in payload["alerts"])
    assert payload["filters"]["severity"] == "WATCH"
    assert payload["filters"]["matched"] >= len(payload["alerts"])


def test_alerts_min_score_filter(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/alerts", params={"min_score": 0.9})
    assert response.status_code == 200
    payload = response.json()
    assert all(a["score"] >= 0.9 for a in payload["alerts"])


def test_alerts_limit(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/alerts", params={"limit": 2})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["alerts"]) <= 2
    assert payload["filters"]["limit"] == 2


def test_cell_detail_returns_single_cell(fixture_client):
    # prendre une cellule réelle depuis la liste
    alerts = fixture_client.get("/api/v1/early-warning/alerts", params={"limit": 1}).json()["alerts"]
    assert alerts, "aucune alerte dans la fixture"
    cell_id = alerts[0]["cell_id"]
    response = fixture_client.get(f"/api/v1/early-warning/alerts/{cell_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["cell"]["cell_id"] == cell_id
    assert payload["cell"]["severity"] == alerts[0]["severity"]
    assert payload["estimate_kind"] == "historical_backtest"
    _assert_no_local_path(response.text)


def test_cell_detail_unknown_returns_404(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/alerts/0:0")
    assert response.status_code == 404
    assert "error" in response.json()


def test_cell_detail_invalid_format_returns_400(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/alerts/pasunecellule")
    assert response.status_code == 400


def test_invalid_severity_returns_400(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/summary", params={"severity": "bogus"})
    assert response.status_code == 400


def test_invalid_min_score_returns_400(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/summary", params={"min_score": 1.5})
    assert response.status_code == 400


def test_invalid_grid_deg_returns_400(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/summary", params={"grid_deg": 5.0})
    assert response.status_code == 400


def test_invalid_recent_days_returns_400(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/summary", params={"recent_days": 0})
    assert response.status_code == 400


def test_invalid_baseline_days_returns_400(fixture_client):
    # baseline_days < recent_days → 400
    response = fixture_client.get(
        "/api/v1/early-warning/summary",
        params={"recent_days": 30, "baseline_days": 10},
    )
    assert response.status_code == 400


def test_invalid_reference_date_returns_400(fixture_client):
    response = fixture_client.get(
        "/api/v1/early-warning/summary", params={"reference_date": "20/01/2020"}
    )
    assert response.status_code == 400


def test_unknown_query_param_returns_400(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/summary", params={"foo": "bar"})
    assert response.status_code == 400


def test_source_fixture_explicit(fixture_client):
    response = fixture_client.get("/api/v1/early-warning/summary", params={"source": "fixture"})
    assert response.status_code == 200
    assert response.json()["data_origin"] == "synthetic_fixture"


def test_source_auto_empty_dir_returns_409(tmp_path):
    """source=auto sur un répertoire sans CSV → 409 propre, jamais 500."""
    from fastapi.testclient import TestClient

    from api.app import create_app
    from api.settings import Settings

    empty = tmp_path / "empty_source"
    empty.mkdir()
    app = create_app(Settings(source_dir=empty, experiments_dir=tmp_path / "exp"))
    with TestClient(app) as client:
        response = client.get("/api/v1/early-warning/summary")
    assert response.status_code == 409
    assert "error" in response.json()


def test_cache_returns_consistent_results(fixture_client):
    """Deux appels identiques → même contenu scientifique (cache)."""
    r1 = fixture_client.get("/api/v1/early-warning/summary").json()
    r2 = fixture_client.get("/api/v1/early-warning/summary").json()
    assert r1["summary"] == r2["summary"]
    assert r1["period"] == r2["period"]
    assert r1["source"]["digest_sha256"] == r2["source"]["digest_sha256"]


def test_different_params_different_cache_keys(fixture_client):
    """Des paramètres différents → calcul différent (pas de collision de cache)."""
    r14 = fixture_client.get("/api/v1/early-warning/summary", params={"recent_days": 14}).json()
    r30 = fixture_client.get("/api/v1/early-warning/summary", params={"recent_days": 30}).json()
    assert r14["params"]["recent_days"] == 14
    assert r30["params"]["recent_days"] == 30
    # les périodes récentes diffèrent
    assert r14["period"]["recent_start"] != r30["period"]["recent_start"]


def test_openapi_documents_early_warning_endpoints(client):
    spec = client.get("/api/v1/openapi.json").json()
    paths = spec["paths"]
    assert "/api/v1/early-warning/summary" in paths
    assert "/api/v1/early-warning/alerts" in paths
    assert "/api/v1/early-warning/alerts/{cell_id}" in paths
    for path in ("/api/v1/early-warning/summary", "/api/v1/early-warning/alerts"):
        assert "get" in paths[path]
