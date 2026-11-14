"""Modèle Observation — détection individuelle de point chaud."""

from __future__ import annotations

from pydantic import Field

from api.models.base import BaseModel


class Observation(BaseModel):
    """Une détection individuelle de point chaud (ligne brute d'un fichier FIRMS)."""

    observation_id: str = Field(description="Identifiant technique unique de l'observation.")
    dataset_id: str = Field(description="Identifiant du jeu de données source (référence Dataset).")
    satellite_id: str = Field(description="Identifiant du satellite (référence Satellite).")
    latitude: float = Field(description="Latitude en degrés décimaux (WGS84).")
    longitude: float = Field(description="Longitude en degrés décimaux (WGS84).")
    acq_date: str = Field(description="Date d'acquisition (AAAA-MM-JJ, UTC).")
    acq_time: str | None = Field(
        default=None, description="Heure d'acquisition (HHMM UTC, sans zéro de tête)."
    )
    brightness: float | None = Field(default=None, description="Température de brillance (K).")
    scan: float | None = Field(default=None, description="Numéro de scan.")
    track: float | None = Field(default=None, description="Numéro de track.")
    satellite_field: str | None = Field(
        default=None, description="Nom du satellite dans le fichier source."
    )
    instrument: str | None = Field(default=None, description="Instrument (ex. MODIS, VIIRS).")
    confidence: str | int | None = Field(
        default=None, description="Niveau de confiance (0-100 MODIS, ou catégorie VIIRS)."
    )
    version: str | None = Field(default=None, description="Version du produit source.")
    bright_t31: float | None = Field(default=None, description="Température du canal 3.1 µm (K).")
    frp: float | None = Field(default=None, description="Puissance radiative du feu (MW).")
    daynight: str | None = Field(default=None, description="D (jour) ou N (nuit).")
    type_field: str | None = Field(
        default=None, description="Type de détection (ex. point chaud, volcan, etc.)."
    )
    is_valid: bool = Field(default=True, description="Ligne valide après contrôle qualité.")
    anomaly_categories: list[str] = Field(
        default_factory=list, description="Catégories d'anomalie détectées sur cette ligne."
    )