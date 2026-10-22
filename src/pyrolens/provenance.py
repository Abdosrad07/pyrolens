"""Provenance : sommes de contrôle SHA-256 et manifests de téléchargement.

Les chemins publiés dans les manifests sont **relatifs au dépôt** : un manifeste
est un artefact partagé (artefacts web, dépôt public), il ne doit jamais contenir
de chemin absolu local (invariant « aucun chemin local »).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pyrolens.config import PROJECT_ROOT


def publishable_path(value: Any) -> Any:
    """Transforme un chemin de manifeste en forme publiable (relatif au dépôt).

    - chemin relatif : conservé tel quel (idempotent) ;
    - absolu dans le dépôt : relatif au dépôt, séparateurs `/` ;
    - absolu hors dépôt : nom du fichier seul (jamais de chemin local).
    """
    if not isinstance(value, str) or not value:
        return value
    path = Path(value)
    if not path.is_absolute():
        return value
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return path.name


def sha256_of(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_manifest(manifest_dir: Path, name: str, entries: list[dict[str, Any]]) -> Path:
    """Écrit un manifest JSON horodaté (provenance, sha256, statut HTTP).

    Les entrées sont copiées et leurs éventuels champs ``path`` sont rendus
    relatifs au dépôt avant écriture (aucun chemin local publié).
    """
    manifest_dir = Path(manifest_dir)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    safe_entries = [
        {**entry, "path": publishable_path(entry.get("path"))}
        if isinstance(entry, dict) and "path" in entry
        else entry
        for entry in entries
    ]
    payload = {
        "generated_at": now_iso(),
        "entry_count": len(safe_entries),
        "entries": safe_entries,
    }
    out = manifest_dir / name
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def append_log(log_dir: Path, filename: str, line: str) -> Path:
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = log_dir / filename
    with target.open("a", encoding="utf-8") as fh:
        fh.write(f"{now_iso()} {line}\n")
    return target
