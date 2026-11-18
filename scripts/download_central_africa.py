"""
Télécharger les données FIRMS open-access pour l'Afrique centrale
(Cameroun, Congo, DRC, Gabon, Tchad, RCA, Guinée équatoriale, São Tomé).

Période : 2019 → 2025 (archive annuelle FIRMS, sans clé API).
Capteurs : viirs-snpp + modis.

Utilisation :
    python scripts/download_central_africa.py

Les fichiers sont stockés dans data/raw/archive/{sensor}/{year}_{Pays}.csv
(idempotent — les fichiers déjà présents sont ignorés).
Retries automatiques avec backoff pour les gros fichiers DRC.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / "data" / "raw" / "archive"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/data/country"
USER_AGENT = "PyroLens/0.2 (+central-africa)"

# Pays d'Afrique centrale (slugs FIRMS validés)
COUNTRIES = [
    "Cameroon",
    "Chad",
    "Central_African_Republic",
    "Gabon",
    "Republic_of_Congo",
    "Democratic_Republic_of_the_Congo",
    "Equatorial_Guinea",
    "Sao_Tome_and_Principe",
]

# Capteurs (identifiants FIRMS archive)
SENSORS = ["viirs-snpp", "modis"]

# Années disponibles (2026 → 404, donc jusqu'à 2025)
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

# Config retries
MAX_ATTEMPTS = 4
BASE_DELAY_S = 5
CHUNK_SIZE = 1 << 20  # 1 Mo


def download_one(sensor: str, year: int, country: str) -> dict:
    """Télécharge un fichier FIRMS archive avec retries chunk par chunk."""
    url = f"{FIRMS_BASE}/{sensor}/{year}/{sensor}_{year}_{country}.csv"
    target = ARCHIVE_DIR / sensor / f"{year}_{country}.csv"

    # Cache : déjà présent ?
    if target.exists() and target.stat().st_size > 0:
        return {"country": country, "sensor": sensor, "year": year, "status": "cached", "bytes": target.stat().st_size}

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")

    last_exc: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=300) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                data = bytearray()
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    data.extend(chunk)

            if total and len(data) != total:
                raise IOError(f"tronqué : {len(data)}/{total}")

            tmp.write_bytes(bytes(data))
            tmp.replace(target)
            return {"country": country, "sensor": sensor, "year": year, "status": "downloaded", "bytes": len(data)}

        except Exception as exc:
            last_exc = exc
            tmp.unlink(missing_ok=True)
            if attempt < MAX_ATTEMPTS:
                delay = BASE_DELAY_S * attempt
                print(f"  (retry {attempt}/{MAX_ATTEMPTS-1} en {delay}s — {exc}) ... ", end="", flush=True)
                time.sleep(delay)

    return {"country": country, "sensor": sensor, "year": year, "status": "error", "error": str(last_exc)}


def main():
    total_tasks = len(COUNTRIES) * len(SENSORS) * len(YEARS)
    print(f"Afrique centrale — FIRMS open-access")
    print(f"  Pays    : {len(COUNTRIES)} ({', '.join(COUNTRIES)})")
    print(f"  Capteurs: {', '.join(SENSORS)}")
    print(f"  Années  : {YEARS[0]}-{YEARS[-1]}")
    print(f"  Tâches  : {total_tasks}")
    print(f"  Retries : {MAX_ATTEMPTS} par fichier (backoff {BASE_DELAY_S}s)")
    print(f"  Sortie  : {ARCHIVE_DIR}")
    print()

    manifest = []
    n = 0
    ok = cached = error = 0
    total_bytes = 0

    for country in COUNTRIES:
        for sensor in SENSORS:
            for year in YEARS:
                n += 1
                label = f"  [{n}/{total_tasks}] {country} / {sensor} / {year} ... "
                print(label, end="", flush=True)

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
                else:
                    error += 1
                    print(f"ERREUR: {result.get('error', '?')}")

                # Pause courte entre pays (throttle FIRMS)
                if n % 10 == 0:
                    time.sleep(2)

    # Résumé
    print(f"\n=== Résumé ===")
    print(f"  Téléchargés : {ok}")
    print(f"  En cache    : {cached}")
    print(f"  Erreurs     : {error}")
    print(f"  Taille totale: {total_bytes / (1024*1024):.1f} Mo")

    # Manifest JSON
    manifest_path = ARCHIVE_DIR / "central_africa_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"  Manifest    : {manifest_path}")

    if error > 0:
        print(f"\n⚠ {error} fichiers en échec — relancer le script pour les retenter (idempotent).")


if __name__ == "__main__":
    main()
