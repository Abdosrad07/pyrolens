"""Modèles d'expérience d'harmonisation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from api.models.base import BaseModel, TimestampMixin


class ExperimentStatus(str):
    """États du cycle de vie d'une expérience."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentConfiguration(BaseModel, TimestampMixin):
    """Paramètres d'une expérience d'harmonisation."""

    config_id: str = Field(description="Identifiant technique unique de la configuration.")
    pair: str = Field(
        description="Paire de capteurs : terra__aqua | aqua__viirs_snpp."
    )
    grid_deg: float = Field(
        description="Maille spatiale en degrés : 0.1 | 0.25 | 0.50 (ou valeur personnalisée)."
    )
    window_days: int = Field(
        description="Fenêtre temporelle en jours : 1 | 4 | 8 | 16 (ou valeur personnalisée)."
    )
    period_start: str | None = Field(
        default=None, description="Date de début de la période d'analyse (ISO-8601 UTC)."
    )
    period_end: str | None = Field(
        default=None, description="Date de fin de la période d'analyse (ISO-8601 UTC)."
    )
    source: Literal["auto", "fixture", "raw"] = Field(
        default="auto",
        description="Source des données : auto | fixture | raw.",
    )
    key_definition: str = Field(
        description="Définition de la clé d'ensemble : (cellule,date) ou (cellule,fenêtre)."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class HarmonizationExperiment(BaseModel, TimestampMixin):
    """Une expérience d'harmonisation exécutée."""

    experiment_id: str = Field(description="Identifiant technique unique de l'expérience.")
    config_id: str = Field(description="Identifiant de la configuration utilisée (référence ExperimentConfiguration).")
    pair: str = Field(description="Paire de capteurs comparée.")
    grid_deg: float = Field(description="Maille spatiale utilisée (degrés).")
    window_days: int = Field(description="Fenêtre temporelle utilisée (jours).")
    status: str = Field(
        description="État : pending | running | completed | failed | cancelled."
    )
    data_origin: str = Field(description="Origine des données utilisées.")
    source_digest: str | None = Field(
        default=None, description="Empreinte des fichiers source."
    )
    started_at: str | None = Field(default=None)
    finished_at: str | None = Field(default=None)
    elapsed_s: float | None = Field(
        default=None, description="Durée d'exécution en secondes."
    )
    error: str | None = Field(
        default=None, description="Message d'erreur si l'expérience a échoué."
    )
    result: dict[str, Any] | None = Field(
        default=None, description="Résultats calculés (métriques, séries, cellules, etc.)."
    )
    software: dict[str, str] | None = Field(
        default=None, description="Versions logicielles utilisées."
    )