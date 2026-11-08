    # -- overview (statistiques globales) --------------------------------

    def get_overview_summary(self) -> dict:
        """Résumé de l'exécution du pipeline (étapes, origine, période)."""
        exec_data = self.require_json("execution")
        return {
            "project_version": exec_data.get("project_version", "unknown"),
            "period_start": exec_data.get("period_start"),
            "period_end": exec_data.get("period_end"),
            "generated_at": exec_data.get("generated_at"),
            "origin": self.get_overview_origin(),
            "summary": {
                "total_files": len(self.list_satellites()),
                "sources": self.get_sources_summary(),
            },
        }

    def get_overview_origin(self) -> str:
        baselines = self.get_json("baselines")
        return (baselines or {}).get("data_origin", "unknown")

    def get_overview_statistics(self) -> dict:
        """Statistiques générales du projet (observations, cellules, FRP)."""
        inv = self.get_json("inventory")
        audit = self.get_json("audit")
        obs = self.get_json("observability")
        baselines = self.get_json("baselines")

        sensors = {}
        inv_sensors = (inv or {}).get("sensors", {})
        for key, s in (inv_sensors or {}).items():
            sensors[key] = {
                "label": s.get("label", key),
                "sensor_id": key,
    def get_overview_summary(self) -> dict:
        """Résumé de l'exécution du pipeline (étapes, origine, periode)."""
        exec_data = self.require_json("execution")
        return {
            "project_version": exec_data.get("project_version", "unknown"),
            "period_start": exec_data.get("period_start"),
            "period_end": exec_data.get("period_end"),
            "generated_at": exec_data.get("generated_at"),
            "origin": self.get_overview_origin(),
            "summary": {
                "total_files": len(self.list_satellites()),
                "sources": self.get_sources_summary(),
            },
        }

    def get_overview_origin(self) -> str:
        baselines = self.get_json("baselines")
        return (baselines or {}).get("data_origin", "unknown")

    def get_overview_statistics(self) -> dict:
        """Statistiques generales du projet (observations, cellules, FRP)."""
        inv = self.get_json("inventory")
        audit = self.get_json("audit")
        obs = self.get_json("observability")
        baselines = self.get_json("baselines")

        sensors = {}
        inv_sensors = (inv or {}).get("sensors", {})
        for key, s in (inv_sensors or {}).items():
            sensors[key] = {
                "label": s.get("label", key),
                "sensor_id": key,
                "total_observations": int(s.get("total_observations", 0)),
                "period": f"{s.get('period_start')} → {s.get('period_end')}",
                "primary_version": s.get("primary_version"),
            }

        # cellules geo actives (top 200 sur la maille primaire)
        spatial = (baselines or {}).get("spatial", [])
        top_cells = spatial[:200] if isinstance(spatial, list) else []

        total_observations = sum(
            int((s or {}).get("total_observations", 0))
            for s in (inv_sensors or {}).values()
        )

        return {
            "data_origin": self.get_overview_origin(),
            "total_observations": total_observations,
            "total_files": len(self.list_satellites()),
            "period": f"{inv.get('period_start')} → {inv.get('period_end')}",
            "sources": {
                k: v.get("label") for k, v in (inv_sensors or {}).items()
            },
            "sensors": sensors,
            "coverage_products_acquired": (obs or {}).get("coverage_products_acquired", False),
            "active_cells_top200": top_cells,
            "n_satellites": len(self.list_satellites()),
        }

    def get_overview_hotspots(self) -> dict:
        """Donnees pour la carte des points chauds : observations filtrees par zone."""
        bbox = self.get_json("inventory") or {}
        bbox_bounds = bbox.get("bounds", {}) or {}
        hotspots = (self.get_json("audit") or {}).get("hotspots", [])
        if not isinstance(hotspots, list):
            hotspots = []
        if bbox_bounds:
            return {
                "hotspots": hotspots,
    # -- overview -----------------------------------------------------------

    def get_overview_statistics(self) -> dict:
        """Statistiques generales du projet (observations, cellules, FRP)."""
        inv = self.get_json("inventory")
        audit = self.get_json("audit")
        obs = self.get_json("observability")
        baselines = self.get_json("baselines")

        sensors = {}
        inv_sensors = (inv or {}).get("sensors", {})
        for key, s in (inv_sensors or {}).items():
            sensors[key] = {
                "label": s.get("label", key),
                "sensor_id": key,
                "total_observations": int(s.get("total_observations", 0)),
                "period": f"{s.get('period_start')} → {s.get('period_end')}",
                "primary_version": s.get("primary_version"),
            }

        # cellules geo actives (top 200 sur la maille primaire)
        spatial = (baselines or {}).get("spatial", [])
        top_cells = spatial[:200] if isinstance(spatial, list) else []

        total_observations = sum(
            int((s or {}).get("total_observations", 0))
            for s in (inv_sensors or {}).values()
        )

        return {
            "data_origin": self.get_overview_origin(),
            "total_observations": total_observations,
            "total_files": len(self.list_satellites()),
            "period": f"{inv.get('period_start')} → {inv.get('period_end')}",
            "sources": {
                k: v.get("label") for k, v in (inv_sensors or {}).items()
            },
            "sensors": sensors,
            "coverage_products_acquired": (obs or {}).get("coverage_products_acquired", False),
            "active_cells_top200": top_cells,
            "n_satellites": len(self.list_satellites()),
        }

    def get_overview_hotspots(self) -> dict:
        """Donnees pour la carte des points chauds : observations filtrees par zone."""
    # -- overview -----------------------------------------------------------

    def get_overview_summary(self) -> dict:
        """Resume de l'execution du pipeline (etapes, origine, periode)."""
        exec_data = self.require_json("execution")
        return {
            "project_version": exec_data.get("project_version", "unknown"),
            "period_start": exec_data.get("period_start"),
            "period_end": exec_data.get("period_end"),
            "generated_at": exec_data.get("generated_at"),
            "origin": self.get_overview_origin(),
            "summary": {
                "total_files": len(self.list_satellites()),
                "sources": self.get_sources_summary(),
            },
        }

    def get_overview_origin(self) -> str:
        baselines = self.get_json("baselines")
        return (baselines or {}).get("data_origin", "unknown")

    def get_overview_statistics(self) -> dict:
        """Statistiques generale du projet (observations, cellules, FRP)."""
        inv = self.get_json("inventory")
        audit = self.get_json("audit")
        obs = self.get_json("observability")
        baselines = self.get_json("baselines")

        sensors = {}
        inv_sensors = (inv or {}).get("sensors", {})
        for key, s in (inv_sensors or {}).items():
            sensors[key] = {
                "label": s.get("label", key),
                "sensor_id": key,
                "total_observations": int(s.get("total_observations", 0)),
                "period": f"{s.get('period_start')} → {s.get('period_end')}",
                "primary_version": s.get("primary_version"),
            }

        # cellules geo actives (top 200 sur la maille primaire)
        spatial = (baselines or {}).get("spatial", [])
        top_cells = spatial[:200] if isinstance(spatial, list) else []

        total_observations = sum(
            int((s or {}).get("total_observations", 0))
            for s in (inv_sensors or {}).values()
        )

        return {
            "data_origin": self.get_overview_origin(),
            "total_observations": total_observations,
            "total_files": len(self.list_satellites()),
            "period": f"{inv.get('period_start')} → {inv.get('period_end')}",
            "sources": {
                k: v.get("label") for k, v in (inv_sensors or {}).items()
            },
            "sensors": sensors,
            "coverage_products_acquired": (obs or {}).get("coverage_products_acquired", False),
            "active_cells_top200": top_cells,
            "n_satellites": len(self.list_satellites()),
        }

    def get_overview_hotspots(self) -> dict:
        """Donnees pour la carte des points chauds : observations filtrees par zone."""
        bbox = self.get_json("inventory") or {}
        bbox_bounds = bbox.get("bounds", {}) or {}
        hotspots = (self.get_json("audit") or {}).get("hotspots", [])
        if not isinstance(hotspots, list):
            hotspots = []
        if bbox_bounds:
            return {
                "hotspots": hotspots,
                "bounds": bbox_bounds,
                "sources": self.get_json("inventory") or {},
            }
        return {"hotspots": hotspots}

    def get_sources_summary(self) -> dict:
        """Resume des sources d'acquisition."""
        dl = self.get_json("downloads_summary")
        if dl is None:
            dl = self.get_json("downloads")
        counts = {}
        if dl and isinstance(dl, dict):
            for status, entry in dl.items():
                if isinstance(entry, dict):
                    counts.setdefault(entry.get("status", "unknown"), 0)
                    counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        return counts
        bbox = self.get_json("inventory") or {}
        bbox_bounds = bbox.get("bounds", {}) or {}
        hotspots = (self.get_json("audit") or {}).get("hotspots", [])
        if not isinstance(hotspots, list):
            hotspots = []
        if bbox_bounds:
            return {
                "hotspots": hotspots,
                "bounds": bbox_bounds,
                "sources": self.get_json("inventory") or {},
            }
        return {"hotspots": hotspots}

    def get_sources_summary(self) -> dict:
        """Resume des sources d'acquisition."""
        dl = self.get_json("downloads_summary")
        if dl is None:
            dl = self.get_json("downloads")
        counts = {}
        if dl and isinstance(dl, dict):
            for status, entry in dl.items():
                if isinstance(entry, dict):
                    counts.setdefault(entry.get("status", "unknown"), 0)
                    counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        return counts
                "bounds": bbox_bounds,
                "sources": self.get_json("inventory") or {},
            }
        return {"hotspots": hotspots}

    def get_sources_summary(self) -> dict:
        """Resume des sources d'acquisition."""
        dl = self.get_json("downloads_summary")
        if dl is None:
            dl = self.get_json("downloads")
        counts = {}
        if dl and isinstance(dl, dict):
            for status, entry in dl.items():
                if isinstance(entry, dict):
                    counts.setdefault(entry.get("status", "unknown"), 0)
                    counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        return counts
                "total_observations": int(s.get("total_observations", 0)),
                "period": f"{s.get('period_start')} → {s.get('period_end')}",
                "primary_version": s.get("primary_version"),
            }

        # cellules géographiques actives (top 200 sur la maille primaire)
        spatial = (baselines or {}).get("spatial", [])
        top_cells = spatial[:200] if isinstance(spatial, list) else []

        # FRP : distribution basique à partir de audit + baselines
        frp_values = []
        audit_data = audit or {}
        frp_values.extend(audit_data.get("frp_values", []))

        total_observations = sum(
            int((s or {}).get("total_observations", 0))
            for s in (inv_sensors or {}).values()
        )

        return {
            "data_origin": self.get_overview_origin(),
            "total_observations": total_observations,
            "total_files": len(self.list_satellites()),
            "period": f"{exec_data := self.get_json('execution') or {}}.get('period_start')} → {exec_data.get('period_end')}",
            "sources": {
                k: v["label"] for k, v in (inv_sensors or {}).items()
            },
            "sensors": sensors,
            "coverage_products_acquired": (obs or {}).get("coverage_products_acquired", False),
            "active_cells_top200": top_cells,
            "n_satellites": len(self.list_satellites()),
        }

    def get_overview_hotspots(self) -> dict:
        """Données pour la carte des points chauds : observations filtrées par zone."""
        bbox = self.get_json("inventory") or {}
        bbox_bounds = bbox.get("bounds", {}) or {}
        hotspots = (self.get_json("audit") or {}).get("hotspots", [])
        if not isinstance(hotspots, list):
            hotspots = []
        if bbox_bounds:
            return {
                "hotspots": hotspots,
                "bounds": bbox_bounds,
                "sources": self.get_json("inventory") or {},
            }
        return {"hotspots": hotspots}

    def get_sources_summary(self) -> dict:
        """Résumé des sources d'acquisition."""
        dl = self.get_json("downloads_summary")
        if dl is None:
            dl = self.get_json("downloads")
        counts = {}
        if dl and isinstance(dl, dict):
            for status, entry in dl.items():
                if isinstance(entry, dict):
                    counts.setdefault(entry.get("status", "unknown"), 0)
                    counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        return counts
