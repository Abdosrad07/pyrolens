"""API REST PyroLens (FastAPI) — lecture des artefacts du pipeline + expériences.

Point d'entrée d'hébergement : ``api/index.py`` (importe ``api.app:app``).
Le répertoire ``src/`` est ajouté au ``sys.path`` pour importer le pipeline
``pyrolens`` sans installation du paquet (l'hébergement n'exécute que
``requirements.txt``).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

for _extra in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(_extra) not in sys.path:
        sys.path.insert(0, str(_extra))
