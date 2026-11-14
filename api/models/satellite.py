"""Modèle Satellite — capteurs d'observation de la Terre."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from api.models.base import BaseModel, TimestampMixin


class Satellite(BaseModel, TimestampMixin):
    """Un satellite producteur de détections de points chauds.

    Exemples : MODIS Terra, MODIS Aqua, VIIRS Suomi NPP.
    """

    satellite_id: str = Field(
        description="Identifiant technique unique : terra | aqua | viirs_snpp."
    )
    label: str = Field(description="Nom lisible : MODIS Terra | MODIS Aqua | VIIRS Suomi NPP 375 m.")
    kind: str = Field(description="Famille : modis | viirs.")
    cmr_short_name: str | None = Field(
        default=None, description="Short name CMR du produit associé (ex. MOD14)."
    )
    cmr_version: str | None = Field(
        default=None, description="Version de collection CMR (ex. 061)."
    )
    firms_source: str | None = Field(
        default=None, description="Nom de la source API FIRMS (ex. MODIS_SP)."
    )
    resolution_m: float | None = Field(
        default=None, description="Résolution spatiale nominale en mètres."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)