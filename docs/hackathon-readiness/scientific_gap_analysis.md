# Écarts scientifiques — PyroLens face au défi « Harmonization of MODIS and VIIRS Hot Spots »

## 1. Question de recherche du défi vs mise en œuvre PyroLens

| Attendu par le défi | Réalité PyroLens | Écart |
|---|---|---|
| Rapprocher MODIS Terra, MODIS Aqua, VIIRS S-NPP | Fait au niveau des clés d'ensemble (Jaccard) | Partiel |
| Harmoniser spatialement (diff. résolution 1 km vs 375 m) | Fait : grilles 0,10 / 0,25 / 0,50°, sensibilité publiée | Opérationnel |
| Harmoniser temporellement (heures de passage, fenêtres) | Fait : fenêtres 1/4/8/16 jours, clés alignées sur l'epoch | Opérationnel |
| Gérer observations manquantes | Fait : état « inconnu », jamais « pas de feu » | Opérationnel mais par défaut |
| Valider scientifiquement (seuils, référence externe) | **Non fait** (H4-H6 bloqués) | **Écart critique** |
| Corriger / évaluer le FRP | **Non fait** (géométrie d'observation absente) | **Écart critique** |

## 2. Sources de données (évaluation A)

| Critère | État | Preuve |
|---|---|---|
| Authenticité / provenance | Réelles (NASA FIRMS API) | `data_origin = nasa_firms`, `downloads.json`, `data_inventory.md` |
| MODIS Terra (MOD14 C6.1) | Acquis via FIRMS | `config/pipeline.yaml`, `sensors.terra` |
| MODIS Aqua (MYD14 C6.1) | Acquis via FIRMS | `config/pipeline.yaml`, `sensors.aqua` |
| VIIRS S-NPP 375 m (VNP14IMG C2) | Acquis via FIRMS | `config/pipeline.yaml`, `sensors.viirs_snpp` |
| Couverture géographique | Cameroun (ISO3 CMR), polygon Natural Earth 110 m | `pipeline.yaml`, `data/raw/geo/` |
| Couverture temporelle | 2013-01-01 → 2020-12-31, 0 jour manquant | `data_inventory.md` §4 |
| Qualité fichiers | Audit qualité : 2 634 700 anomalies classées, 0 ligne mal formée sur données réelles | `audit.json`, `data_validation.md` §4 |
| Granules standard (HDF) | **Non accessibles** (Earthdata Login) | `download.py`, `downloads.json` (HTTP 302) |
| Produits couverture/nuages | **Non accessibles** (même cause) | `pipeline.yaml` `coverage_products_acquired: false` |

**Constat** : les détections FIRMS sont authentiques et complètes. En revanche, les granules standard et produits d'observabilité sont bloqués, ce qui interdit tout contrôle d'intégrité produit-à-produit et toute attribution de conditions d'observation plausibles.

## 3. Harmonisation (évaluation B)

### H1 — Représentation (schéma commun)
- **Statut** : EXÉCUTÉ sur données réelles (18/10/2026).
- **Preuve** : `harmonization.py` H1, `audit.json` : 4 460 288 lignes bien formées, 0 mal formée, 0 colonne de confiance fusionnée.
- **Évaluation** : conforme. Les confiances MODIS (0-100) et VIIRS (low/nominal/high) sont conservées distinctes, jamais converties.

### H2 — Spatiale (grille commune)
- **Statut** : EXÉCUTÉ sur données réelles.
- **Preuve** : `baselines/summary.csv`, 24 configs, Jaccard 0,102715 → 0,658829.
- **Évaluation** : conforme. L'effet mécanique de la maille est documenté comme tel (pas d'amélioration présentée comme telle).

### H3 — Temporel (fenêtres alignées)
- **Statut** : EXÉCUTÉ sur données réelles.
- **Preuve** : `baselines.py` clés `(cellule, fenêtre)` alignées sur l'epoch.
- **Évaluation** : conforme.

### H4 — Seuils de confiance
- **Statut** : NON EXÉCUTÉ.
- **Cause** : aucune référence indépendante (registre au sol, pyrométrie, autre agence) dans l'environnement (D5).
- **Conséquence** : aucun seuil de sélection par classe ne peut être calé ni évalué. L'affirmation « seuils de confiance » est impossible à ce stade.

### H5 — Calibration FRP avec covariables géométriques
- **Statut** : NON EXÉCUTÉ.
- **Cause** : géométrie d'observation (MOD03/MYD03) non acquise (blocage Earthdata D4).
- **Conséquence** : aucune correction de FRP par angle de vue, taille de pixel ou scan/track.

### H6 — Validation externe
- **Statut** : NON EXÉCUTÉ.
- **Cause** : pas de référence indépendante (D5). Split temporel/régional possible mais non exécuté (lot S4).
- **Conséquence** : aucune méthode ne peut être déclarée validée.

## 4. Évaluation scientifique (évaluation C)

### Métriques utilisées
- **Jaccard** = |A ∩ B| / |A ∪ B| sur clés d'ensemble. Mesure un **recouvrement**, pas une précision de détection.
- **Divergences** mensuelles/journalières (A seulement, B seulement, les deux).
- **Distribution spatiale** (top 30 cellules, configuration primaire).
- **Divergence régionale** (terciles de latitude, proxy documenté et arbitraire).

### Risque de présentation abusive
Le code et la documentation explicitent à plusieurs reprises que le Jaccard n'est pas une précision (`docs/methodology.md` §1 non-objectifs, `harmonization.py` warning, `api/routers/system.py` `/meta` note d'interprétation). Ce risque est maîtrisé dans le code. Cependant, le frontend `Baselines.jsx` présente un heatmap du Jaccard sans légende explicite rappelant « recouvrement ≠ précision » sur chaque cellule — mineure mais à corriger pour une démonstration.

### Reproductibilité
- Configuration versionnée (`pipeline.yaml`).
- Commandes documentées (`README.md`, `docs/technical.md` §2).
- Tests 31/31 documentés verts.
- `data/raw` immuable (SHA-256 avant/après, `test_reproducibility.py`).
- **Limite** : `data/raw/firms/` ignoré par git (>330 Mo), reproduction nécessite `pyrolens download` avec clés FIRMS.

### Limites méthodologiques (déjà assumées par le projet)
1. Pas de mise en correspondance événement-à-événement (non justifiable sans géométrie d'observation).
2. Pas de référence indépendante → validation externe impossible.
3. Emprise 110 m (frontières simplifiées).
4. Aucun produit d'observabilité → état par défaut « inconnu ».

## 5. Différences entre produit actuel et produit attendu

Le défi demande de l'**harmonisation effective** (approche, validation, crédibilité scientifique). PyroLens livre actuellement :
- Une **baseline de concordance** (Jaccard, 24 configs) — utile, mais ce n'est pas une méthode d'harmonisation validée.
- Une **infrastructure** (pipeline, API, frontend) prête à recevoir des expériences d'harmonisation — mais sans UI dédiée (Harmonization Lab, Fire Calendar absents).

**Écart scientifique principal** : le projet mesure le recouvrement entre capteurs mais n'harmonise pas encore les détections au sens du défi (pas de seuils H4, pas de calibration FRP H5, pas de validation externe H6).