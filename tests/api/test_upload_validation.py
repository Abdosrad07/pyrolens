"""Tests de validation de fichiers téléversés (limites, anomalies, aucune intégration)."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.settings import Settings

VALID_HEADER = (
    "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,"
    "confidence,version,frp,daynight,type"
)
VALID_ROW = "7.3,13.6,320.1,1.2,1.1,2019-03-15,1030,Terra,80,6.1NRT,12.3,D,0"


def _csv_file(content: str, name: str = "upload.csv", content_type: str = "text/csv"):
    return {"file": (name, io.BytesIO(content.encode("utf-8")), content_type)}


def test_valid_upload_is_audited_not_integrated(client):
    response = client.post("/api/v1/datasets/validate", files=_csv_file(VALID_HEADER + "\n" + VALID_ROW + "\n"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_origin"] == "uploaded_file"
    assert payload["integrated"] is False
    assert payload["dataset"]["sensor"] == "modis"
    assert payload["counts"]["n_records"] == 1
    assert payload["period"]["start"] == "2019-03-15"
    assert "aucune correction" in payload["note"].lower() or "Aucune correction" in payload["note"]


def test_invalid_latitude_is_traced_never_corrected(client):
    bad = VALID_HEADER + "\n" + "999.0,12.4,320.1,1.2,1.1,2019-03-15,1030,Terra,80,6.1NRT,12.3,D,0\n"
    payload = client.post("/api/v1/datasets/validate", files=_csv_file(bad)).json()
    assert payload["anomalies_by_category"].get("invalid_latitude") == 1
    # Aucune correction : la valeur brute reste tracée telle quelle
    sample = [a for a in payload["anomalies_sample"] if a["category"] == "invalid_latitude"]
    assert sample and sample[0]["raw_value"] == "999.0"


def test_missing_required_column_is_400(client):
    response = client.post(
        "/api/v1/datasets/validate",
        files=_csv_file("foo,bar\n1,2\n", name="sans_colonnes.csv"),
    )
    assert response.status_code == 400
    assert "latitude" in response.json()["error"]["message"]


def test_empty_file_is_400(client):
    response = client.post("/api/v1/datasets/validate", files=_csv_file(""))
    assert response.status_code == 400


def test_non_csv_name_is_400(client):
    response = client.post("/api/v1/datasets/validate", files=_csv_file("x", name="upload.txt"))
    assert response.status_code == 400


def test_wrong_content_type_is_415(client):
    response = client.post(
        "/api/v1/datasets/validate",
        files=_csv_file(VALID_HEADER + "\n", name="upload.csv", content_type="application/pdf"),
    )
    assert response.status_code == 415


def test_oversized_upload_is_413():
    app = create_app(Settings(max_upload_bytes=1024))
    with TestClient(app) as small_client:
        payload = VALID_HEADER + "\n" + (VALID_ROW + "\n") * 100
        response = small_client.post("/api/v1/datasets/validate", files=_csv_file(payload))
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "413"


def test_response_contains_no_local_path(client):
    response = client.post("/api/v1/datasets/validate", files=_csv_file(VALID_HEADER + "\n" + VALID_ROW + "\n"))
    body = response.text
    assert "/tmp/" not in body
    assert "pyrolens-upload" not in body
