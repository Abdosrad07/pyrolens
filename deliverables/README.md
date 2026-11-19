# PyroLens — Livrables NASA Space Apps 2026

## Fichiers produits

```
deliverables/
├── video/
│   ├── PyroLens_Demo_30s.mp4       (à générer)
│   ├── PyroLens_Subtitles.srt      ✓ généré
│   └── video_script.md            ✓ généré
├── presentation/
│   └── PyroLens_NASA_2026.pptx    ✓ généré (7 slides)
├── screenshots/
│   ├── 01_map_risk.png            ✓ (4.8 MB, 1440×900 @2x)
│   ├── 02_sensor_comparison.png   ✓
│   ├── 03_historical_calendar.png ✓
│   ├── 04_risk_model.png          ✓
│   ├── 05_jobs_dashboard.png      ✓
│   └── 06_data_quality.png        ✓
└── README.md                      (ce fichier)
```

## Outils utilisés

| Outil | Usage |
|-------|-------|
| Playwright (Chromium) | Captures d'écran authentiques de l'app |
| python-pptx 1.0.2 | Génération du PPTX 7 slides |
| MoviePy | Montage vidéo (à exécuter) |
| NASA FIRMS | Source de données (nasa_firms) |
| NASA GIBS | Imagerie satellite (couches carte) |
| Esri | Fonds cartographiques |
| OpenStreetMap | Géocodage |

## Sources de données

- **NASA FIRMS** : 1,170 fichiers MODIS SP + VIIRS SNPP, 2013–2020.
- **4,46 millions de détections** auditées (schema, dates, bornes).
- **117 0 fichiers audités** (audit.json, data_origin = nasa_firms).

## Métriques scientifiques retenues

| Métrique | Valeur | Contexte |
|----------|--------|----------|
| PR-AUC (test 2019–2020) | 0.926 | Backtest historique |
| F1-score | 0.841 | Backtest historique |
| Brier Score | 0.072 | Backtest historique |
| Baseline PR-AUC | 0.875 | Fréquence (train) |
| Jaccard (MODIS/VIIRS) | 0.335 | Recouvrement d'ensembles |

## Limitations

- La vidéo (`PyroLens_Demo_30s.mp4`) n'est pas encore générée (MoviePy requis).
- Certaines captures d'écran montrent la vue carte (le dock est visible dans les 6 vues).
- L'app fonctionne en mode statique si le backend n'est pas démarré.

## Vérifications effectuées

- [x] API FastAPI répond sur `http://127.0.0.1:8010/api/v1/health`
- [x] Endpoint `/api/v1/fire-risk` retourne les métriques réelles
- [x] `data_origin = nasa_firms` confirmée
- [x] `estimate_kind = historical_backtest` (pas de prévision opérationnelle)
- [x] PPTX : 7 slides, 16:9, notes de présentation incluses
- [x] Sous-titres SRT : 6 segments, 30s au total

## Déclaration IA

Les livrables (PPTX, script de vidéo, sous-titres) ont été générés avec assistance
IA (Claude Code). Les données scientifiques et les captures d'écran sont authentiques
et proviennent de l'application PyroLens.

## Crédit

- NASA FIRMS — open access data
- NASA GIBS — satellite imagery layers
- Esri — base maps
- OpenStreetMap — geocoding
- Code source : MIT License (vérifier `LICENSE` à la racine du repo)
