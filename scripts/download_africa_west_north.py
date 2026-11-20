"""
Télécharger les données FIRMS open-access pour l'Afrique de l'Ouest
et l'Afrique du Nord (période 2019 → 2025, capteurs viirs-snpp + modis).

Utilisation :
    python scripts/download_africa_west_north.py [--region west|north|all]

Les fichiers sont stockés dans data/raw/archive/{sensor}/{year}_{Pays}.csv
(idempotent — les fichiers déjà présents sont ignorés). Retries avec backoff
pour les gros fichiers.

Slugs FIRMS validés (vérifier au premier lancement — certains pays peuvent
avoir des slugs spécifiques, ex. Cote_dIvoire, Guinea-Bissau, Western_Sahara).
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
USER_AGENT = "PyroLens/0.2 (+west-north-africa)"

# ── Afrique de l'Ouest (15 pays) ──
WEST_AFRICA = [
    "Mauritania",
    "Mali",
    "Algeria",        # frontalière Nord/Ouest
    "Morocco",
    "Western_Sahara",
    "Senegal",
    "Guinea-Bissau",
    "Guinea",
    "Sierra_Leone",
    "Liberia",
    "Cote_dIvoire",
    "Ghana",
    "Togo",
    "Benin",
    "Niger",
]

# ── Afrique du Nord (6 pays + Soudan) ──
NORTH_AFRICA = [
    "Algeria",
    "Morocco",
    "Tunisia",
    "Libya",
    "Egypt",
    "Sudan",
]

SENSORS = ["viirs-snpp", "modis"]
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

MAX_ATTEMPTS = 4
BASE_DELAY_S = 5
CHUNK_SIZE = 1 << 20  # 1 Mo


def select_countries(region: str) -> list[str]:
    if region == "west":
        return WEST_AFRICA
    if region == "north":
        return NORTH_AFRICA
    # all : union dédupliquée (Algeria + Morocco apparaissent dans les deux)
    return list(dict.fromkeys(WEST_AFRICA + NORTH_AFRICA))


def download_one(sensor: str, year: int, country: str) -> dict:
    url = f"{FIRMS_BASE}/{sensor}/{year}/{sensor}_{year}_{country}.csv"
    target = ARCHIVE_DIR / sensor / f"{year}_{country}.csv"

    if target.exists() and target.stat().st_size > 0:
        return {"country": country, "sensor": sensor, "year": year,
                "status": "cached", "bytes": target.stat().st_size}

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")
    last_exc: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=300) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                buf = bytearray()
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    buf.extend(chunk)
            if total and len(buf) != total:
                raise IOError(f"tronqué : {len(buf)}/{total}")
            tmp.write_bytes(bytes(buf))
            tmp.replace(target)
            return {"country": country, "sensor": sensor, "year": year,
                    "status": "downloaded", "bytes": len(buf)}
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                # pays inexistant dans FIRMS — on ne retente pas
                tmp.unlink(missing_ok=True)
                return {"country": country, "sensor": sensor, "year": year,
                        "status": "not_found", "error": "HTTP 404"}
            last_exc = exc
        except Exception as exc:
            last_exc = exc
            tmp.unlink(missing_ok=True)

        if attempt < MAX_ATTEMPTS:
            time.sleep(BASE_DELAY_S * attempt)

    return {"country": country, "sensor": sensor, "year": year,
            "status": "error", "error": str(last_exc)}


def main() -> None:
    region = "all"
    if "--region" in sys.argv:
        idx = sys.argv.index("--region")
        region = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "all"

    countries = select_countries(region)
    total_tasks = len(countries) * len(SENSORS) * len(YEARS)

    print(f"Afrique {region.upper()} — FIRMS open-access")
    print(f"  Pays    : {len(countries)} ({', '.join(countries)})")
    print(f"  Capteurs: {', '.join(SENSORS)}")
    print(f"  Années  : {YEARS[0]}-{YEARS[-1]}")
    print(f"  Tâches  : {total_tasks}")
    print(f"  Sortie  : {ARCHIVE_DIR}")
    print()

    manifest = []
    n = 0
    ok = cached = notfound = error = 0
    total_bytes = 0

    for country in countries:
        for sensor in SENSORS:
            for year in YEARS:
                n += 1
                print(f"  [{n}/{total_tasks}] {country} / {sensor} / {year} ... ", end="", flush=True)
                result = download_one(sensor, year, country)
                manifest.append(result)

                status = result["status"]
                if status == "downloaded":
                    ok += 1
                    total_bytes += result.get("bytes", 0)
                    print(f"OK ({result['bytes']:,} B)")
                elif status == "cached":
                    cached += 1
                    print(f"CACHED ({result.get('bytes', 0):,} B)")
                elif status == "not_found":
                    notfound += 1
                    print("404 (pays inexistant dans FIRMS)")
                else:
                    error += 1
                    print(f"ERREUR: {result.get('error', '?')}")

                if n % 10 == 0:
                    time.sleep(2)

    print(f"\n=== Résumé ({region}) ===")
    print(f"  Téléchargés : {ok}")
    print(f"  En cache    : {cached}")
    print(f"  Non trouvés : {notfound}")
    print(f"  Erreurs     : {error}")
    print(f"  Taille      : {total_bytes / (1024*1024):.1f} Mo")

    manifest_path = ARCHIVE_DIR / f"africa_{region}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"  Manifest    : {manifest_path}")

    if error > 0:
        print(f"\n⚠ {error} fichiers en échec — relancer pour retenter (idempotent).")
    if notfound > 0:
        print(f"ℹ {notfound} pays/années 404 — vérifier les slugs FIRMS.")


if __name__ == "__main__":
    main()