"""Accès aux artefacts horodatés du pipeline (lecture seule, cache en mémoire).

Les artefacts sont la source de vérité (``docs/phase2/api_contract.md`` §1).
Le cache est invalidé par empreinte fichier (mtime + taille) ; un artefact absent
est mis en cache négativement pendant ``cache_ttl_s`` pour éviter un accès
disque par requête. Les messages d'erreur ne contiennent jamais de chemin
serveur.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

from api.errors import ApiError
from api.models import (
    Dataset,
    DatasetStatus,
    ExperimentConfiguration,
    HarmonizationExperiment,
    ExperimentStatus,
    Observation,
    Satellite,
    GeographicGridCell,
    QualityReport,
    ProcessingLog,
    DataProvenance,
)
from api.settings import Settings

    # -- accès fichiers -------------------------------------------------

    def path(self, name: str) -> Path:
        return self.settings.artifacts_dir / name

    def reference_path(self, name: str) -> Path:
        """Chemin d'un fichier de référence métier (satellites, datasets)."""
        return self.settings.artifacts_dir / "references" / name

    def _fingerprint(self, name: str) -> str | None:
        try:
            st = self.path(name).stat()
        except OSError:
            return None
        return f"{st.st_mtime_ns}:{st.st_size}"

    def etag(self, *names: str) -> str | None:
        digests = []
        for name in names:
            fp = self._fingerprint(name)
            if fp is None:
                return None
            digests.append(f"{name}:{fp}")
        return 'W/"' + hashlib.sha256("|".join(digests).encode()).hexdigest()[:16] + '"'

    # -- cache ----------------------------------------------------------

    def _load(self, name: str, loader) -> Any:
        fp = self._fingerprint(name)
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(name)
            if cached is not None:
                cached_fp, charged_at, payload = cached
                if cached_fp == fp and (fp is None or now - charged_at < self.settings.cache_ttl_s):
                    return payload
            payload = loader()
            self._cache[name] = (fp, now, payload)
            return payload

    def get_text(self, name: str) -> str | None:
        def loader() -> str | None:
            try:
                return self.path(name).read_text(encoding="utf-8")
            except OSError:
                return None

        return self._load(name, loader)

    def get_json(self, name: str) -> dict | None:
        text = self.get_text(name)
        if text is None:
            return None
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ApiError(500, f"Artefact illisible : {name}.") from exc
        if not isinstance(payload, dict):
            raise ApiError(500, f"Artefact illisible : {name}.")
        return payload

    def require_json(self, name: str) -> dict:
        payload = self.get_json(name)
        if payload is None:
            raise ApiError(500, f"Artefact indisponible : {name}. Exécuter le pipeline (pyrolens).")
        return payload

    def require_text(self, name: str) -> str:
        text = self.get_text(name)
        if text is None:
            raise ApiError(500, f"Artefact indisponible : {name}. Exécuter le pipeline (pyrolens).")
        return text

    def has(self, name: str) -> bool:
        return self._fingerprint(name) is not None

    # -- références -----------------------------------------------------

    def get_reference(self, name: str) -> dict | None:
        """Lecture d'un fichier de référence métier (satellites, datasets)."""
        try:
            return self.get_json(name)
        except ApiError:
            return None

    def require_reference(self, name: str) -> dict:
        payload = self.get_reference(name)
        if payload is None:
            raise ApiError(500, f"Fichier de référence indisponible : {name}.")
        return payload

    # -- modèles métier -------------------------------------------------

    def get_satellites(self) -> list[dict[str, Any]]:
        """Retourne la liste des satellites connus (données statiques)."""
        data = self.get_reference("satellites")
        if data is None:
            return []
        items = data.get("satellites", data.get("items", []))
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        return []

    def list_satellites(self) -> list[dict[str, Any]]:
        return self.get_satellites()

    def get_datasets(self) -> list[dict[str, Any]]:
        data = self.get_reference("datasets")
        if data is None:
            return []
        items = data.get("datasets", data.get("items", []))
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        return []

    def list_datasets(self) -> list[dict[str, Any]]:
        return self.get_datasets()

    # -- expériences ---------------------------------------------------

    def get_experiments(self) -> list[dict[str, Any]]:
        return ExperimentStore(self).list_all()

    def get_experiment(self, experiment_id: str) -> dict | None:
        return ExperimentStore(self).get_by_id(experiment_id)

    def create_experiment(self, payload: dict[str, Any]) -> dict:
        return ExperimentStore(self).create(payload)

    def update_experiment(self, experiment_id: str, payload: dict[str, Any]) -> dict | None:
        return ExperimentStore(self).update(experiment_id, payload)


