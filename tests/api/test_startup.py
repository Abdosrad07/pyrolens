"""Démarrage du service : lifespan, santé, document OpenAPI, uvicorn réel."""

from __future__ import annotations

import socket
import threading
import time

import httpx


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["project_version"]
    assert payload["data_origin"] == "nasa_firms"


def test_root_points_to_documentation(client):
    payload = client.get("/").json()
    assert payload["docs"] == "/api/v1/docs"
    assert payload["openapi"] == "/api/v1/openapi.json"


def test_openapi_document_is_complete(client):
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for expected in (
        "/api/v1/health",
        "/api/v1/meta",
        "/api/v1/catalog",
        "/api/v1/catalog/{dataset_id}",
        "/api/v1/audit/summary",
        "/api/v1/summary",
        "/api/v1/series/jaccard",
        "/api/v1/series/divergence",
        "/api/v1/spatial",
        "/api/v1/observability",
        "/api/v1/report",
        "/api/v1/export",
        "/api/v1/datasets/validate",
        "/api/v1/experiments",
        "/api/v1/experiments/{job_id}",
        "/api/v1/experiments/{job_id}/result",
    ):
        assert expected in paths, f"chemin manquant dans OpenAPI : {expected}"
    assert client.get("/api/v1/docs").status_code == 200


def test_uvicorn_starts_and_serves_health():
    """Test de démarrage du vrai serveur (uvicorn) sur un port libre, puis arrêt propre."""
    from api.app import create_app
    from api.settings import Settings

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    import uvicorn

    server = uvicorn.Server(uvicorn.Config(create_app(Settings()), host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 20
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                response = httpx.get(f"http://127.0.0.1:{port}/api/v1/health", timeout=2.0)
                assert response.status_code == 200
                assert response.json()["status"] == "ok"
                break
            except httpx.HTTPError as exc:  # serveur pas encore prêt
                last_error = exc
                time.sleep(0.2)
        else:
            raise AssertionError(f"le service n'a jamais répondu : {last_error}")
    finally:
        server.should_exit = True
        thread.join(timeout=15)
    assert not thread.is_alive()
