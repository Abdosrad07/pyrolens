"""Générateur d'échantillon SYNTHÉTIQUE (non scientifique).

Cet échantillon sert UNIQUEMENT à exécuter et tester le pipeline quand les
données NASA réelles sont bloquées (Earthdata Login / FIRMS MAP_KEY). Toutes
les fichiers produits portent data_origin = "synthetic_fixture" et les rapports
l'indiquent en évidence. Ce sont des nombres de démonstration, jamais des
mesures du Cameroun.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

HEADER_MODIS = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,confidence,version,frp,daynight,type"
HEADER_VIIRS = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,frp,daynight,type"

BBOX = (8.4, 4.1, 16.4, 13.2)  # [west, south, east, north]
NIGHT_ZONES = [  # clusters (lon, lat, sigma) — agrégats synthétiques
    (12.4, 9.6, 1.1),   # Nord
    (11.5, 7.2, 1.0),   # Ouest / collines
    (14.2, 5.4, 0.9),   # Sud-Est
    (10.5, 4.9, 0.8),   # Sud-Ouest
]


_POLYGON_CACHE: dict[str, object] = {}


def _cameroon_polygon():
    """Polygone réel Natural Earth si disponible (les points synthétiques restent dans le pays)."""
    if "geom" not in _POLYGON_CACHE:
        path = (
            Path(__file__).resolve().parents[2]
            / "data" / "raw" / "geo" / "ne_110m_admin_0_countries.geojson"
        )
        geom = None
        if path.exists():
            try:
                from .emprise import load_region_polygon

                geom = load_region_polygon(path, "CMR")
            except Exception:  # noqa: BLE001
                geom = None
        _POLYGON_CACHE["geom"] = geom
    return _POLYGON_CACHE["geom"]


def _sample_point(rng: random.Random) -> tuple[float, float]:
    lon0, lat0, sigma = rng.choice(NIGHT_ZONES)
    geom = _cameroon_polygon()
    for _ in range(30):
        lon = max(BBOX[0], min(BBOX[2], rng.gauss(lon0, sigma)))
        lat = max(BBOX[1], min(BBOX[3], rng.gauss(lat0, sigma)))
        if geom is None:
            break
        from shapely.geometry import Point

        if geom.contains(Point(lon, lat)):
            break
    return round(lon, 4), round(lat, 4)


def _mkrow(rng: random.Random, d: date, satellite: str, intensity: float, kind: str,
            point: tuple[float, float]) -> str:
    # Même événement pour les trois capteurs : léger bruit de géolocalisation
    # (emprise de pixel / géolocalisation propre à l'instrument), jamais une
    # localisation "corrigée".
    lon = point[0] + rng.gauss(0.0, 0.03)
    lat = point[1] + rng.gauss(0.0, 0.03)
    lon = max(BBOX[0], min(BBOX[2], lon))
    lat = max(BBOX[1], min(BBOX[3], lat))
    hh = (10 if satellite == "Terra" else 13) + rng.randint(0, 1)
    mm = rng.randint(0, 59)
    time = hh * 100 + mm
    if kind == "modis":
        conf = max(0, min(100, int(rng.gauss(30 + 60 * intensity, 15))))
        version = "6.1NRT"
        brightness = round(rng.gauss(300 + 60 * intensity, 15), 1)
        frp = round(max(0.1, rng.gauss(3 + 40 * intensity, 6)), 1)
    else:
        conf = "high" if intensity > 0.75 else ("nominal" if intensity > 0.4 else "low")
        version = "2.0NRT"
        brightness = round(rng.gauss(320 + 60 * intensity, 20), 1)
        frp = round(max(0.1, rng.gauss(1.5 + 25 * intensity, 5)), 1)
    scan = round(rng.uniform(0.8, 1.6), 2)
    track = round(rng.uniform(0.8, 1.6), 2)
    daynight = "D" if 6 <= hh <= 18 else "N"
    return (
        f"{lat},{lon},{brightness},{scan},{track},{d.isoformat()},{time},"
        f"{satellite},{conf},{version},{frp},{daynight},0"
    )


def generate(start: date, end: date, seed: int = 20260101) -> dict[str, list[str]]:
    """Retourne {nom_fichier: [lignes_csv]} pour les trois capteurs (2019 par défaut)."""
    rng = random.Random(seed)
    rows: dict[str, list[str]] = {
        "SYNTHETIC_MODIS_terra_2019.csv": [HEADER_MODIS],
        "SYNTHETIC_MODIS_aqua_2019.csv": [HEADER_MODIS],
        "SYNTHETIC_VIIRS_snpp_2019.csv": [HEADER_VIIRS],
    }
    keys = list(rows)
    d = start
    while d <= end:
        n_events = rng.randint(0, 6)
        for _ in range(n_events):
            intensity = rng.random()
            event_point = _sample_point(rng)
            # L'événement est "vu" par chaque capteur avec une probabilité liée à
            # son intensité ET à sa résolution (VIIRS 375 m détecte plus de petits feux).
            for key in keys:
                lower_key = key.lower()
                if "viirs_snpp" in lower_key:
                    p_detect = min(0.97, 0.35 + 0.75 * intensity)
                    kind = "viirs"
                    sat = "N"
                elif "_aqua" in lower_key:
                    p_detect = min(0.9, 0.15 + 0.7 * intensity)
                    kind = "modis"
                    sat = "Aqua"
                else:
                    p_detect = min(0.9, 0.12 + 0.68 * intensity)
                    kind = "modis"
                    sat = "Terra"
                if rng.random() < p_detect:
                    rows[key].append(_mkrow(rng, d, sat, intensity, kind, event_point))
        d += timedelta(days=1)
    return rows


def inject_anomalies(rows: list[str]) -> list[str]:
    """Insère des anomalies explicites (conservées brutes, jamais corrigées)."""
    out = list(rows)
    if len(out) < 6:
        return out
    out.insert(2, "12.031,14.401,320.1")                                    # champ manquant
    out.insert(5, "999.0,10.500,310.0,1.1,1.1,2019-01-02,1120,Terra,61,6.1NRT,4.2,D,0")   # lat hors plage
    out.insert(8, "5.45,,305.2,1.0,1.0,2019-01-03,1145,Terra,55,6.1NRT,3.9,D,0")           # lon manquant
    out.insert(11, "6.123,12.456,300.0,1.0,1.0,03/01/2019,1110,Terra,50,6.1NRT,3.0,D,0")   # date invalide
    out.insert(14, "7.777,13.333,301.0,1.0,1.0,2019-01-04,2560,Terra,50,6.1NRT,3.0,D,0")   # heure invalide
    out.insert(17, "8.888,14.444,302.0,1.0,1.0,2019-01-05,1230,Terra,50,6.1NRT,-2.5,D,0")  # FRP négatif
    out.insert(20, "9.000,10.000,303.0,1.0,1.0,2019-01-06,1300,Terra,fort,6.1NRT,4.0,D,0") # confiance invalide
    out.insert(23, "60.500,130.500,304.0,1.0,1.0,2019-01-07,1315,Terra,70,6.1NRT,4.0,D,0") # hors emprise + hors bbox monde
    out.insert(26, out[26])                                              # doublon strict
    out.insert(27, "20.10/20.10/20.10")                                  # ligne mal formée
    return out


def write_fixture(out_dir: Path, start: date, end: date, seed: int = 20260101) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, lines in generate(start, end, seed=seed).items():
        if "MODIS_terra" in name:
            lines = inject_anomalies(lines)
        target = out_dir / name
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(target)
    readme = out_dir / "README.md"
    readme.write_text(
        "# Échantillon SYNTHÉTIQUE de démonstration\n\n"
        "Ces fichiers sont **générés par `pyrolens fixture`** (graine déterministe) pour "
        "exécuter et tester le pipeline lorsque les données NASA réelles sont bloquées "
        "(Earthdata Login / FIRMS MAP_KEY absents de l'environnement).\n\n"
        "**Ils ne contiennent aucune détection réelle.** Toute métrique calculée sur ces "
        "fichiers porte `data_origin = synthetic_fixture` et ne doit pas être interprétée "
        "comme un résultat scientifique sur le Cameroun.\n",
        encoding="utf-8",
    )
    written.append(readme)
    return written
