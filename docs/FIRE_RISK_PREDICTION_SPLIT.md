# Fire Risk Prediction — Répartition du travail

> Document de coordination pour la fonctionnalité « Fire Risk Prediction »
> (voir `docs/FIRE_RISK_PREDICTION_FEASIBILITY.md` — GO WITH LIMITATIONS).
> **Aurel** = frontend · **Abdourahim** = backend/pipeline.

---

## 1. Vue d'ensemble

```
CSV FIRMS (data/raw/firms/)                web/public/fire-monitor.html
        │                                          ▲
        ▼                                          │
┌─────────────────────┐                    couche « risque » sur la carte
│  BACKEND — Abdourahim│                    (probabilités + légende + disclaimer)
│  src/pyrolens/       │                            ▲
│  api/                │                            │
└─────────────────────┘                    GET /api/v1/fire-risk (optionnel)
        │
        ▼
web/public/artifacts/fire_risk.json  ← artefact JSON horodaté
(model.joblib à côté, jamais servi)
```

Le frontend ne fait **aucun calcul** : il lit l'artefact (mode statique) ou
l'endpoint API (mode API). Le backend produit une **probabilité calibrée**,
jamais une certitude.

---

## 2. Abdourahim — Backend / Pipeline

### 2.1 Livrables

| # | Livrable | Fichiers | Contenu |
| --- | --- | --- | --- |
| B1 | Module de prédiction | `src/pyrolens/prediction.py` (nouveau) | agrégation cellule-jour (polars), features trailing 8/16/32 j, label union capteurs J+8, split chrono 2013-16/17-18/19-20 avec purge ±16 j, baseline fréquence + RandomForest, calibration proba, dump artefact |
| B2 | Commande CLI | `src/pyrolens/cli.py` | `pyrolens predict [--grid 0.25] [--window 8]` → écrit `web/public/artifacts/fire_risk.json` + métriques |
| B3 | Artefact | `web/public/artifacts/fire_risk.json` | `{generated_at, data_origin, model:{type,version,features}, metrics:{pr_auc, f1, baseline_pr_auc}, cells:[{cell_i,cell_j,prob,level}]}` |
| B4 | Endpoint API (optionnel) | `api/routers/` + `api/store.py` | `GET /api/v1/fire-risk` sert l'artefact comme les autres ; ETag standard |
| B5 | Tests | `tests/` | tests unitaires features/label sur fixture + test endpoint |

### 2.2 Exigences scientifiques (non négociables)

- Label = « ≥1 détection **tous capteurs confondus** sur [t+1, t+8] » — jamais « incendie ».
- Features calculées **uniquement sur données ≤ t** (fenêtres trailing).
- Split **chronologique**, purge ±16 jours aux frontières.
- `data_origin` propagé : `nasa_firms` ou `synthetic_fixture` — le frontend
  l'affiche, un modèle fixture ne doit jamais passer pour réel.
- Si le RF ne bat pas la baseline de ~5 % PR-AUC → **livrer la baseline**.
- sklearn : l'ajouter à `requirements.txt` (déjà installé, 1.5.2).

### 2.3 Critère de done backend

`pyrolens predict` produit un artefact valide, les métriques de validation
sont écrites dedans, et `GET /api/v1/fire-risk` (si B4 fait) renvoie le JSON
avec provenance. Les 91 tests existants restent verts.

---

## 3. Aurel — Frontend

### 3.1 Livrables

| # | Livrable | Fichier | Contenu |
| --- | --- | --- | --- |
| F1 | Couche risque sur la carte | `web/public/fire-monitor.html` | grille de cellules `L.rectangle` colorées par probabilité (échelle rouge/orange), uniquement dans les limites de l'emprise |
| F2 | Légende + niveaux | même fichier | échelle « Faible / Modéré / Élevé » avec seuils explicites, probabilités au survol (popup : %, cellule, date de référence) |
| F3 | Bandeau honnêteté | même fichier | « Estimation du risque d'activité de feu **détectée** — pas une alerte incendie · données `data_origin` · généré le … » via le `banner()` existant |
| F4 | Contrôles (optionnel) | même fichier | sélecteur de date de référence, bascule couche risque on/off, slider de seuil |
| F5 | Vue Qualité (optionnel) | même fichier | PR-AUC / F1 / baseline affichés depuis l'artefact, matrice de confusion si fournie |

### 3.2 Règles UI

- **Aucun calcul côté client** : lire `fire_risk.json` (statique) ou
  `/api/v1/fire-risk` (API) — même pattern que `fireSeries()`/`fireCal()`.
- Ne jamais afficher une probabilité sans son `data_origin` et sa date.
- Les libellés disent « risque d'activité détectée », pas « incendie »,
  pas « alerte », pas « prévision météo de feu ».
- Palette existante : ember/orange pour l'intensité — cohérent avec GIBS.

### 3.3 Contrat de données attendu (artefact)

```json
{
  "generated_at": "ISO-8601",
  "data_origin": "nasa_firms | synthetic_fixture",
  "model": { "type": "random_forest|frequency_baseline", "version": "…" },
  "metrics": { "pr_auc": 0.0, "f1": 0.0, "baseline_pr_auc": 0.0 },
  "cells": [{ "cell_i": 0, "cell_j": 0, "lat": 0.0, "lon": 0.0, "prob": 0.0 }]
}
```

Tant que l'artefact n'existe pas, la couche est masquée proprement (comme les
vues en mode statique sans données).

---

## 4. Points de contact

| Sujet | Qui |
| --- | --- |
| Noms exacts des champs de l'artefact | Abdourahim définit → Aurel consomme |
| Seuils des niveaux de risque | À valider ensemble (probas calibrées) |
| `data_origin` / disclaimers | Aurel les affiche, Abdourahim les produit |
| Tests croisés (artefact → carte) | Aurel vérifie le rendu sur fixture puis réel |

## 5. Ordre suggéré

1. **Abdourahim** : A1 (récupérer les CSV) → A2/A3 (module + baseline/RF) → artefact
2. **Aurel** : maquette de la couche avec des données fictives étiquetées,
   en parallèle — branchement réel dès l'artefact disponible
3. **Ensemble** : revue des métriques, wording final, démo

Le MVP reste additif : aucun fichier du moteur d'harmonisation n'est modifié.
