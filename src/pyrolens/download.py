"""Acquisition des données : géométrie d'emprise, FIRMS API, granules Earthdata.

Toute authentification est préparée mais JAMAIS contournée :
  - FIRMS API  : variable d'environnement FIRMS_MAP_KEY (clé gratuite FIRMS) ;
  - Earthdata  : fichier ~/.netrc ou EARTHDATA_USER/EARTHDATA_PASSWORD, sinon
                 EARTHDATA_TOKEN (bearer) ; le mécanisme est prêt, non renseigné.
Chaque tentative (succès ou échec) est écrite dans un manifest SHA-256.
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from .provenance import sha256_of, write_manifest

FIRMS_API = "https://firms.modaps.eosdis.nasa.gov/api"
EARTHDATA_URS = "https://urs.earthdata.nasa.gov"
GEO_SOURCES = [
    {
        "name": "ne_110m_admin_0_countries.geojson",
        "url": "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson",
        "dataset": "Natural Earth 110m admin_0_countries",
    },
    {
        "name": "ne_110m_admin_0_countries.geojson",
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson",
        "dataset": "Natural Earth 110m admin_0_countries (miroir GitHub officiel du jeu natural-earth-vector)",
    },
]


def _http_get(url: str, *, timeout: float = 60.0, headers: dict[str, str] | None = None,
              follow: bool = True, params: dict[str, Any] | None = None) -> httpx.Response:
    with httpx.Client(timeout=timeout, follow_redirects=follow, headers=headers or {}) as client:
        return client.get(url, params=params)


def _record(entries: list[dict[str, Any]], **kwargs: Any) -> None:
    entries.append(kwargs)


# ---------------------------------------------------------------- géométrie
def download_emprise(raw_dir: Path, entries: list[dict[str, Any]]) -> Path | None:
    """Télécharge le polygone administratif documenté (source naturelle et gratuite)."""
    geo_dir = raw_dir / "geo"
    geo_dir.mkdir(parents=True, exist_ok=True)
    for source in GEO_SOURCES:
        target = geo_dir / source["name"]
        if target.exists() and target.stat().st_size > 0:
            _record(
                entries,
                url=source["url"],
                dataset=source["dataset"],
                status="already_present",
                http_status=None,
                path=str(target),
                bytes=target.stat().st_size,
                sha256=sha256_of(target),
                acquired=True,
                downloaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            return target
        try:
            resp = _http_get(source["url"])
        except Exception as exc:  # noqa: BLE001
            _record(entries, url=source["url"], dataset=source["dataset"],
                    status="error", http_status=None, error=str(exc), acquired=False)
            continue
        if resp.status_code == 200 and len(resp.content) > 1000:
            target.write_bytes(resp.content)
            _record(
                entries,
                url=source["url"],
                dataset=source["dataset"],
                status="downloaded",
                http_status=resp.status_code,
                path=str(target),
                bytes=len(resp.content),
                sha256=sha256_of(target),
                acquired=True,
                downloaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            return target
        _record(entries, url=source["url"], dataset=source["dataset"],
                status="http_error", http_status=resp.status_code, acquired=False)
    return None


# ------------------------------------------------------------ FIRMS API
def _firms_map_key() -> str | None:
    return os.environ.get("FIRMS_MAP_KEY") or None


def _daterange(start: date, end: date, chunk_days: int = 5) -> list[tuple[date, date]]:
    chunks = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=chunk_days - 1), end)   # API area : 1..5 jours (vérifié)
        chunks.append((cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return chunks


def download_firms(cfg, raw_dir: Path, entries: list[dict[str, Any]],
                   start: date | None = None, end: date | None = None,
                   sensor_keys: list[str] | None = None,
                   workers: int = 4,
                   deadline_s: float | None = None) -> dict[str, Any]:
    """Téléchargement FIRMS API (sources standard documentées). Requiert FIRMS_MAP_KEY."""
    key = _firms_map_key()
    bbox = ",".join(str(v) for v in cfg.get("region.bbox"))
    start = start or date.fromisoformat(cfg.get("period.start"))
    end = end or date.fromisoformat(cfg.get("period.end"))
    firms_dir = raw_dir / "firms"
    firms_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"map_key_present": bool(key), "chunks": [], "files": []}
    sensors_cfg: dict[str, Any] = cfg.get("sensors") or {}
    if sensor_keys:
        unknown = [k for k in sensor_keys if k not in sensors_cfg]
        if unknown:
            raise ValueError(f"capteurs inconnus : {unknown} (connus : {list(sensors_cfg)})")
        sensors_cfg = {k: sensors_cfg[k] for k in sensor_keys}
    if not key:
        for sensor_key, spec in sensors_cfg.items():
            _record(
                entries,
                url=f"{FIRMS_API}/area/csv/<FIRMS_MAP_KEY>/{spec.get('firms_source')}/{bbox}/<dates>",
                dataset=f"FIRMS API — {spec.get('label')}",
                status="blocked_missing_credential",
                http_status=None,
                reason="FIRMS_MAP_KEY absent de l'environnement (clé gratuite : inscription FIRMS)",
                acquired=False,
            )
        result["blocked"] = True
        return result

    # Un même source FIRMS peut couvrir plusieurs capteurs (MODIS_SP = Terra + Aqua
    # combinés, colonne « satellite » à l'intérieur) : on télécharge CHAQUE SOURCE
    # une seule fois par tronçon de dates, le nom de fichier porte le source.
    sources: dict[str, list[str]] = {}
    for sensor_key, spec in sensors_cfg.items():
        sources.setdefault(str(spec.get("firms_source")), []).append(sensor_key)

    tasks: list[tuple[str, list[str], str, str, date, date]] = []
    for source, keys in sources.items():
        for (c_start, c_end) in _daterange(start, end):
            # API area (v4.2.0) : /area/csv/[MAP_KEY]/[SOURCE]/[BBOX]/[DAY_RANGE]/[DATE]
            # avec DAY_RANGE ∈ [1..5] et fenêtre [DATE, DATE + DAY_RANGE - 1].
            day_range = (c_end - c_start).days + 1
            url = (f"{FIRMS_API}/area/csv/{key}/{source}/{bbox}/"
                   f"{day_range}/{c_start.isoformat()}")
            name = f"{source.lower()}_{c_start.isoformat()}_{c_end.isoformat()}.csv"
            tasks.append((source, keys, url, name, c_start, c_end))

    def fetch(task: tuple[str, list[str], str, str, date, date]) -> dict[str, Any]:
        source, keys, url, name, c_start, c_end = task
        mask_url = url.replace(key, "<FIRMS_MAP_KEY>")
        dataset = f"FIRMS API — {source} (capteurs : {', '.join(keys)})"
        target = firms_dir / name
        if target.exists() and target.stat().st_size > 0:
            return _entry_result(mask_url, dataset, "already_present", None,
                                 path=str(target), bytes=target.stat().st_size,
                                 sha256=sha256_of(target), acquired=True,
                                 covers_sensors=keys, span=[c_start.isoformat(), c_end.isoformat()])
        try:
            attempts = 0
            while True:
                attempts += 1
                try:
                    resp = _http_get(url, headers={}, timeout=60.0)
                except Exception:
                    if attempts < 4:
                        time.sleep(2 * attempts)
                        continue
                    raise
                if resp.status_code == 200 and b"latitude" in resp.content[:200]:
                    break
                body = resp.text[:200]
                retryable = (
                    "transaction limit" in body
                    or "Invalid MAP_KEY" in body
                    or resp.status_code in (429, 500, 502, 503, 504)
                )
                if retryable and attempts < 4:
                    # Backoff : limite de transactions FIRMS (5 000 / 10 min) ou
                    # réponse transitoire — on réessaie, on n'écrit jamais l'erreur.
                    time.sleep(5 * attempts)
                    continue
                break
            entry: dict[str, Any] = {
                "attempts": attempts,
            }
        except Exception as exc:  # noqa: BLE001
            return _entry_result(mask_url, dataset, "error", None, error=str(exc),
                                 acquired=False, covers_sensors=keys,
                                 span=[c_start.isoformat(), c_end.isoformat()])
        if resp.status_code == 200 and b"latitude" in resp.content[:200]:
            # Écriture atomique : jamais de CSV tronqué présenté comme acquis.
            tmp = target.with_name(target.name + ".part")
            tmp.write_bytes(resp.content)
            tmp.replace(target)
            return _entry_result(
                mask_url, dataset, "downloaded", resp.status_code,
                path=str(target), bytes=len(resp.content), sha256=sha256_of(target),
                acquired=True, processing="standard_processing_selon_source_FIRMS",
                downloaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                covers_sensors=keys, span=[c_start.isoformat(), c_end.isoformat()],
                **entry)
        return _entry_result(mask_url, dataset, "http_error", resp.status_code,
                             body_preview=resp.text[:200], acquired=False,
                             covers_sensors=keys, span=[c_start.isoformat(), c_end.isoformat()],
                             **entry)

    deadline = (time.monotonic() + deadline_s) if deadline_s else None
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(fetch, task): task for task in tasks}
        for fut in as_completed(futures):
            source, keys, url, name, c_start, c_end = futures[fut]
            try:
                res = fut.result()
            except Exception as exc:  # noqa: BLE001
                res = _entry_result(url.replace(key, "<FIRMS_MAP_KEY>"),
                                    f"FIRMS API — {source}", "error", None,
                                    error=str(exc), acquired=False, covers_sensors=keys,
                                    span=[c_start.isoformat(), c_end.isoformat()])
            entries.append(res)
            if res.get("acquired") and res.get("path"):
                result["files"].append(res["path"])
            result["chunks"].append(res.get("span"))
            if deadline is not None and time.monotonic() > deadline:
                # Budget de commande atteint : annuler proprement ce qui n'a pas
                # commencé — ces tronçons seront repris (idempotence) à l'exécution
                # suivante, jamais présentés comme acquis.
                for f2, t2 in futures.items():
                    if f2.cancel():
                        entries.append(_entry_result(
                            t2[2].replace(key, "<FIRMS_MAP_KEY>"),
                            f"FIRMS API — {t2[0]}", "deferred", None, acquired=False,
                            covers_sensors=t2[1],
                            span=[t2[4].isoformat(), t2[5].isoformat()],
                            reason="budget de commande atteint — repris à l'exécution suivante"))
                result["deferred"] = True
                break
    result["blocked"] = False
    result["tasks"] = len(tasks)
    return result


def _entry_result(url: str, dataset: str, status: str, http_status: int | None,
                  **extra: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "url": url, "dataset": dataset, "status": status,
        "http_status": http_status, "acquired": bool(extra.get("acquired")),
    }
    entry.update({k: v for k, v in extra.items() if k != "acquired"})
    return entry


# --------------------------------------------------- granules Earthdata
def earthdata_credentials() -> dict[str, Any]:
    """Détecte un mécanisme d'authentification Earthdata sans jamais afficher de secret."""
    if os.environ.get("EARTHDATA_TOKEN"):
        return {"mode": "token", "present": True, "env": "EARTHDATA_TOKEN"}
    if os.environ.get("EARTHDATA_USER") and os.environ.get("EARTHDATA_PASSWORD"):
        return {"mode": "user_password", "present": True, "env": "EARTHDATA_USER/EARTHDATA_PASSWORD"}
    netrc = Path.home() / ".netrc"
    if netrc.exists() and "urs.earthdata.nasa.gov" in netrc.read_text(errors="ignore"):
        return {"mode": "netrc", "present": True, "env": str(netrc)}
    return {"mode": "none", "present": False, "env": None}


