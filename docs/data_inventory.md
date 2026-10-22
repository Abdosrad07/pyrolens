# Inventaire des données — PyroLens phase 2

Date d'établissement : **octobre 2026**. Toutes les valeurs « réel » de ce document ont
été produites par exécution du pipeline (`pyrolens inventory`, `pyrolens download`,
`pyrolens geo`) dans cet environnement ; elles ne sont pas recopiées d'un autre document.

---

## 1. Périmètre

| Élément | Valeur | Source / justification |
|---|---|---|
| Période cible | **2013-01-01 → 2020-12-31** | choix du pilote ; vérifié couvert par les trois produits (cf. §3) |
| Région | Cameroun (ISO3 `CMR`) | pilote PyroLens |
| Emprise polygonale | **Natural Earth 110m `ne_110m_admin_0_countries`**, entité `ADM0_A3 = CMR` | téléchargée ce jour : HTTP 200, 838 726 octets, **SHA-256 `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`**, chemin `data/raw/geo/ne_110m_admin_0_countries.geojson` |
| Boîte englobante (bbox) | `[8.4, 4.1, 16.4, 13.2]` = ouest, sud, est, nord | **proxy de requête uniquement** (CMR, API FIRMS) |

> **Distinction bbox / frontière.** La bbox n'est **jamais** présentée comme les frontières
> du Cameroun : elle englobe des zones maritimes et des territoires voisins. Les détections
> sont rattachées au **polygon** (filtre `shapely`), la bbox servant uniquement à cadrer les
> requêtes. Le test `tests/test_emprise.py` vérifie qu'un point à l'intérieur de la bbox mais
> hors Cameroun est bien exclu du polygon. Une emprise à résolution 110 m reste grossière
> (détails de frontière) : pour une publication, migrer vers Natural Earth 10 m/50 m ou une
> source administrative officielle (documenté comme limite §8).

## 2. Statut d'accès aux trois familles de produits (vérifié par exécution)

| Produit | Statut standard | Méthode d'accès officielle | Test réel (oct. 2026) | Résultat |
|---|---|---|---|---|
| MODIS Terra `MOD14` C6.1 | standard (`version 061`) | LAADS/LP DAAC + **Earthdata Login** | GET granule LP DAAC | **HTTP 302 → urs.earthdata.nasa.gov** : bloqué sans authentification |
| MODIS Aqua `MYD14` C6.1 | standard (`version 061`) | idem | (même mécanisme) | bloqué — même cause |
| VIIRS S-NPP `VNP14IMG` | standard (`version 002`, Collection 2) | idem | (même mécanisme) | bloqué — même cause |
| FIRMS API (CSV par emprise) | sources standard **et** NRT exposées | `GET /api/area/csv/[MAP_KEY]/...` | sans clé | **HTTP 400 « Invalid MAP_KEY »** ; `data_availability` → **HTTP 401** |
| FIRMS Archive Download | NRT remplacé par le standard (~2-5 mois) | page web + Earthdata Login **ou** code e-mail | non exécuté (authentification) | non acquis |
| Géométrie d'emprise (Natural Earth) | non concerné | HTTPS public | GET | **HTTP 200 — acquis** (SHA-256 §1) |
| Métadonnées CMR (Earthdata) | non concerné | API publique sans clé | GET collections + granules | **HTTP 200 — acquis** |

**Aucun mécanisme d'authentification n'a été contourné.** Les échecs sont enregistrés dans
`data/manifests/downloads.json` avec leur code HTTP et dans `web/public/artifacts/execution.json`
(section `blockers`).

## 3. Inventaire CMR réel (exécuté : `pyrolens inventory`)

Source : **NASA CMR Search API** (`https://cmr.earthdata.nasa.gov/search`), accès public.
Emprise de requête = bbox §1 ; période = 2013-2020. Fichier brut :
`data/raw/cmr/inventory.json` (copie : `web/public/artifacts/inventory.json`).

### Versions de collection disponibles

| Produit | short_name | version configurée | version réellement trouvée | couverture CMR |
|---|---|---|---|---|
| MODIS Terra | `MOD14` | 061 | **061** (autre version exposée : `6.1NRT`, depuis 2021-02-07) | 2000-02-24 → |
| MODIS Aqua | `MYD14` | 061 | **061** (autre : `6.1NRT`) | 2002-07-04 → |
| VIIRS S-NPP 375 m | `VNP14IMG` | 002 | **002** | 2012-01-17 → |

→ Les trois produits **couvrent intégralement la période cible 2013-2020 en traitement
scientifique standard** (et non en NRT). La variante `6.1NRT` n'existe qu'à partir de 2021
et n'est **pas** utilisée.

### Nombre de granules dans la bbox, par année (réel, compté via `CMR-Hits`)

| Année | MOD14 (Terra) | MYD14 (Aqua) | VNP14IMG (S-NPP) |
|---:|---:|---:|---:|
| 2013 | 1 354 | 1 407 | 1 628 |
| 2014 | 1 356 | 1 408 | 1 626 |
| 2015 | 1 376 | 1 406 | 1 634 |
| 2016 | 1 334 | 1 386 | 1 612 |
| 2017 | 1 349 | 1 364 | 1 634 |
| 2018 | 1 403 | 1 411 | 1 637 |
| 2019 | 1 350 | 1 377 | 1 643 |
| 2020 | 1 356 | 1 324 | 1 644 |
| **Total** | **10 878** | **11 083** | **13 058** |

Total cumulé : **35 019 granules** dans la bbox sur la période (commande : `pyrolens inventory`).
Exemples de granules réellement référencés : `MOD14.A2019001.0925.061.2021351024504`,
`MYD14.A2019001.0000.061.2021351022955`, `VNP14IMG.A2018365.2354.002.2024082201002`.

