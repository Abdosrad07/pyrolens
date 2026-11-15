# MISSION: PyroLens – NASA Space Apps 2026 Demo Production

Tu interviens comme un ingénieur audiovisuel, développeur Python, spécialiste du montage vidéo et designer de présentations scientifiques.

Ta mission est de produire deux démonstrations professionnelles du projet **PyroLens** :

1. Une vidéo de démonstration de 30 secondes maximum.
2. Une présentation PowerPoint de 7 diapositives maximum, entièrement modifiable et avec des notes de présentation.

Tu dois également produire les captures d'écran originales et le script de narration.

**IMPORTANT : Ne te contente pas de proposer un plan ou du code. Exécute réellement les tâches et génère les fichiers finaux.**

---

# 1. CONTEXTE DU PROJET

PyroLens est un projet développé dans le cadre du NASA Space Apps Challenge 2026.

Il propose une approche reproductible de comparaison, d'harmonisation et de modélisation du risque de détection d'anomalies thermiques MODIS et VIIRS au Cameroun et en Afrique de l'Ouest.

Le projet repose sur :
- NASA FIRMS.
- MODIS Terra et Aqua.
- VIIRS Suomi-NPP.
- Une grille spatiale de 0,25°.
- Des fenêtres temporelles de 5 et 8 jours.
- Un moteur de comparaison utilisant notamment l'indice de Jaccard.
- Un modèle Random Forest avec calibration isotonic.
- Une application interactive de visualisation et d'analyse.
- Un système de traçabilité des données.

## DISTINCTION SCIENTIFIQUE FONDAMENTALE

PyroLens NE PRÉDIT PAS LES INCENDIES.

Il estime la probabilité qu'un satellite détecte au moins une anomalie thermique dans une cellule géographique pendant une fenêtre temporelle donnée.

Cette distinction doit être respectée dans absolument tous les textes, graphiques, commentaires et narrations.

Règles obligatoires :

1. Une détection satellite est une observation, pas nécessairement un incendie confirmé.
2. Une cellule sans détection ne signifie jamais qu'il n'y a aucun incendie.
3. Les nuages, les horaires de passage, les conditions d'observation et les angles de vision créent des zones d'incertitude.
4. L'indice de Jaccard mesure un chevauchement entre ensembles de détections. Ce n'est PAS une mesure de précision ou d'exactitude.
5. Les performances du modèle correspondent à un backtest historique 2019-2020, et non à une prévision opérationnelle.
6. Les informations de provenance doivent être visibles : `data_origin`, `estimate_kind` et `generated_at`.

Formulation recommandée :

"Probability of satellite-detected fire activity"

Ne jamais utiliser :

"Fire prediction" ou "Wildfire prediction".

---

# 2. PHASE 1 — EXPLORATION ET VÉRIFICATION

Avant toute production, explore intégralement le projet.

Ressources disponibles :

- Frontend React : http://localhost:5174
- Fire Monitor : web/public/fire-monitor.html
- API : http://127.0.0.1:8010/api/v1/docs
- Artifacts : web/public/artifacts/
- Code source et documentation : répertoire du projet.

## Actions obligatoires

1. Examiner l'architecture du projet.
2. Identifier les fonctionnalités réellement opérationnelles.
3. Examiner les fichiers de données et les résultats scientifiques.
4. Identifier les véritables métriques du modèle.
5. Vérifier les statistiques dans les fichiers d'audit.
6. Démarrer les services nécessaires si ceux-ci sont arrêtés.
7. Ouvrir l'application et vérifier son fonctionnement.
8. Identifier les pages et fonctionnalités à capturer.

Utilise Playwright ou un outil équivalent pour naviguer dans l'application et capturer les véritables interfaces.

Tu peux utiliser FFmpeg pour le montage vidéo et python-pptx pour la présentation.

### Règle absolue

Ne fabrique aucune capture d'écran.

Ne crée pas de fausses données pour rendre les interfaces plus impressionnantes.

Ne présente jamais une fonctionnalité simulée comme une fonctionnalité opérationnelle.

Si une fonctionnalité est indisponible :
- Identifie précisément le problème.
- Cherche une solution dans le code existant.
- Si elle ne peut pas être récupérée, ne simule pas son fonctionnement.
- Adapte la démonstration en utilisant une fonctionnalité réellement disponible.

Les données et les fichiers d'audit constituent la source de vérité.

Ne considère pas automatiquement les statistiques fournies dans ce prompt comme vérifiées.

---

