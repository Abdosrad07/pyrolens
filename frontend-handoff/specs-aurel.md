# Spécifications de développement - Aurel

**Développeur:** Aurel  
**Modules:** Overview + Fire Calendar  
**Estimation temps:** 20-25 heures

---

## Contexte

Ce document détaille les fonctionnalités à implémenter pour les modules **Overview** et **Fire Calendar** de PyroLens. Ces modules permettent l'exploration visuelle et temporelle des observations de feux satellitaires.

**Références:**
- Spécifications générales: `Pyrolens_Specification_Frontend.md`
- Design system: `frontend-handoff/design-system.md`
- API contract: `docs/api.md`
- Intégration API: `frontend-handoff/api-integration.md`

---

## MODULE 1 - Overview

**Route:** `/`  
**Objectif:** Permettre à un nouvel utilisateur de comprendre rapidement les données disponibles et les possibilités de PyroLens.

### 1.1 Structure de la page

#### A. Bandeau d'introduction

**Contenu:**
- Nom de PyroLens
- Présentation courte (1-2 phrases)
- Zone d'étude active (ex: "Cameroun")
- Période couverte par les données (ex: "2013-01-01 → 2020-12-31")

**Implémentation:**
- Utiliser `.banner.info` ou `.banner.warn` selon l'origine des données
- Afficher `data_origin` et `generated_at` depuis les artefacts

#### B. Cartes statistiques

**Contenu (5+ cartes):**
- Nombre total d'observations
- Nombre d'observations par satellite (MODIS Terra, MODIS Aqua, VIIRS)
- Nombre de jours couverts
- Nombre de cellules géographiques actives
- Indicateurs de FRP (min, moy, max) lorsque disponibles

**Chaque carte doit préciser:**
- Le libellé (ex: "Observations totales")
- La valeur (formatée avec `fmt()`)
- L'unité éventuelle (ex: "observations", "MW")
- Une explication courte (ex: "sur la période étudiée")

**Implémentation:**
- Réutiliser la classe `.card` existante
- Utiliser `.cards` pour la grille responsive
- Adapter `.k`, `.v`, `.d` pour le contenu

#### C. Carte des points chauds

