# Fire Risk Prediction — Documentation technique

> Module backend de prédiction du risque d'activité de feu **détectée**.
> Étude de faisabilité : `docs/FIRE_RISK_PREDICTION_FEASIBILITY.md` (GO WITH LIMITATIONS).
> Répartition Aurel/Abdourahim : `docs/FIRE_RISK_PREDICTION_SPLIT.md`.

---

## 1. Ce que le modèle prédit — et ce qu'il ne prédit pas

Pour une cellule `(i,j)` de la grille PyroLens et une date de référence `t`,
le modèle estime :

```
P( ≥1 détection FIRMS dans la cellule sur les `horizon` jours suivant t )
```

**Formulation verrouillée** : « risque d'activité de feu **détectée** par les
satellites » — jamais « risque d'incendie », jamais « alerte ». Une absence
de détection ne prouve pas l'absence de feu (nuages, heure de passage,
résolution) ; les périodes sous-couvertes produisent des labels bruités,
limite assumée et documentée dans l'artefact (`notes`).

## 2. Architecture

```
data/raw/firms/*.csv  (ou data/fixture/)
        │  pyrolens predict
        ▼
src/pyrolens/prediction.py
  ├─ load_events()        CSV → événements (ci, cj, d, sensor, frp, conf)
  ├─ build_cell_index()   index trié par date par cellule (numpy/searchsorted)
  ├─ build_dataset()      features trailing + label J+horizon, pas = stride
  ├─ split_mask()         train 2013-16 / val 2017-18 / test 2019-20 + purge
  ├─ fit_models()         baseline fréquence + RandomForest + calibration
  └─ export_artifact()    web/public/artifacts/fire_risk.json
        │
        ▼  (optionnel)
GET /api/v1/fire-risk     sert l'artefact, ETag, 404 propre si absent
```

Le modèle sérialisé va dans `models/` (racine projet) — **jamais** dans
`web/public/` : `fire_risk_model.joblib` ou `fire_risk_baseline.json`.

## 3. Données

- **Réelles** : `data/raw/firms/` — 1 170 fenêtres canoniques 5 j,
  2013-01 → 2020-12, ~1,83 M détections analysables (audit.json).
  `data_origin = nasa_firms`.
- **Fixture** : `data/fixture/` — 3 CSV synthétiques 2019.
  `data_origin = synthetic_fixture` — propagé jusqu'au JSON et à l'UI.
- Colonnes exploitées : `latitude, longitude, acq_date, satellite,
  confidence, frp, daynight`. **Non disponibles** : météo, végétation,
  vent — non utilisées (collecte externe hors périmètre).

## 4. Features (24)

Fenêtres trailing `[t-w+1, t]` — jamais postérieures à t :

| Groupe | Features |
| --- | --- |
| Comptes capteur | `n_{terra,aqua,viirs_snpp}_{8,16,32}` (9) |
| Union | `n_all_{8,16,32}` (3) |
| FRP | `frp_mean_16`, `frp_max_16` (union) |
| Activité | `days_active_32`, `day_frac_32` (jour/nuit) |
| Confiance native | `viirs_conf_{low,nominal,high}_16` + `modis_conf_mean_16` — **échelles jamais fusionnées** |
| Contexte | `month_sin`, `month_cos`, `lat`, `lon` (centroïde cellule) |

## 5. Label

`y=1` si ≥1 détection **tous capteurs confondus** dans `]t, t+horizon]`
(horizon = 8 j par défaut). L'union maximise la sensibilité du label.

## 6. Modèles et sélection

| Modèle | Rôle |
| --- | --- |
| **Baseline fréquence** | Taux (cellule, mois) lissé bêta à deux niveaux (pseudo-comptages α=30 cellule, α=15 mois) — stable sur cellules rares |
| **RandomForest** | `n_estimators=200, class_weight="balanced_subsample", min_samples_leaf=5, random_state=42` |
| **Calibration** | Isotonic si val ≥ 500 échantillons, sinon Platt (logit + logistique) — les probabilités RF brutes ne sont jamais publiées |

**Règle de sélection** (sur la **validation** uniquement) : le RF n'est
retenu que si `PR-AUC_RF > PR-AUC_baseline × 1.05` (**relatif**, pas absolu).
Sinon la baseline est le modèle final — c'est une fonctionnalité défendable.

## 7. Protocole d'évaluation

| Split | Période | Usage |
| --- | --- | --- |
| train | 2013–2016 | entraînement baseline + RF |
| validation | 2017–2018 | calibration, choix du seuil F1, choix du modèle |
| test | 2019–2020 | évaluation finale — jamais touché avant |

