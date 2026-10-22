"""Tests des endpoints de lecture : meta, summary, séries, spatial, observabilité, rapport."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyrolens.config import PROJECT_ROOT

ARTIFACTS = PROJECT_ROOT / "web" / "public" / "artifacts"


# --------------------------------------------------------------------- meta
def test_meta_matches_artifact(client):
    artifact = json.loads((ARTIFACTS / "baselines.json").read_text(encoding="utf-8"))
    payload = client.get("/api/v1/meta").json()
    assert payload["generated_at"] == artifact["generated_at"]
    assert payload["data_origin"] == "nasa_firms"
    assert payload["primary"] == artifact["primary"]
    assert payload["grids_deg"] == artifact["grids_deg"]
    assert payload["window_days"] == artifact["window_days"]
    assert sorted(payload["pairs"]) == ["aqua__viirs_snpp", "terra__aqua"]
    assert payload["coverage_products_acquired"] is False


def test_unknown_query_parameter_is_400(client):
    response = client.get("/api/v1/summary", params={"bogus": "1"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "400"
    assert "bogus" in response.json()["error"]["message"]


def test_etag_returns_304(client):
    first = client.get("/api/v1/summary")
    assert first.status_code == 200
    etag = first.headers["etag"]
    second = client.get("/api/v1/summary", headers={"If-None-Match": etag})
    assert second.status_code == 304


# ------------------------------------------------------------------ summary
def test_summary_lists_all_24_configurations(client):
    artifact = json.loads((ARTIFACTS / "baselines.json").read_text(encoding="utf-8"))
    rows = client.get("/api/v1/summary").json()["rows"]
    assert len(rows) == len(artifact["summary"]) == 24


def test_summary_filters_and_jaccard_equation(client):
    rows = client.get(
        "/api/v1/summary",
        params={"pair": "terra__aqua", "grid_deg": 0.25, "window_days": 8},
    ).json()["rows"]
    assert len(rows) == 1
    row = rows[0]
    assert row["sensor_a"] == "terra" and row["sensor_b"] == "aqua"
    assert row["union"] == row["n_a"] + row["n_b"] - row["intersection"]
    assert row["jaccard"] == pytest.approx(row["intersection"] / row["union"], abs=1e-6)


def test_summary_unknown_pair_is_404(client):
    response = client.get("/api/v1/summary", params={"pair": "terra__viirs"})
    assert response.status_code == 404
    assert "terra__viirs" in response.json()["error"]["message"]


def test_summary_unknown_grid_is_404(client):
    assert client.get("/api/v1/summary", params={"grid_deg": 0.3}).status_code == 404


def test_summary_invalid_type_is_400(client):
    assert client.get("/api/v1/summary", params={"grid_deg": "abc"}).status_code == 400


# ------------------------------------------------------------------- séries
def test_jaccard_series_sorted_and_bounded(client):
    rows = client.get("/api/v1/series/jaccard", params={"pair": "terra__aqua"}).json()["rows"]
    assert rows, "série mensuelle vide"
    months = [row["month"] for row in rows]
    assert months == sorted(months)
    for row in rows:
        assert 0.0 <= row["jaccard"] <= 1.0
        assert row["a_only"] >= 0 and row["b_only"] >= 0 and row["both"] >= 0


def test_jaccard_series_requires_pair(client):
    response = client.get("/api/v1/series/jaccard")
    assert response.status_code == 400


@pytest.mark.parametrize("resolution", ["day", "month", "region"])
def test_divergence_resolutions(client, resolution):
    rows = client.get(
        "/api/v1/series/divergence", params={"pair": "terra__aqua", "resolution": resolution}
    ).json()["rows"]
    assert rows
    key = {"day": "date", "month": "month", "region": "region"}[resolution]
    assert all(key in row for row in rows)


def test_divergence_invalid_resolution_is_400(client):
    response = client.get(
        "/api/v1/series/divergence", params={"pair": "terra__aqua", "resolution": "hour"}
    )
    assert response.status_code == 400


# ------------------------------------------------------------------- spatial
def test_spatial_pagination(client):
    first = client.get("/api/v1/spatial", params={"pair": "terra__aqua", "limit": 5, "offset": 0}).json()
    second = client.get("/api/v1/spatial", params={"pair": "terra__aqua", "limit": 5, "offset": 5}).json()
    assert first["total"] == second["total"] > 0
    assert len(first["rows"]) == 5 and len(second["rows"]) == 5
    assert first["rows"] != second["rows"]
    assert {"cell_i", "cell_j", "lon", "lat", "a_count", "b_count"} <= set(first["rows"][0])


def test_spatial_unknown_config_is_404(client):
    response = client.get(
        "/api/v1/spatial", params={"pair": "terra__aqua", "grid_deg": 0.1, "window_days": 1}
    )
    assert response.status_code == 404


# -------------------------------------------------------------- observabilité
def test_observability_states_and_labels(client):
    payload = client.get("/api/v1/observability").json()
    assert payload["coverage_products_acquired"] is False
    assert set(payload["states"]) == {"terra", "aqua", "viirs_snpp"}
    assert "state_labels" in payload and "note" in payload
    # Politique éditoriale : l'avertissement existe et interdit l'affirmation d'absence de feu.
    assert "pas de feu" in payload["note"] and "jamais" in payload["note"]


def test_observability_wrong_grid_is_404(client):
    assert client.get("/api/v1/observability", params={"grid_deg": 0.5}).status_code == 404


# -------------------------------------------------------------------- rapport
def test_report_is_markdown(client):
    response = client.get("/api/v1/report")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.text.lstrip().startswith("#")
    assert len(response.text) > 1000