# 3. PHASE 2 — PRODUCTION DE LA VIDÉO

Produis une vidéo professionnelle de 30 secondes maximum.

## Caractéristiques techniques

- Format : MP4.
- Résolution : 1920 × 1080 minimum.
- Format d'image : 16:9.
- Fréquence : 30 FPS.
- Codec vidéo : H.264.
- Audio : AAC si une narration est utilisée.
- Sous-titres anglais intégrés à la vidéo.
- Transitions fluides et discrètes.
- Texte parfaitement lisible.

Esthétique :
- Scientifique.
- Professionnelle.
- Moderne.
- Sobre.
- Bleu marine et orange.
- Typographie claire.
- Animations limitées et fonctionnelles.

Ne reproduis aucun logo NASA.

Utilise uniquement les mentions textuelles d'attribution autorisées.

## STORYBOARD OBLIGATOIRE

### SÉQUENCE 1 — OPENING (0-4 secondes)

Objectif : présenter immédiatement le problème.

Visuels :
- Carte du monde.
- Zoom progressif vers le Cameroun.
- Apparition des hotspots provenant des données FIRMS.

Texte anglais :

"Two NASA satellite sensors observe the same fire activity differently."

### SÉQUENCE 2 — SENSOR COMPARISON (4-10 secondes)

Objectif : montrer la capacité de comparaison.

Visuels :
- Interaction avec une zone géographique.
- Ouverture du panneau d'analyse.
- Affichage des statistiques MODIS et VIIRS.
- Visualisation du chevauchement entre les deux ensembles.

Afficher un véritable indice de Jaccard.

Mention :

"Jaccard Index — Set Overlap, Not Accuracy"

### SÉQUENCE 3 — HISTORICAL ANALYSIS (10-16 secondes)

Objectif : démontrer la profondeur historique du projet.

Visuels :
- Transition vers la vue historique.
- Calendrier couvrant plusieurs années.
- Visualisation des tendances historiques 2019-2025, si les données correspondantes sont réellement disponibles.

Texte :

"Explore historical satellite detection patterns."

### SÉQUENCE 4 — RISK MODEL (16-22 secondes)

Objectif : présenter la valeur scientifique du modèle.

Visuels :
- Activation de la couche de risque.
- Heatmap des cellules géographiques.
- Affichage des probabilités calibrées.
- Mise en évidence de 1 215 cellules uniquement si ce nombre est confirmé par les artefacts.

Métriques à vérifier :
- PR-AUC : 0.926.
- F1-score : 0.841.
- Brier Score : récupérer la véritable valeur.

Mention obligatoire :

"HISTORICAL BACKTEST — 2019-2020"

Texte explicatif :

"Probability of satellite-detected activity, not wildfire prediction."

### SÉQUENCE 5 — DATA QUALITY AND JOBS (22-27 secondes)

Objectif : montrer la robustesse technique.

Visuels :
- Vue Calendar avec des données réelles.
- Vue Quality avec les statistiques issues de audit.json.
- Vue Jobs avec un véritable job.

Ne simule jamais un job en cours.

Si aucun job n'est actif, lance un véritable traitement disponible dans l'application.

### SÉQUENCE 6 — CLOSING (27-30 secondes)

Afficher :
- Logo original PyroLens.
- Nom du projet.
- Signature :

"PyroLens — Reproducible, Honest Fire Monitoring"

Fondu progressif vers le noir.

---

# 4. PHASE 3 — CAPTURES D'ÉCRAN

Produis au minimum les six captures suivantes en haute résolution :

1. `01_map_risk.png`
   Carte avec hotspots et couche de risque active.

2. `02_sensor_comparison.png`
   Panneau d'analyse avec les métriques Jaccard.

3. `03_historical_calendar.png`
   Calendrier historique multiannuel.

4. `04_risk_model.png`
   Panneau du modèle avec PR-AUC, F1 et Brier Score.

5. `05_jobs_dashboard.png`
   Tableau de bord présentant un véritable traitement.

6. `06_data_quality.png`
   Vue qualité avec les informations de audit.json.

Conditions :
- Interface en anglais.
- Données réelles.
- Résolution élevée.
- Aucun élément artificiel.
- Informations de provenance visibles lorsque l'interface les expose.

---

# 5. PHASE 4 — POWERPOINT PROFESSIONNEL

Créer une présentation de 7 diapositives maximum.

Format :
- PPTX.
- 16:9.
- Entièrement modifiable.
- Notes du présentateur incluses.
- Graphiques, tableaux et diagrammes modifiables autant que possible.
- Captures authentiques de l'application.

