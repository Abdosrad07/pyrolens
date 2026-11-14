"""Modèles de contrôle qualité, traçabilité et provenance."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from api.models.base import BaseModel, TimestampMixin


class Anomaly(BaseModel, TimestampMixin):
    """Une anomalie détectée lors du contrôle qualité."""

    observation_id: str | None = Field(
        default=None, description="Identifiant de l'observation concernée."
    )
    dataset_id: str | None = Field(
        default=None, description="Identifiant du jeu de données source."
    )
    file: str | None = Field(
        default=None, description="Nom du fichier source (sans chemin absolu)."
    )
    line_number: int | None = Field(
        default=None, description="Numéro de ligne physique dans le fichier source."
    )
    column: str | None = Field(
        default=None, description="Colonne concernée (prénom de la colonne)."
    )
    raw_value: Any | None = Field(
        default=None, description="Valeur brute détectée comme suspecte."
    )
    category: str = Field(
        description="Catégorie : malformed_row | missing_required_column | invalid_latitude | invalid_longitude | invalid_date | invalid_time | outside_emprise | invalid_frp | invalid_confidence | duplicate_row | duplicate_key | missing_value."
    )
    reason: str = Field(description="Explication de l'anomalie.")
    classification: str = Field(
        description="Classement : excluded | ambiguous | retained."
    )


class QualityReport(BaseModel, TimestampMixin):
    """Rapport de contrôle qualité sur un jeu de données."""

    dataset_id: str = Field(description="Identifiant du jeu de données contrôlé.")
    satellite_id: str = Field(description="Identifiant du satellite producteur.")
    n_files: int = Field(description="Nombre de fichiers analysés.")
    n_records: int = Field(description="Nombre total de lignes analysables.")
    n_anomalies: int = Field(description="Nombre total d'anomalies détectées.")
    rows_analysable: int = Field(description="Lignes conservées après filtrage.")
    rows_excluded: int = Field(
        default=0, description="Lignes exclues (malformées, coordonnées invalides)."
    )
    rows_outside_emprise: int = Field(
        default=0, description="Lignes hors emprise (ambiguë, conservée dans les ensembles)."
    )
    anomalies_by_category: dict[str, int] = Field(
        default_factory=dict, description="Comptage des anomalies par catégorie."
    )
    row_accounting: dict[str, Any] = Field(
        default_factory=dict, description="Détail du compte des lignes."
    )
    rows_bien_formees: int = Field(
        default=0, description="Lignes bien formées (utilisables)."
    )
    anomalies_sample: list[Anomaly] = Field(
        default_factory=list, description="Échantillon d'anomalies conservé (TFVC max)."
    )
    interpretation_warning: str | None = Field(
        default=None, description="Avertissement d'interprétation du pipeline."
    )


class ProcessingLog(BaseModel, TimestampMixin):
    """Enregistrement d'une étape de traitement (import, audit, calcul, etc.)."""

    process_id: str = Field(
        description="Identifiant technique de l'étape de traitement."
    )
    step: str = Field(
        description="Nom de l'étape : download | normalize | audit | baselines | observability | figures | report."
    )
    status: str = Field(description="Statut : ok | blocked | failed | deferred.")
    detail: str | None = Field(default=None, description="Message descriptif.")
    http_status: int | None = Field(
        default=None, description="Code HTTP le cas échéant."
    )
    error: str | None = Field(default=None, description="Message d'erreur le cas échéant.")
    action: str | None = Field(
        default=None, description="Action conseillée si le statut est bloqué."
    )


class DataProvenance(BaseModel, TimestampMixin):
    """Traçabilité des données d'acquisition."""

    dataset_id: str = Field(description="Identifiant du jeu de données.")
    source: str = Field(description="Source : nasa_firms | synthetic_fixture | uploaded_file.")
    acquisition_method: str = Field(
        description="Méthode : api | direct_file | fixture | api_request."
    )
    n_requests: int = Field(default=0, description="Nombre de requêtes d'acquisition.")
    bytes_downloaded: int = Field(
        default=0, description="Octets téléchargés au total."
    )
    entries: list[dict[str, Any]] = Field(
        default_factory=list, description="Entrées détaillées (statut, sha256, etc.)."
    )
    manifests_sha256: list[str] = Field(
        default_factory=list, description="Liste des empreintes SHA-256 des fichiers conservés."
    )
    blocked_entries_sample: list[dict[str, Any]] = Field(
        default_factory=list, description="Échantillon des entrées bloquées (erreur / blocage)."
    )
    note: str | None = Field(
        default=None, description="Note explicative si la provenance est inhabituelle."
    )