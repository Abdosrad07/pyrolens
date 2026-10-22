"""Chargement de la configuration versionnée (config/pipeline.yaml)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "pipeline.yaml"


class Config:
    """Accès en point notation à une configuration YAML."""

    def __init__(self, data: dict[str, Any], path: Path | None = None) -> None:
        self.data = data
        self.path = path

    # -- lecture ---------------------------------------------------------
    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for key in dotted.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    # -- chemins ---------------------------------------------------------
    def path_of(self, key: str, root: Path | None = None) -> Path:
        rel = self.get(f"paths.{key}", key)
        base = root or PROJECT_ROOT
        p = Path(rel)
        return p if p.is_absolute() else base / p

    # -- environnement (secrets) ----------------------------------------
    @staticmethod
    def env(name: str, default: str | None = None) -> str | None:
        value = os.environ.get(name, default)
        if value is not None and not value.strip():
            return default
        return value


def load_config(path: str | Path | None = None) -> Config:
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    if not cfg_path.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Configuration invalide (attendu un mapping) : {cfg_path}")
    return Config(data, cfg_path)
