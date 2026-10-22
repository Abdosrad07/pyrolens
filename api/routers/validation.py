"""Route de validation d'un CSV FIRMS téléversé (POST, lecture seule du pipeline)."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile

from api.errors import ApiError
from api.routers.deps import get_cfg, get_settings
from api.schemas import ValidationResponse
from api.security import require_token_if_configured
from api.services.validation import validate_csv
from api.settings import Settings

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/octet-stream",
    "application/vnd.ms-excel",
    "",
}
_CHUNK = 1024 * 1024


@router.post(
    "/datasets/validate",
    response_model=ValidationResponse,
    summary="Valider un CSV FIRMS téléversé",
    description=(
        "Audit en mémoire d'un fichier CSV FIRMS (aucune intégration, aucune correction). "
        "Colonnes obligatoires : latitude, longitude, acq_date, acq_time, satellite. "
        "Taille maximale : PYROLENS_MAX_UPLOAD_BYTES (10 Mo par défaut)."
    ),
    dependencies=[Depends(require_token_if_configured)],
    status_code=200,
)
async def validate_dataset(
    request: Request,
    file: UploadFile = File(..., description="CSV FIRMS (UTF-8)"),
) -> ValidationResponse:
    settings: Settings = get_settings(request)
    cfg = get_cfg(request)

    name = file.filename or ""
    if not name.lower().endswith(".csv"):
        raise ApiError(400, "Seuls les fichiers .csv sont acceptés.")
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise ApiError(415, f"Type de contenu non accepté : {content_type}. Utiliser text/csv.")

    geometry = getattr(request.app.state, "geometry", None)

    with tempfile.TemporaryDirectory(prefix="pyrolens-upload-") as tmp:
        target = Path(tmp) / Path(name).name
        size = 0
        with target.open("wb") as out:
            while True:
                chunk = await file.read(_CHUNK)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise ApiError(
                        413,
                        f"Fichier trop volumineux (max {settings.max_upload_bytes} octets).",
                    )
                out.write(chunk)
        if size == 0:
            raise ApiError(400, "Fichier vide.")

        payload = validate_csv(target, name, cfg, settings, geometry=geometry)

    payload["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return ValidationResponse(**payload)
