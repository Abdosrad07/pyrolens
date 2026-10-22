"""Schéma des fichiers FIRMS : normalisation des colonnes et règles par capteur.

Règle de rigueur : les niveaux de confiance MODIS ( numérique 0-100, classes
low/nominal/high ) et VIIRS ( catégories low/nominal/high ) sont validés selon
leur propre sémantique et NE SONT JAMAIS ramenés à une échelle numérique
commune.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Colonnes attendues (noms FIRMS officiels, en minuscules)
CORE_COLUMNS = ("latitude", "longitude", "acq_date", "acq_time", "satellite")
RECOMMENDED_COLUMNS = ("frp", "confidence", "version", "daynight")
OPTIONAL_COLUMNS = (
    "brightness",
    "bright_ti4",
    "bright_ti5",
    "scan",
    "track",
    "type",
    "sensor",
)

COLUMN_ALIASES = {
    "lat": "latitude",
    "latitude": "latitude",
    "lon": "longitude",
    "lng": "longitude",
    "long": "longitude",
    "longitude": "longitude",
    "acq_date": "acq_date",
    "acquisition_date": "acq_date",
    "date": "acq_date",
    "acq_time": "acq_time",
    "acquisition_time": "acq_time",
    "time": "acq_time",
    "sat": "satellite",
    "satellite": "satellite",
    "sensor": "sensor",
    "conf": "confidence",
    "confidence": "confidence",
    "frp": "frp",
    "fire_radiative_power": "frp",
    "daynight": "daynight",
    "day_night": "daynight",
    "dn": "daynight",
    "version": "version",
    "brightness": "brightness",
    "bright_ti4": "bright_ti4",
    "bright_ti5": "bright_ti5",
    "scan": "scan",
    "track": "track",
    "type": "type",
}

VIIRS_CONFIDENCE_CATEGORIES = {"low", "nominal", "high"}
# Échelle littérale réellement émise par FIRMS pour VIIRS : l = low, n = normal,
# h = high. On ACCEPTE la valeur brute sans la convertir vers une autre échelle.
VIIRS_CONFIDENCE_LETTERS = {"l", "n", "h"}
MODIS_LEGACY_CATEGORIES = {"low", "nominal", "high", "medium"}


def normalize_column(name: str) -> str:
    key = name.strip().lower().replace(" ", "_")
    return COLUMN_ALIASES.get(key, key)


def normalize_header(header: list[str]) -> list[str]:
    return [normalize_column(c) for c in header]


@dataclass
class SensorSpec:
    key: str                 # "modis" | "viirs" | "unknown"
    label: str
    satellites: set[str] = field(default_factory=set)
    confidence_kind: str = "unknown"   # "numeric_0_100" | "categorical" | "either"


MODIS_SPEC = SensorSpec(
    key="modis",
    label="MODIS (Terra/Aqua)",
    satellites={"Terra", "Aqua"},
    confidence_kind="numeric_0_100",
)

VIIRS_SPEC = SensorSpec(
    key="viirs",
    label="VIIRS Suomi-NPP 375 m",
    satellites={"N", "1", "2"},
    confidence_kind="categorical",
)

UNKNOWN_SPEC = SensorSpec(key="unknown", label="Inconnu")


def spec_from_name(name: str) -> SensorSpec:
    """Déduit le capteur d'un nom de fichier (MOD14/MYD14/MCD14 vs VNP14...)."""
    lower = name.lower()
    if any(token in lower for token in ("vnp14", "vj114", "viirs", "snpp")):
        return VIIRS_SPEC
    if any(token in lower for token in ("mod14", "myd14", "mcd14", "modis")):
        return MODIS_SPEC
    return UNKNOWN_SPEC


def spec_from_records(satellites: set[str]) -> SensorSpec:
    """Déduit le capteur à partir des valeurs de la colonne satellite."""
    if not satellites:
        return UNKNOWN_SPEC
    if satellites <= {"Terra", "Aqua"}:
        return MODIS_SPEC
    if satellites <= {"N", "1", "2"}:
        return VIIRS_SPEC
    return UNKNOWN_SPEC


def validate_confidence(value: str, spec: SensorSpec) -> tuple[bool, str | None]:
    """Valide une valeur de confiance SANS la convertir vers une autre échelle.

    Retourne (valide, motif_d_anomalie éventuel).
    """
    raw = value.strip()
    if raw == "":
        return False, "confiance manquante"
    low = raw.lower()
    if spec.key == "modis":
        if low in MODIS_LEGACY_CATEGORIES:
            return True, None
        try:
            num = float(raw)
        except ValueError:
            return False, f"confiance MODIS non numérique : {raw!r}"
        if 0.0 <= num <= 100.0:
            return True, None
        return False, f"confiance MODIS hors échelle 0-100 : {raw!r}"
    if spec.key == "viirs":
        if low in VIIRS_CONFIDENCE_CATEGORIES or low in VIIRS_CONFIDENCE_LETTERS:
            return True, None
        # Les distributions standard VIIRS parfois numériques restent acceptées
        # comme valeur brute, sans conversion.
        try:
            float(raw)
            return True, None
        except ValueError:
            return False, f"confiance VIIRS hors catégories low/nominal/high : {raw!r}"
    return True, None
