"""Tests des erreurs et de la sécurité contractuelle (pas de pile, pas de chemin, pas d'écriture)."""

from __future__ import annotations


def test_unknown_route_is_enveloped_404(client):
    response = client.get("/api/v1/inconnu")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "404"
    assert isinstance(payload["error"]["message"], str)


def test_wrong_method_is_enveloped_405(client):
    response = client.delete("/api/v1/summary")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "405"


def test_error_messages_leak_no_path_nor_stack(client):
    for url in ("/api/v1/inconnu", "/api/v1/summary?pair=inconnu", "/api/v1/experiments/zzz"):
        response = client.get(url)
        assert "Traceback" not in response.text
        assert str(__import__("pyrolens.config", fromlist=["PROJECT_ROOT"]).PROJECT_ROOT) not in response.text


def test_no_write_endpoints_exist(client):
    """Contrat v2 : lecture seule ; seules les expériences/valisations POST sont admises."""
    openapi = client.get("/api/v1/openapi.json").json()
    for path, methods in openapi["paths"].items():
        for method in methods:
            assert method in ("get", "post"), f"méthode interdite {method} sur {path}"
            if method == "post":
                assert path in ("/api/v1/experiments", "/api/v1/datasets/validate", "/api/v1/firms/analyze", "/api/v1/firms/history", "/api/v1/predict", "/api/v1/chat")


def test_responses_carry_data_origin_and_no_secret(client):
    for url in ("/api/v1/meta", "/api/v1/summary", "/api/v1/observability"):
        body = client.get(url).text
        assert "FIRMS_MAP_KEY=" not in body
        assert "EARTHDATA_PASSWORD" not in body


def test_no_filter_interprets_absence(client):
    """Aucun paramètre ne doit permettre d'interpréter une absence de détection."""
    openapi = client.get("/api/v1/openapi.json").json()
    forbidden = {"fire_absent", "no_detection", "without_fire"}
    for path, methods in openapi["paths"].items():
        for method, spec in methods.items():
            names = {p["name"] for p in spec.get("parameters", [])}
            assert not (names & forbidden), f"paramètre interdit sur {method.upper()} {path}"


def test_published_artifacts_contain_no_local_path():
    """Artefacts web + manifests publiés : jamais de chemin absolu local (dépôt public)."""
    from pyrolens.config import PROJECT_ROOT

    roots = [PROJECT_ROOT / "web" / "public" / "artifacts", PROJECT_ROOT / "data" / "manifests"]
    checked = 0
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".json", ".md", ".txt", ".csv"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            checked += 1
            assert str(PROJECT_ROOT) not in text, f"chemin local du dépôt exposé : {path.name}"
            assert "/home/" not in text and "/root/" not in text, f"chemin absolu local : {path.name}"
    assert checked >= 10, "jeu d'artefacts publié introuvable"
