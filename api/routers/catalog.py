"""Routes catalogue des jeux de données."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from api.routers.deps import apply_cache_headers, cache_guard, get_store
from api.services.catalog import build_catalog, dataset_detail
from api.store import ArtifactStore

router = APIRouter()


@router.get(
    "/catalog",
    summary="Catalogue des jeux de données",
    description=(
        "Jeux source (fenêtres canoniques FIRMS par capteur) et jeux dérivés (artefacts horodatés), "
        "avec provenance et indicateurs de qualité. Noms de fichiers relatifs uniquement."
    ),
)
def catalog(request: Request, response: Response) -> dict:
    guard = cache_guard(request, "audit.json", "inventory.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    payload = build_catalog(store)
    apply_cache_headers(request, response, "audit.json", "inventory.json")
    return payload


@router.get(
    "/catalog/{dataset_id}",
    summary="Détail d'un jeu de données",
    description="Fichier par fichier (comptes, anomalies, période) pour les jeux source ; métadonnées pour les dérivés.",
)
def catalog_detail(dataset_id: str, request: Request, response: Response) -> dict:
    guard = cache_guard(request, "audit.json")
    if guard is not None:
        return guard
    store: ArtifactStore = get_store(request)
    payload = dataset_detail(store, dataset_id)
    apply_cache_headers(request, response, "audit.json")
    return payload
