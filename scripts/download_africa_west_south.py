"""
Télécharger les données FIRMS open-access pour l'Afrique de l'Ouest et du Sud
(période 2019 → 2025, capteurs viirs-snpp + modis).

Usage :
    python scripts/download_africa_west_south.py [--region west|south|all]

Idempotent — fichiers déjà présents ignorés. Retries + backoff. Manifest JSON.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / "data" / "raw" / "archive"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/data/country"
USER_AGENT = "PyroLens/0.2 (+west-south-africa)"

WEST_AFRICA = [
    "Mauritania","Mali","Algeria","Morocco","Western_Sahara",
    "Senegal","Guinea-Bissau","Guinea","Sierra_Leone","Liberia",
    "Cote_dIvoire","Ghana","Togo","Benin","Niger",
]

SOUTH_AFRICA = [
    "Angola","Zambia","Malawi","Mozambique","Zimbabwe",
    "Botswana","Namibia","South_Africa","Eswatini","Lesotho",
]

SENSORS = ["viirs-snpp", "modis"]
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
MAX_ATTEMPTS = 4
BASE_DELAY_S = 5
CHUNK_SIZE = 1 << 20


def select_countries(region):
    if region == "west":
        return WEST_AFRICA
    if region == "south":
        return SOUTH_AFRICA
    return list(dict.fromkeys(WEST_AFRICA + SOUTH_AFRICA))


def download_one(sensor, year, country):
    url = f"{FIRMS_BASE}/{sensor}/{year}/{sensor}_{year}_{country}.csv"
    target = ARCHIVE_DIR / sensor / f"{year}_{country}.csv"

    if target.exists() and target.stat().st_size > 0:
        return {"status": "cached", "bytes": target.stat().st_size}

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")
    last_exc = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=300) as resp:
                buf = bytearray()
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    buf.extend(chunk)
            tmp.write_bytes(bytes(buf))
            tmp.replace(target)
            return {"status": "downloaded", "bytes": len(buf)}
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                tmp.unlink(missing_ok=True)
                return {"status": "not_found", "error": "HTTP 404"}
            last_exc = exc
        except Exception as exc:
            last_exc = exc
            tmp.unlink(missing_ok=True)

        if attempt < MAX_ATTEMPTS:
            time.sleep(BASE_DELAY_S * attempt)

    return {"status": "error", "error": str(last_exc)}


def main():
    region = "all"
    if "--region" in sys.argv:
        idx = sys.argv.index("--region")
        region = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "all"

    countries = select_countries(region)
    total = len(countries) * len(SENSORS) * len(YEARS)

    print(f"Afrique {region.upper()} — FIRMS open-access")
    print(f"  Pays    : {len(countries)} ({', '.join(countries)})")
    print(f"  Capteurs: {', '.join(SENSORS)}")
    print(f"  Annees  : {YEARS[0]}-{YEARS[-1]}")
    print(f"  Taches  : {total}")
    print(f"  Sortie  : {ARCHIVE_DIR}")
    print()

    manifest = []
    n = ok = cached = nf = err = 0
    total_bytes = 0

    for country in countries:
        for sensor in SENSORS:
            for year in YEARS:
                n += 1
                print(f"  [{n}/{total}] {country} / {sensor} / {year} ... ", end="", flush=True)
                result = download_one(sensor, year, country)
                result["country"] = country
                result["sensor"] = sensor
                result["year"] = year
                manifest.append(result)

                status = result["status"]
                if status == "downloaded":
                    ok += 1
                    total_bytes += result.get("bytes", 0)
                    print(f"OK ({result['bytes']:,} B)")
                elif status == "cached":
                    cached += 1
                    print(f"CACHE ({result.get('bytes', 0):,} B)")
                elif status == "not_found":
                    nf += 1
                    print("404 (inexistant)")
                else:
                    err += 1
                    print(f"ERREUR: {result.get('error', '?')}")

                if n % 10 == 0:
                    time.sleep(2)

    print(f"\n=== Resume {region} ===")
    print(f"  Downloades : {ok}")
    print(f"  En cache   : {cached}")
    print(f"  404        : {nf}")
    print(f"  Erreurs    : {err}")
    print(f"  Taille     : {total_bytes / (1024*1024):.1f} Mo")

    manifest_path = ARCHIVE_DIR / f"africa_{region}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"  Manifest   : {manifest_path}")

    if err > 0:
        print(f"\n⚠ {err} fichiers en echec — relancer pour retenter (idempotent).")
    if nf > 0:
        print(f"ℹ {nf} pays/annees 404 — verifier les slugs FIRMS.")


if __name__ == "__main__":
    main()