**Fonctionnalités:**
- Affichage des observations géolocalisées sur une carte
- Légende distinguant les satellites (couleurs différentes)
- Info-bulle au clic ou au survol (détails: satellite, date, FRP, confiance)
- Filtres temporels (date début, date fin)
- Filtres géographiques (si supporté par l'API)
- Activation/désactivation de chaque source satellite (checkboxes)
- Regroupement/clustering si le volume de points est important

**Composant à créer:**
- `MapView` - Nouveau composant utilisant Leaflet ou MapLibre

**Données requises:**
- Coordonnées (latitude, longitude)
- Satellite source
- Timestamp
- FRP (optionnel)
- Confiance (optionnel)

**Intégration API:**
- Endpoint: `GET /observations?start_date&end_date&satellites&bbox`
- Mode statique: lire depuis artefact JSON si disponible

#### D. Comparaison des satellites

**Contenu:**
- Comparaison MODIS Terra, MODIS Aqua et VIIRS
- Graphiques ou tableaux
- Libellés et unités explicites
- Explication des indicateurs affichés

**Graphiques suggérés:**
- Bar chart: nombre d'observations par satellite
- Line chart: évolution temporelle par satellite
- Scatter plot: FRP par satellite

**Implémentation:**
- Utiliser Recharts (déjà installé)
- Réutiliser `.chart-box` pour le conteneur
- Ajouter `.legend-note` pour les explications

#### E. Accès rapide

**Liens ou boutons vers:**
- Lancement d'une expérience (`/harmonization/new`)
- Calendrier des feux (`/fire-calendar`)
- Catalogue des données (`/data`)
- Méthodologie (`/methodology`)

**Implémentation:**
- Boutons `.btn.primary` ou `.btn.ghost`
- Grille de cartes cliquables

### 1.2 Interactions utilisateur

**L'utilisateur doit pouvoir:**
- Filtrer par période (DateRangeFilter)
- Filtrer par zone géographique (si API supporte)
- Sélectionner un ou plusieurs satellites (SatelliteSelector)
- Actualiser les statistiques et la carte selon les filtres
- Ouvrir les détails d'un jeu de données ou d'une expérience

### 1.3 Critères de validation

- [ ] Toutes les valeurs proviennent de l'API (pas de valeurs codées en dur)
- [ ] Les filtres ont un effet réel sur les données affichées
- [ ] La légende distingue clairement les satellites
- [ ] Une absence de résultat affiche un état vide explicite (`.loading` ou message)
- [ ] Les unités et périodes sont visibles
- [ ] La carte fonctionne en mode statique et mode API
- [ ] Responsive ≤ 900px: carte et cartes statistiques adaptées

### 1.4 Composants à créer

| Composant | Description | Priorité |
|-----------|-------------|----------|
| `MapView` | Carte interactive avec Leaflet/MapLibre | P0 |
| `StatCard` | Adapter `.card` existant pour statistiques | P0 |
| `SatelliteFilter` | Filtre multi-select satellites | P0 |
| `DateRangeFilter` | Filtre période avec dates | P0 |
| `GeoFilter` | Filtre zone géographique (optionnel) | P1 |

### 1.5 Estimation temps

- Implémentation structure page: 2h
- Cartes statistiques: 2h
- Carte des points chauds (MapView): 6-8h
- Comparaison satellites (graphiques): 3h
- Filtres et interactions: 2h
- Tests et validation: 2h
- **Total: 17-19h**

---

## MODULE 2 - Fire Calendar

**Route:** `/fire-calendar`  
**Objectif:** Explorer l'évolution temporelle des observations de feux.

### 2.1 Structure de la page

#### A. Filtres

**Contenu:**
- Période de début et de fin (DateRangeFilter)
- Satellite ou groupe de satellites (SatelliteSelector)
- Zone géographique (GeoFilter - optionnel)
- Type de données: originales ou harmonisées (si disponible)

**Implémentation:**
- Utiliser `.controls` pour le conteneur
- Labels avec `label` + `select` existants

#### B. Calendrier

**Fonctionnalités:**
- Vue quotidienne (grille de jours)
- Intensité visuelle basée sur une mesure explicitement définie (ex: nombre d'observations)
- Légende (échelle de couleurs)
- Possibilité de sélectionner un jour pour afficher ses détails
- Navigation entre mois/années

**Composant à créer:**
- `CalendarView` - Calendrier interactif personnalisé

**Données requises:**
- Données agrégées par jour
- Comptage d'observations par jour
- Satellite source
- FRP agrégé (optionnel)

#### C. Agrégations temporelles

**Vues disponibles:**
- Vue quotidienne (calendrier)
- Vue hebdomadaire (graphique bar)
- Vue mensuelle (graphique line)

**Implémentation:**
- Toggle ou tabs pour changer de vue
- Réutiliser Recharts pour graphiques

#### D. Graphiques

**Contenu:**
- Évolution du nombre d'observations (line chart)
- Évolution du nombre de cellules actives (line chart)
- Évolution de la FRP (line chart, si disponible)
- Comparaison entre satellites (multi-line)
- Comparaison des données originales et harmonisées (si résultats existent)

**Implémentation:**
- Utiliser Recharts
- `.chart-box` pour conteneurs
- `.legend-note` pour explications

#### E. Détail d'une période

**Au clic sur un jour, une semaine ou un mois:**
- Afficher les statistiques correspondantes
- Afficher les satellites concernés
- Afficher les observations ou cellules concernées
- Permettre d'accéder à la carte si les données sont disponibles

**Composant à créer:**
- `PeriodDetail` - Panneau de détail

### 2.2 Interactions utilisateur

**L'utilisateur doit pouvoir:**
- Changer la période analysée
- Sélectionner/désélectionner des satellites
- Changer le type d'agrégation (jour/semaine/mois)
- Cliquer sur une période pour voir les détails
- Naviguer entre les périodes

### 2.3 Critères de validation

- [ ] Les agrégations correspondent aux données de l'API
- [ ] La période sélectionnée est visible
- [ ] Les graphiques précisent leurs unités
- [ ] Les données originales et harmonisées sont différenciées
- [ ] Une période sans observation n'est jamais présentée comme "pas de feu"
- [ ] Le calendrier est responsive
- [ ] Fonctionne en mode statique et mode API

### 2.4 Composants à créer

| Composant | Description | Priorité |
|-----------|-------------|----------|
| `CalendarView` | Calendrier interactif quotidien | P0 |
| `CalendarControls` | Filtres et sélecteur d'agrégation | P0 |
| `TimeSeriesChart` | Graphiques temporels (réutiliser Recharts) | P0 |
| `PeriodDetail` | Détail période sélectionnée | P0 |
| `AggregationToggle` | Switch jour/semaine/mois | P1 |

### 2.5 Estimation temps

- Implémentation structure page: 2h
- Calendrier interactif (CalendarView): 6-8h
- Graphiques temporels: 4h
- Filtres et agrégations: 2h
- Détail période: 2h
- Tests et validation: 2h
- **Total: 18-20h**

---

## TRAVAIL COMMUN (avec Abdourahim)

### Layout et navigation

**À coordonner:**
- Adapter `App.jsx` pour nouvelles routes (`/`, `/fire-calendar`)
- Mettre à jour sidebar avec les 4 modules
- Navigation principale persistante

**Responsabilités partagées:**
- Aurel: routes Overview et Fire Calendar
- Abdourahim: routes Harmonization et Data/Methodology
- Ensemble: layout général et navigation

### Composants partagés

**Composants à créer ensemble:**
- `DateRangeFilter` - Utilisé par Overview et Fire Calendar
- `SatelliteSelector` - Utilisé par Overview et Fire Calendar
- `MapView` - Utilisé par Overview et Harmonization (résultats)

**Coordination:**
- Définir l'interface des composants partagés
- Implémentation conjointe ou répartition claire
- Tests d'intégration

### Intégration API

**À coordonner:**
- Brancher tous les endpoints sur `data.js`
- Gérer états loading/success/empty/error de manière cohérente
- Normaliser les réponses API

**Endpoints spécifiques Aurel:**
- `GET /observations` - pour carte Overview
- `GET /series/temporal?resolution=day|week|month` - pour Fire Calendar
- `GET /summary` - pour statistiques Overview

### Tests

**Tests fonctionnels à rédiger:**
- Parcours utilisateur: Landing → Overview → filtres → carte
- Parcours utilisateur: Overview → Fire Calendar → agrégations → détail
- Tests d'intégration avec API
- Tests responsive

---

## Règles éditoriales à respecter

1. **Jamais d'affirmation d'absence de feu**
   - Libellés: "aucun_enregistrement", "observabilité inconnue"
   - `grep -ri "pas de feu"` ne doit trouver que des négations explicites

2. **Provenance visible**
   - `data_origin` + `generated_at` sur tout écran chiffré
   - Banner d'origine systématique

3. **Chiffres = artefacts (D1)**
   - Source unique: API ou artefacts JSON
   - Formatage via `fmt()`
   - Aucune constante numérique dans les vues

4. **Avertissements d'interprétation**
   - Jaccard ≠ précision
   - Croissance du recouvrement avec maille/fenêtre = effet mécanique
   - Hors-emprise = ambigu exclu

5. **Aucun secret côté client**
   - Pas de `FIRMS_MAP_KEY`/`EARTHDATA_*`
   - Pas d'URL d'acquisition
   - Pas de jeton dans le bundle

---

## Checklist de validation finale

### Overview
- [ ] Page responsive
- [ ] Carte des points chauds fonctionnelle
- [ ] Filtres temporels et satellites opérationnels
- [ ] Statistiques affichées correctement
- [ ] Comparaison satellites avec graphiques
- [ ] Mode statique et mode API fonctionnent
- [ ] Contrat éditorial respecté

### Fire Calendar
- [ ] Calendrier interactif fonctionnel
- [ ] Agrégations jour/semaine/mois opérationnelles
- [ ] Graphiques temporels corrects
- [ ] Détail période affiché
- [ ] Filtres fonctionnels
- [ ] Mode statique et mode API fonctionnent
- [ ] Contrat éditorial respecté

### Integration
- [ ] Navigation vers autres modules fonctionnelle
- [ ] Composants partagés testés
- [ ] API branchée correctement
- [ ] Tests fonctionnels passent
- [ ] Build sans erreur: `npm --prefix web run build`

---

## Dépendances techniques

**À installer:**
- `leaflet` ou `maplibre-gl` pour MapView
- `react-leaflet` ou `maplibre-gl-react` pour intégration React
- `date-fns` ou `luxon` pour manipulation de dates (CalendarView)

**Commandes:**
```bash
npm --prefix web install leaflet react-leaflet
npm --prefix web install date-fns
```

**CSS additionnel:**
- Styles Leaflet/MapLibre à intégrer dans `index.css`
- Styles personnalisés pour CalendarView

---

## Points de blocage potentiels

1. **Données géolocalisées non disponibles**
   - Solution: Mode dégradé avec message explicite

2. **API endpoints non implémentés**
   - Solution: Mode statique avec artefacts JSON

3. **Performance carte avec beaucoup de points**
   - Solution: Clustering/heatmap, pagination

4. **Calendrier complexe à implémenter**
   - Solution: Utiliser une librairie existante (ex: `react-calendar`) ou implémentation simplifiée

---

## Livrables

1. **Code:**
   - `web/src/views/Overview.jsx` (nouveau ou refonte)
   - `web/src/views/FireCalendar.jsx` (nouveau)
   - `web/src/components/MapView.jsx` (nouveau)
   - `web/src/components/CalendarView.jsx` (nouveau)
   - `web/src/components/DateRangeFilter.jsx` (nouveau)
   - `web/src/components/SatelliteSelector.jsx` (nouveau)
   - Mises à jour `web/src/App.jsx` (routes)
   - Mises à jour `web/src/data.js` (API endpoints)

2. **Documentation:**
   - Composants documentés avec JSDoc
   - README d'utilisation des composants
   - Notes d'intégration

3. **Tests:**
   - Tests fonctionnels pour chaque module
   - Tests d'intégration API
   - Tests responsive

---

## Communication avec Abdourahim

**À coordonner:**
- Interface des composants partagés (props, callbacks)
- Conventions de nommage
- Structure des données API
- Planification des reviews de code

**Fréquence:**
- Daily standup (15 min)
- Review de code avant merge
- Tests d'intégration conjoints

---

## Questions en attente

1. **Librairie de carte:** Leaflet ou MapLibre?
2. **Données géolocalisées:** Disponibles dans l'API ou artefacts?
3. **Calendrier:** Librairie existante ou implémentation from scratch?
4. **Performance:** Volume de données attendu pour la carte?

---

**Document version:** 1.0  
**Dernière mise à jour:** 10 novembre 2026
