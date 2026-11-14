"""Archive FIRMS annuelle par pays — historique par zone (2019 → aujourd'hui).

Source : ``https://firms.modaps.eosdis.nasa.gov/data/country/{sensor}/{year}/
{sensor}_{year}_{Country}.csv`` — fichiers **ouverts, sans clé**, qualité
standard processing (SP). Capteurs disponibles : ``viirs-snpp`` (depuis 2012)
et ``modis`` (depuis 2000, Terra+Aqua combinés, colonne ``satellite``).

Stratégie : une bbox arbitraire est couverte par les fichiers des pays
qu'elle intersecte (polygones Natural Earth déjà dans ``data/raw/geo``).
Chaque fichier est téléchargé **une seule fois** dans
``data/raw/archive/{sensor}/{year}_{Pays}.csv`` puis filtré par bbox —
le cache rend les analyses suivantes quasi instantanées.

Limites assumées :
* le nom de fichier FIRMS n'est pas toujours identique au ``NAME``
  Natural Earth — on essaie des variantes documentées et on rapporte les
  pays non résolus au lieu d'échouer silencieusement ;
* un point près d'une frontière peut appartenir au fichier du pays voisin —
  le filtre bbox final garantit qu'aucune détection hors zone n'entre,
  et une détection frontalière n'est jamais comptée deux fois (chaque
  enregistrement FIRMS appartient à un seul fichier pays).
"""

from __future__ import annotations

import json
import logging
import math
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger("pyrolens.archive")

FIRMS_COUNTRY_BASE = "https://firms.modaps.eosdis.nasa.gov/data/country"
# capteur logique PyroLens -> identifiant FIRMS archive
ARCHIVE_SENSORS = {"viirs": "viirs-snpp", "modis": "modis"}
DEFAULT_ARCHIVE_DIR = "data/raw/archive"
FETCH_TIMEOUT_S = 300.0  # fichiers jusqu'à ~30-50 Mo
USER_AGENT = "PyroLens/0.2 (+archive)"

# Alias FIRMS connus pour les noms Natural Earth les plus divergents.
# (affiné au fil des 404 réels — chaque entrée documentée ici.)
COUNTRY_ALIASES: dict[str, list[str]] = {
    "United States of America": ["United_States", "United_States_of_America", "USA", "United States"],
    "Dem. Rep. Congo": ["Democratic_Republic_of_the_Congo", "Congo_Democratic_Republic", "DRC"],
    "Congo": ["Republic_of_the_Congo", "Congo_Republic"],
    "Central African Republic": ["Central_African_Republic"],
    "Bosnia and Herz.": ["Bosnia_and_Herzegovina", "Bosnia"],
    "Macedonia": ["North_Macedonia", "Macedonia"],
    "eSwatini": ["Swaziland", "Eswatini"],
    "Côte d'Ivoire": ["Ivory_Coast", "Cote_d_Ivoire"],
    "Czechia": ["Czech_Republic"],
    "Türkiye": ["Turkey"],
    "Russia": ["Russian_Federation"],
    "S. Sudan": ["South_Sudan"],
    "W. Sahara": ["Western_Sahara"],
    "Fr. S. Antarctic Lands": ["French_Southern_and_Antarctic_Lands"],
    "N. Cyprus": ["Northern_Cyprus"],
    "Somaliland": ["Somaliland"],
}


def _name_variants(name: str, extra: dict[str, str] | None = None) -> list[str]:
    """Candidats de nom de fichier FIRMS pour un pays Natural Earth."""
    seen: list[str] = []
    for cand in [name, *(extra or {}).values(), *COUNTRY_ALIASES.get(name, [])]:
        for form in (cand, cand.replace(" ", "_"), cand.replace(" ", "")):
            if form and form not in seen:
                seen.append(form)
    return seen


@dataclass
class CountryHit:
    iso3: str
    name: str
    variants: list[str]


def countries_for_bbox(
    bbox: list[float],
    geojson_path: str | Path,
    max_countries: int = 12,
) -> list[CountryHit]:
    """Pays intersectant la bbox [w,s,e,n] via les polygones Natural Earth.

    Utilise l'intersection bbox-polygone (approximation : polygone borné à sa
    bbox — conservateur, peut inclure un pays supplémentaire aux marges,
    jamais en exclure un).
    """
    from shapely.geometry import box, shape

    w, s, e, n = bbox
    zone = box(w, s, e, n)
    data = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    hits: list[CountryHit] = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        name = props.get("NAME") or props.get("ADMIN") or props.get("NAME_EN")
        if not name:
            continue
        try:
            geom = shape(feat.get("geometry") or {})
        except Exception:  # noqa: BLE001
            continue
        if geom.is_empty:
            continue
        if geom.intersects(zone):
            variants = _name_variants(name, {"long": props.get("NAME_LONG") or "",
                                             "formal": props.get("FORMAL_EN") or "",
                                             "en": props.get("NAME_EN") or ""})
            hits.append(CountryHit(iso3=props.get("ISO_A3") or "???", name=name, variants=variants))
            if len(hits) >= max_countries:
                logger.warning("bbox touche >%d pays : tronqué à %d", max_countries, max_countries)
                break
    return hits