def probe_granule_access(granule_url: str, entries: list[dict[str, Any]], dataset: str) -> dict[str, Any]:
    """Vérifie l'accès à un granule SANS contournement : redirection URS = bloqué."""
    creds = earthdata_credentials()
    try:
        resp = _http_get(granule_url, follow=False, timeout=30.0)
    except Exception as exc:  # noqa: BLE001
        _record(entries, url=granule_url, dataset=dataset, status="error",
                http_status=None, error=str(exc), acquired=False, auth=creds["mode"])
        return {"acquired": False, "http_status": None, "error": str(exc)}
    if resp.status_code == 200:
        _record(entries, url=granule_url, dataset=dataset, status="downloaded",
                http_status=200, bytes=len(resp.content), acquired=True, auth=creds["mode"])
        return {"acquired": True, "http_status": 200}
    location = resp.headers.get("location", "")
    blocked = resp.status_code in (302, 303, 401, 403) or "urs.earthdata" in location
    _record(
        entries,
        url=granule_url,
        dataset=dataset,
        status="blocked_earthdata_login" if blocked else "http_error",
        http_status=resp.status_code,
        location=location[:200],
        reason=(
            "Redirection vers Earthdata Login : authentification requise (aucun contournement)."
            if blocked else f"Réponse HTTP {resp.status_code}"
        ),
        acquired=False,
        auth_mode=creds["mode"],
    )
    return {"acquired": False, "http_status": resp.status_code, "blocked": blocked}


def write_download_manifest(manifest_dir: Path, entries: list[dict[str, Any]], name: str = "downloads.json") -> Path:
    return write_manifest(manifest_dir, name, entries)
