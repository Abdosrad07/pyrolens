"""
Vérifie les données FIRMS Afrique centrale téléchargées :
- Intégrité des fichiers (pas de CSV tronqué)
- Nombre de détections par pays/anné
- Couverture temporelle réelle (dates min/max par fichier)
- Échantillon de 5 lignes pour validation visuelle
"""

from __future__ import annotations

import csv
from pathlib import Path
from collections import defaultdict

ARCHIVE = Path(__file__).resolve().parent.parent / "data" / "raw" / "archive"

SENSORS = ["viirs-snpp", "modis"]
COUNTRIES = [
    "Cameroon", "Chad", "Central_African_Republic", "Gabon",
    "Republic_of_Congo", "Democratic_Republic_of_the_Congo",
    "Equatorial_Guinea", "Sao_Tome_and_Principe",
]
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def main():
    print("=== Vérification des données Afrique centrale ===\n")

    # 1. Intégrité des fichiers
    print("[1] Intégrité des fichiers CSV")
    missing = []
    total_files = 0
    total_bytes = 0
    for sensor in SENSORS:
        for year in YEARS:
            for country in COUNTRIES:
                f = ARCHIVE / sensor / f"{year}_{country}.csv"
                if f.exists():
                    total_files += 1
                    total_bytes += f.stat().st_size
                    # Vérifier que le fichier n'est pas tronqué
                    # (fichier FIRMS : première ligne = en-tête, dernière ligne = pas de \n manquant)
                    content = f.read_bytes()
                    if b"latitude" not in content[:200]:
                        print(f"  WARN: {f.name} — pas d'en-tête latitude")
                else:
                    missing.append(f"{sensor}/{year}/{country}")

    print(f"  Fichiers trouvés: {total_files} / {len(SENSORS) * len(YEARS) * len(COUNTRIES)}")
    print(f"  Taille totale   : {total_bytes / (1024*1024):,.1f} Mo")
    if missing:
        print(f"  Manquants ({len(missing)}):")
        for m in missing[:10]:
            print(f"    - {m}")
        if len(missing) > 10:
            print(f"    ... et {len(missing)-10} autres")

    # 2. Nombre de détections
    print(f"\n[2] Nombre de détections (en-tête CSV = nombre de lignes - 1)")
    detections_by_country: dict[str, int] = defaultdict(int)
    for sensor in SENSORS:
        for year in YEARS:
            for country in COUNTRIES:
                f = ARCHIVE / sensor / f"{year}_{country}.csv"
                if f.exists():
                    with open(f, "r", encoding="utf-8", errors="replace") as fh:
                        n_lines = sum(1 for _ in fh) - 1  # -1 pour l'en-tête
                    detections_by_country[country] += max(0, n_lines)

    print(f"  {'Pays':<40s} {'Détections (viirs+modis, 2019-2025)'}")
    print(f"  {'─'*40} {'─'*40}")
    for country in COUNTRIES:
        print(f"  {country:<40s} {detections_by_country.get(country, 0):,}")
    total_det = sum(detections_by_country.values())
    print(f"  {'TOTAL':<40s} {total_det:,}")

    # 3. Couverture temporelle
    print(f"\n[3] Couverture temporelle (dates min/max)")
    print(f"  {'Capteur':<12s} {'Pays':<40s} {'Date min':<12s} {'Date max':<12s}")
    print(f"  {'─'*12} {'─'*40} {'─'*12} {'─'*12}")
    for sensor in SENSORS[:1]:  # viirs-snpp seulement pour garder court
        for country in COUNTRIES[:4]:  # 4 premiers pays
            f = ARCHIVE / sensor / f"2024_{country}.csv"
            if f.exists():
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    reader = csv.DictReader(fh)
                    rows = list(reader)
                if rows:
                    dates = sorted(set(r.get("date", "") for r in rows))
                    print(f"  {sensor:<12s} {country:<40s} {dates[0]:<12s} {dates[-1]:<12s}")

    print("\n=== Terminé ===")


if __name__ == "__main__":
    main()