class ExperimentStore:
    """Gestion des expériences d'harmonisation (persistées en JSON sur disque).

    Remplace le ``JobManager`` existant (``api/jobs.py``) à terme. L'implémentation
    est actuellement un cache mémoire + fichiers JSON pour ne pas casser le
    comportement en cours ; elle sera remplacée par un stockage durable dans un
    futur bloc (PHASE 4/5 de la mission).
    """

    def __init__(self, store: ArtifactStore) -> None:
        self.store = store
        self._experiments: dict[str, dict[str, Any]] = {}
        self._load()

    def _experiments_path(self) -> Path:
        art = self.store.settings.artifacts_dir / "experiments"
        art.mkdir(parents=True, exist_ok=True)
        return art / "registry.json"

    def _load(self) -> None:
        path = self._experiments_path()
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(raw, dict):
            self._experiments = raw

    def _save(self) -> None:
        path = self._experiments_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._experiments, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _next_id(self) -> str:
        existing = [int(k) for k in self._experiments.keys() if k.isdigit()]
        return str(max(existing) + 1 if existing else 1)

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._experiments.values())

    def get_by_id(self, experiment_id: str) -> dict | None:
        return self._experiments.get(experiment_id)

    def create(self, payload: dict[str, Any]) -> dict:
        experiment_id = str(payload.get("experiment_id") or self._next_id())
        now = _now_iso()
        record = {
            "experiment_id": experiment_id,
            "pair": payload.get("pair"),
            "grid_deg": float(payload.get("grid_deg", 0.25)),
            "window_days": int(payload.get("window_days", 8)),
            "source": payload.get("source", "auto"),
            "data_origin": payload.get("data_origin", "custom_source"),
            "status": ExperimentStatus.PENDING,
            "created_at": now,
            "started_at": None,
            "finished_at": None,
            "error": None,
            "result": None,
            "source_digest": payload.get("source_digest"),
        }
        self._experiments[experiment_id] = record
        self._save()
        return record

    def update(self, experiment_id: str, payload: dict[str, Any]) -> dict | None:
        record = self._experiments.get(experiment_id)
        if record is None:
            return None
        if "status" in payload:
            record["status"] = payload["status"]
        if "started_at" in payload:
            record["started_at"] = payload["started_at"]
        if "finished_at" in payload:
            record["finished_at"] = payload["finished_at"]
        if "error" in payload:
            record["error"] = payload["error"]
        if "result" in payload:
            record["result"] = payload["result"]
        self._save()
        return record


def http_cache_headers(store: ArtifactStore, *names: str) -> dict[str, str]:
    headers = {"Cache-Control": "public, max-age=60"}
    etag = store.etag(*names)
    if etag:
        headers["ETag"] = etag
    return headers
class ArtifactStore:
    """Accès lecture seule aux artefacts JSON du pipeline, avec cache en mémoire.

    Hérite du comportement existant (fingerprint mtime+taille, ETag faible) et
    ajoute l'accès aux fichiers de référence métier (``satellites.json``,
    ``datasets.json``) ainsi que l'interface des expériences ``ExperimentStore``.
    La couche de persistence des modèles métier est conservée dans
    ``api/models/experiment.py`` jusqu'à la PHASE 5.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        # name -> (fingerprint, charged_at, payload)
        self._cache: dict[str, tuple[str | None, float, Any]] = {}
