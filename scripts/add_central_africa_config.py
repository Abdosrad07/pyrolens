"""
Ajoute la section "central_africa" dans pipeline.yaml pour couvrir
les 8 pays d'Afrique centrale (2019-2025) en plus du Cameroun (pilot).

Le mode d'analyse multi-pays est activé par le champ `region.presets`.
"""

from __future__ import annotations

from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config" / "pipeline.yaml"

CENTRAL_AFRICA_SECTION = """
# ── Afrique centrale — extension du jeu de données (2019 → 2025) ──────────
# Les 8 pays ci-dessous sont disponibles via l'archive FIRMS open-access
# (fichier annuel par pays, sans clé API). La période 2019-2025 correspond
# à la couverture VIIRS SNPP + MODIS SP. Les années 2013-2018 (pilot CMR)
# restent sur le mode FIRMS API (clé requise).
#
# Pour activer l'analyse multi-pays, utiliser :
#   pyrolens analyze --preset central-africa
# ou directement :
#   POST /api/v1/firms/analyze { "region_preset": "central_africa" }

central_africa:
  name: "Afrique centrale"
  countries:
    - Cameroon
    - Chad
    - Central_African_Republic
    - Gabon
    - Republic_of_Congo
    - Democratic_Republic_of_the_Congo
    - Equatorial_Guinea
    - Sao_Tome_and_Principe
  sensors:
    viirs: viirs-snpp
    modis: modis
  period:
    start: "2019-01-01"
    end: "2025-12-31"
  grid_deg: 0.25
  window_days: 8
  data_origin: nasa_firms_open_access
"""

def main():
    text = CONFIG.read_text(encoding="utf-8")

    if "central_africa:" in text:
        print("Section central_africa déjà présente dans pipeline.yaml — aucune action.")
        return

    # Insérer avant la fin du fichier (ou après la section paths)
    # On ajoute simplement en fin de fichier avec un commentaire
    new_text = text.rstrip() + "\n\n" + CENTRAL_AFRICA_SECTION + "\n"
    CONFIG.write_text(new_text, encoding="utf-8")
    print(f"Section central_africa ajoutée dans {CONFIG}")

if __name__ == "__main__":
    main()