La présentation doit être compréhensible sans explication orale.

## SLIDE 1 — THE CHALLENGE

Titre :
"The Challenge"

Contenu :
- MODIS Terra/Aqua and VIIRS observe thermal anomalies differently.
- Different spatial resolutions and observation characteristics.
- Need for transparent multi-sensor comparison.

Sous-titre :

"Making multi-sensor fire monitoring transparent."

Visuel :
Photographie pertinente d'activité thermique ou d'incendie, obtenue auprès d'une source autorisée, avec attribution.

## SLIDE 2 — OUR SOLUTION

Titre :
"PyroLens in One Sentence"

Présenter :

"A reproducible Python pipeline, interactive satellite monitoring platform, and calibrated detection-probability model."

Trois capacités :

1. Sensor comparison — Jaccard set overlap.
2. On-demand zone analysis — NRT and historical data.
3. Detection activity probability modeling.

Visuel :
Diagramme architectural simplifié :

NASA FIRMS Data
↓
Data Processing and Harmonization
↓
Spatial and Temporal Grid
↓
Sensor Comparison + Random Forest
↓
Calibration
↓
Interactive PyroLens Platform

## SLIDE 3 — DATA CREDIBILITY

Titre :
"Data Credibility"

Présenter les statistiques réellement vérifiées :

- Nombre de fichiers FIRMS.
- Période couverte.
- Nombre de détections.
- Nombre de pays disponibles.
- Comparaison MODIS/VIIRS.
- Indice Jaccard.

Les chiffres suivants sont des valeurs candidates à vérifier :

- 1,171 FIRMS files.
- Approximately 1.8 million detections.
- 18 country archives.
- 410,000 VIIRS detections.
- 80,000 MODIS detections.
- Jaccard: 0.335.

Présenter également :
- `data_origin`.
- SHA-256 manifests.
- Sources ouvertes.

Ne jamais mélanger des périodes de couverture différentes sans les préciser.

## SLIDE 4 — SCIENTIFIC METHODOLOGY

Titre :
"Scientific Rigor"

Présenter :

- Spatial resolution: 0.25°.
- Temporal windows: 5 and 8 days.
- Jaccard index: set overlap, not accuracy.
- Chronological split:
  - Training: 2013-2016.
  - Validation: 2017-2018.
  - Testing: 2019-2020.
- Eight-day purge at temporal boundaries.
- Isotonic calibration fitted on validation data only.

Visuel :

Features → Random Forest → Isotonic Calibration → Detection Probability.

Le diagramme doit être scientifiquement fidèle à l'implémentation réelle.

## SLIDE 5 — INTERACTIVE PLATFORM

Titre :
"Explore PyroLens"

Présenter 3 à 4 captures authentiques :

- Interactive map.
- Sensor comparison.
- Historical calendar.
- Jobs and data quality.

Les captures doivent être grandes et lisibles.

Ne pas surcharger cette diapositive.

## SLIDE 6 — RESULTS AND IMPACT

Titre :
"Transparency. Reproducibility. Scientific Honesty."

Mettre en avant :

- PR-AUC: 0.926.
- F1-score: 0.841.
- Brier Score: valeur vérifiée.
- 119 automated tests, uniquement si le résultat est confirmé.

Présenter quatre engagements :

1. Transparent data provenance.
2. No false claims of fire absence.
3. Reproducible processing.
4. Open-access country archives.

Mention très visible :

"NO DETECTION ≠ NO FIRE"

Et :

"Historical backtest — 2019-2020."

## SLIDE 7 — FUTURE DIRECTIONS

Titre :
"Beyond Cameroon"

Présenter une feuille de route :

- Expand to continental Africa.
- Integrate ERA5 weather drivers.
- Improve spatial calibration.
- Support operational decision-making for NGOs.
- Develop early-warning support tools.

Visuel :
Carte de l'Afrique avec une extension progressive de la couverture.

Conclusion :

"Better observations. Better understanding. Better decisions."

Ne présente pas les fonctionnalités futures comme déjà opérationnelles.

---

# 6. PHASE 5 — SCRIPT DE NARRATION

Produire un document contenant :

- Le texte complet de la narration anglaise.
- Le minutage précis.
- Les sous-titres correspondants.
- Les indications visuelles associées à chaque séquence.

La narration doit être concise et naturelle.

Le débit doit être compatible avec une vidéo de 30 secondes maximum.

Si aucune voix de qualité professionnelle n'est disponible, privilégie une bande sonore discrète et des textes animés plutôt qu'une voix artificielle de mauvaise qualité.

