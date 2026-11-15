"""Tests de la whitelist POST (``PYROLENS_ALLOWED_POSTS`` / ``Settings.allowed_posts``)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import create_app
from api.settings import Settings, normalize_post_path


def _client(allowed: tuple[str, ...]) -> TestClient:
    return TestClient(create_app(Settings(allowed_posts=allowed)))


class TestNormalizePostPath:
    def test_variants(self):
        assert normalize_post_path("/api/v1/firms/analyze") == "firms/analyze"
        assert normalize_post_path("api/v1/firms/analyze") == "firms/analyze"
        assert normalize_post_path("firms/analyze") == "firms/analyze"
        assert normalize_post_path("/api/v1/chat") == "chat"
        assert normalize_post_path("/api/v1") == ""


class TestAllowedPosts:
    def test_empty_whitelist_allows_everything(self):
        client = _client(())
        assert client.post("/api/v1/chat", json={"message": "bonjour"}).status_code == 200

    def test_post_outside_whitelist_gets_403(self):
        client = _client(("chat", "firms/analyze", "firms/history"))
        for path in ("/api/v1/predict", "/api/v1/experiments", "/api/v1/datasets/validate"):
            response = client.post(path, json={})
            assert response.status_code == 403, path
            assert response.json()["error"]["code"] == "403"

    def test_post_inside_whitelist_passes(self):
        client = _client(("chat", "firms/analyze", "firms/history"))
        # /chat est dans la liste : la garde ne doit pas la bloquer (le corps
        # peut être invalide, mais jamais 403 de la garde).
        response = client.post("/api/v1/chat", json={"message": "bonjour"})
        assert response.status_code != 403

    def test_get_requests_unaffected(self):
        client = _client(("chat",))
        assert client.get("/api/v1/health").status_code == 200
