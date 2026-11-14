# Fire Risk Prediction — Étude de faisabilité

> **Statut** : étude préalable — aucune implémentation n'est autorisée par ce document.
> **Date** : 14/11/2026 · **Périmètre** : PyroLens, NASA Space Apps Challenge 2026.

---

## 1. Résumé exécutif

La prédiction du « risque d'activité de feu détectée » à 8 jours sur les cellules
de la grille PyroLens est **réalisable** avec les données existantes, à condition
de disposer des CSV FIRMS bruts (absents de ce clone — voir §3.4) et d'accepter
les limitesscientifiques inhérentes aux observations satellitaires.

- **Données** : 1 170 fenêtres FIRMS canoniques (5 j), 2013-01 → 2020-12,
  ~1,83 M de détections analysables dans l'emprise camerounaise.
- **Modèle recommandé** : **Random Forest** (scikit-learn déjà installé) avec une
  **baseline de fréquences historiques** comme référence obligatoire.
- **Verrou scientifique majeur** : une absence de détection ≠ absence de feu
  (nuages, heure de passage, résolution). Le label doit être formulé
  « détection future », jamais « incendie futur ».
- **Recommandation** : **GO WITH LIMITATIONS** — MVP démo possible en ~2 jours
  de travail, sans compromettre le moteur d'harmonisation.

---

## 2. État actuel du projet

| Composant | État vérifié | Référence |
| --- | --- | --- |
| Pipeline Python (audit, baselines, observabilité) | ✅ Fonctionnel, 91 tests | `src/pyrolens/` |
| Artefacts JSON (audit, baselines, observability, inventory) | ✅ Présents dans `web/public/artifacts/` | `data_origin=nasa_firms` |
| API FastAPI `/api/v1` | ✅ Lecture + jobs asynchrones avec progression | `api/`, `api/jobs.py` |
| Analyse de zone FIRMS NRT (bbox → Jaccard VIIRS/MODIS) | ✅ Opérationnelle | `api/services/firms_analysis.py` |
| Frontend Fire Monitor (carte Leaflet + 7 vues) | ✅ Fonctionnel | `web/public/fire-monitor.html` |
| Frontend React (6 écrans + Harmonization Lab) | ✅ Fonctionnel | `web/src/` |
| CSV FIRMS bruts 2013-2020 | ❌ **Absents de ce clone** | `data/raw/firms/` inexistant |
| Fixtures synthétiques | ✅ 3 CSV 2019 | `data/fixture/` |

**Architecture réutilisable** :

- Grilles et fenêtres : `src/pyrolens/grids.py` (`cell_id`, `make_key`,
  `window_index` — fenêtres alignées epoch, pas mois).
- Lecteur/normalisation : `src/pyrolens/ingest.py`, `normalize.py` (polars).
- Jobs de fond avec progression : `api/jobs.py` (`JobManager.submit`,
  `job.report(step, pct, detail)`).
- Artefacts → frontend : `api/store.py` (`ArtifactStore`) + JSON dans
  `web/public/artifacts/`.
- Visualisation carte : Leaflet dans `fire-monitor.html` (couche GIBS +
  `L.rectangle`/`L.circleMarker` déjà utilisés).

---

## 3. Inventaire des données disponibles

### 3.1 Périmètre et période

- **Emprise** : Cameroun (polygone Natural Earth, `data/raw/geo/`).
- **Période** : 2013-01-01 → 2020-12-31 (~2 922 jours, 8 ans).
- **Capteurs** : MODIS Terra, MODIS Aqua (produit `MODIS_SP`), VIIRS Suomi-NPP
  375 m (`VIIRS_SNPP_SP`) — 3 capteurs, 2 paires d'étude
  (`terra__aqua`, `aqua__viirs_snpp`).

### 3.2 Volumétrie (artefact `audit.json`, `row_accounting`)

