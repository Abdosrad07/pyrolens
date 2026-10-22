# Références — PyroLens phase 2

Règle de citation : **seules les pages ci-dessous ont été effectivement consultées et
lues** dans cette session (octobre 2026). Les pages qui n'ont pas pu être lues sont
listées en fin de document avec la raison exacte. Aucun article n'est cité sur la base
d'un simple extrait de résultat de recherche.

Chaque entrée indique : (1) la question scientifique qu'elle permet de traiter,
(2) les variables/produits disponibles, (3) les contraintes d'accès,
(4) la période couverte, (5) les limites pour PyroLens.

---

## 1. Accès et services FIRMS (NASA LANCE)

### 1.1 Archive Download — FIRMS
- **URL** : https://firms.modaps.eosdis.nasa.gov/download/
- **Titre** : *Archive Download - NASA | LANCE* — **Organisme** : NASA LANCE FIRMS
- **Date affichée** : aucune date de mise à jour sur la page.
- **Question traitée** : où obtenir les détections historiques et depuis quand.
- **Produits / variables** : détections de points chauds MODIS et VIIRS en SHP, CSV, JSON ;
  couverture **MODIS Collection 6.1 à partir du 1er novembre 2000** et
  **VIIRS S-NPP 375 m à partir du 20 janvier 2012**.
- **Contraintes d'accès** : téléchargement possible par Earthdata Login **ou** code
  d'accès envoyé par e-mail ; les fichiers de moins de 7 jours relèvent du NRT.
- **Période couverte** : 2000 → aujourd'hui (MODIS C6.1), 2012 → aujourd'hui (VIIRS S-NPP 375 m).
- **Limites pour PyroLens** : les enregistrements NRT sont **remplacés** par les données
  standard « science-quality » avec un décalage d'environ cinq mois ; une extraction
  récente n'est donc **pas** une archive de traitement standard.

### 1.2 Active Fire Data (description des périodes par plateforme)
- **URL** : https://firms.modaps.eosdis.nasa.gov/content/active_fire/
- **Titre** : *Active Fire Data* — **Organisme** : NASA LANCE FIRMS
- **Question traitée** : disponibilité temporelle par capteur ; statut NRT vs standard.
- **Produits / variables** : MODIS C6.1 (Terra depuis novembre 2000, Aqua depuis juillet 2002),
  VIIRS S-NPP 375 m depuis le 20 janvier 2012 ; périodes NOAA-20 et NOAA-21 également listées.
