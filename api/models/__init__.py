"""Modèles de données métier du backend PyroLens.

Ces modèles structurent les entités du domaine (satellites, jeux de données,
observations, cellules de grille, expériences, qualité, provenance) et servent
de schémas de validation pour les artefacts JSON du pipeline. Ils n'imposent pas
de base de données SQL : le stockage reste fichier (artefacts horodatés), comme
l'exige l'architecture actuelle du projet.
"""

from api.models.base import BaseModel, TimestampMixin, ProvenanceMixin
from api.models.satellite import Satellite
from api.models.dataset import Dataset
from api.models.observation import Observation
from api.models.grid_cell import GeographicGridCell
from api.models.experiment import (
    HarmonizationExperiment,
    ExperimentConfiguration,
    ExperimentResult,
    ExperimentStatus,
)
from api.models.quality import QualityReport, ProcessingLog, DataProvenance

__all__ = [
    "BaseModel",
    "TimestampMixin",
    "ProvenanceMixin",
    "Satellite",
    "Dataset",
    "Observation",
    "GeographicGridCell",
    "HarmonizationExperiment",
    "ExperimentConfiguration",
    "ExperimentResult",
    "ExperimentStatus",
    "QualityReport",
    "ProcessingLog",
    "DataProvenance",
]