| Indicateur | Valeur |
| --- | --- |
| Fichiers canoniques | 1 170 fenêtres de 5 jours |
| Lignes bien formées | 4 460 288 |
| **Lignes analysables (dans l'emprise)** | **1 825 588** |
| Hors emprise conservées | 2 634 700 |
| Lignes mal formées | 0 |
| FRP : moyenne / max | 10,7 MW / 2 015,7 MW (`frp_stats`) |
| Par capteur (volumes mensuels) | VIIRS ≈ 1,50 M lignes · MODIS ≈ 0,32 M lignes |

### 3.3 Colonnes CSV disponibles

`lat, lon, bright_ti4/ti5, scan, track, acq_date, acq_time, satellite,
instrument, confidence, version, frp, daynight, type`

Exploitables pour le ML : `latitude`, `longitude`, `acq_date`, `frp`,
`satellite`/`instrument`, `confidence` (classes natives par capteur),
`daynight`. **Non disponibles** : Météo (pluie, vent, humidité), végétation,
sol — toute variable externe nécessiterait une collecte supplémentaire.

### 3.4 ⚠️ Verrou pratique : les CSV bruts sont absents

`data/raw/firms/` **n'existe pas** dans ce clone : seules 3 fixtures
synthétiques 2019 sont présentes. Les artefacts ont été produits sur une
autre machine (`data/manifests/downloads.json` documente 9 802 requêtes).
Conséquences :

- `pyrolens` / API en mode auto → **fixture synthétique** (honnêtement
  étiquetée `synthetic_fixture`).
- Pour entraîner un vrai modèle : soit **relancer `pyrolens download`**
  (~9 802 requêtes FIRMS, des heures), soit **récupérer les CSV** depuis la
  machine d'origine. C'est le prérequis n°1 du MVP.

### 3.5 Grille et fenêtres existantes

- Mailles : **0,10° / 0,25° / 0,50°** (`config/pipeline.yaml`).
- Fenêtres : **1 / 4 / 8 / 16 jours**, alignées epoch
  (`window_index = epoch_days // W`).
- Configuration primaire : **0,25° × 8 jours**.
- Clé d'ensemble : `(cellule, date)` ou `(cellule, fenêtre)` — le même
  mécanisme sert directement au feature engineering.

---

## 4. Faisabilité scientifique

### 4.1 Quantité de données

À la maille primaire 0,25° sur l'emprise (~1 000–1 400 cellules effectives) :
~2 922 jours × ~1 200 cellules ≈ **3,5 M d'échantillons cellule-jour** possibles.
VIIRS ≈ 515 détections/jour, MODIS ≈ 110/jour sur toute l'emprise — dense en
agrégat, **creuse par cellule-jour** : les features doivent agréger sur
8–32 jours (exactement ce que les fenêtres du pipeline savent faire).

### 4.2 Couverture temporelle et géographique

- 8 ans complets, 0 jour manquant (audit `temporal_gaps` : 2 entrées à
  examiner, non bloquant).
- Un seul domaine spatial (Cameroun) → **généralisation non prouvable** ;
  la revue H6 du pipeline propose déjà le split 2013-2016 / 2017-2020.
- VIIRS SNPP : données dès ~2013 (volumes mensuels cohérents sur toute la
  période) — pas de rupture de couverture à gérer.

### 4.3 Construction des variables demandées

| Variable | Faisable ? | Source |
| --- | --- | --- |
| Nb détections 8/16/32 derniers jours | ✅ | CSV bruts + `window_index` |
| FRP moyen / max | ✅ | colonne `frp` |
| Nb jours avec détection | ✅ | dédoublonnage cellule-date |
| Mois / saison | ✅ | `acq_date` |
| Latitude / longitude | ✅ | centroïde de cellule |
| Jour/nuit (`daynight`) | ✅ | colonne native |
| Confiance par classe | ⚠️ partielle | classes natives non convertibles (H4 non exécuté) — utilisable en features catégorielles par capteur, pas en score commun |
| Météo / végétation / vent | ❌ | **collecte externe requise** (ERA5, etc.) — hors périmètre MVP |

### 4.4 ⚠️ Point scientifique essentiel : le label

**Détection ≠ feu.** Causes de faux négatifs : nuages, passage du satellite
~13h30 locale seulement, pixels 375 m/1 km, feux sous couvert. Le pipeline
l'a déjà formalisé : observabilité 4 états, « jamais de feu absent ».

**Stratégie recommandée pour le MVP** :

1. Label = **« ≥ 1 détection dans la cellule pendant les 8 prochains jours,
   tous capteurs confondus (union) »** — maximiser la sensibilité du label.
2. Features par capteur séparées (VIIRS plus sensible que MODIS) + union.
3. Formulation UI/rapport : **« risque d'activité de feu détectée »** —
   jamais « risque d'incendie ».
4. Limite assumée : les cellules/périodes sous-couvertes (nuages saison
   des pluies) produisent des labels bruités ; l'observabilité n'existe
   qu'au niveau emprise, pas par cellule → **ne pas prétendre filtrer
   les périodes non couvertes** sans donnée additionnelle.

### 4.5 Déséquilibre

Attendu : positif (détection à J+8) probablement 10–35 % selon cellule et
saison (saison sèche camerounaise déc.–mars). **À mesurer à l'étape 1** —
le seuil de décision et le PR-AUC absorbsent le déséquilibre ; ne pas
sur-échantillonner sans le documenter.

### 4.6 Fuites de données (data leakage)

Règles strictes :

- Features calculées **uniquement sur données ≤ date de prédiction**
  (fenêtres trailing, jamais centrées).
- Split **chronologique** train/val/test — jamais aléatoire (les fenêtres
  16 j se chevauchent : purger ±16 j autour des frontières).
- Pas de normalisation globale apprise sur le test.

---

## 5. Définition du problème prédictif

```text
Entrée  : cellule (i,j) de la grille + date t
Sortie  : P( ≥1 détection FIRMS dans la cellule sur [t+1, t+8] )
Label   : union VIIRS+MODIS+Terra+Aqua — binaire
Métrique:cible = PR-AUC / F1 sur classe positive (rappel prioritaire)
```

Le pas de prédiction peut être journalier (rolling) ou hebdomadaire —
**hebdomadaire recommandé** : moins corrélé, ~4× moins d'échantillons,
cohérent avec la fenêtre de 8 jours.

---

## 6. Comparaison des modèles

| Critère | Baseline fréquences | Random Forest | XGBoost |
| --- | --- | --- | --- |
| Principe | Taux historique par cellule-mois | Arbres bootstrap, non linéaire | Gradient boosting |
| Avantages | Quasi gratuit, interprétable, référence honnête | Non linéaire, robuste, pas de scaling, `sklearn` **déjà installé** | Souvent + précis |
| Limites | Ignore les features fines | Moins précis que boosting sur gros data | Nouvelle dépendance lourde (~200 Mo), tuning requis |
| Coût calcul | Négligeable | Secondes–minutes sur ~1 M lignes × ~15 features | Minutes, GPU non requis mais RAM |
| Données nécessaires | ~1 saison | ~2-3 ans | ~3+ ans pour briller |
| Intégration | Pure Python/CSV | `joblib` + sklearn | idem + dépendance |
| Hackathon | **Obligatoire** (référence) | **Recommandé** | Optionnel (si temps) |

**Recommandation** : baseline de fréquences + **RandomForestClassifier**
(`n_estimators≈200`, `class_weight='balanced_subsample'` ou seuil ajusté
sur PR-AUC). XGBoost seulement si le RF déçoit et que le temps reste.

---

## 7. Architecture proposée

```text
data/raw/firms/*.csv
      │  pyrolens predict (nouvelle commande CLI)
      ▼
src/pyrolens/prediction.py
  ├─ build_cell_day_table()   # réutilise grids.cell_id + fenêtre
  ├─ engineer_features()      # counts 8/16/32j, frp moy/max, saison…
  ├─ train_rf()               # split chrono, calibration proba (isotonic/Platt)
  └─ dump artifact → web/public/artifacts/fire_risk.json
                          + model.joblib (artefacts/, non servi)
      │
      ▼
GET /api/v1/fire-risk        # sert l'artefact (provenance incluse)
      │
      ▼
fire-monitor.html : couche L.rectangle par cellule colorée par
probabilité + légende + bandeau « estimation — pas une alerte incendie »
```

Réutilisation maximale : `grids.py` (clés), `ArtifactStore` (lecture),
`JobManager` (si entraînement lancé via API — **recommandé : CLI uniquement**
pour le MVP, l'entraînement est batch), pattern `data_origin`/`generated_at`.

---

## 8. Pipeline de traitement (détail)

1. **Agrégation cellule-jour** : polars `group_by(cell_i, cell_j, date)` sur
   les CSV → compte, frp_moy, frp_max, nb_capteurs, daynight_ratio.
2. **Label** : union des capteurs → `fire_next8 = max(detect[t+1..t+8])`.
3. **Features trailing** : sommes/glissantes sur 8/16/32 j par capteur et
   union ; `month`, `sin/cos` saison ; centroïde cellule ; `days_since_last`.
4. **Split** : train 2013-2016 · val 2017-2018 · test 2019-2020, purge ±16 j.
5. **Entraînement** : baseline fréquence → RF → comparaison PR-AUC/F1.
6. **Sortie** : probabilité par cellule pour les 8 derniers jours glissants
   → artefact JSON `{generated_at, data_origin, model:{...}, cells:[…]}`.

---

## 9. Stratégie d'évaluation

| Métrique | Usage |
| --- | --- |
| **PR-AUC** | métrique principale (classe positive rare) |
| Recall / F1 | au seuil choisi (rappel prioritaire : louper un feu coûte plus qu'un faux positif d'affichage) |
| Matrice de confusion | transparence |
| **Baseline fréquence** | doit être battue sinon le ML n'apporte rien |
| Calibration | reliability sur jeu test (probabilités affichées ⇒ doivent être calibrées) |

**Règle d'honnêteté** : si le RF ne bat pas la baseline de plus de ~5 %
PR-AUC, **livrer la baseline** — c'est déjà une fonctionnalité défendable.

---

## 10. Plan d'implémentation MVP

### A. Indispensables

| # | Étape | Fichiers | Résultat | Validation | Temps |
| --- | --- | --- | --- | --- | --- |
| A1 | Récupérer les CSV FIRMS bruts | `data/raw/firms/` | 1 170 CSV présents | `ls` + `pyrolens doctor` | 0,5–4 h (download) ou copie |
| A2 | Module agrégation + features | `src/pyrolens/prediction.py` (nouveau) | table cellule-jour + features | tests unitaires sur fixture | 0,5 j |
| A3 | Baseline fréquence + RF + éval | même fichier + `tests/` | métriques PR-AUC/F1 vs baseline | rapport de validation | 0,5 j |
| A4 | Artefact `fire_risk.json` + commande `pyrolens predict` | `src/pyrolens/cli.py`, `prediction.py` | JSON horodaté + provenance | `web-artifacts` check | 0,25 j |
| A5 | Couche risque sur la carte | `web/public/fire-monitor.html` | cellules colorées + légende + disclaimer | vérif visuelle | 0,25–0,5 j |

### B. Améliorations facultatives

| # | Étape | Temps |
| --- | --- | --- |
| B1 | `GET /api/v1/fire-risk` + intégration mode API | 0,25 j |
| B2 | Courbe PR + matrice de confusion dans la vue Qualité | 0,25 j |
| B3 | Seuil de risque réglable (curseur) côté UI | 0,25 j |
| B4 | XGBoost si RF insuffisant | 0,5 j + dépendance |

### C. À abandonner faute de temps

- Variables météo/vegetation externes (collecte + pipeline dédié).
- Prédiction intra-journalière ou probabilités horaires.
- Validation sur d'autres pays (données absentes).
- Endpoint de prédiction temps réel sur la bbox NRT (les features
  exigent l'historique 2013-2020 — un modèle « NRT » serait un autre sujet).

---

## 11. Estimation de temps totale

- **MVP (A1–A5)** : ~2 jours de travail effectif (hors téléchargement des
  données, qui peut tourner en tâche de fond).
- **Avec B1–B3** : ~2,5–3 jours.
- **Prérequis bloquant** : A1 — sans les CSV réels, tout le reste ne
  produit qu'un modèle sur fixture (démo possible mais à étiqueter
  `synthetic_fixture`, ce qui affaiblit fortement la démo).

---

## 12. Risques et limites

| Risque | Gravité | Mitigation |
| --- | --- | --- |
| CSV FIRMS absents du clone | 🔴 bloquant | download ou récupération machine d'origine |
| Label bruité (nuages/couverture) | 🟠 élevé | label = union capteurs, formulation « détection », pas de filtre d'observabilité par cellule (donnée inexistante) |
| Un seul domaine (Cameroun) | 🟠 | claims limités à l'emprise ; split chrono documenté |
| sklearn absent de requirements.txt | 🟡 | l'ajouter (déjà installé : 1.5.2) |
| Sur-apprentissage saisonnier | 🟡 | split chrono + purge ±16 j |
| Attentes juges (« prévision d'incendie ») | 🟡 | wording verrouillé : « risque d'activité détectée » |
| Temps hackathon | 🟠 | fallback = baseline fréquence seule (déjà une feature) |

---

## 13. Critères de réussite

1. Modèle entraîné sur données `nasa_firms` réelles, artefact
   `fire_risk.json` horodaté avec `data_origin` et version du modèle.
2. PR-AUC > baseline fréquence sur le jeu test 2019-2020 (sinon livrer
   la baseline — voir §9).
3. Carte : couches de risque visibles, légende, disclaimer « estimation
   d'activité détectée — pas une alerte incendie ».
4. Zéro régression : 91 tests verts, harmonisation et vues existantes
   inchangées.
5. Documentation : méthode, limites, métriques dans le rapport.

---

## 14. Recommandation finale

## **GO WITH LIMITATIONS**

La fonctionnalité est réalisable et défendable scientifiquement **si** :

1. Les CSV FIRMS bruts sont récupérés (prérequis absolu) ;
2. Le label reste « détection future » et non « incendie » ;
3. La baseline de fréquences est livrée comme référence obligatoire ;
4. Le moteur d'harmonisation reste prioritaire — la prédiction est un
   module **additif** (nouveau fichier pipeline + artefact + couche
   carte), jamais une modification du cœur scientifique.

Le pire scénario acceptable : baseline seule sur la carte = fonctionnalité
« risque » déjà visible et honnête, en attendant le ML.

---

## Annexe — Références dépôt

- `src/pyrolens/grids.py` — `cell_id`, `make_key`, `window_index` (clés
  cellule/date/epoch, base du feature engineering).
- `src/pyrolens/baselines.py` — `build_set`, `compare_sets` (Jaccard),
  `_monthly/_daily/_region_divergence` (patterns d'agrégation réutilisables).
- `api/jobs.py` — `JobManager` + `job.report()` (progression temps réel,
  pattern pour un futur entraînement asynchrone).
- `api/services/experiments.py` — `resolve_source_dir`, `data_origin_of`,
  `_source_digest` (provenance source, réutilisable pour `predict`).
- `api/store.py` — `ArtifactStore` (lecture/ETag des artefacts JSON).
- `web/public/artifacts/baselines.json` — `grids_deg`, `window_days`,
  `summary`, `daily`, `spatial` (structures de sortie existantes).
- `web/public/artifacts/audit.json` — `row_accounting`, `frp_stats`,
  `volumes_by_month`, `temporal_gaps`, `satellites`.
- `web/public/fire-monitor.html` — couche Leaflet, `zoneCal`, `drawLines`,
  `banner(data_origin)` (points d'intégration frontend).
- `src/pyrolens/harmonization.py` — H1–H6 : catalogue des approches,
  H4 (confiance) et H5 (FRP) explicitement NON exécutées — la prédiction
  ne doit pas prétendre les avoir résolues.
- `requirements.txt` — polars/pandas/numpy/pyarrow présents ; **sklearn
  absent du fichier mais installé (1.5.2)** ; xgboost/lightgbm absents.