def archive_path(archive_dir: str | Path, sensor_key: str, year: int, country_slug: str) -> Path:
    return Path(archive_dir) / ARCHIVE_SENSORS[sensor_key] / f"{year}_{country_slug}.csv"


def _probe(url: str) -> int | None:
    """HEAD léger : code HTTP ou None si injoignable."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001
        return None


def resolve_country_file(
    sensor_key: str,
    year: int,
    hit: CountryHit,
) -> tuple[str | None, str | None]:
    """Trouve le slug FIRMS d'un pays pour (capteur, année). Renvoie (slug, url)."""
    sensor = ARCHIVE_SENSORS[sensor_key]
    for slug in hit.variants:
        url = f"{FIRMS_COUNTRY_BASE}/{sensor}/{year}/{sensor}_{year}_{slug}.csv"
        code = _probe(url)
        if code == 200:
            return slug, url
        if code not in (404, 403):
            logger.warning("probe %s → HTTP %s (variant suivante)", url, code)
    return None, None


def ensure_country_file(
    sensor_key: str,
    year: int,
    hit: CountryHit,
    archive_dir: str | Path,
) -> dict[str, Any]:
    """Garantit la présence locale du CSV annuel ; télécharge sinon.

    Renvoie un dict de traçabilité : pays, slug, chemin, statut, octets.
    """
    slug, url = resolve_country_file(sensor_key, year, hit)
    base = {"country": hit.name, "iso3": hit.iso3, "sensor": sensor_key,
            "year": year, "slug": slug}
    if slug is None:
        return {**base, "status": "unresolved", "path": None,
                "reason": "aucun nom de fichier FIRMS ne correspond (404 sur toutes les variantes)"}
    target = archive_path(archive_dir, sensor_key, year, slug)
    if target.exists() and target.stat().st_size > 0:
        return {**base, "status": "cached", "path": str(target),
                "bytes": target.stat().st_size}
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            _download_file(url, tmp)
            tmp.replace(target)
            return {**base, "status": "downloaded", "path": str(target),
                    "bytes": target.stat().st_size, "url": url.split("/data/")[-1]}
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            tmp.unlink(missing_ok=True)
            for part in target.parent.glob(target.stem + ".part*"):
                part.unlink(missing_ok=True)
            time.sleep(2 * (attempt + 1))
    return {**base, "status": "error", "path": None,
            "error": f"{type(last_exc).__name__}: {last_exc}"}


def _download_file(url: str, dest: Path, n_chunks: int = 6) -> None:
    """Télécharge ``url`` vers ``dest`` — parallélisé par plages HTTP si possible.

    Le serveur FIRMS archive est lent en flux simple (~Ko/s) mais accepte
    ``Accept-Ranges: bytes`` : on découpe le fichier en ``n_chunks`` plages
    téléchargées en parallèle puis assemblées. Repli flux unique si le
    serveur ne supporte pas les ranges ou si la taille est inconnue.
    """
    import concurrent.futures

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_S) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        accepts_ranges = (resp.headers.get("Accept-Ranges") or "").lower() == "bytes"
    if not accepts_ranges or total <= 0:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_S) as resp, \
                open(dest, "wb") as fh:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
        got = dest.stat().st_size
        if total and got != total:
            raise IOError(f"téléchargement tronqué : {got}/{total} octets")
        return

    chunk = max(1, math.ceil(total / n_chunks))
    ranges = [(i, min(total, (i + 1) * chunk) - 1) for i in range(n_chunks)]
    ranges = [(a, b) for a, b in ranges if a <= b]
    parts = [dest.with_suffix(f".part{i}") for i in range(len(ranges))]

    def _fetch_range(idx_a_b: tuple[int, int, Path]) -> None:
        i, (a, b), part = idx_a_b
        r = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Range": f"bytes={a}-{b}"}
        )
        with urllib.request.urlopen(r, timeout=FETCH_TIMEOUT_S) as resp, \
                open(part, "wb") as fh:
            while True:
                data = resp.read(1 << 20)
                if not data:
                    break
                fh.write(data)

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(ranges)) as pool:
            list(pool.map(_fetch_range, [(i, rb, parts[i]) for i, rb in enumerate(ranges)]))
        # vérifier chaque plage avant assemblage (connexion coupée = plage courte)
        expected = {i: b - a + 1 for i, (a, b) in enumerate(ranges)}
        for i, part in enumerate(parts):
            got = part.stat().st_size if part.exists() else 0
            if got != expected[i]:
                raise IOError(f"plage {i} tronquée : {got}/{expected[i]} octets")
        with open(dest, "wb") as out:
            for part in parts:
                out.write(part.read_bytes())
                part.unlink()
        if dest.stat().st_size != total:
            raise IOError(f"fichier tronqué : {dest.stat().st_size}/{total} octets")
    except Exception:
        for part in parts:
            part.unlink(missing_ok=True)
        raise