Purge : ±16 jours autour des frontières 2017/2019 (labels 8 j + marge).
Pas d'échantillonnage : `stride=7` jours (décorrélation). Cellules actives
uniquement (≥1 détection sur la période).

**Métriques** (sur test) : PR-AUC (principale), ROC-AUC, recall, precision,
F1, Brier, matrice de confusion, table de calibration (10 bins).
Le seuil est le F1-max de la **validation**, jamais du test.

## 8. Artefact `fire_risk.json`

```json
{
  "generated_at": "…", "reference_date": "AAAA-MM-JJ",
  "prediction_horizon_days": 8, "estimate_kind": "historical_backtest",
  "data_origin": "nasa_firms | synthetic_fixture",
  "model": {"type": "…", "version": "…", "features": […], "calibration": "…", "threshold": 0.x},
  "metrics": {"pr_auc": …, "f1": …, "recall": …, "brier": …, "confusion_matrix": [[…]], "validation": {…}},
  "period": {"start": "…", "end": "…"},
  "cells": [{"cell_i": 0, "cell_j": 0, "lat": 0.0, "lon": 0.0, "prob": 0.x, "level": "low|moderate|high"}],
  "notes": "…"
}
```

`level` : `high` si prob ≥ seuil F1, `moderate` si ≥ seuil/2, sinon `low`.

## 9. Gestion de la date de référence

- `reference_date` = max des données par défaut → **backtest historique**.
- `estimate_kind` est **toujours** `historical_backtest` : les données
  s'arrêtent en 2020, aucune estimation « actuelle » n'est produite.
- Pour un jour J réel il faudrait des observations FIRMS récentes en entrée
  (module séparé, non implémenté — la zone NRT existe déjà via
  `/firms/analyze` mais ne fournit pas 32 j d'historique par cellule).

## 10. Exécution

```bash
# données réelles (après pyrolens download) ou fixture
PYTHONPATH=src python -m pyrolens.cli predict                 # tout par défaut
PYTHONPATH=src python -m pyrolens.cli predict --grid 0.25 --window 8
PYTHONPATH=src python -m pyrolens.cli predict --source data/fixture --reference-date 2019-12-31
PYTHONPATH=src python -m pyrolens.cli predict --stride 3      # échantillonnage plus fin
```\n
Sorties : `web/public/artifacts/fire_risk.json` + `models/fire_risk_*.joblib|json`.

API : `GET /api/v1/fire-risk` → artefact + ETag ; 404 propre si absent ;
aucun recalcul à la requête.

## 11. Résultats sur données réelles (2026-11-14)

Exécution : `pyrolens predict --grid 0.25 --window 8` sur les 1 170 CSV
FIRMS canoniques (2013-01 → 2020-12, `data_origin=nasa_firms`).

| Indicateur | Valeur |
| --- | --- |
| Cellules actives | 1 215 |
| Échantillons | 489 645 (train 245 430 / val 121 500 / test 122 715) |
| Taux de positifs | **31,8 %** (38 964 / 122 715) |
| **Modèle retenu** | `random_forest` (PR-AUC val 0,928 > baseline 0,875 × 1,05) |
| Calibration | isotonic |
| Seuil F1 (val) | 0,42 |
| **PR-AUC test** | **0,926** |
| F1 / recall test | 0,841 / 0,844 |
| Brier test | 0,072 |

Interprétation : le RF exploite la forte persistance de l'activité de feu
(comptes récents par capteur) — PR-AUC élevé mais **pas** une probabilité
d'incendie : c'est P(≥1 détection FIRMS dans les 8 j). La baseline seule
atteint déjà 0,875 : le signal est dominé par la persistance, pas par des
drivers météo (absents des features).

## 12. Reproduction

1. `pip install -r requirements.txt` (inclut `scikit-learn>=1.5`)
2. `pyrolens download` (données réelles) ou `pyrolens fixture`
3. `pyrolens predict` → artefact reproductible (graines fixes : RF
   `random_state=42`, échantillonnage déterministe par tri des dates)
4. `python -m pytest` → 105 tests

## 13. Limites scientifiques

- **Un seul domaine** (Cameroun) : aucune généralisation spatiale revendiquée.
- Label bruité par la couverture (nuages) — atténué par l'union capteurs,
  pas éliminé ; l'observabilité n'existe qu'au niveau emprise.
- Features limitées aux détections : pas de météo/végétation/sécheresse —
  le modèle capture la **persistance** de l'activité, pas les drivers.
- Fenêtre NRT non exploitable pour les features 32 j : la prédiction est
  un backtest, pas un produit temps réel.
- Sur fixture (1 an synthétique) le split chronologique est dégénéré —
  la validation réelle exige les CSV 2013-2020.