- **Contraintes** : fichiers jour récents en texte ; Earthdata Login pour les archives.
- **Limites pour PyroLens** : la page précise le remplacement NRT → standard (2-3 mois,
  jusqu'à 5 mois) : distinguer explicitement les deux flux dans toute collection.

### 1.3 Documentation de l'API FIRMS
- **URL** : https://firms.modaps.eosdis.nasa.gov/api/ — **version API affichée : 4.2.0**
- **Titre** : *NASA | LANCE | FIRMS (API)* — **Organisme** : NASA LANCE FIRMS
- **Question traitée** : quelles requêtes automatisables pour l'ingestion.
- **Services** : `area`, `countries`, `country`, `data_availability`, `map_key`, recherche de données manquantes.
- **Contraintes** : **clé MAP_KEY obligatoire** ; la page signale les fonctions
  `country` / `countries` actuellement indisponibles.
- **Limites** : la zone couverte par `area` est limitée (1 à 5 jours par requête),
  ce qui impose un découpage périodique pour 2013-2020.

### 1.4 Clé MAP_KEY
- **URL** : https://firms.modaps.eosdis.nasa.gov/api/map_key/
- **Titre** : *API - Map Key* — **Organisme** : NASA LANCE FIRMS
- **Question traitée** : condition d'accès aux services web FIRMS.
- **Contraintes** : MAP_KEY gratuite envoyée par e-mail à l'inscription ;
  limite de **5 000 transactions / 10 minutes** (une grande requête peut compter pour plusieurs).
- **Limites** : la clé est un secret d'environnement — jamais versionnée (voir README).

### 1.5 Endpoint `area` (CSV)
- **URL** : https://firms.modaps.eosdis.nasa.gov/api/area/
- **Question traitée** : format de requête par emprise.
- **Contenu** : `/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]`,
  sources NRT **et** traitement standard, bornes [ouest,sud,est,nord], plage 1-5 jours,
  date optionnelle pour les requêtes historiques.
- **Limites** : volumétrie à découper ; le format de réponse doit être vérifié
  ligne d'en-tête par ligne d'en-tête (cf. audit).

### 1.6 Endpoint `data_availability`
- **URL** : https://firms.modaps.eosdis.nasa.gov/api/data_availability/
- **Question traitée** : quelles années/produits sont réellement exposés par FIRMS.
- **Contenu** : `/api/data_availability/csv/[MAP_KEY]/[SENSOR]`, identifiants de sources
  MODIS NRT et traitement standard, VIIRS S-NPP standard, etc.
- **Contraintes** : MAP_KEY obligatoire (voir §10 — **non exécutable dans cet environnement**).

### 1.7 Tutoriel Python FIRMS API
- **URL** : https://firms.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html
- **Titre** : *NASA FIRMS - How to use FIRMS API in Python*
- **Question traitée** : patron de requête, dataset IDs, distinction NRT / standard.
- **Limites** : le patron `country` y est décrit alors que la page API signale
  l'indisponibilité actuelle de cette fonction — à re-vérifier avant tout usage.

## 2. Description des attributs et interprétation

### 2.1 Attributs MODIS (MOD14/MYD14/MCD14)
- **URL** : https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html
- **Titre** : *MODIS Fire and Thermal Anomalies* — **Organisme** : NASA FIRMS
- **Variables** : latitude/longitude (centre du pixel 1 km), brightness, scan/track,
  acq_date/acq_time (UTC), satellite (Terra/Aqua), **confiance 0-100 %** (classes
  low/nominal/high), version (URT/RT/NRT/standard), **FRP (MW, intégré au pixel)**, daynight.
- **Couverture** : Terra depuis le 1er novembre 2000 ; Aqua depuis le 3 juillet 2002.
- **Limites pour PyroLens** : la confiance MODIS est **numérique 0-100** — ne jamais la
  relier à l'échelle catégorielle VIIRS ; le centre du pixel n'est pas la position du feu.

### 2.2 Attributs VIIRS 375 m
- **URL** : https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html
- **Titre** : *VIIRS Fire and Thermal Anomalies* — **Organisme** : NASA FIRMS
- **Variables** : bright_ti4/bright_ti5, scan/track (taille réelle du pixel),
  acq_date/acq_time, satellite (N = Suomi-NPP, 1 = NOAA-20, 2 = NOAA-21),
  **confiance catégorielle low / nominal / high**, version (suffixe NRT), FRP (MW), daynight.
- **Sémantique** : low = brouillard solaire possible / anomalie < 15 K le jour ;
  nominal = anomalie > 15 K ; high = pixel saturé.
- **Limites pour PyroLens** : FRP 375 m systématique fondé sur une approche hybride
  375/750 m, saturation fréquente de I4 → caractérisation sous-pixel fiable surtout
  pour les petits feux ; **pas de conversion de confiance vers une échelle numérique commune**.

### 2.3 Attributs FIRMS (NASA Earthdata)
- **URL** : https://www.earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs
- **Titre** : *Active Fire Data Attributes for MODIS and VIIRS* — **Organisme** : NASA Earthdata
- **Question traitée** : définitions communes des champs ; FRP = puissance radiative
  intégrée au pixel en MW ; confiance MODIS numérique vs confiance VIIRS catégorielle.
- **Limites** : page centrée sur les flux NRT ; les définitions de confiance ne sont pas
  interchangeables entre capteurs.

### 2.4 FIRMS FAQ
- **URL** : https://www.earthdata.nasa.gov/data/tools/firms/faq
- **Titre** : *FIRMS FAQ* — **Organisme** : NASA Earthdata
- **Dates citées par la page** : guides utilisateurs mis à jour **juin 2025** (VIIRS C2) et
  **mai 2021** (MODIS C6/C6.1).
- **Question traitée** : standard vs URT/RT/NRT ; horaires de passage (Terra ~10 h 30,
  Aqua et S-NPP ~13 h 30 locales) ; couverture MODIS 1-2 jours, VIIRS ~12 h ;
  détection = centre de pixel classifié, pas position exacte du feu ; géolocalisation NRT
  dégradée possible (erreurs de plusieurs km après manœuvres ou événements spatiaux).
- **Limites** : précieux pour l'interprétation, mais ne fournit **pas** de produit de
  couverture d'observation par cellule.

## 3. Produits de traitement standard (LAADS DAAC / LP DAAC)

| URL | Titre | Organisme | Contenu clé | Accès |
|---|---|---|---|---|
| https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD14 | *MOD14 - MODIS/Terra Thermal Anomalies/Fire 5-Min L2 Swath 1km* | NASA LAADS DAAC | L2, 5 min, 1 km, Collection 6.1 (ArchiveSet 61) | Earthdata Login |
| https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MYD14 | *MYD14 - MODIS/Aqua ... 1km* | NASA LAADS DAAC | équivalent Aqua, Collection 6.1 | Earthdata Login |
| https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP14IMG/ | *VNP14IMG - VIIRS/NPP Active Fires 6-Min L2 Swath 375m* | NASA LAADS DAAC | L2 375 m, Collection 2 (ArchiveSet 5200, VIIRS data 2.0) | Earthdata Login |
| https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD14A1 | *MOD14A1* | NASA LAADS DAAC | L3 journalier 1 km griddé, C6.1 | Earthdata Login |
| https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MYD14A1 | *MYD14A1* | NASA LAADS DAAC | L3 journalier 1 km griddé, C6.1 | Earthdata Login |
| https://ladsweb.modaps.eosdis.nasa.gov/learn/how-to-view-and-find-data-at-laads-daac/ | *How To View & Find Data At LAADS DAAC* | NASA LAADS DAAC | procédure de recherche/commande : **Earthdata Login requis** | Earthdata Login |
| https://www.earthdata.nasa.gov/data/earthdata-login | *Earthdata Login* | NASA Earthdata | inscription obligatoire pour télécharger depuis les DAAC ; pages d'information libres | inscription |

**Écart constaté sur `VNP14IMG`** : la fiche LAADS indique une résolution temporelle
« 5 minutes » (convention granule) alors que NASA décrit des acquisitions VIIRS de
6 minutes ; les deux sont des conventions de catalogue, **pas** un intervalle de revisit.

## 4. Statut de validation (NASA)

- **MOD14 (MODIS Terra Collection 6)** — *Status for: Thermal Anomalies/Fire (MOD14)*,
  NASA MODIS Land Team, https://modis-land.gsfc.nasa.gov/ValStatus.php?ProductID=MOD14
  (statut produit mis à jour **novembre 2019**) : **validation Stage 3 pour la détection**
  (~2 500 scènes ASTER, ~16 000 pixels feu diurnes, ~700 nocturnes ; erreur d'omission
  proche de 5 % pour les grands feux) mais **Stage 1 pour le FRP** (incertitude TOA
  potentiellement ~50 % selon les conditions d'observation).
  → *Limite PyroLens* : « détection MODIS validée » ≠ « FRP MODIS validé ».
- **VIIRS (VNP14 / VNP14IMG)** — *VIIRS NASA Fire Product Validation*,
  NASA VIIRS Land Products, https://viirsland.gsfc.nasa.gov/Val/Fire_Val.html
  (page revue **février 2024**) : **Stage 1** pour les deux produits ; atténuation
  atmosphérique de la radiance M13 (FRP VIIRS) sensiblement plus forte que pour la
  bande MIR MODIS (≈ 50 % selon la modélisation radiative).
  → *Limite PyroLens* : les niveaux de validation MODIS et VIIRS ne sont pas équivalents.

## 5. Algorithmes et documentation produit

- *VIIRS I-Band 375 m Active Fire Data* — NASA Earthdata,
  https://www.earthdata.nasa.gov/data/instruments/viirs/viirs-i-band-375-m-active-fire-data
  : algorithme contextuel multi-spectral utilisant les 5 canaux 375 m (+ canaux 750 m en
  entrée) ; amélioration des petits feux et de la performance nocturne ; saturation
  fréquente de I4 → FRP hybride 375/750 m, ajout du canal M13 depuis 2015.
- *MODIS Thermal Anomalies/Fire* — NASA MODIS, https://modis.gsfc.nasa.gov/data/dataprod/mod14.php
  : détection sur 4 µm et 11 µm (force absolue + comparaison au fond du pixel) ;
  champs jour/nuit, position, confiance, FRP, et information feu / pas de feu /
  **pas d'observation** ; Terra + Aqua donnent typiquement 4 observations diurnes/jour
  aux moyennes latitudes.
- *FIRMS / VNP14IMG_NRT catalogue* — NASA Earthdata,
  https://www.earthdata.nasa.gov/data/catalog/lancemodis-vnp14img-nrt-2
  (**publié le 14 février 2020**) : distribution NRT NetCDF4 + fichiers ASCII de
  détection via LANCE FIRMS — **entrée NRT**, à ne pas confondre avec la fiche
  LAADS `VNP14IMG` (traitement standard).
- *MCD14DL NRT MODIS* — https://www.earthdata.nasa.gov/data/catalog/lancemodis-mcd14dl-6.1nrt
  : localisations NRT 1 km Collection 6.1 dérivées de MOD14/MYD14.

## 6. Produits complémentaires (observabilité : couverture, nuages, géométrie)

| URL | Produit | Ce qu'il apporte | Résolution / calendrier | Limite pour PyroLens |
|---|---|---|---|---|
| https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD35_L2 | MOD35_L2 (cloud mask) | confiance ciel clair, ombres | L2, 1 km, par granule | « trou » du masque quand les radiances sont incomplètes ; masque **MODIS**, non interchangeable avec VIIRS |
| https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD09GA | MOD09GA | statistiques d'observation (observation coverage/number, angles capteur, QA) | journalier 500 m, observation/géolocalisation 1 km | dit **si** la zone a été observée, pas si un feu aurait été détectable |
| https://modis.gsfc.nasa.gov/data/dataprod/mod03.php | MOD03 / MYD03 (géolocalisation) | lat/lon, angles soleil/satellite, masque terre/mer | par granule | indispensable pour la dépendance du FRP à l'angle de vue (Li et al., 2018) |
| https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD03 | MOD03 (catalogue LAADS) | angles de capteur, géométrie | par granule | la fiche catalogue renvoie à la **Collection 7** : aligner la collection avec les granules comparés |

**Aucun de ces produits n'a encore été acquis** : la classification d'observabilité
reste donc par défaut en « observabilité inconnue » (voir `docs/methodology.md` §5).

## 7. Littérature évaluée par les pairs

1. **Li, F., Zhang, X., Kondragunta, S., Csiszar, I. (2018)** — *Comparison of Fire
   Radiative Power Estimates From VIIRS and MODIS Observations*, **Journal of
   Geophysical Research: Atmospheres**.
   URL consultée (résumé) : https://modis.gsfc.nasa.gov/sci_team/pubs/abstract_new.php?id=28428
   - *Question* : le FRP MODIS et VIIRS est-il interchangeable ?
   - *Constat* : capability VIIRS homogène sur la balayage vs MODIS fortement dépendant
     de l'angle de vue ; à l'échelle des grilles 1°, différences moyennes ~20 % dans les
     zones à feux ; VIIRS ~47 % plus bas pour de grands feux de forêt boréale ;
     corrélations fortes à l'échelle continentale.
   - *Limite pour PyroLens* : interdire tout facteur constant de correction du FRP ;
     stratifier par angle de vue et échelle d'agrégation.
2. **Coskuner, K. A. (2022)** — *Assessing the performance of MODIS and VIIRS active fire
   products in the monitoring of wildfires: a case study in Turkey*, **iForest –
   Biogeosciences and Forestry**, 15, 85-94.
   URL consultée : https://iforest.sisef.org/abstract/?id=ifor3754-015
   - *Question* : taux de détection réel vs références au sol.
   - *Constat* (Turquie 2015-2019) : détection des feux du registre 0,6-16,6 % (MODIS) et
     1,3-25,6 % (VIIRS) ; croissance avec la taille du feu ; limites liées au couvert
     fermé et à la fumée.
   - *Limite pour PyroLens* : résultat local, **aucun facteur de conversion universel**.
3. **Algorithme VIIRS 375 m** : la référence citée par la documentation NASA est
   *Schroeder, Oliva, Giglio, Csiszar (2014), Remote Sensing of Environment, 143, 85-96*
   — **page de l'article NON lue** dans cette session (voir §8) : elle n'est donc pas
   utilisée comme source de constats ici.

## 8. Sources non accessibles (à ne pas citer comme consultées)

| Source | Raison exacte |
|---|---|
| https://modis-fire.umd.edu/files/MODIS_C6_Fire_User_Guide_C.pdf | erreur de vérification de certificat à la lecture |
| https://lpdaac.usgs.gov/documents/427/VNP14_User_Guide_V1.pdf | HTTP 500 |
| https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/.../VIIRS_C2_AF-375m_User_Guide_1.2.pdf | type de contenu PDF non extractible par l'outil de lecture |
| https://firms.modaps.eosdis.nasa.gov/api/country/ et /countries/ | HTTP 400 (fonction signalée indisponible sur la page API) |
| Page/abstract de Schroeder et al. (2014) | inaccessible en lecture directe |
| Pages PMC (intercomparison MODIS Aqua–VIIRS 2018 ; algorithme MODIS C6 2016) | erreur d'accès |

## 9. Contrôle d'accès réellement exécuté (cette session, octobre 2026)

| Cible | Résultat observé | Conséquence |
|---|---|---|
| https://cmr.earthdata.nasa.gov/search (collections + granules) | **HTTP 200**, en-tête `cmr-hits` exploitable | inventaire produit/période **réel** réalisé (voir `docs/data_inventory.md`) |
| https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson | **HTTP 200**, 838 726 octets, SHA-256 `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f` | emprise documentée acquise |
| https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/MOD14.061/...hdf | **HTTP 302 → urs.earthdata.nasa.gov** | granule standard **non accessible sans Earthdata Login** |
| https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD14/2019/001/...hdf | **HTTP 303** (redirection d'authentification) | idem |
| https://firms.modaps.eosdis.nasa.gov/api/area/csv/<clé>/... | **HTTP 400** « Invalid MAP_KEY » | clé FIRMS requise |
| https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/<clé>/... | **HTTP 401** « Invalid MAP_KEY » | idem |
| https://data-api.globalforestwatch.org/dataset/... | **HTTP 404** | pas de source alternative ouverte retenue |
| https://queimadas.dpi.inpe.br/... | échec de résolution DNS | idem |
