#!/usr/bin/env python3
"""Téléchargement en masse de l'archive FIRMS pays — Afrique de l'Ouest, 2013-2025.

Reprenable : chaque fichier complété est en cache sous data/raw/archive/ et
n'est jamais retéléchargé. Un manifest JSONL trace chaque tentative.

Usage : PYTHONPATH=src python scripts/download_west_africa_archive.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyrolens.archive import CountryHit, ensure_country_file, _name_variants  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / "data" / "raw" / "archive"
MANIFEST = ROOT / "data" / "manifests" / "archive_bulk_west_africa.jsonl"
GEOJSON = ROOT / "data" / "raw" / "geo" / "ne_110m_admin_0_countries.geojson"

YEARS = list(range(2013, 2026))
SENSORS = ["viirs", "modis"]

# Noms Natural Earth (geojson 110m) + variantes FIRMS supplémentaires
COUNTRIES = [
    ("Benin", "BEN"),
    ("Burkina Faso", "BFA"),
    ("Ghana", "GHA"),
    ("Guinea", "GIN"),
    ("Guinea-Bissau", "GNB", ["Guinea_Bissau", "GuineaBissau", "Guinea-Bissau", "GNB"]),
    ("Liberia", "LBR"),
    ("Mali", "MLI"),
    ("Mauritania", "MRT"),
    ("Niger", "NER"),
    ("Nigeria", "NGA"),
    ("Senegal", "SEN"),
    ("Sierra Leone", "SLE"),
    ("Togo", "TGO"),
    ("Cameroon", "CMR"),
    ("Chad", "TCD"),
    # absents du geojson 110m — variantes manuelles
    ("Côte d'Ivoire", "CIV", ["Cote_d'Ivoire", "Cote d'Ivoire", "CotedIvoire", "Ivory_Coast", "IvoryCoast", "CIV"]),
    ("Cape Verde", "CPV", ["Cape_Verde", "Cabo_Verde", "CapeVerde", "CaboVerde", "CPV"]),
]


def _geo_names() -> dict[str, str]:
    data = json.loads(GEOJSON.read_text(encoding="utf-8"))
    return {
        f["properties"].get("NAME"): f["properties"].get("NAME")
        for f in data.get("features", [])
    }


def build_hits() -> list[CountryHit]:
    hits = []
    for entry in COUNTRIES:
        name, iso3 = entry[0], entry[1]
        extra = entry[2] if len(entry) > 2 else []
        variants = _name_variants(name) + [v.replace(" ", "_") for v in extra]
        hits.append(CountryHit(iso3=iso3, name=name, variants=variants))
    return hits


def main() -> int:
    hits = build_hits()
    total = len(hits) * len(SENSORS) * len(YEARS)
    done = skipped = errors = unresolved = 0
    t0 = time.time()
    print(f"{len(hits)} pays × {len(SENSORS)} capteurs × {len(YEARS)} ans = {total} fichiers")
    print(f"Archive : {ARCHIVE_DIR} — manifest : {MANIFEST}")

    with MANIFEST.open("a", encoding="utf-8") as mf:
        for hit in hits:
            for sensor in SENSORS:
                for year in YEARS:
                    try:
                        res = ensure_country_file(sensor, year, hit, archive_dir=ARCHIVE_DIR)
                    except Exception as exc:  # noqa: BLE001
                        res = {"status": "error", "reason": str(exc)[:200]}
                    status = res.get("status")
                    rec = {
                        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "country": hit.name,
                        "iso3": hit.iso3,
                        "sensor": sensor,
                        "year": year,
                        "status": status,
                        "slug": res.get("slug"),
                        "bytes": res.get("bytes"),
                        "reason": res.get("reason"),
                        "elapsed_s": round(time.time() - t0, 1),
                    }
                    mf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    mf.flush()
                    if status == "cached":
                        skipped += 1
                    elif status in ("downloaded", "ok"):
                        done += 1
                        print(f"[{done+skipped+errors+unresolved}/{total}] {sensor} {year} {hit.name} -> {status} {res.get('bytes',0)//1024} Ko")
                    elif status == "unresolved":
                        unresolved += 1
                        print(f"  ? non résolu : {sensor} {year} {hit.name}")
                    else:
                        errors += 1
                        print(f"  ! erreur : {sensor} {year} {hit.name} — {res.get('reason','')[:120]}")
                    time.sleep(0.2)  # politesse : le serveur bride les rafales de sondes
    print(f"Terminé en {round(time.time()-t0)} s — téléchargés={done} cachés={skipped} erreurs={errors} non_résolus={unresolved}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
