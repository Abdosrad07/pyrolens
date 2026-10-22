"""Routes des expériences d'harmonisation (configuration, suivi, résultats)."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Request, Response

from api.errors import ApiError
from api.jobs import JOB_ID_PATTERN, JobManager
from api.routers.deps import get_cfg, get_jobs, get_settings
from api.schemas import ExperimentRequest, ExperimentResultResponse, JobListView, JobView
from api.security import require_token_if_configured
from api.services.experiments import run_harmonization_experiment
from api.settings import Settings

router = APIRouter()

_JOB_ID_RE = re.compile(JOB_ID_PATTERN)


def _valid_params(cfg, body: ExperimentRequest) -> list[str]:
    pairs = [f"{a}__{b}" for a, b in (cfg.get("analysis.pairs") or [])]
    grids = [float(g) for g in (cfg.get("analysis.grid_sizes_deg") or [])]
    windows = [int(w) for w in (cfg.get("analysis.window_days") or [])]
    if body.pair not in pairs:
        raise ApiError(400, f"Paire inconnue : {body.pair}. Valeurs admises : {', '.join(pairs)}.")
    if not any(round(g - body.grid_deg, 6) == 0.0 for g in grids):
        raise ApiError(400, f"Maille inconnue : {body.grid_deg}. Valeurs admises : {grids}.")
    if body.window_days not in windows:
        raise ApiError(400, f"Fenêtre inconnue : {body.window_days}. Valeurs admises : {windows}.")
    return pairs


@router.post(
    "/experiments",
    response_model=JobView,
    status_code=202,
    summary="Configurer et lancer une expérience d'harmonisation",
    description=(
        "Calcule une comparaison (paire × maille × fenêtre) sur la source configurée "
        "(données FIRMS normalisées ou échantillon synthétique). La réponse 202 porte l'identifiant "
        "de la tâche ; le suivi se fait sur /experiments/{job_id}. Si PYROLENS_API_TOKEN est défini, "
        "l'en-tête Authorization: Bearer <jeton> est exigé."
    ),
    dependencies=[Depends(require_token_if_configured)],
)
def create_experiment(
    body: ExperimentRequest,
    request: Request,
    response: Response,
) -> JobView:
    cfg = get_cfg(request)
    settings: Settings = get_settings(request)
    jobs: JobManager = get_jobs(request)
    _valid_params(cfg, body)

    params = {
        "pair": body.pair,
        "grid_deg": body.grid_deg,
        "window_days": body.window_days,
        "source": body.source,
    }
    job = jobs.submit(params, lambda: run_harmonization_experiment(params, cfg, settings))
    response.headers["Location"] = f"/api/v1/experiments/{job.id}"
    return JobView(**job.view())


@router.get(
    "/experiments",
    response_model=JobListView,
    summary="Lister les expériences",
    description="Tâches connues du processus courant (plus les résultats persistés des tâches terminées).",
)
def list_experiments(request: Request) -> JobListView:
    jobs: JobManager = get_jobs(request)
    return JobListView(count=0 if not jobs else len(jobs.list()), items=[JobView(**j.view()) for j in jobs.list()])


@router.get(
    "/experiments/{job_id}",
    response_model=JobView,
    summary="Suivi d'une tâche",
    description="Statut : queued → running → succeeded | failed. Le résultat se lit sur /result.",
)
def get_experiment(job_id: str, request: Request) -> JobView:
    if not _JOB_ID_RE.match(job_id):
        raise ApiError(404, "Tâche inconnue.")
    jobs: JobManager = get_jobs(request)
    job = jobs.get(job_id)
    if job is None:
        raise ApiError(404, "Tâche inconnue.")
    return JobView(**job.view())


@router.get(
    "/experiments/{job_id}/result",
    response_model=ExperimentResultResponse,
    summary="Résultat d'une expérience",
    description=(
        "Résultat complet avec provenance : paramètres, origine des données, empreinte de la source, "
        "versions logicielles, horodatages. 409 tant que la tâche n'est pas terminée."
    ),
)
def get_experiment_result(job_id: str, request: Request) -> ExperimentResultResponse:
    if not _JOB_ID_RE.match(job_id):
        raise ApiError(404, "Tâche inconnue.")
    jobs: JobManager = get_jobs(request)
    job = jobs.get(job_id)
    if job is None:
        raise ApiError(404, "Tâche inconnue.")
    if job.status == "failed":
        raise ApiError(409, f"Tâche échouée : {job.error or 'erreur inconnue'}.")
    if job.result is None:
        raise ApiError(409, f"Tâche non terminée (statut : {job.status}). Réessayer plus tard.")
    view = job.view()
    return ExperimentResultResponse(
        job_id=job.id,
        kind=job.kind,
        params=view["params"],
        status=job.status,
        created_at=job.created_at,
        result=job.result,
    )
