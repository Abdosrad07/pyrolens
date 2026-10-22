"""Point d'entrée d'exécution de l'API (hébergement : `api/index.py`).

Le répertoire du projet et `src/` sont ajoutés au ``sys.path`` avant tout import,
pour que le pipeline ``pyrolens`` soit importable sans installation du paquet
(l'hébergement n'exécute que ``requirements.txt``).

Lancement local : `uvicorn api.index:app --host 0.0.0.0 --port 8000` (depuis la racine).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _extra in (str(_ROOT), str(_ROOT / "src")):
    if _extra not in sys.path:
        sys.path.insert(0, _extra)

from api.app import app  # noqa: E402, F401 — application exportée pour uvicorn/hébergement

if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
