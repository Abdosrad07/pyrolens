"""Classes de base pour les modèles de données PyroLens.

Fournit :
- ``BaseModel`` : modèle Pydantic avec configuration commune (JSON, alias,
  interdiction des champs supplémentaires par défaut).
- ``TimestampMixin`` : champs ``created_at`` / ``updated_at``.
- ``ProvenanceMixin`` : champs ``data_origin`` / ``source_digest`` / ``generated_at``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class BaseModel(PydanticBaseModel):
    """Modèle de base : JSON en camelCase, champs supplémentaires interdits,
    sérialisation des dates en ISO-8601 UTC."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_encoders={
            datetime: lambda v: v.isoformat(timespec="seconds"),
        },
    )


class TimestampMixin:
    """Ajoute ``created_at`` et ``updated_at`` (ISO-8601 UTC)."""

    created_at: str = Field(default_factory=_now_iso)
    updated_at: str | None = None


class ProvenanceMixin:
    """Ajoute la traçabilité de l'origine des données."""

    data_origin: str = Field(
        description="Origine des données : nasa_firms | synthetic_fixture | uploaded_file | custom_source."
    )
    source_digest: str | None = Field(
        default=None,
        description="Empreinte déterministe des fichiers source (noms + tailles).",
    )
    generated_at: str = Field(default_factory=_now_iso)