"""Fixtures des tests d'intégration API.

Deux applications sont testées :
- ``client`` : artefacts réels du dépôt (origine `nasa_firms`) ;
- ``fixture_client`` : source = échantillon **synthétique** généré ici
  (graine déterministe, origine `synthetic_fixture`), pour les expériences.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.settings import Settings

from pyrolens.config import PROJECT_ROOT
from pyrolens.fixture import write_fixture

ARTIFACTS_DIR = PROJECT_ROOT / "web" / "public" / "artifacts"


@pytest.fixture(scope="session")
def client() -> TestClient:
    app = create_app(Settings())
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def fixture_dir(tmp_path_factory) -> "Path":  # type: ignore[valid-type]
    directory = tmp_path_factory.mktemp("fixture")
    write_fixture(directory, date(2019, 1, 1), date(2019, 3, 31), 20260101)
    return directory


@pytest.fixture(scope="session")
def fixture_client(fixture_dir) -> TestClient:
    experiments_dir = fixture_dir.parent / "experiments"
    app = create_app(Settings(source_dir=fixture_dir, experiments_dir=experiments_dir))
    with TestClient(app) as test_client:
        yield test_client


def wait_for_job(client: TestClient, job_id: str, timeout_s: float = 120.0) -> dict:
    """Attend la fin d'une tâche et retourne son objet job."""
    import time

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        view = client.get(f"/api/v1/experiments/{job_id}").json()
        if view["status"] in ("succeeded", "failed"):
            return view
        time.sleep(0.2)
    raise AssertionError(f"la tâche {job_id} n'est pas terminée en {timeout_s}s")


@pytest.fixture
def wait_job():
    """Fixture exposant l'attente de fin de tâche aux tests."""

    def _wait(client: TestClient, job_id: str, timeout_s: float = 120.0) -> dict:
        return wait_for_job(client, job_id, timeout_s)

    return _wait
