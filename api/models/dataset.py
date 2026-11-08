"""Modèle Dataset — jeu de données satellitaires."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from api.models.base import BaseModel, ProvenanceMixin


class Dataset(BaseModel, ProvenanceMixin):
    """Un jeu de données satellitaires acquis et catalogué.

    Exemples : fenêtres FIRMS 5 jours MODIS Terra, archives granules, etc.
    """

    dataset_id: str = Field(description="Identifiant technique unique du jeu de données.")
    name: str = Field(description="Nom lisible du jeu de données.")
    satellite_id: str = Field(description="Identifiant du satellite producteur (référence Satellite).")
    period_start: str = Field(description="Date de début de couverture (ISO-8601 UTC).")
    period_end: str = Field(description="Date de fin de couverture (ISO-8601 UTC).")
    file_count: int = Field(default=0, description="Nombre de fichiers constitutifs.")
    row_count: int = Field(default=0, description="Nombre total d'enregistrements.")
    status: str = Field(
        default="catalogued",
        description="Statut : catalogued | imported | quality_checked | blocked.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)