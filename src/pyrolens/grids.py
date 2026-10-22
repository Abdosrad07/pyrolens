"""Grilles spatiales et fenêtres temporelles.

Clés d'ensemble formelles (voir docs/methodology.md) :
  - fenêtre 1 jour  -> clé = (cellule, date)
  - fenêtre W>1     -> clé = (cellule, fenêtre) où fenêtre = epoch_days // W
Les fenêtres sont alignées sur l'origine des jours entiers (epoch), pas sur le
début de mois : l'alignement est explicite pour être reproductible.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from math import floor
from typing import Iterable

ORIGIN_LON = -180.0
ORIGIN_LAT = -90.0


def cell_index(value: float, size: float, origin: float) -> int:
    """Index de cellule stable (arrondi à 1e-9 pour neutraliser l'erreur binaire).

    Sans cet arrondi, un point situé exactement sur une frontière de cellule
    (ex. 0,0° avec une maille de 0,10°) bascule d'une cellule selon la
    représentation binaire du pas, ce qui rendrait les clés instables.
    """
    return int(floor(round((value - origin) / size, 9)))


def cell_id(lon: float, lat: float, size: float) -> tuple[int, int]:
    return (
        cell_index(lon, size, ORIGIN_LON),
        cell_index(lat, size, ORIGIN_LAT),
    )


def cell_center(i: int, j: int, size: float) -> tuple[float, float]:
    lon = ORIGIN_LON + (i + 0.5) * size
    lat = ORIGIN_LAT + (j + 0.5) * size
    return lon, lat


def cell_key(i: int, j: int) -> str:
    return f"{i}:{j}"


def parse_date(value: str | date) -> date:
    """Accepte une chaîne AAAA-MM-JJ ou un objet date (jamais de conversion silencieuse)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = value.strip()
    # Chemin rapide AAAA-MM-JJ : strptime coûte ~12 µs, date() ~0,2 µs — mêmes
    # erreurs levées (ValueError) pour les dates invalides.
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        try:
            return date(int(text[:4]), int(text[5:7]), int(text[8:10]))
        except ValueError:
            pass  # format partiellement correct : strptime lèvera l'erreur standard
    return datetime.strptime(text, "%Y-%m-%d").date()


def epoch_days(d: date) -> int:
    return (d - date(1970, 1, 1)).days


def window_index(d: date, window_days: int) -> int:
    if window_days <= 0:
        raise ValueError("window_days doit être >= 1")
    return epoch_days(d) // window_days


def window_start(window_idx: int, window_days: int) -> date:
    return date(1970, 1, 1) + timedelta(days=window_idx * window_days)


def make_key(lon: float, lat: float, acq_date: str, grid_deg: float, window_days: int) -> str:
    """Clé d'ensemble (cellule, date) ou (cellule, fenêtre)."""
    i, j = cell_id(lon, lat, grid_deg)
    d = parse_date(acq_date)
    if window_days == 1:
        return f"{cell_key(i, j)}|{d.isoformat()}"
    return f"{cell_key(i, j)}|w{window_index(d, window_days)}"


def build_set(
    rows: Iterable[dict],
    grid_deg: float,
    window_days: int,
) -> set[str]:
    keys: set[str] = set()
    for row in rows:
        keys.add(make_key(row["longitude"], row["latitude"], row["acq_date"], grid_deg, window_days))
    return keys
