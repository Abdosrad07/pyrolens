from fastapi.testclient import TestClient

from api.app import create_app
from api.settings import Settings


def test_demo_routes_receive_requests_without_query_validation_errors():
    with TestClient(create_app(Settings(demo=True))) as client:
        cases = (
            ("GET", "/api/v1/health", None),
            ("GET", "/api/v1/fire-risk", None),
            (
                "POST",
                "/api/v1/chat",
                {"messages": [{"role": "user", "content": "Explique VIIRS"}]},
            ),
            ("POST", "/api/v1/predict", {}),
            ("GET", "/api/v1/predict", None),
            ("GET", "/api/v1/experiments", None),
            ("GET", "/api/v1/fire-calendar/daily?limit=5", None),
            ("GET", "/api/v1/early-warning/summary", None),
            ("GET", "/api/v1/early-warning/alerts", None),
            ("GET", "/api/v1/baselines/summary", None),
            (
                "GET",
                "/api/v1/baselines/series/jaccard?pair=viirs-snpp__modis",
                None,
            ),
            (
                "GET",
                "/api/v1/baselines/spatial?pair=viirs-snpp__modis&limit=5",
                None,
            ),
        )
        for method, path, body in cases:
            response = client.request(method, path, json=body)
            assert response.status_code == 200, f"{method} {path}: {response.text}"

        alerts = client.get("/api/v1/early-warning/alerts").json()["items"]
        assert client.get(
            f"/api/v1/early-warning/alerts/{alerts[0]['cell_id']}"
        ).status_code == 200
        job_id = client.post("/api/v1/predict", json={}).json()["job_id"]
        assert client.get(f"/api/v1/predict/{job_id}").status_code == 200
