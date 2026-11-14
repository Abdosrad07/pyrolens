"""Application FastAPI PyroLens.

Entrée unique exportée : ``app`` (utilisable par ``uvicorn api.index:app`` ou
l'import direct de ``api.app``). La couche HTTP ne contient aucune logique
métier : tout le calcul vit dans ``api/services/`` et ``src/pyrolens/``.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import PROJECT_ROOT


def _load_env_files() -> None:
    """Charge `.env` puis `.env.local` (prioritaire) — même convention que le pipeline."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_file = PROJECT_ROOT / ".env"
    local_file = PROJECT_ROOT / ".env.local"
    if env_file.exists():
        load_dotenv(env_file)
    if local_file.exists():
        load_dotenv(local_file, override=True)


_load_env_files()

try:
    from pyrolens import __version__ as PYROLENS_VERSION
except Exception:  # noqa: BLE001 — l'API reste servable si le pipeline n'est pas importable
    PYROLENS_VERSION = "unknown"

from api.errors import UTF8JSONResponse, install_error_handlers
from api.jobs import JobManager
from api.routers import audit as audit_router
from api.routers import baselines as baselines_router
from api.routers import catalog as catalog_router
from api.routers import experiments as experiments_router
from api.routers import firms as firms_router
from api.routers import fire_calendar as fire_calendar_router
from api.routers import methodology as methodology_router
from api.routers import system as system_router
from api.routers import validation as validation_router
from api.settings import Settings
from api.store import ArtifactStore

logger = logging.getLogger("pyrolens.api")

DESCRIPTION = """
API de lecture des artefacts PyroLens et d'exécution des expériences d'harmonisation.

* **Source de vérité** : le pipeline Python (`pyrolens`) écrit des artefacts horodatés ;
  cette API les sert en lecture seule et exécute les expériences demandées dans un
  thread séparé (aucun calcul scientifique n'est fait « à la va-vite » dans une requête).
* **Intégrité** : aucun état n'affirme une absence de feu ; les valeurs manquantes ne
  sont jamais converties ; chaque résultat porte sa provenance (paramètres, versions,
  empreinte de la source, horodatage).
* **Contrat** : `docs/api.md` (exemples curl + champs) ; contrat de référence dans
  `docs/openapi.json` (exporté depuis `/api/v1/openapi.json`).
""".strip()

ROUTERS = (
    (system_router.router, "system"),
    (catalog_router.router, "catalogue"),
    (audit_router.router, "audit"),
    (baselines_router.router, "comparaisons"),
    (fire_calendar_router.router, "calendrier des feux"),
    (methodology_router.router, "méthodologie"),
    (validation_router.router, "validation"),
    (experiments_router.router, "expériences"),
    (firms_router.router, "analyse de zone FIRMS"),
)


def _load_geometry_lazily(cfg):
    """Polygone d'emprise documenté, chargé une fois au démarrage (optionnel)."""
    geo_file = cfg.path_of("raw") / "geo" / "ne_110m_admin_0_countries.geojson"
    if not geo_file.exists():
        return None
    try:
        from pyrolens.emprise import load_region_polygon

        return load_region_polygon(geo_file, cfg.get("region.iso3", "CMR"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("polygone d'emprise indisponible (%s) : filtre bbox seul", exc)
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "PyroLens API %s — artefacts: %s, jobs: %s",
        PYROLENS_VERSION,
        app.state.settings.artifacts_dir,
        "activés" if app.state.settings.jobs_enabled else "désactivés",
    )
    yield
    app.state.jobs.shutdown()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    from pyrolens.config import load_config

    cfg = load_config()

    app = FastAPI(
        title="PyroLens API",
        version=PYROLENS_VERSION,
        description=DESCRIPTION,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        default_response_class=UTF8JSONResponse,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.store = ArtifactStore(settings)
    app.state.jobs = JobManager(settings)
    app.state.cfg = cfg
    app.state.geometry = _load_geometry_lazily(cfg)

    install_error_handlers(app)

    if settings.cors_origins:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

    for router, tag in ROUTERS:
        app.include_router(router, prefix="/api/v1", tags=[tag])

    @app.get("/", include_in_schema=False, tags=["system"])
    def root() -> dict:
        return {
            "name": "PyroLens API",
            "version": PYROLENS_VERSION,
            "docs": "/api/v1/docs",
            "openapi": "/api/v1/openapi.json",
            "health": "/api/v1/health",
        }

    return app


app = create_app()
