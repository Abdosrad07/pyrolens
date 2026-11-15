# PyroLens — Documentation complète du projet

> Étude de faisabilité NASA Space Apps Challenge 2026 : comparaison et
> harmonisation des détections thermiques **MODIS** et **VIIRS** (NASA FIRMS),
> analyse de zone historique, et modèle de prédiction de risque d'activité
> détectée sur le Cameroun et l'Afrique de l'Ouest.

---

## 1. Vue d'ensemble

PyroLens répond à trois questions :

1. **Les capteurs se comportent-ils pareil ?** — Comparaison VIIRS/MODIS sur
   grille commune et fenêtres canoniques, mesurée par le **Jaccard** (recouvrement
   d'ensembles, jamais une précision).
2. **Que s'est-il passé sur une zone donnée ?** — Analyse à la demande sur un
   périmètre cliqué à la carte : NRT (~5 jours) ou **historique archive**
   (2013→aujourd'hui, fichiers annuels par pays).
3. **Où l'activité détectée va-t-elle continuer ?** — Modèle de risque
   **RandomForest calibré** : P(≥1 détection FIRMS dans les 8 jours) par cellule.

### Principe scientifique directeur

> Une détection satellite est une **observation**, pas un incendie.
> Une cellule vide ne signifie **jamais** « pas de feu » : nuages, nuit,
> angles de visée et passages satellites créent des angles morts.
> Toutes les sorties portent `data_origin` (nasa_firms /
> synthetic_fixture / firms_archive_sp) et `estimate_kind`
> (historical_backtest) pour que l'interface ne puisse pas sur-vendre
> les résultats.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  DONNÉES                                                         │
│  data/raw/firms/        1 171 CSV canoniques (2013-2020, 344 Mo) │
│  data/raw/archive/      CSV annuels par pays (2013-2025, ~18 p.) │
│  data/fixture/          fixtures synthétiques (tests/démo)      │
│  data/raw/geo/          Natural Earth 110m (pays → bbox)        │
└──────────────┬──────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────┐
│  PIPELINE  src/pyrolens/  (CLI `pyrolens …`)                     │
│  ingest → audit → baselines → observability → normalize →       │
│  figures → report → predict (modèle de risque)                  │
└──────────────┬──────────────────────────────────────────────────┘
               │ écrit des artefacts JSON horodatés
┌──────────────▼──────────────────────────────────────────────────┐
│  API FastAPI  api/  →  http://127.0.0.1:8010/api/v1             │
│  Lecture artefacts (ETag) · jobs async (1 worker) · POST        │
│  protégés par PYROLENS_API_TOKEN                                │
└───────┬───────────────────────────────┬─────────────────────────┘
        │ /api proxy                     │ /artifacts statiques
┌───────▼──────────┐          ┌──────────▼────────────────────────┐
│ frontend/ React  │          │ web/public/fire-monitor.html     │
│ Vite, port 5174  │          │ Fire Monitor vanilla JS           │
│ (interface       │          │ (interface autonome, conservée)  │
│  principale)     │          │ + web/ ancienne app React 5173   │
└──────────────────┘          └───────────────────────────────────┘
```

**Règle d'or de l'API** : lecture seule des artefacts + exécution de jobs
bornés. Aucun calcul scientifique n'est fait « à la volée » dans une
requête GET ; les POST (analyze, history, predict, chat, experiments)
soumettent des jobs au `JobManager` (thread unique, progression réelle,
reprise sur disque pour les gros jobs).

---

## 3. Données

### 3.1 Sources

| Source | Contenu | Accès |
|---|---|---|
| FIRMS NRT API (`firms.modaps…/api/area/csv`) | Détections ~5 derniers jours par bbox | `FIRMS_MAP_KEY` requis |
| FIRMS **archive pays** (`/data/country/{capteur}/{année}/{fichier}.csv`) | Années complètes par pays, standard processing | **ouvert, sans clé** |
| GeoJSON Natural Earth 110m | Polygones pays → intersection bbox | local |
| `data/fixture/` | CSV synthétiques reproductibles (graine fixe) | local, pour tests/démo |

### 3.2 Volumes réels acquis

- **Pipeline** : 1 171 fichiers canoniques (fenêtres 5 j, 2013-01 → 2020-12)
  — ~1,8 M détections, 344 Mo
- **Archive zone** : 12 fichiers (Chad/Nigeria/Cameroon 2019-2020) —
  410 370 détections VIIRS + 79 666 MODIS sur la bbox test
- **Archive Afrique de l'Ouest** (en cours) : 18 pays × 2 capteurs ×
  13 ans (2013-2025) ≈ 468 fichiers — script
  `scripts/download_west_africa_archive.py`, manifest
  `data/manifests/archive_bulk_west_africa.jsonl`

### 3.3 Normalisation

`pyrolens normalize` fusionne les tronçons 5 j en **fenêtres canoniques**
[date, date+5j[ avec dédoublonnage strict par `(cellule, date, capteur)`.
Une date appartient à une seule fenêtre → pas de double comptage.

---

## 4. Le pipeline (`src/pyrolens/`)

| Étape CLI | Rôle | Artefact produit |
|---|---|---|
| `download` | Acquiert FIRMS NRT + sonde Earthdata | `data/manifests/downloads.json` |
| `audit` | Qualité : anomalies, trous temporels, valeurs manquantes | `artifacts/audit.json` |
| `baselines` | Comparaison A (Terra-Aqua), B (Aqua-VIIRS), C (sensibilité) | `artifacts/baselines.json` |
| `observability` | 4 états d'observabilité — **jamais** « pas de feu » | `artifacts/observability.json` |
| `normalize` | Fenêtres canoniques 5 j | CSV normalisés |
| `figures` / `report` | Graphiques + rapport Markdown/DOCX | `figures/`, `reports/` |
| `predict` | **Modèle de risque** (voir §7) | `artifacts/fire_risk.json` + `models/` |

Le point clé : chaque artefact porte `generated_at`, `data_origin`,
`project_version` — la provenance est dans la donnée, pas dans un README.

---

## 5. L'API (`api/`)

Base : `http://127.0.0.1:8010/api/v1` — doc interactive `/api/v1/docs`.

### Lecture (GET, sans token)

| Endpoint | Contenu |
|---|---|
| `/health` `/meta` | Santé, période, config primaire, paires |
| `/catalog`, `/catalog/{id}` | Jeux de données et variables |
| `/audit/summary` | Synthèse audit |
| `/baselines*` `/fire-calendar/{daily,weekly,monthly,timeseries}` | Comparaisons + séries temporelles |
| `/methodology*` `/validation*` | Méthodologie et décisions |
| `/fire-risk` | **Artefact du modèle de risque** |
| `/report` | Rapport scientifique Markdown |
| `/downloads/status` | Progression pipeline + archive (disque seul) |

### Écriture (POST, token `PYROLENS_API_TOKEN` si configuré)

| Endpoint | Effet |
|---|---|
| `/experiments` | Job d'harmonisation paramétrable |
| `/firms/analyze` | Analyse de zone NRT (bbox + rayon + grille) |
| `/firms/history` | Historique archive par zone (années + grille) |
| `/predict` | (Ré)entraînement du modèle de risque — job ~10 min |
| `/chat` | Assistant déterministe (voir §8) |
| `/datasets/validate` | Validation de fichier CSV |

Chaque job expose `GET …/{id}` (statut + `progress{step,pct,detail}`) et
`GET …/{id}/result`. `GET /experiments` liste **tous** les jobs.

---

## 6. Les interfaces

### `frontend/` — React (principale, port 5174)

Vite + React 18 + react-leaflet + recharts. Proxy `/api` → `VITE_API_ORIGIN`
(8010). Vues : **Carte** (tuiles GIBS + couche risque GeoJSON), **Aperçu**
(artefacts), **Calendrier** (divergence quotidienne réelle), **Jobs**
(jobs API réels), **Qualité** (audit.json), **Risque** (panneau config +
« Exécuter prédiction » → `POST /predict` + polling).

```bash
cd frontend && npm install && npm run dev   # http://localhost:5174
```

### `web/public/fire-monitor.html` — Fire Monitor vanilla (autonome)

Même design, zéro build : servi par n'importe quel statique ou par le dev
server `web/` (5173). Ajouts : clic carte → analyse zone NRT/historique,
calendrier multi-années, jauge downloads temps réel.

### `web/` — ancienne app React

Conservée pour les vues pipeline (baselines, observability, méthodologie).

---

## 7. Le modèle de prédiction de risque — en détail

Module : `src/pyrolens/prediction.py` — fonction `run_prediction()`.

### 7.1 Le problème

Pour chaque **cellule de grille 0,25°** et chaque **date t** :

```
label(t) = 1  si ≥ 1 détection FIRMS dans ]t, t+8 jours]
         = 0  sinon
```

Le modèle estime `P(label = 1 | features(t))` — la probabilité qu'une
cellule connaisse au moins une détection dans les 8 jours. **Ce n'est
pas une probabilité d'incendie** : c'est une probabilité de détection.

### 7.2 Les données d'entraînement

- 1 170 CSV FIRMS canoniques → ~1,8 M détections → cellules (i, j) sur
  grille 0,25° + jour d'acquisition
- Fenêtre d'échantillonnage : `[min_date + 32 j, max_date − 8 j]`,
  **pas de 7 jours** entre deux dates par cellule
- 1 215 cellules « actives » (≥ 1 détection sur la période) →
  **489 645 échantillons**

### 7.3 Les features — 100 % « trailing »

Règle absolue : à la date `t`, seules des observations `≤ t` sont
utilisées. Pour chaque cellule :

| Feature | Description |
|---|---|
| `n_{terra,aqua,viirs}_8/16/32` | détections par capteur sur 8/16/32 j glissants |
| `n_all_*` | tous capteurs confondus |
| `frp_mean_16`, `frp_max_16` | puissance radiative moyenne/max (16 j) |
| `days_active_32`, `day_frac_32` | jours avec ≥1 détection / fraction (32 j) |
| `viirs_conf_{low,nominal,high}_16` | détections par confiance VIIRS |
| `modis_conf_mean_16` | confiance moyenne MODIS |
| `month_sin`, `month_cos` | saisonnalité (saison sèche) |
| `lat`, `lon` | position de la cellule |

Implémentation : `CellIndex` trie les dates par cellule ;
`_count_in/_sum_in/_max_in/_mean_in` utilisent `np.searchsorted` →
features en O(log n) par cellule-date.

### 7.4 Le split — chronologique, jamais aléatoire

```
train      : 2013 → 2016   (245 430 échantillons)
validation : 2017 → 2018   (121 500)
test       : 2019 → 2020   (122 715)   ← jamais touché avant le rapport
```

**Purge de 8 jours** aux frontières : un label train ne peut pas chevaucher
une feature validation/test (fuite par la fenêtre). C'est ce qui rend les
métriques test honnêtes — un split aléatoire aurait gonflé les scores.

### 7.5 Les deux modèles en compétition

**Baseline « fréquence »** (référence) : pour chaque cellule, probabilité =
fréquence de jours avec détection, lissée sur l'historique train +
ajustement saisonnier mensuel. Aucune ML — pure statistique.
Validation : **PR-AUC = 0,875**.

**RandomForest** (`sklearn.ensemble.RandomForestClassifier`) :
- 200 arbres, `class_weight='balanced_subsample'` (seulement ~6 % de
  positifs — sinon le modèle prédit « non » partout)
- `min_samples_leaf=20`, profondeur libre, `random_state=42`
- 24 features → le RF capture les interactions non linéaires
  (« 3 détections cette semaine » ≠ « il y a 3 semaines ») sans normalisation

Validation : **PR-AUC = 0,928** → retenu (règle : > baseline × 1,05).
`feature_importances_` confirme que les comptes récents dominent —
la **persistance** de l'activité est le signal principal.

### 7.6 La calibration isotonic

Le RF sort des scores, pas des probabilités fiables. Une **isotonic
regression** est ajustée **uniquement sur la validation** : une probabilité
affichée de 42 % correspond alors à une fréquence observée ~42 %.
Sans cette étape, les % de la carte seraient trompeurs.

### 7.7 Les métriques (test 2019-2020, jamais vu à l'entraînement)

| Métrique | Valeur | Lecture |
|---|---|---|
| **PR-AUC** | **0,926** | aire sous la courbe précision-rappel — la métrique clé avec 6 % de positifs |
| F1 | 0,841 | compromis précision/rappel au seuil optimal (0,42) |
| Rappel | 0,844 | 84 % des jours à détection sont couverts |
| Brier | 0,072 | qualité probabiliste (probabilités calibrées) |

### 7.8 Sortie

`fire_risk.json` : `cells[]` {cell_i, cell_j, lat, lon, prob, level},
`metrics`, `period`, `reference_date` (2020-12-31), `estimate_kind` =
`historical_backtest`, `data_origin` = `nasa_firms`. Le modèle
sérialisé (`models/fire_risk_model.joblib`, ~300 Mo) est **hors Git** —
régénérable par `pyrolens predict` en ~10 min.

### 7.9 Limites honnêtes

- **Backtest uniquement** : données ≤ 2020 ; la carte est une simulation
  historique, pas une prévision d'aujourd'hui
- Label = détection, pas feu → les métriques mesurent la capacité à
  anticiper ce que les satellites *verront*, nuages inclus
- Pas de drivers météo (précipitations, vent, humidité) — le signal est
  dominé par la persistance ; ajouter ERA5 est la suite logique
- Un seuil unique (0,42) pour tout le Cameroun — une calibration
  spatiale améliorerait la carte

---

## 8. L'assistant (`/api/v1/chat`)

Déterministe, **sans LLM** : `api/services/chat.py` détecte 8 intentions
(prédiction, zone, historique, données, calendrier, jobs, qualité, aide)
et répond depuis les artefacts réels + l'état live des jobs. Chaque
réponse cite sa source — cohérent avec la rigueur du projet, et le point
d'injection naturel si un LLM est ajouté plus tard.

---

## 9. Lancer le projet

```bash
# 1. Backend (prérequis : .env.local avec FIRMS_MAP_KEY, PYROLENS_API_TOKEN)
set PYTHONPATH=src
python -m uvicorn api.app:app --host 127.0.0.1 --port 8010

# 2. Frontend React (principal)
cd frontend && npm install && npm run dev        # → http://localhost:5174

# 3. Ou Fire Monitor autonome (statique)
cd web && npm install && npm run dev              # → http://localhost:5173
# ou simplement ouvrir web/public/fire-monitor.html

# 4. Pipeline (si besoin de régénérer)
python -m pyrolens.cli download                   # données FIRMS
python -m pyrolens.cli audit baselines observability normalize
python -m pyrolens.cli predict                    # modèle de risque (~10 min)
python -m pyrolens.cli report                     # rapport final
```

### Tests

```bash
python -m pytest tests        # 114 tests (pipeline + API + predict + archive)
cd frontend && npm run build  # vérif build React
```

---

## 10. Limites scientifiques (rappel)

1. Détection ≠ incendie ; cellule vide ≠ absence de feu
2. Jaccard = recouvrement d'ensembles entre capteurs, pas une précision
3. Les données < 2021 proviennent du **pipeline** (NRT canoniques) ;
   2019+ proviennent aussi de l'**archive SP** quand disponible —
   la provenance est toujours affichée
4. L'archive pays a quelques mois de retard sur l'année courante ;
   le NRT couvre les ~5 derniers jours
5. Tous les chiffres du modèle sont des **backtests** sur données
   historiques — jamais présentés comme des prévisions opérationnelles

---

## 11. Structure du dépôt

```
pyrolens/
├── api/                  FastAPI — routers/, services/, jobs.py, store.py
├── src/pyrolens/         pipeline : ingest, audit, baselines, normalize,
│                         observability, archive, prediction, cli, report
├── frontend/             React principal (port 5174)
├── web/                  ancienne app React + fire-monitor.html autonome
├── scripts/              download_west_africa_archive.py (bulk archive)
├── data/
│   ├── raw/firms/        CSV pipeline (gitignoré)
│   ├── raw/archive/      CSV archive pays (gitignoré)
│   ├── raw/geo/          Natural Earth
│   ├── fixture/          synthétiques
│   └── manifests/        downloads.json + archive_bulk_*.jsonl
├── models/               .joblib (gitignoré, régénérable)
├── web/public/artifacts/ artefacts JSON servis (versionnés)
├── docs/                 ce fichier + FIRE_RISK_PREDICTION*.md + phase2/
└── tests/                pytest (pipeline, api, prediction, archive)
```
