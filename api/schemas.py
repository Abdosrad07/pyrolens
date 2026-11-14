"""Schémas d'entrée/sortie de l'API (Pydantic v2).

Les réponses à lignes utilisent ``{"meta", "rows"}`` (contrat v2) ; les lignes
elles-mêmes sont des objets libres documentés champ par champ dans
``docs/api.md`` (les fichiers d'artefacts évoluent par ajout de champ).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Meta(BaseModel):
    """Métadonnées communes : horodatage de l'artefact et origine des données."""

    generated_at: str | None = Field(default=None, description="Horodatage ISO-8601 UTC de l'artefact source.")
    data_origin: str | None = Field(
        default=None,
        description="Origine des données : nasa_firms | synthetic_fixture | uploaded_file | custom_source.",
    )
    artifact: str | None = Field(default=None, description="Nom de l'artefact (jamais de chemin serveur).")
    filters: dict[str, Any] = Field(default_factory=dict, description="Filtres effectivement appliqués.")


class RowsResponse(BaseModel):
    meta: Meta
    rows: list[dict[str, Any]] = Field(default_factory=list)


class ZoneAnalysisRequest(BaseModel):
    """Demande d'analyse FIRMS sur une bbox arbitraire (VIIRS vs MODIS)."""

    model_config = ConfigDict(extra="forbid")

    bbox: list[float] = Field(
        description="[min_lon, min_lat, max_lon, max_lat] en degrés (WGS84).",
        min_length=4, max_length=4,
    )
    window: Literal["nrt", "archive"] = Field(
        default="nrt",
        description="Fenêtre : nrt (récent ~5 jours, FIRMS SP) | archive (non supporté par zone).",
    )
    grid_deg: float = Field(
        default=0.05, gt=0.0, le=1.0,
        description="Maille d'appariement en degrés (défaut 0.05 ≈ 5 km).",
    )


class ExperimentRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"pair": "terra__aqua", "grid_deg": 0.25, "window_days": 8, "source": "auto"},
                {"pair": "aqua__viirs_snpp", "grid_deg": 0.1, "window_days": 1, "source": "fixture"},
            ]
        },
    )

    pair: str = Field(description="Paire de capteurs : terra__aqua | aqua__viirs_snpp.")
    grid_deg: float = Field(description="Maille en degrés : 0.1 | 0.25 | 0.5 (valeurs de la configuration).")
    window_days: int = Field(ge=1, le=365, description="Fenêtre temporelle en jours : 1 | 4 | 8 | 16.")
    source: Literal["auto", "fixture", "raw"] = Field(
        default="auto",
        description="Source : auto (données réelles sinon fixture), fixture (synthétique), raw (FIRMS normalisées).",
    )


class JobView(BaseModel):
    job_id: str
    kind: str
    params: dict[str, Any]
    status: str = Field(description="queued | running | succeeded | failed")
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    progress: dict[str, Any] = Field(
        default_factory=dict,
        description="Avancement temps réel : {step, pct, detail, at} pendant l'exécution.",
    )
    links: dict[str, str] = Field(default_factory=dict)


class JobListView(BaseModel):
    count: int
    items: list[JobView]


class ValidationResponse(BaseModel):
    generated_at: str | None = None
    data_origin: str = "uploaded_file"
    dataset: dict[str, Any]
    counts: dict[str, Any]
    period: dict[str, Any]
    anomalies_by_category: dict[str, int]
    anomalies_sample: list[dict[str, Any]]
    software: str
    integrated: bool = False
    note: str


class ExperimentResultResponse(BaseModel):
    job_id: str
    kind: str
    params: dict[str, Any]
    status: str
    created_at: str
    result: dict[str, Any]
