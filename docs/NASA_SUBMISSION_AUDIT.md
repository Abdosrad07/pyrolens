# PyroLens — Audit de préparation soumission NASA Space Apps 2026

> Audit technique, scientifique et éditorial — état au 2026-11-15, branche `main`.
> Ce document ne contient **aucune soumission définitive** : ce sont des
> propositions et un état des lieux vérifié. Les points invérifiables sont
> marqués `À CONFIRMER PAR L'ÉQUIPE`.

---

## 1. Résumé de l'état du projet

**PyroLens** (équipe Fire Force) est une étude de faisabilité complète et
opérationnelle : pipeline Python d'audit et d'harmonisation des détections
thermiques **MODIS Terra/Aqua** et **VIIRS Suomi-NPP** (NASA FIRMS), analyse
de zone à la demande (NRT ~5 j + historique archive 2013→aujourd'hui), et
modèle de **prédiction du risque d'activité détectée** (RandomForest
calibré, backtest réel).

| Dimension | État |
|---|---|
| Pipeline données | ✅ Opérationnel — 1 171 fichiers canoniques 2013-2020 + archive pays en cours |
| API FastAPI | ✅ Opérationnelle — ~30 endpoints, jobs async, tests |
| Frontend React (`frontend/`) | ✅ Connecté au backend, données réelles partout |
| Fire Monitor vanilla (`fire-monitor.html`) | ✅ Autonome, analyses zone + historique |
| Modèle de risque | ✅ Entraîné sur données réelles — PR-AUC test 0,926 |
| Tests | ✅ 114 pytest + build frontend OK |
| Déploiement public | ❌ **Absent** — tout tourne en local |
| Vidéo/diapositive démo | ❌ Non produite |
| Validation scientifique externe (H4-H6) | ❌ Non exécutée (documenté honnêtement) |

**Verdict** : socle technique et scientifique solide et honnête. Le
bloquant principal est **la mise en ligne publique de la démo**.

---

## 2. Analyse des six sections officielles

### A. High-Level Summary (50-200 mots)

**Éléments à mettre en avant (vérifiés)** :
- Comparaison MODIS/VIIRS sur grille commune 0,25° — Jaccard = recouvrement, pas précision
- 1 171 fichiers FIRMS réels (2013-2020) + archive annuelle par pays sans clé
- Modèle RF calibré : P(détection ≥1 dans 8 j) — PR-AUC 0,926 sur test jamais vu
- Interface cartographique temps réel avec analyse de zone NRT/historique
- Rigueur : provenance propagée, `data_origin`, backtest étiqueté, jamais « pas de feu »

**Attention** : ne pas écrire « predicts wildfires » — c'est « detected
fire activity ». Le résumé doit le dire explicitement.

**Proposition (anglais, ~130 mots)** :

> PyroLens harmonizes and compares thermal anomaly detections from MODIS
> Terra, MODIS Aqua and VIIRS Suomi-NPP (NASA FIRMS) over Cameroon and West
> Africa. A reproducible Python pipeline audits, normalizes and compares the
> sensors on a common 0.25° grid using set-overlap metrics — never claiming
> that a missing detection means no fire. An interactive map lets users
> analyze any zone in near-real time or across yearly FIRMS archives since
> 2013. A calibrated RandomForest model estimates the probability of future
> *detected* fire activity (PR-AUC 0.926 on a held-out 2019–2020 test),
> clearly labeled as a historical backtest, not an operational alert.
> PyroLens makes multi-sensor fire monitoring transparent, reproducible and
> scientifically honest.

### B. Link to Project Demo and Link to Project

**Exigence** : UN lien, sans mot de passe — vidéo 30 s (sous-titrée EN) ou
≤7 diapositives.

**Constat** : le projet a **assez de fonctionnalités opérationnelles** pour
une vidéo percutante (carte live + couche risque + analyse zone + calendrier
réel + jobs). Le PowerPoint serait moins convaincant car la force du projet
est **visuelle et interactive**.

