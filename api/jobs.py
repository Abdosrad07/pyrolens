"""Gestionnaire de tâches asynchrones (expériences d'harmonisation).

File d'attente en mémoire, exécution dans un thread séparé : les requêtes HTTP
ne sont jamais bloquées par un calcul (`mvp_scope`/mission phase 3). Chaque
résultat est persisté dans ``PYROLENS_EXPERIMENTS_DIR`` (JSON horodaté avec
provenance) ; le registre des tâches est en mémoire et survit donc au redémarrage
via les fichiers de résultat (statut « succeeded » rechargé depuis le disque).

Limites assumées (documentées dans ``docs/limitations.md``) : processus unique,
pas de reprise après redémarrage d'une tâche en cours, exécution séquentielle.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.errors import ApiError
from api.settings import Settings

logger = logging.getLogger("pyrolens.api.jobs")

JOB_ID_PATTERN = "^[0-9a-f]{12}$"
TERMINAL = ("succeeded", "failed")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


JOB_KIND_PATHS = {
    "harmonization": "experiments",
    "firms_analyze": "firms/analyze",
    "firms_history": "firms/history",
}


class Job:
    def __init__(self, kind: str, params: dict[str, Any]) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.kind = kind
        self.params = params
        self.status = "queued"
        self.created_at = _now()
        self.started_at: str | None = None
        self.finished_at: str | None = None
        self.error: str | None = None
        self.result: dict[str, Any] | None = None
        self.result_path: Path | None = None
        self.progress: dict[str, Any] = {}
        self.lock = threading.Lock()

    def report(self, step: str, pct: float, detail: str | None = None) -> None:
        """Publication de l'avancement courant (lu par GET …/{id})."""
        with self.lock:
            self.progress = {"step": step, "pct": max(0.0, min(100.0, pct)), "detail": detail, "at": _now()}

    def view(self) -> dict[str, Any]:
        with self.lock:
            base = JOB_KIND_PATHS.get(self.kind, "experiments")
            view: dict[str, Any] = {
                "job_id": self.id,
                "kind": self.kind,
                "params": dict(self.params),
                "status": self.status,
                "created_at": self.created_at,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "error": self.error,
                "progress": dict(self.progress),
                "links": {
                    "self": f"/api/v1/{base}/{self.id}",
                    "result": f"/api/v1/{base}/{self.id}/result",
                },
            }
        return view


class JobManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pyrolens-exp")

    # -- API publique ----------------------------------------------------
    def submit(
        self,
        params: dict[str, Any],
        fn: Callable[[Callable[[str, float, str | None], None]], dict[str, Any]],
        kind: str = "harmonization",
    ) -> Job:
        if not self.settings.jobs_enabled:
            raise ApiError(403, "Exécution d'expériences désactivée (PYROLENS_JOBS_ENABLED=0).")
        job = Job(kind, params)
        with self._lock:
            self._evict_locked()
            self._jobs[job.id] = job
        self._executor.submit(self._run, job, fn)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is not None:
            return job
        return self._load_from_disk(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            jobs = list(self._jobs.values())
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    # -- Internes ---------------------------------------------------------
    def _evict_locked(self) -> None:
        while len(self._jobs) >= self.settings.max_jobs:
            finished = [j for j in self._jobs.values() if j.status in TERMINAL]
            victim = min(finished or list(self._jobs.values()), key=lambda j: j.created_at)
            self._jobs.pop(victim.id, None)

    def _result_path(self, job_id: str) -> Path:
        return self.settings.experiments_dir / f"{job_id}.json"

    def _run(self, job: Job, fn: Callable[[], dict[str, Any]]) -> None:
        with job.lock:
            job.status = "running"
            job.started_at = _now()
        try:
            result = fn(job.report)
            path = self._result_path(job.id)
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"job_id": job.id, "kind": job.kind, "params": job.params, "status": "succeeded"}
            payload.update(result)
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            with job.lock:
                job.result = result
                job.result_path = path
                job.status = "succeeded"
                job.finished_at = _now()
            logger.info("expérience %s terminée en %ss", job.id, result.get("elapsed_s"))
        except ApiError as exc:
            with job.lock:
                job.status = "failed"
                job.error = exc.message
                job.finished_at = _now()
            logger.warning("expérience %s échouée : %s", job.id, exc.message)
        except MemoryError:
            with job.lock:
                job.status = "failed"
                job.error = "Mémoire insuffisante pour la source demandée."
                job.finished_at = _now()
            logger.exception("expérience %s : mémoire épuisée", job.id)
        except Exception as exc:  # jamais de pile dans la réponse
            with job.lock:
                job.status = "failed"
                job.error = f"Erreur interne pendant le calcul ({type(exc).__name__})."
                job.finished_at = _now()
            logger.exception("expérience %s : erreur interne", job.id)

    def _load_from_disk(self, job_id: str) -> Job | None:
        path = self._result_path(job_id)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        job = Job(payload.get("kind", "harmonization"), payload.get("params", {}))
        job.id = job_id
        job.status = payload.get("status", "succeeded")
        job.created_at = payload.get("created_at", job.created_at)
        job.started_at = payload.get("started_at")
        job.finished_at = payload.get("finished_at")
        job.result = {k: v for k, v in payload.items() if k not in ("job_id", "kind", "params", "status")}
        job.result_path = path
        return job
