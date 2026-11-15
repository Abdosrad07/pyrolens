"""Routes de prédiction Fire Risk : POST /predict lance `pyrolens predict` en job.

Le modèle n'est JAMAIS réentraîné à la volée par une requête GET — uniquement
via ce POST (token-protégé comme les autres écritures). Le résultat est
l'artefact `fire_risk.json` + les métriques, identique au CLI.

Garde-fous :
* une seule exécution à la fois (JobManager = 1 worker) ;
* `data_origin` propagé (nasa_firms / synthetic_fixture) ;
* le résultat reste un backtest historique (données ≤ 2020).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from api.errors import ApiError
from api.jobs import JOB_ID_PATTERN, Job, JobManager
from api.routers.deps import get_jobs
from api.schemas import ExperimentResultResponse, JobListView, JobView
from api.security import require_token_if_configured

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grid_deg: float = Field(default=0.25, gt=0.0, le=1.0)
    window: int = Field(default=8, ge=1, le=60, description="horizon en jours")
    reference_date: str | None = Field(
        default=None, description="AAAA-MM-JJ (défaut : max des données)"
    )
    source: str = Field(default="auto", pattern="^(auto|raw|fixture)$")


def _csv_dir(source: str) -> tuple[Path, str]:
    raw = PROJECT_ROOT / "data" / "raw" / "firms"
    fixture = PROJECT_ROOT / "data" / "fixture"
    if source in ("auto", "raw") and raw.exists() and list(raw.glob("*.csv")):
        return raw, "nasa_firms"
    if fixture.exists() and list(fixture.glob("*.csv")):
        return fixture, "synthetic_fixture"
    raise ApiError(409, "Aucun CSV disponible : ni data/raw/firms ni data/fixture.")


def _run_predict(params: dict, report) -> dict:
    from pyrolens.prediction import run_prediction

    src_dir, origin = _csv_dir(params.get("source", "auto"))
    csv_paths = sorted(src_dir.glob("*.csv"))
    ref = date.fromisoformat(params["reference_date"]) if params.get("reference_date") else None
    out = PROJECT_ROOT / "web" / "public" / "artifacts" / "fire_risk.json"
    payload = run_prediction(
        csv_paths,
        grid_deg=float(params["grid_deg"]),
        horizon=int(params["window"]),
        reference_date=ref,
        out_path=out,
        model_dir=PROJECT_ROOT / "models",
        progress=lambda step, pct, detail: report(step, pct, detail),
    )
    # résultat allégé : le JSON complet reste dans l'artefact
    return {
        "artifact": "web/public/artifacts/fire_risk.json",
        "data_origin": payload["data_origin"],
        "model": payload["model"]["type"],
        "reference_date": payload["reference_date"],
        "cells": len(payload["cells"]),
        "metrics": payload["metrics"],
        "period": payload["period"],
        "estimate_kind": payload["estimate_kind"],
    }


@router.post(
    "/predict",
    response_model=JobView,
    status_code=202,
    summary="Entraîner/mettre à jour le modèle de risque de feu",
    description=(
        "Lance `pyrolens predict` en tâche de fond (peut durer ~10 min sur "
        "données réelles — un seul worker). Réécrit fire_risk.json à la fin. "
        "Source : data/raw/firms par défaut, data/fixture si absente."
    ),
    dependencies=[Depends(require_token_if_configured)],
)
def create_predict(body: PredictRequest, request: Request, response: Response) -> JobView:
    jobs: JobManager = get_jobs(request)
    params = {
        "grid_deg": body.grid_deg,
        "window": body.window,
        "reference_date": body.reference_date,
        "source": body.source,
    }
    job = jobs.submit(params, lambda report: _run_predict(params, report), kind="predict")
    response.headers["Location"] = f"/api/v1/predict/{job.id}"
    return JobView(**job.view())


@router.get("/predict", response_model=JobListView, summary="Lister les exécutions predict")
def list_predicts(request: Request) -> JobListView:
    jobs: JobManager = get_jobs(request)
    items = [JobView(**j.view()) for j in jobs.list() if j.kind == "predict"]
    return JobListView(count=len(items), items=items)


def _get_job(job_id: str, request: Request) -> Job:
    if not re.match(JOB_ID_PATTERN, job_id):
        raise ApiError(404, "Tâche inconnue.")
    job = get_jobs(request).get(job_id)
    if job is None or job.kind != "predict":
        raise ApiError(404, "Tâche inconnue.")
    return job


@router.get("/predict/{job_id}", response_model=JobView, summary="Suivi d'une exécution predict")
def get_predict(job_id: str, request: Request) -> JobView:
    return JobView(**_get_job(job_id, request).view())


@router.get(
    "/predict/{job_id}/result",
    response_model=ExperimentResultResponse,
    summary="Résultat d'une exécution predict",
)
def get_predict_result(job_id: str, request: Request) -> ExperimentResultResponse:
    job = _get_job(job_id, request)
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