---

# 7. CONFORMITÉ NASA SPACE APPS 2026

Consulte les règles officielles :

https://www.spaceappschallenge.org/legal/

https://www.spaceappschallenge.org/brand/

https://www.spaceappschallenge.org/2026/

Respecte notamment les exigences suivantes :

1. Vidéo de 30 secondes maximum OU présentation de 7 diapositives maximum pour la démonstration officielle.
2. Projet et démonstration principalement en anglais.
3. Sources de données et ressources correctement attribuées.
4. Respect des droits d'auteur et des licences.
5. Déclaration des outils d'intelligence artificielle utilisés.
6. Aucun contenu confidentiel ou personnel.
7. Aucun logo NASA généré ou modifié.
8. Aucun élément graphique trompeur pouvant laisser croire à une validation ou à un partenariat officiel avec NASA.

Crédits à intégrer dans les livrables et/ou leurs informations complémentaires :

- NASA FIRMS.
- NASA GIBS.
- CMR, si cette source est effectivement utilisée.
- Esri pour les fonds cartographiques concernés.
- OpenStreetMap pour les données de géocodage concernées.
- MIT License pour le code, sous réserve de vérification de la licence effective.

Ne crédite pas une ressource qui n'a pas réellement été utilisée.

Documente également les outils utilisés pour la création de la vidéo et de la présentation.

---

# 8. ORGANISATION DES FICHIERS

Créer un dossier :

`deliverables/`

Avec cette structure :

deliverables/
│
├── video/
│   ├── PyroLens_Demo_30s.mp4
│   ├── PyroLens_Subtitles.srt
│   └── video_script.md
│
├── presentation/
│   └── PyroLens_NASA_2026.pptx
│
├── screenshots/
│   ├── 01_map_risk.png
│   ├── 02_sensor_comparison.png
│   ├── 03_historical_calendar.png
│   ├── 04_risk_model.png
│   ├── 05_jobs_dashboard.png
│   └── 06_data_quality.png
│
└── README.md

Le README doit expliquer :
- Les livrables produits.
- Les outils utilisés.
- Les sources de données.
- Les vérifications effectuées.
- Les éventuelles limitations.
- Les métriques scientifiques retenues.

---

# 9. CONTRÔLE QUALITÉ FINAL

Avant de considérer le travail terminé :

## Vidéo
- Vérifier la durée réelle.
- Vérifier la résolution.
- Vérifier la lisibilité des sous-titres.
- Vérifier la synchronisation audio/vidéo.
- Vérifier les transitions.
- Vérifier les crédits.

## PowerPoint
- Vérifier le nombre de diapositives.
- Vérifier les notes du présentateur.
- Vérifier les polices et les alignements.
- Vérifier que les captures sont lisibles.
- Vérifier les métriques et les attributions.
- Vérifier l'ouverture du fichier dans PowerPoint.

## Cohérence scientifique
- Aucun discours de prédiction d'incendie.
- Aucun Jaccard présenté comme une précision.
- Aucune cellule vide présentée comme une absence d'incendie.
- Toutes les métriques du modèle identifiées comme historiques.
- Aucune statistique non vérifiée.

Si possible, extrais également quelques images de la vidéo finale pour contrôler visuellement le rendu.

---

# 10. MODE DE TRAVAIL

Travaille de manière autonome et méthodique.

Ne gaspille pas de temps à expliquer des possibilités avant de commencer.

Ne demande pas de confirmation pour les décisions techniques ordinaires.

Privilégie les outils déjà installés dans l'environnement.

Évite d'installer des dépendances lourdes si une alternative existante convient.

Si une dépendance manque, vérifie d'abord si elle est déjà disponible dans un autre environnement du projet.

Ne modifie pas inutilement le code métier de PyroLens.

Les éventuelles modifications doivent rester limitées aux besoins de la démonstration.

Après chaque grande phase :
1. Vérifie le résultat.
2. Corrige les erreurs.
3. Passe à la phase suivante.

À la fin, fournis un rapport indiquant :
- Les fichiers effectivement générés.
- Leur emplacement.
- La durée exacte de la vidéo.
- La résolution.
- Le nombre de diapositives.
- Les contrôles réussis.
- Les problèmes non résolus.

**OBJECTIF FINAL : produire deux démonstrations de niveau professionnel, capables de présenter clairement la valeur scientifique, technique et pratique de PyroLens devant un jury international NASA Space Apps Challenge 2026.**