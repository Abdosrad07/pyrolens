"""Routes d'analyse de zone FIRMS à la demande (VIIRS vs MODIS + Jaccard).

``POST /firms/analyze`` lance une tâche de fond (JobManager, kind
``firms_analyze``) : téléchargement des CSV FIRMS pour la bbox demandée,
normalisation et appariement — progression réelle exposée sur ``progress``.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Request, Response

from api.errors import ApiError
from api.jobs import JOB_ID_PATTERN, Job, JobManager
from api.routers.deps import get_jobs, get_settings
from api.schemas import ExperimentResultResponse, JobListView, JobView, ZoneAnalysisRequest
from api.security import require_token_if_configured
from api.services.firms_analysis import run_zone_analysis
from api.settings import Settings

router = APIRouter()

_JOB_ID_RE = re.compile(JOB_ID_PATTERN)
MAX_BBOX_SPAN_DEG = 20.0


def _valid_bbox(bbox: list[float]) -> list[float]:
    w, s, e, n = bbox
    if not (-180 <= w < e <= 180) or not (-90 <= s < n <= 90):
        raise ApiError(400, "bbox invalide : attendre [min_lon, min_lat, max_lon, max_lat] dans les bornes WGS84.")
    if (e - w) > MAX_BBOX_SPAN_DEG or (n - s) > MAX_BBOX_SPAN_DEG:
        raise ApiError(400, f"bbox trop grande : span max {MAX_BBOX_SPAN_DEG}° par côté (téléchargement borné).")
    return [w, s, e, n]


@router.post(
    "/firms/analyze",
    response_model=JobView,
    status_code=202,
    summary="Analyser une zone : détections VIIRS vs MODIS (FIRMS)",
    description=(
        "Lance une tâche de fond : téléchargement FIRMS (sources SP, fenêtre ~5 jours), "
        "normalisation et appariement par cellule/date → Jaccard de recouvrement. "
        "Nécessite FIRMS_MAP_KEY côté serveur. L'avancement réel est visible sur "
        "GET /firms/analyze/{job_id} (champ progress)."
    ),
    dependencies=[Depends(require_token_if_configured)],
)
def create_zone_analysis(
    body: ZoneAnalysisRequest,
    request: Request,
    response: Response,
) -> JobView:
    settings: Settings = get_settings(request)
    jobs: JobManager = get_jobs(request)
    bbox = _valid_bbox(body.bbox)
    params = {"bbox": bbox, "window": body.window, "grid_deg": body.grid_deg}
    job = jobs.submit(
        params,
        lambda report: run_zone_analysis(params, settings, report),
        kind="firms_analyze",
    )
    response.headers["Location"] = f"/api/v1/firms/analyze/{job.id}"
    return JobView(**job.view())


@router.get(
    "/firms/analyze",
    response_model=JobListView,
    summary="Lister les analyses de zone",
    description="Tâches firms_analyze connues du processus courant (+ résultats persistés).",
)
def list_zone_analyses(request: Request) -> JobListView:
    jobs: JobManager = get_jobs(request)
    items = [JobView(**j.view()) for j in jobs.list() if j.kind == "firms_analyze"]
    return JobListView(count=len(items), items=items)


def _get_zone_job(job_id: str, request: Request) -> Job:
    jobs: JobManager = get_jobs(request)
    if not _JOB_ID_RE.match(job_id):
        raise ApiError(404, "Tâche inconnue.")
    job = jobs.get(job_id)
    if job is None or job.kind != "firms_analyze":
        raise ApiError(404, "Tâche inconnue.")
    return job


@router.get(
    "/firms/analyze/{job_id}",
    response_model=JobView,
    summary="Suivi d'une analyse de zone",
    description="Statut : queued → running → succeeded | failed. Le champ `progress` porte l'étape courante.",
)
def get_zone_analysis(job_id: str, request: Request) -> JobView:
    job = _get_zone_job(job_id, request)
    return JobView(**job.view())


@router.get(
    "/firms/analyze/{job_id}/result",
    response_model=ExperimentResultResponse,
    summary="Résultat d'une analyse de zone",
    description=(
        "Compteurs par capteur, Jaccard, série quotidienne, échantillon de points "
        "(carte) et provenance. 409 tant que la tâche n'est pas terminée."
    ),
)
def get_zone_analysis_result(job_id: str, request: Request) -> ExperimentResultResponse:
    job = _get_zone_job(job_id, request)
    if job.status == "failed":
        raise ApiError(409, f"Tâche échouée : {job.error or 'erreur inconnue'}.")
    if job.result is None:
        raise ApiError(409, f"Tâche non terminée (statut : {job.status}).")
    view = job.view()
    return ExperimentResultResponse(
        job_id=job.id,
        kind=job.kind,
        params=view["params"],
        status=job.status,
        created_at=job.created_at,
        result=job.result,
    )
