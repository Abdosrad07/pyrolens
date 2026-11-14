"""Modèle GeographicGridCell — cellule de grille spatiale."""

from __future__ import annotations

from pydantic import Field

from api.models.base import BaseModel


class GeographicGridCell(BaseModel):
    """Une cellule de grille géographique commune pour l'harmonisation spatiale."""

    cell_id: str = Field(
        description="Identifiant de cellule au format 'i:j' (index entier depuis l'origine -180/-90)."
    )
    grid_deg: float = Field(description="Taille de la maille en degrés (0.1 | 0.25 | 0.50).")
    cell_i: int = Field(description="Index de colonne (longitude).")
    cell_j: int = Field(description="Index de ligne (latitude).")
    lon_center: float = Field(description="Longitude du centre de cellule (degrés).")
    lat_center: float = Field(description="Latitude du centre de cellule (degrés).")
    area_km2: float | None = Field(
        default=None, description="Aire approximative de la cellule en km²."
    )
    observation_count: int = Field(
        default=0, description="Nombre d'observations dans la cellule."
    )