**Interprétation** : ces compteurs de granules sont des métadonnées d'inventaire
(existence et couverture), **pas** un décompte de détections. Ils ne disent rien sur le
nombre de feux.

## 4. Ce qui a réellement été acquis

| Fichier | Origine | Provenance | SHA-256 |
|---|---|---|---|
| `data/raw/geo/ne_110m_admin_0_countries.geojson` | Natural Earth (source primaire naciscdn.org) | `pyrolens geo` | `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f` |
| `data/raw/cmr/inventory.json` | NASA CMR Search API (public) | `pyrolens inventory` | calculé à l'exécution (fichier texte) |
| `data/raw/firms/modis_sp_*.csv`, `viirs_snpp_sp_*.csv` | **API FIRMS réelle** (clé `FIRMS_MAP_KEY`) | `pyrolens download` puis `pyrolens normalize` | 1 170 fenêtres canoniques de 5 jours (585 + 585), 2013-01-01 → 2020-12-31, 0 jour manquant ; SHA-256 par entrée dans `data/manifests/downloads.json` (9 802 requêtes journalisées) |
| `data/manifests/normalize.json` | journal de provenance local | `pyrolens normalize` | dédoublonnage vérifié : 1 432 → 1 170 fenêtres, 557 292 doublons stricts supprimés (5 017 580 → 4 460 288 lignes) |
| `data/manifests/downloads.json` | journal de provenance local | `pyrolens download` | — |
| `data/fixture/SYNTHETIC_*.csv` | **SYNTHÉTIQUE**, graine 20260101 | `pyrolens fixture` | déterministe (testé) |

## 5. Ce qui n'a PAS été acquis (blocage exact)

| Donnée voulue | Blocage | Preuve HTTP | Action minimale attendue de l'utilisateur |
|---|---|---|---|
| ~~Détections MODIS/VIIRS 2013-2020 (CSV FIRMS)~~ | **acquis** le 2026-10-18 avec `FIRMS_MAP_KEY` | 200 | — (voir §4) |
| Granules L2 standard (MOD14 / MYD14 / VNP14IMG, HDF) | **Earthdata Login absent** | 302 → `urs.earthdata.nasa.gov` | créer un compte Earthdata gratuit, puis renseigner `EARTHDATA_USER` + `EARTHDATA_PASSWORD`, **ou** `EARTHDATA_TOKEN`, **ou** un `~/.netrc` contenant `urs.earthdata.nasa.gov` |
| Produits d'observabilité (MOD35_L2, MOD09GA, MOD03/MYD03) | mêmes credentials Earthdata | 302 | idem ; leur absence maintient l'état « observabilité inconnue » |

**Aucun secret n'est à transmettre dans le chat** : les valeurs passent par l'interface
Environment du projet, puis sont lues par le pipeline via `os.environ`.

## 6. État actuel des données d'exécution

**Données réelles acquises** : `data/raw/firms/` contient 1 170 fenêtres canoniques
(585 MODIS + 585 VIIRS, 2013-2020, 0 jour manquant). L'audit, les baselines,
l'observabilité, les figures et le rapport récents portent tous
`"data_origin": "nasa_firms"`. L'échantillon synthétique (`data/fixture/`, `SYNTHETIC_*`)
reste en place pour la démo et les tests ; il n'est **plus** utilisé par les rapports
publics.

Toujours bloqué sans identifiants Earthdata (§5) : granules standard et produits de
couverture/nuages — d'où l'état par défaut « observabilité inconnue » de l'observabilité.

Reproduction : `pyrolens download` (idempotent, fenêtres déjà écrites ignorées) →
`pyrolens normalize` → `pyrolens audit --source data/raw/firms` → `pyrolens baselines` →
`pyrolens observability` → `pyrolens figures` → `pyrolens report` (ou `pyrolens run`).

## 7. Organisation du stockage (aucune base de données, aucun service payant)

```
data/raw/            données brutes acquises, JAMAIS modifiées (testé : tests/test_reproducibility.py)
data/raw/geo/        géométrie d'emprise
data/raw/cmr/        métadonnées CMR
data/raw/firms/      CSV FIRMS acquis + fenêtres canoniques 5 j normalisées
data/fixture/        échantillon SYNTHÉTIQUE de démonstration
data/manifests/      SHA-256 + provenance + codes HTTP (downloads.json, downloads_geo.json)
reports/             data_quality_audit.md, anomalies/*.csv, logs/*.log, scientific_report.md/.docx
baselines/           summary.csv, jaccard_monthly.csv, daily_divergence.csv, monthly_divergence.csv,
                     spatial_distribution.csv, regional_divergence.csv, observability_states.csv
figures/             PNG (copiés vers web/public/artifacts/figures/)
web/public/artifacts/ artefacts JSON consommés par le frontend
```

## 8. Limites de l'inventaire

- Comptages **granules** uniquement : aucun décompte de détections avant acquisition des CSV.
- bbox de requête ≠ frontière (voir §1) ; un granule intersecte la bbox sans nécessairement
  couvrir le polygon.
- Résolution de la géométrie d'emprise : Natural Earth **110 m** (frontières simplifiées).
- Les fichiers HDF des granules exigent une chaîne de lecture HDF4/HDF5 non installée ici :
  l'ingestion retenue à ce stade est l'**API FIRMS / CSV** (mêmes définitions d'attributs,
  cf. `docs/references.md` §2), les granules restant la voie de référence pour un contrôle
  d'intégrité produit à produit.
- Les produits de couverture/nuages (MOD35_L2, MOD09GA) ne sont pas encore inventoriés
  individuellement au niveau granule : leur acquisition est conditionnée aux mêmes
  credentials et reste à faire (architecturée par tuiles/périodes, voir `docs/methodology.md` §6).
