"""Audit de qualité des données (fichiers FIRMS).

Principes :
  - le contenu brut est toujours conservé ;
  - chaque anomalie conserve son numéro de ligne, sa colonne et son motif ;
  - aucune latitude/longitude n'est jamais corrigée parce qu'une autre valeur
    "paraîtrait plus plausible" ;
  - toute reconstruction doit être démontrable et déclarée dans la config
    (règles vides par défaut -> zéro reconstruction) ;
  - l'absence de détection n'est JAMAIS interprétée comme une absence de feu.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from .emprise import inside_mask, region_of
from .grids import parse_date
from .ingest import Anomaly, ParsedFile, parse_csv_file
from .schema import (
    CORE_COLUMNS,
    spec_from_name,
    spec_from_records,
    validate_confidence,
)

CLASSIFICATION_BY_CATEGORY = {
    "malformed_row": "excluded",
    "missing_required_column": "excluded",
    "invalid_latitude": "excluded",
    "invalid_longitude": "excluded",
    "invalid_date": "excluded",
    "invalid_time": "excluded",
    "outside_emprise": "ambiguous",
    "invalid_frp": "ambiguous",
    "invalid_confidence": "ambiguous",
    "missing_value": "ambiguous",
    "duplicate_row": "ambiguous",
    "duplicate_key": "ambiguous",
}


def classify(category: str) -> str:
    return CLASSIFICATION_BY_CATEGORY.get(category, "ambiguous")


def _add(anomalies: list[Anomaly], file: str, line: int, column: str, value: str, category: str, reason: str) -> None:
    anomalies.append(
        Anomaly(
            file=file,
            line_number=line,
            column=column,
            raw_value=value,
            category=category,
            reason=reason,
            classification=classify(category),
        )
    )


@dataclass
class FileAudit:
    path: Path
    sensor: str                     # modis | viirs | unknown
    header: list[str]
    n_physical_lines: int
    n_records: int                  # lignes bien formées
    rows: list[dict[str, Any]] = field(default_factory=list)   # lignes analysables (déjà filtrées)
    anomalies: list[Anomaly] = field(default_factory=list)
    counts: Counter = field(default_factory=Counter)
    volumes_by_day: Counter = field(default_factory=Counter)
    volumes_by_month: Counter = field(default_factory=Counter)
    frp_values: list[float] = field(default_factory=list)
    confidence_values: Counter = field(default_factory=Counter)
    satellites: set[str] = field(default_factory=set)
    versions: set[str] = field(default_factory=set)
    dates: list[date] = field(default_factory=list)


def _parse_time(raw: str) -> int | None:
    text = raw.strip()
    if not text:
        return None
    if text.endswith(".0"):
        text = text[:-2]
    if not text.isdigit():
        return None
    if len(text) <= 4:
        # Les CSV FIRMS écrivent HHMM sans zéro de tête quand l'heure < 10 :
        # "21" = 00:21, "136" = 01:36, "931" = 09:31. On complète seulement
        # (aucune autre transformation) ; au-delà de 4 chiffres, invalide.
        text = text.zfill(4)
    if len(text) != 4:
        return None
    hh, mm = int(text[:2]), int(text[2:])
    if hh > 23 or mm > 59:
        return None
    return hh * 100 + mm


def audit_file(
    path: str | Path,
    bbox: list[float],
    iso3: str = "CMR",
    geometry=None,
    n_regions: int = 3,
) -> FileAudit:
    """Audite un fichier FIRMS et retourne ses lignes analysables + anomalies."""
    p = Path(path)
    parsed: ParsedFile = parse_csv_file(p)
    result = FileAudit(
        path=p,
        sensor="unknown",
        header=parsed.header,
        n_physical_lines=parsed.n_physical_lines if hasattr(parsed, "n_physical_lines") else 0,
        n_records=len(parsed.records),
    )
    result.anomalies.extend(parsed.anomalies)

    # Colonnes obligatoires
    missing = [c for c in CORE_COLUMNS if c not in parsed.header]
    for col in missing:
        _add(result.anomalies, p.name, 1, col, "", "missing_required_column", "colonne obligatoire absente")
    if missing:
        return result

    result.sensor = spec_from_name(p.name).key
    file = p.name

    # Sélection des colonnes analysables
    usable_idx: list[int] = []
    usable_records: list[dict[str, str]] = []
    for idx, rec in zip(parsed.record_lines, parsed.records):
        usable_idx.append(idx)
        usable_records.append(rec)

    # Parsing coordonnées / dates (sans jamais corriger)
    lat_vals: list[float | None] = []
    lon_vals: list[float | None] = []
    for line, rec in zip(usable_idx, usable_records):
        lat_raw, lon_raw = rec.get("latitude", ""), rec.get("longitude", "")
        try:
            lat = float(lat_raw)
            if not -90.0 <= lat <= 90.0:
                raise ValueError
        except ValueError:
            lat = None
            _add(result.anomalies, file, line, "latitude", lat_raw, "invalid_latitude",
                 "latitude non numérique ou hors [-90;90] (aucune correction appliquée)")
        try:
            lon = float(lon_raw)
            if not -180.0 <= lon <= 180.0:
                raise ValueError
        except ValueError:
            lon = None
            _add(result.anomalies, file, line, "longitude", lon_raw, "invalid_longitude",
                 "longitude non numérique ou hors [-180;180] (aucune correction appliquée)")
        lat_vals.append(lat)
        lon_vals.append(lon)

    date_vals: list[date | None] = []
    for line, rec in zip(usable_idx, usable_records):
        raw = rec.get("acq_date", "")
        try:
            date_vals.append(parse_date(raw))
        except ValueError:
            date_vals.append(None)
            _add(result.anomalies, file, line, "acq_date", raw, "invalid_date",
                 "date d'acquisition non interprétable au format AAAA-MM-JJ")

    time_vals: list[int | None] = []
    for line, rec in zip(usable_idx, usable_records):
        raw = rec.get("acq_time", "")
        t = _parse_time(raw)
        if t is None:
            _add(result.anomalies, file, line, "acq_time", raw, "invalid_time",
                 "heure d'acquisition HHMM invalide")
        time_vals.append(t)

    # Satellites / capteur
    for rec in usable_records:
        sat = rec.get("satellite", "").strip()
        if sat:
            result.satellites.add(sat)
    detected = spec_from_records(result.satellites)
    if detected.key != "unknown":
        result.sensor = detected.key
    sensor_spec = detected if detected.key != "unknown" else spec_from_name(p.name)

    # Test point-in-polygon en UN SEUL appel par fichier : identique au test
    # unitaire (même shapely.contains_xy dans emprise.inside_mask), mais sans
    # l'appel par point (~6 µs × N) qui rendait l'audit trop lent sur CSV réels.
    inside_flags: list[bool | None] = [None] * len(lat_vals)
    if geometry is not None:
        idx_valid = [i for i, (la, lo) in enumerate(zip(lat_vals, lon_vals))
                     if la is not None and lo is not None]
        if idx_valid:
            flags = inside_mask(geometry,
                                [lon_vals[i] for i in idx_valid],
                                [lat_vals[i] for i in idx_valid])
            for i, flag in zip(idx_valid, flags):
                inside_flags[i] = flag

    # FRP, confiance, valeurs manquantes, emprise
    for pos, ((line, rec), lat, lon, d, t) in enumerate(zip(
        zip(usable_idx, usable_records), lat_vals, lon_vals, date_vals, time_vals
    )):
        for col in CORE_COLUMNS:
            if not rec.get(col, "").strip():
                _add(result.anomalies, file, line, col, "", "missing_value", "valeur obligatoire manquante")

        frp_raw = rec.get("frp", "")
        frp: float | None
        if frp_raw.strip() == "":
            frp = None
            if "frp" in parsed.header:
                _add(result.anomalies, file, line, "frp", frp_raw, "missing_value", "FRP manquant")
        else:
            try:
                frp = float(frp_raw)
                if frp < 0:
                    _add(result.anomalies, file, line, "frp", frp_raw, "invalid_frp", "FRP négatif")
                    frp = None
            except ValueError:
                frp = None
                _add(result.anomalies, file, line, "frp", frp_raw, "invalid_frp", "FRP non numérique")

        conf_raw = rec.get("confidence", "")
        if "confidence" in parsed.header and conf_raw.strip() != "":
            ok, reason = validate_confidence(conf_raw, sensor_spec)
            if not ok:
                _add(result.anomalies, file, line, "confidence", conf_raw, "invalid_confidence", reason or "")
            else:
                result.confidence_values[f"{sensor_spec.key}:{conf_raw.strip()}"] += 1
        elif "confidence" in parsed.header:
            result.confidence_values[f"{sensor_spec.key}:<vide>"] += 1

        outside = None
        if lat is not None and lon is not None:
            in_bbox = bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]
            if not in_bbox:
                outside = True
                _add(result.anomalies, file, line, "latitude,longitude", f"{lat},{lon}",
                     "outside_emprise", "hors bbox de l'emprise documentée")
            elif geometry is not None and not inside_flags[pos]:
                outside = True
                _add(result.anomalies, file, line, "latitude,longitude", f"{lat},{lon}",
                     "outside_emprise", "hors polygon administratif (bbox englobante uniquement)")
            else:
                outside = False

        if lat is None or lon is None or d is None or t is None:
            result.counts["rows_excluded"] += 1
            continue
        if outside:
            result.counts["rows_outside_emprise"] += 1
            continue

        result.rows.append(
            {
                "latitude": lat,
                "longitude": lon,
                "acq_date": d,
                "acq_time": t,
                "satellite": rec.get("satellite", "").strip(),
                "frp": frp,
                "confidence": rec.get("confidence", "").strip(),
                "version": rec.get("version", "").strip(),
                "daynight": rec.get("daynight", "").strip(),
                "sensor": sensor_spec.key,
                "region": region_of(lon, lat, bbox, n_regions),
                "line_number": line,
                "file": file,
            }
        )

    # Doublons (sur les lignes analysables)
    seen_full: Counter = Counter()
    seen_key: Counter = Counter()
    kept_rows: list[dict[str, Any]] = []
    for row in result.rows:
        full = (
            row["latitude"], row["longitude"], row["acq_date"], row["acq_time"],
            row["satellite"], row["frp"], row["confidence"],
        )
        key = (row["latitude"], row["longitude"], row["acq_date"], row["acq_time"], row["satellite"])
        seen_full[full] += 1
        if seen_full[full] > 1:
            _add(result.anomalies, file, row["line_number"], "<ligne>", str(full),
                 "duplicate_row", "ligne strictement identique déjà rencontrée")
            result.counts["duplicate_rows"] += 1
            continue
        seen_key[key] += 1
        if seen_key[key] > 1:
            _add(result.anomalies, file, row["line_number"], "<clé>", str(key),
                 "duplicate_key", "même (lat,lon,date,heure,satellite) déjà présent")
            result.counts["duplicate_keys"] += 1
            continue
        kept_rows.append(row)
    result.rows = kept_rows

    # Agrégats
    for row in result.rows:
        d: date = row["acq_date"]
        result.volumes_by_day[f"{row['sensor']}|{d.isoformat()}"] += 1
        result.volumes_by_month[f"{row['sensor']}|{d.strftime('%Y-%m')}"] += 1
        result.dates.append(d)
        if row["frp"] is not None:
            result.frp_values.append(row["frp"])
        if row["version"]:
            result.versions.add(row["version"])

    result.counts["rows_analysable"] = len(result.rows)
    return result


def temporal_gaps(audits: Iterable[FileAudit]) -> list[dict[str, Any]]:
    """Jours sans aucun enregistrement pour un capteur, dans sa propre plage couverte.

    Interprétation : "aucun enregistrement ce jour-là", JAMAIS "pas de feu".
    """
    per_sensor: dict[str, list[date]] = defaultdict(list)
    for audit in audits:
        for d in audit.dates:
            per_sensor[audit.sensor].append(d)

    gaps: list[dict[str, Any]] = []
    for sensor, dates in sorted(per_sensor.items()):
        lo, hi = min(dates), max(dates)
        present = set(dates)
        current = lo
        count = 0
        while current <= hi:
            if current not in present:
                count += 1
                if len(gaps) < 5000:
                    gaps.append(
                        {
                            "sensor": sensor,
                            "date": current.isoformat(),
                            "interpretation": "aucun_enregistrement",
                        }
                    )
            current += timedelta(days=1)
        if count:
            gaps.append(
                {
                    "sensor": sensor,
                    "date": "*",
                    "interpretation": f"{count} jours sans enregistrement entre {lo} et {hi}",
                }
            )
    return gaps


def write_anomaly_csvs(audits: list[FileAudit], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    fieldnames = ["file", "line_number", "column", "raw_value", "category", "reason", "classification"]
    for audit in audits:
        if not audit.anomalies:
            continue
        target = out_dir / f"{audit.path.stem}__anomalies.csv"
        with target.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for anomaly in audit.anomalies:
                writer.writerow(anomaly.as_row())
        written.append(target)
    return written
