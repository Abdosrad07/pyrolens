"""Application FastAPI PyroLens.

Entrée unique exportée : ``app`` (utilisable par ``uvicorn api.index:app`` ou
l'import direct de ``api.app``). La couche HTTP ne contient aucune logique
métier : tout le calcul vit dans ``api/services/`` et ``src/pyrolens/``.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

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
from api.routers import early_warning as early_warning_router
from api.routers import experiments as experiments_router
from api.routers import firms as firms_router
from api.routers import fire_calendar as fire_calendar_router
from api.routers import methodology as methodology_router
from api.routers import predict as predict_router
from api.routers import system as system_router
from api.routers import validation as validation_router
from api.settings import Settings, normalize_post_path
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
    (predict_router.router, "prédiction de risque"),
    (early_warning_router.router, "early warning"),
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

    if settings.allowed_posts:
        allowed = set(settings.allowed_posts)

        @app.middleware("http")
        async def _allowed_posts_guard(request, call_next):
            """Whitelist des POST (démo publique) : 403 JSON hors liste.

            Enregistré avant CORS pour que CORSMiddleware reste le
            middleware le plus externe (en-têtes CORS sur les 403).
            """
            if request.method == "POST" and normalize_post_path(request.url.path) not in allowed:
                return UTF8JSONResponse(
                    {
                        "error": {
                            "code": "403",
                            "message": "Endpoint POST non autorisé sur cette instance.",
                        }
                    },
                    status_code=403,
                )
            return await call_next(request)

    if settings.cors_origins:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

    # ── Mode démo : override endpoints avec des données réalistes ──────────────
    # Activer avec : PYROLENS_DEMO=1 uvicorn api.index:app --reload
    # En mode démo, les routers réels sont désactivés (pas de pipeline ni données).
    if not settings.demo:
        for router, tag in ROUTERS:
            app.include_router(router, prefix="/api/v1", tags=[tag])

    if settings.demo:
        from api.demo_data import get_demo_router as _get_demo
        _demo = _get_demo()
        _prefix = "/api/v1"

        async def _demo_chat(request: Request):
            return _demo.post_chat(await request.json())

        async def _demo_predict_post(request: Request):
            return _demo.post_predict(await request.json())

        async def _demo_predict_job(request: Request, job_id: str):
            return _demo.get_predict_job(job_id)

        async def _demo_calendar(request: Request):
            return _demo.get_fire_calendar_daily(dict(request.query_params))

        async def _demo_alert_detail(request: Request, cell_id: str):
            result = _demo.get_early_warning_alert_detail(cell_id)
            return result if result else {"error": "not found", "cell_id": cell_id}

        async def _demo_baselines_summary(request: Request):
            return _demo.get_baselines_summary(dict(request.query_params))

        async def _demo_baselines_jaccard(request: Request):
            return _demo.get_baselines_jaccard_series(dict(request.query_params))

        async def _demo_baselines_spatial(request: Request):
            return _demo.get_baselines_spatial(dict(request.query_params))

        async def _demo_health(request: Request):
            return {
                "status": "ok",
                "generated_at": _demo.get_fire_risk()["generated_at"],
                "data_origin": "synthetic_fixture",
                "project_version": PYROLENS_VERSION,
                "mode": "demo",
            }

        async def _demo_fire_risk(request: Request):
            return _demo.get_fire_risk()

        async def _demo_predict_list(request: Request):
            return _demo.get_predict_list()

        async def _demo_experiments(request: Request):
            return _demo.get_experiments()

        async def _demo_warning_summary(request: Request):
            return _demo.get_early_warning_summary()

        async def _demo_warning_alerts(request: Request):
            return _demo.get_early_warning_alerts()

        _routes = [
            ("GET",    f"{_prefix}/health",                     _demo_health),
            ("GET",    f"{_prefix}/fire-risk",                  _demo_fire_risk),
            ("POST",   f"{_prefix}/chat",                       _demo_chat),
            ("POST",   f"{_prefix}/predict",                    _demo_predict_post),
            ("GET",    f"{_prefix}/predict",                    _demo_predict_list),
            ("GET",    f"{_prefix}/predict/{{job_id}}",         _demo_predict_job),
            ("GET",    f"{_prefix}/experiments",                _demo_experiments),
            ("GET",    f"{_prefix}/fire-calendar/daily",        _demo_calendar),
            ("GET",    f"{_prefix}/early-warning/summary",      _demo_warning_summary),
            ("GET",    f"{_prefix}/early-warning/alerts",       _demo_warning_alerts),
            ("GET",    f"{_prefix}/early-warning/alerts/{{cell_id}}", _demo_alert_detail),
            ("GET",    f"{_prefix}/baselines/summary",          _demo_baselines_summary),
            ("GET",    f"{_prefix}/baselines/series/jaccard",   _demo_baselines_jaccard),
            ("GET",    f"{_prefix}/baselines/spatial",          _demo_baselines_spatial),
        ]
        for method, path, handler in _routes:
            app.add_api_route(path, handler, methods=[method], tags=["demo"], include_in_schema=True)

        logger.info("Mode DEMO active — donnees simulees sur %d endpoints", len(_routes))

    # Mount static files for artifacts
    artifacts_dir = settings.artifacts_dir
    if artifacts_dir.exists():
        app.mount("/artifacts", StaticFiles(directory=str(artifacts_dir)), name="artifacts")

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
