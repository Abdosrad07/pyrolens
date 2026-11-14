"""Configuration de l'API lue dans l'environnement (aucune valeur sensible en dur).

Toutes les variables sont documentées dans ``.env.example``. ``FIRMS_MAP_KEY`` est
lue **uniquement côté serveur** pour l'analyse de zone à la demande
(``POST /firms/analyze``) : elle n'est jamais exposée dans une réponse ni côté
client. ``EARTHDATA_*`` reste réservé au pipeline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from api import PROJECT_ROOT

DEFAULT_ARTIFACTS_DIR = PROJECT_ROOT / "web" / "public" / "artifacts"
DEFAULT_EXPERIMENTS_DIR = PROJECT_ROOT / "reports" / "experiments"


def _env_str(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _env_int(name: str, default: int) -> int:
    raw = _env_str(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = _env_str(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = _env_str(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_path(name: str, default: Path) -> Path:
    raw = _env_str(name)
    if raw is None:
        return default
    p = Path(raw).expanduser()
    return p if p.is_absolute() else (PROJECT_ROOT / p)


@dataclass(frozen=True)
class Settings:
    """Paramètres d'exécution de l'API (dérivés de l'environnement)."""

    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR
    experiments_dir: Path = DEFAULT_EXPERIMENTS_DIR
    # None = choix automatique : data/raw/firms s'il contient des CSV, sinon data/fixture.
    source_dir: Path | None = None
    cache_ttl_s: float = 30.0
    max_upload_bytes: int = 10 * 1024 * 1024
    max_anomalies_sample: int = 100
    max_spatial_top: int = 500
    jobs_enabled: bool = True
    max_jobs: int = 20
    # Si défini, les endpoints POST exigent « Authorization: Bearer <jeton> ».
    api_token: str | None = None
    cors_origins: tuple[str, ...] = field(default_factory=tuple)
    # Clé FIRMS (usage serveur uniquement — jamais renvoyée au client).
    firms_map_key: str | None = None
    # Cache des CSV annuels FIRMS par pays (archive, sans clé).
    archive_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "raw" / "archive")

    @staticmethod
    def from_env() -> "Settings":
        source_raw = _env_str("PYROLENS_SOURCE_DIR")
        source: Path | None = None
        if source_raw:
            p = Path(source_raw).expanduser()
            source = p if p.is_absolute() else (PROJECT_ROOT / p)
        origins = tuple(
            o.strip() for o in (_env_str("PYROLENS_CORS_ORIGINS", "") or "").split(",") if o.strip()
        )
        return Settings(
            artifacts_dir=_env_path("PYROLENS_ARTIFACTS_DIR", DEFAULT_ARTIFACTS_DIR),
            experiments_dir=_env_path("PYROLENS_EXPERIMENTS_DIR", DEFAULT_EXPERIMENTS_DIR),
            source_dir=source,
            cache_ttl_s=_env_float("PYROLENS_CACHE_TTL_SECONDS", 30.0),
            max_upload_bytes=_env_int("PYROLENS_MAX_UPLOAD_BYTES", 10 * 1024 * 1024),
            jobs_enabled=_env_bool("PYROLENS_JOBS_ENABLED", True),
            max_jobs=max(1, _env_int("PYROLENS_MAX_JOBS", 20)),
            api_token=_env_str("PYROLENS_API_TOKEN"),
            cors_origins=origins,
            firms_map_key=_env_str("FIRMS_MAP_KEY"),
            archive_dir=_env_path("PYROLENS_ARCHIVE_DIR", PROJECT_ROOT / "data" / "raw" / "archive"),
        )