**Recommandation : VIDÉO 30 s** (plus forte qu'un deck pour une démo cartographique).

**Scénario vidéo proposé (30 s)** :
1. (0-4 s) Carte monde → zoom Cameroun, hotspots GIBS allumés — « Two NASA
   sensors see the same fires differently »
2. (4-10 s) Clic sur une zone → panneau analyse → Jaccard VIIRS/MODIS
3. (10-16 s) Bascule « Historique » → calendrier multi-années 2019-2025
4. (16-22 s) Couche risque → heatmap 1 215 cellules, probabilités calibrées
5. (22-27 s) Vue Calendrier/Qualité → données réelles, audit
6. (27-30 s) Logo + « PyroLens — reproducible, honest fire monitoring »

**Captures d'écran nécessaires** :
- Carte avec hotspots + couche risque active
- Panneau analyse zone avec Jaccard
- Calendrier historique multi-années
- Panneau Risque (métriques PR-AUC/F1)
- Vue Jobs avec un vrai job
- Vue Qualité (audit.json)

**Checklist publication** :
- [ ] Déployer frontend + API sur un hébergement public (Render/Railway/Fly/VPS) — `À CONFIRMER PAR L'ÉQUIPE`
- [ ] Vérifier depuis navigateur **non connecté** : `/` (frontend), `/api/v1/health` → 200, `/artifacts/fire_risk.json` → 200
- [ ] Désactiver ou documenter les POST si `PYROLENS_API_TOKEN` non configuré (les POST sont protégés si token défini — vérifier qu'ils répondent 401/403 proprement, pas 500)
- [ ] Vérifier que les tuiles GIBS/Esri chargent sans Referer problématique
- [ ] Tester la vidéo exportée (sous-titres EN gravés)
- [ ] Le lien doit être **unique** — pas de demo interacteve qui exige un compte

### C. Project Details

**Architecture réelle** :
- **Pipeline Python 3.10+** : `src/pyrolens/` — ingest → audit → baselines →
  observability → normalize → predict ; pandas/polars, numpy, shapely,
  pyproj, scikit-learn, matplotlib, typer
- **API FastAPI** : lecture d'artefacts horodatés (ETag) + jobs async
  (thread unique, progression réelle) — ~30 endpoints `/api/v1`
- **Frontend React 18** (Vite, react-leaflet, recharts) + Fire Monitor
  vanilla autonome + ancienne app React
- **Données** : FIRMS NRT API (clé), FIRMS archive pays (sans clé),
  Natural Earth 110m, CMR API (inventaire), GIBS WMTS (tuiles)

**Fonctionnement** : CSV FIRMS → audit qualité → normalisation fenêtres
5 j → comparaison Jaccard par grille 0,25°/fenêtres → artefacts JSON →
API → carte. Le modèle : features trailing 24 dims → RandomForest 200
arbres → calibration isotonic sur validation → backtest test 2019-2020.

**Bénéfices démontrables** : transparence (provenance partout),
reproductibilité (graines fixes, manifests SHA-256), honnêteté scientifique
(jamais « pas de feu », Jaccard ≠ précision), couverture historique
(archives annuelles sans clé), couverture spatiale (bbox arbitraire).

**Perspectives (PAS des fonctionnalités existantes)** : drivers météo
ERA5, validation H4-H6, NOAA20, déploiement continu NRT, calibration
spatiale du modèle.

**Proposition (anglais, structurée pour le formulaire)** :

> PyroLens is a reproducible pipeline + interactive platform that harmonizes
> MODIS Terra/Aqua and VIIRS Suomi-NPP fire detections from NASA FIRMS over
> Cameroon and West Africa.
>
> **What it does**: downloads FIRMS data (NRT API and yearly country
> archives), audits quality, normalizes detections onto a common 0.25°
> grid with canonical 5-day windows, compares sensors via set-overlap
> (Jaccard) metrics, serves an interactive map with on-demand zone
> analysis (near-real-time or multi-year history), and produces a
> calibrated RandomForest estimate of future *detected* fire activity.
>
> **How it works**: Python pipeline → timestamped JSON artifacts → FastAPI
> (read-only artifacts + async jobs) → React/Leaflet frontend.
>
> **Benefits**: full provenance (`data_origin`, SHA-256 manifests), honest
> uncertainty (observability states, never "no fire"), reproducible
> (fixed seeds, 114 tests), open archive access without API key.
>
> **Tools**: Python, FastAPI, scikit-learn, pandas/polars, React, Leaflet,
> NASA FIRMS, GIBS WMTS, CMR, Natural Earth.
>
> **Hope**: extend to continental Africa, add weather drivers (ERA5),
> support operational early-warning use by NGOs.

### D. Use of SI / AI

**Traces réelles trouvées** :
- Commits `Freebuff <cloud@freebuff.local>` / `<desktop@freebuff.local>`
  (outil IA de code) — au moins 3 commits
- Co-auteur `Devin <devin-ai-integration[bot]@users.noreply.github.com>`
  sur les commits générés par Devin (Cognition)
- `.claude/launch.json` présent (config IDE Claude)
- Aucun watermark ni mention IA dans les artefacts ou le produit

**Utilisation réelle** :
- **Assistant de développement** : génération/assistance code (Devin,
  Freebuff, éventuellement Claude via IDE) — OUI, documenté par les commits
- **Composant du produit** : le chatbot `/api/v1/chat` est
  **déterministe, sans LLM** — aucune IA dans le produit livré
- **Génération de contenu** : aucun contenu marketing/généré par IA
  identifié dans le produit

**Déclaration confirmée par l'équipe (2026-11-15)** — répartition officielle :
- **Freebuff** — backend : pose des briques (scaffolding, architecture API)
- **Claude** — peaufinage de l'UI/UX frontend
- **ChatGPT** — brainstorming et supervision du projet
- **Devin (Cognition)** — amélioration du backend et conception du
  modèle de prédiction de risque

**Déclaration à coller dans le formulaire (anglais)** :

> AI-assisted development tools were used during development, with the
> following roles: Freebuff for backend scaffolding, Claude for UI/UX
> refinement, ChatGPT for brainstorming and project supervision, and Devin
> (Cognition) for backend improvements and the fire-risk prediction model.
> The delivered product contains NO generative AI component: the in-app
> assistant is a deterministic, rules-based responder built from project
> artifacts. No AI-generated images, videos or branding assets are used. Le branding "NASA" n'apparaît que dans des
attributions de données (correct) — vérifier qu'aucun logo NASA n'est
reproduit dans les visuels maison (les tuiles GIBS portent leur
attribution, c'est conforme).

### E. NASA Data (obligatoire Global Awards)

| Ressource | Organisme | Utilisation réelle (preuve) | Lien officiel |
|---|---|---|---|
| **FIRMS API** (active fire, NRT) | NASA FIRMS / LANCE | `src/pyrolens/download.py` (téléchargement 1 171 fichiers), `api/services/firms_analysis.py` (analyse zone) | https://firms.modaps.eosdis.nasa.gov/api/ |
| **FIRMS Archive pays** (`/data/country/`) | NASA FIRMS | `src/pyrolens/archive.py` + `scripts/download_west_africa_archive.py` — 12+ fichiers réels | https://firms.modaps.eosdis.nasa.gov/data/country/ |
| **FIRMS Map/Download pages** | NASA FIRMS | Liens dans `web/public/fire-monitor.html` | https://firms.modaps.eosdis.nasa.gov/map/ , /download/ |
| **VIIRS-SNPP 375m** | NASA LaRC / VIIRS | Données FIRMS `viirs-snpp` — 410k+ détections réelles dans l'analyse zone | via FIRMS |
| **MODIS Terra** | NASA MODIS | Données FIRMS `modis` (satellite=Terra) | via FIRMS |
| **MODIS Aqua** | NASA MODIS | Données FIRMS `modis` (satellite=Aqua) | via FIRMS |
| **GIBS WMTS** | NASA GIBS | Tuiles carte : VIIRS true color, **VIIRS Thermal Anomalies 375m**, MODIS Aerosol, Blue Marble — `MapView.jsx`, `fire-monitor.html` | https://gibs.earthdata.nasa.gov/wmts/ |
| **CMR Search API** | NASA CMR | `src/pyrolens/cmr.py` — inventaire produits/granules (MOD14/MYD14/VNP14IMG) | https://cmr.earthdata.nasa.gov/search |
| **Earthdata Login** | NASA Earthdata | Référence dans `download.py` (probe granules — bloqué sans credentials, documenté) | https://urs.earthdata.nasa.gov |
| **Natural Earth** | (non-NASA) | `data/raw/geo/ne_110m_admin_0_countries.geojson` | https://www.naturalearthdata.com |

**Conformité** : ✅ FIRMS + GIBS + CMR sont des ressources NASA du
challenge — éligibilité Global Awards satisfaite. Earthdata granules
standard = **bloqué** (pas de credentials) — documenté honnêtement,
non requis pour l'éligibilité.

### F. Space Agency Partner Data and Other Resources

| Ressource | Type | Source | Utilisation | Licence/attribution |
|---|---|---|---|---|
| Esri World Imagery | Tuiles | server.arcgisonline.com | Fond de carte | Esri — attribution "Esri" requise (présente) |
| Esri World Boundaries | Tuiles labels | server.arcgisonline.com | Labels | Esri — attribution (présente) |
| OpenStreetMap Nominatim | Géocodage | nominatim.openstreetmap.org | Recherche de lieu | **ODbL** — attribution "© OpenStreetMap" À VÉRIFIER dans l'UI |
| Leaflet 1.9.4 | Lib JS | cdnjs | Cartes | BSD-2-Clause |
| React 18 / react-leaflet / recharts / Vite | Frameworks | npm | Frontend | MIT |
| Python: pandas, numpy, scikit-learn, shapely, pyproj, fastapi, typer, matplotlib, polars, pyarrow | Libs | pip | Pipeline+API | BSD/Apache/MIT respectives |
| Google Fonts (Bricolage Grotesque, Instrument Sans) | Fonts | fonts.googleapis.com | Typographie UI | **OFL 1.1** — libre |
| Natural Earth 110m | Données geo | naciscdn.org / github nvkelso | Polygones pays | **Public domain** |
| MIT License | Projet | LICENSE | Tout le code | MIT |

**À corriger** : ajouter "© OpenStreetMap contributors" dans l'attribution
de la recherche Nominatim (OBdL l'exige). Vérifier que l'attribution Esri
est visible dans la carte (actuellement dans `attribution` Leaflet — OK).

---

## 3. Vérification scientifique et cohérence

| Affirmation | Statut | Preuve |
|---|---|---|
| Grille 0,25° | ✅ Réel | `DEFAULT_GRID_DEG=0.25`, `cell_id()` |
| Fenêtre 8 j | ✅ Réel | `DEFAULT_HORIZON_DAYS=8`, label `]t,t+8]` |
| Jaccard = recouvrement | ✅ Correct | `baselines.py`, documenté « pas une précision » |
| FRP utilisé | ✅ Réel | `frp_mean_16`, `frp_max_16` features |
| Backtest 2019-2020 | ✅ Réel | `SPLIT_YEARS`, test jamais touché avant |
| PR-AUC 0,926 | ✅ Calculé | `fire_risk.json` metrics.test |
| « Prédit des feux » | ⚠️ **À reformuler** | Le label = détection FIRMS, pas incendie — toujours écrire « detected fire activity » |
| « Données actuelles » | ❌ Faux | Données ≤ 2020 (pipeline) — `estimate_kind=historical_backtest` le dit déjà |
| « Précision » pour Jaccard | ❌ Interdit | Jamais — c'est un recouvrement |
| Observabilité « pas de feu » | ✅ Jamais affirmé | 4 états, `observability.py` |

**Reformulations obligatoires dans tout support** :
- « fire risk prediction » → « **detected fire activity** prediction »
- « real-time forecast » → « **historical backtest** on satellite detections »
- « accuracy » → « set overlap (Jaccard) » ou « PR-AUC on held-out test »

---

## 4. Plan de démonstration

### Option recommandée : VIDÉO 30 s (cf. §B)

### Plan B : 7 diapositives

| # | Titre | Objectif | Contenu | Visuel |
|---|---|---|---|---|
| 1 | **Problem** | Contexte | 2 capteurs NASA, mesures différentes du même feu ; besoin d'harmonisation | Photo feux + logos capteurs (texte, pas logos NASA reproduits) |
| 2 | **Solution** | PyroLens en 1 phrase | Pipeline reproductible + carte interactive + modèle calibré | Schéma architecture simplifié |
| 3 | **Data** | Crédibilité données | 1 171 fichiers FIRMS 2013-2020 + archives pays 2013-2025, 18 pays | Tableau volumes + carte couverture |
| 4 | **Methodology** | Rigueur | Grille 0,25°, fenêtres 5j/8j, Jaccard, split chrono+purge, calibration isotonic | Schéma features→RF→calibration |
| 5 | **Platform** | Démo | Captures : carte+risque, analyse zone, calendrier, jobs | 3-4 screenshots réels |
| 6 | **Impact** | Bénéfice | Transparence, honnêteté (« pas de feu » jamais affirmé), reproductibilité, open archive | Métriques PR-AUC 0,926 + checklist honnêteté |
| 7 | **Vision** | Perspectives | Afrique continentale, ERA5, early-warning ONG | Carte Afrique + roadmap |

**Captures à réaliser** (checklist) :
- [ ] Carte + couche risque (heatmap 1 215 cellules)
- [ ] Clic zone → résultats Jaccard VIIRS/MODIS
- [ ] Calendrier historique multi-années
- [ ] Panneau Risque avec métriques
- [ ] Vue Jobs avec progression réelle
- [ ] Vue Qualité (audit)

---

## 5. Éléments manquants

| Élément exigé | État actuel | Manquant | Action | Priorité |
|---|---|---|---|---|
| Lien démo public | ❌ Local seulement | Déploiement | Render/Railway/VPS + domaine | **P0** |
| Vidéo/diapositive | ❌ Non produite | Contenu 30 s / 7 slides | Script + captures + montage | **P0** |
| High-Level Summary | 🟡 Proposition prête | Validation équipe | Relire + ajuster | P0 |
| Project Details | 🟡 Proposition prête | Validation équipe | Relire | P0 |
| Déclaration IA | 🟡 Proposition prête | Confirmation outils utilisés | Équipe confirme | P0 |
| NASA Data | ✅ Inventorié | — | RAS | — |
| Partenaires/autres | ✅ Inventorié | Attribution OSM à ajouter | Edit UI | P1 |
| Earthdata credentials | ❌ Bloqué | Identifiants ou renoncement documenté | Équipe décide | P1 |
| Validation H4-H6 | ❌ Non exécutée | Référence terrain ou produits couverture | Documenter limite (déjà fait) | P2 |
| Données >2020 | 🟡 Partiel | `download --start 2021` en cours possible | Lancer si temps | P2 |
| Archive Ouest-africaine | 🔄 ~20% fait | Fin du bulk download | Laisser tourner | P2 |
| RiskView (frontend) | ⚠️ Stub | Vue pleine page risque | Optionnel | P2 |
| Licence fonts OSM | ⚠️ | Attribution OSM contributors | Edit UI | P1 |
| Vidéo sous-titres EN | ❌ | Sous-titres anglais gravés | Montage | P0 |
| Compte/réseau démo | ❌ | Pas de login requis | Vérifier POST → 401 propre | P0 |

---

## 6. Checklist finale de soumission

**Avant de soumettre** :
- [ ] URL publique unique, testée en navigation privée (frontend + API + artefacts)
- [ ] Vidéo 30 s sous-titrée EN OU deck 7 slides — exporté et relu
- [ ] High-Level Summary validé (anglais, 50-200 mots, « detected » pas « wildfire »)
- [ ] Project Details validé (anglais, architecture réelle)
- [ ] Déclaration IA signée par l'équipe
- [ ] Inventaire NASA Data collé (FIRMS, VIIRS, MODIS, GIBS, CMR — liens vérifiés)
- [ ] Inventaire partenaires (Esri, OSM, Leaflet, fonts, Natural Earth — attributions)
- [ ] Aucune métrique inventée ; « backtest » partout où pertinent
- [ ] Aucun logo NASA reproduit dans les visuels maison
- [ ] README + docs à jour (PROJECT_OVERVIEW.md fait foi)

---

## 7. Rapport final à l'équipe

> **Addendum — contrôle final ciblé (2026-11-15)** : vérifications
> supplémentaires consignées en §8 ci-dessous. Deux corrections factuelles
> détectées : la prévalence des positifs du test est **31,8 %** (38 964 /
> 122 715), pas « ~6 % » comme indiqué dans `PROJECT_OVERVIEW.md` §7.2 et
> `FIRE_RISK_PREDICTION.md` §11 — **corrigés depuis** (voir §8.8). L'attribution OpenStreetMap est **confirmée absente**
> de l'UI (recherche Nominatim sans crédit « © OpenStreetMap »).

### Niveau de préparation : **~75 %**

Socle technique/scientifique excellent et honnête. Le projet est
**prêt scientifiquement** — ce qui manque est **éditorial et logistique**.

### Déjà prêt ✅
- Pipeline complet + 1 171 fichiers réels + archive en cours
- API ~30 endpoints + jobs + tests (114)
- Frontend connecté, données réelles partout
- Modèle RF : PR-AUC 0,926 documenté
- Documentation exhaustive (PROJECT_OVERVIEW, FIRE_RISK_PREDICTION, MODEL_TRAINING)
- MIT License, manifests SHA-256, provenance partout

### Bloquant 🔴
1. **Pas d'URL publique** — tout est local ; sans démo en ligne, pas de soumission
2. **Pas de vidéo/diapositive** — le formulaire l'exige
3. **Déclaration IA à confirmer** par l'équipe

### Cinq actions les plus urgentes
1. **Déployer** frontend+API sur un hébergement public (Render/Railway) — P0
2. **Produire la vidéo 30 s** (script §4 prêt) ou le deck 7 slides — P0
3. **Confirmer la déclaration IA** (outils utilisés, co-auteurs) — P0
4. **Relire les textes du formulaire** (Summary + Details, propositions §2A/C) — P0
5. **Tester la démo en navigation privée** une fois déployée — P0

### Informations attendues de l'équipe
- `À CONFIRMER` : hébergement choisi pour la démo publique
- ~~`À CONFIRMER` : liste complète des outils IA utilisés~~ → **confirmé** :
  Freebuff (backend), Claude (UI/UX), ChatGPT (brainstorming/supervision),
  Devin (backend + modèle de prédiction)
- `À CONFIRMER` : crédits des co-auteurs (Abdosrad07, LEMOBENG TANKEU)
- `À CONFIRMER` : identifiants Earthdata disponibles ou renoncement assumé
- `À CONFIRMER` : qui produit la vidéo et qui la monte
- `À CONFIRMER` : nom exact du défi/track Space Apps 2026 visé

---

## 8. Contrôle final ciblé — constats vérifiés

### 8.1 Cohérence des sources de données

| Source | Période réelle | Consommée par |
|---|---|---|
| FIRMS NRT (`data/raw/firms`) | 2013-01-01 → 2020-12-31 (1 171 fenêtres 5 j) | pipeline, baselines, calendrier, **modèle de prédiction** |
| FIRMS archive pays (`data/raw/archive`) | 2013 → 2025 (téléchargement en cours, ~20 %) | analyse historique de zone (`firms_history`) — **PAS** le modèle |
| FIRMS NRT live (API) | ~5 derniers jours | analyse de zone `firms_analyze` |
| `data/fixture` | synthétique | tests/démo uniquement — `data_origin` distinct |

**Le modèle n'a jamais vu les archives** : `run_prediction` lit
`data/raw/firms` (ou `--source` explicite). `firms_archive_sp` n'apparaît
que si on passe `--source data/raw/archive`. La distinction NRT vs
archive SP est propagée dans `data_origin`.

### 8.2 Vérification des métriques du modèle (artefact `fire_risk.json`)

| Métrique | Valeur vérifiée | Source |
|---|---|---|
| Test n | **122 715** | `metrics.n` |
| Positifs test | **38 964 → prévalence 31,8 %** | `metrics.n_positive` |
| PR-AUC test (RF) | **0,9259** | `metrics.pr_auc` |
| PR-AUC val baseline | **0,8747** | `metrics.validation.baseline.pr_auc` |
| PR-AUC val RF | **0,9280** | `metrics.validation.random_forest.pr_auc` |
| Recall / Precision / F1 test | 0,844 / 0,837 / 0,841 | `metrics.*` |
| Brier test | **0,0722** | `metrics.brier` |
| ROC-AUC test | 0,9564 | `metrics.roc_auc` |
| Calibration | **isotonic**, bins test predicted≈observed (ex. 0,9-1,0 → 0,98 vs 0,98) | `metrics.calibration_bins_test` |
| Seuil | 0,42 (argmax F1 sur validation) | `metrics.threshold` |
| Matrice confusion | 32 890 VP / 6 074 FN / 6 389 FP / 77 362 VN — cohérente avec n | `metrics.confusion_matrix` |

**Fuite temporelle** : vérifiée dans `prediction.py` — split chrono
2013-16/2017-18/2019-20 + **purge 8 j** aux frontières + features 100 %
trailing (searchsorted ≤ t) + calibration sur validation uniquement.
**Aucune fuite détectée.**

**⚠️ Correction** : la prévalence réelle est **31,8 %**, pas « ~6-7 % » —
`PROJECT_OVERVIEW.md` §7.2 et `FIRE_RISK_PREDICTION.md` §11 indiquent un
chiffre erroné à corriger.

### 8.3 Harmonisation H1–H6 (`harmonization.py` — statuts réels)

| Hypothèse | Statut | Détail |
|---|---|---|
| H1 schéma commun sans conversion | ✅ **Exécuté** (audit 18/10) | 4 460 288 lignes, 0 malformée |
| H2 grille commune + aire | ✅ **Exécuté** | 24 configurations, Jaccard 0,103→0,659 selon maille/fenêtre |
| H3 fenêtres multiples | ✅ **Exécuté** | 1/4/8/16 j publiées |
| H4 seuils confiance natifs | ❌ **Non exécuté** | prérequis manquants |
| H5 calibration FRP géométrique | ❌ **Non exécuté** | idem |
| H6 validation externe | ❌ **Non exécuté** | aucun split dev/val externe |

Le catalogue le dit lui-même : « aucune méthode n'est annoncée comme
validée — H1-H3 exécutés sur données réelles, H4-H6 non exécutés ».

### 8.4 Captures vidéo — toutes réelles

| Capture prévue | Source réelle vérifiée |
|---|---|
| Carte + couche risque | `fire_risk.json` — 1 215 cellules, `prob` calibrées |
| Analyse zone Jaccard | `firms_analyze` job — résultat archive/NRT réel |
| Calendrier multi-années | `fire-calendar/daily` + `firms_history` — données réelles |
| Panneau Risque métriques | `metrics` de l'artefact (PR-AUC 0,926…) |
| Jobs | `/api/v1/experiments` — jobs réels |
| Qualité | `audit.json` — 2 634 700 anomalies réelles |

**À ne PAS montrer** : `RiskView.jsx` (stub « activez la vue Carte ») et
présenter l'assistant chat comme un LLM (c'est déterministe).

### 8.5 Provenance des 1 215 cellules

- `reference_date = 2020-12-31`, `estimate_kind = historical_backtest`,
  `data_origin = nasa_firms`, `period = 2013-01-01 → 2020-12-31`
- **Backtest historique confirmé** — aucune estimation récente.
- Cellules = grille 0,25° sur l'émprise Cameroun (données limited au
  pipeline, pas à l'archive Ouest-africaine).

### 8.6 Attributions cartographiques — vérifié

| Attribution | État |
|---|---|
| Esri World Imagery | ✅ `attribution: "Earthstar Geographics \| Esri"` (MapView + fire-monitor) |
| NASA GIBS | ✅ attributions par couche (VIIRS SNPP, Blue Marble, FIRMS) |
| Leaflet controls | ✅ `.leaflet-control-attribution` stylé |
| **OpenStreetMap (Nominatim)** | ❌ **ABSENT** — recherche de lieu sans crédit « © OpenStreetMap contributors » (OBdL) — à ajouter dans les 2 frontends |
| Esri boundaries layer | ⚠️ tuiles labels sans chaîne d'attribution propre (couvert par Esri ci-dessus) |

### 8.7 Checklist de déploiement public

**Variables d'environnement** (`.env.local` → variables `PYROLENS_*`) :

| Variable | Requise pour la démo ? | Note |
|---|---|---|
| `PYROLENS_API_TOKEN` | ⚠️ **Décision requise** | Si défini → tous les POST exigent `Authorization: Bearer` ; **le frontend `apiPost` n'envoie pas ce header** → les POST (predict, analyze, history, chat, experiments, validate) renverraient 401. Options : laisser vide (POST ouverts — risque d'abus de compute) OU ajouter le header côté frontend avec un token côté client (visible publiquement = sécurité cosmétique) OU restreindre les POST au backend-only |
| `PYROLENS_CORS_ORIGINS` | ⚠️ Si front≠API | Sinon same-origin via proxy/domaine unique |
| `FIRMS_MAP_KEY` | ❌ Non pour la démo | Seulement pour `download` NRT et `firms_analyze` ; `firms_history` et `predict` n'en ont pas besoin |
| `EARTHDATA_*` | ❌ Non | Granules standard bloqués de toute façon |
| `PYROLENS_JOBS_ENABLED` | ✅ `1` | Sinon tous les POST → 403 |
| `PYROLENS_SOURCE_DIR` / artifacts | ✅ | `web/public/artifacts/` doit être servi (déjà versionné) |

**Endpoints à vérifier en prod** :
- `GET /api/v1/health` → 200 sans auth
- `GET /api/v1/fire-risk` → 200 (artefact commité)
- `GET /artifacts/*.json` → 200 statique
- `POST /api/v1/predict` → 401 propre si token configuré (pas 500)
- `GET /api/v1/firms/history/{id}` → 409/404 propre si jamais lancé

**Données à embarquer** : `web/public/artifacts/*.json` (versionnés ✅),
`frontend/public/artifacts/*.json` (copie ✅). **`data/raw/` n'est PAS
nécessaire pour les GET** — sauf si on veut `firms_history`/`predict`
fon'sctionnels en prod (lourd : des Go — à décider).

**Points de vigilance déploiement** :
- `JobManager` = 1 worker, jobs en mémoire → un `predict` (~10 min)
  bloque tous les autres jobs ; à documenter ou à scaler
- `models/` (300 Mo) non requis — `fire_risk.json` pré-calculé suffit
- CORS : si frontend et API sur domaines différents →
  `PYROLENS_CORS_ORIGINS=https://ton-frontend.app`
- Rate limiting : **absent** — les POST ouverts sans token sont un
  vecteur d'abus (predict = ~10 min de CPU)

### 8.8 Synthèse du contrôle

| Catégorie | Résultat |
|---|---|
| Métriques modèle | ✅ Toutes vérifiées dans l'artefact — PR-AUC 0,926 réel |
| Fuite temporelle | ✅ Aucune détectée (split chrono + purge + trailing) |
| Calibration | ✅ Isotonic, bins test cohérents |
| H1-H6 | ✅ H1-H3 exécutés, H4-H6 honnêtement non exécutés |
| Captures vidéo | ✅ Toutes sourçables du produit réel |
| Backtest vs récent | ✅ `historical_backtest` confirmé, reference 2020-12-31 |
| Attributions | ⚠️ OSM manquante (OBdL), Esri/GIBS OK |
| Déploiement | ⚠️ POST sans auth header côté frontend = décision requise |
| **Correction documentaire** | ✅ Prévalence corrigée : « ~6 % » → **31,8 %** dans `PROJECT_OVERVIEW.md` (§7.2, §7.6, §7.7) et `FIRE_RISK_PREDICTION.md` (§11) |
