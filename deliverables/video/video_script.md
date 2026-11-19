# PyroLens — Video Demo Script (30s)

## Format
- **Durée cible** : 30 secondes maximum
- **Résolution** : 1280 × 720 (720p)
- **FPS** : 30
- **Audio** : bande sonore discrète (pas de voix off)
- **Texte** : sous-titres anglais intégrés

## Scénario

| # | Temps | Écran | Texte (sous-titre) |
|---|-------|-------|-------------------|
| 1 | 0:00–0:05 | Carte interactive avec couche de risque | "PyroLens — a reproducible platform for comparing NASA MODIS and VIIRS fire observations." |
| 2 | 0:05–0:10 | Vue Aperçu / comparaison capteurs | "MODIS and VIIRS see different things. Jaccard overlap quantifies their agreement — not accuracy." |
| 3 | 0:10–0:15 | Calendrier historique 2013–2020 | "Historical calendar: inter-sensor divergence per day, 2013 to 2020." |
| 4 | 0:15–0:20 | Panneau de risque (métriques RF) | "Detection-probability model: Random Forest, isotonic calibration, PR-AUC 0.926." |
| 5 | 0:20–0:25 | Tableau de bord Jobs + qualité | "Live pipeline: jobs, data quality, and full provenance of every artifact." |
| 6 | 0:25–0:30 | Rapport qualité de données | "No detection does not mean no fire. PyroLens keeps that honesty visible in every view." |

## Indications visuelles

- Transition : fondu enchaîné (0.5s) entre chaque écran
- Les sous-titres apparaissent en bas, police sans-serif, blanc sur fond semi-transparent
- La vidéo commence sur la carte (vue dominante) et se termine sur le rapport qualité

## Crédits (fin de vidéo, optionnel)

- NASA FIRMS — Open data
- NASA GIBS — Satellite imagery
- Esri — Base maps
- OpenStreetMap — Geocoding

## Outils utilisés

- **Captures d'écran** : Playwright (Chromium)
- **Montage vidéo** : MoviePy (Python)
- **Sous-titres** : SRT
