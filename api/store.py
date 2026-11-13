"""Accès aux artefacts horodatés du pipeline (lecture seule, cache en mémoire).

Les artefacts sont la source de vérité (``docs/phase2/api_contract.md`` §1). Le cache
est invalidé par empreinte fichier (mtime + taille) ; un artefact absent est mis en
cache négativement pendant ``cache_ttl_s`` pour éviter un accès disque par requête.
Les messages d'erreur ne contiennent jamais de chemin serveur.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

from api.errors import ApiError
from api.settings import Settings


class ArtifactStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        # name -> (fingerprint, charged_at, payload)
        self._cache: dict[str, tuple[str | None, float, Any]] = {}

    # -- accès fichiers -------------------------------------------------
    def path(self, name: str) -> Path:
        return self.settings.artifacts_dir / name

    def _fingerprint(self, name: str) -> str | None:
        try:
            st = self.path(name).stat()
        except OSError:
            return None
        return f"{st.st_mtime_ns}:{st.st_size}"

    def etag(self, *names: str) -> str | None:
        """ETag faible dérivé des empreintes des artefacts consultés."""
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
                if cached_fp == fp and (fp is not None or now - charged_at < self.settings.cache_ttl_s):
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


def http_cache_headers(store: ArtifactStore, *names: str) -> dict[str, str]:
    headers = {"Cache-Control": "public, max-age=60"}
    etag = store.etag(*names)
    if etag:
        headers["ETag"] = etag
    return headers
