# Spécifications de travail commun - Aurel & Abdourahim

**Développeurs:** Aurel & Abdourahim  
**Objectif:** Coordination du travail partagé (layout, composants, intégration)  
**Estimation temps:** 6-8 heures

---

## Contexte

Ce document définit le travail à coordonner entre Aurel et Abdourahim pour assurer une intégration cohérente de tous les modules PyroLens.

**Références:**
- Spécifications Aurel: `specs-aurel.md` (Overview + Fire Calendar)
- Spécifications Abdourahim: `specs-abdourahim.md` (Harmonization Lab + Data & Methodology)
- Design system: `frontend-handoff/design-system.md`
- API contract: `docs/api.md`

---

## 1. Layout et navigation

### 1.1 Adaptation de App.jsx

**Objectif:** Mettre à jour la navigation principale pour les 4 nouveaux modules.

**État actuel:**
- 8 vues existantes: Landing, Auth, Overview, Audit, Baselines, Observability, Report, Figures
- Sidebar avec navigation vers ces vues

**Nouvel état souhaité:**
- Conserver Landing et Auth
- Remplacer les 6 vues de rapport par les 4 modules d'exploration:
  - Overview (`/`)
  - Harmonization Lab (`/harmonization`, `/harmonization/new`, `/harmonization/:id`)
  - Fire Calendar (`/fire-calendar`)
  - Data & Methodology (`/data`, `/data/:id`, `/methodology`)

**Implémentation:**

```jsx
// Dans web/src/App.jsx
const VIEWS = [
  { id: 'landing', path: '/', label: 'Accueil', component: Landing },
  { id: 'overview', path: '/overview', label: 'Overview', component: Overview },
  { id: 'harmonization', path: '/harmonization', label: 'Harmonization', component: HarmonizationList },
  { id: 'fire-calendar', path: '/fire-calendar', label: 'Fire Calendar', component: FireCalendar },
  { id: 'data', path: '/data', label: 'Data', component: DataCatalog },
  { id: 'methodology', path: '/methodology', label: 'Methodology', component: Methodology },
];
```

**Routes supplémentaires:**
- `/harmonization/new` - Création expérience
- `/harmonization/:id` - Détail expérience
- `/data/:id` - Détail dataset

**Responsabilités:**
- Abdourahim: Routes Harmonization et Data/Methodology
- Aurel: Routes Overview et Fire Calendar
- Ensemble: Définition de la structure VIEWS et navigation

### 1.2 Sidebar

**Objectif:** Mettre à jour la sidebar pour refléter les nouveaux modules.

**Modifications:**
- Remplacer les liens vers Audit, Baselines, Observability, Report, Figures
- Ajouter liens vers Overview, Harmonization, Fire Calendar, Data, Methodology
- Conserver le style existant (`.sidebar`, `.nav-link`)

**Responsabilités:**
- Ensemble: Définir la structure de la sidebar
- Abdourahim: Implémentation (car il gère plus de routes)

### 1.3 PageHeader

**Objectif:** Créer un composant de titre de page cohérent.

**Contenu:**
- Titre de la page
- Sous-titre optionnel
- Actions (boutons, filtres) si applicable

**Implémentation:**
- Réutiliser `.page-title` existant
- Créer `PageHeader.jsx` comme composant partagé

**Responsabilités:**
- Ensemble: Définir l'interface du composant
- Aurel: Implémentation initiale

---

## 2. Composants partagés

### 2.1 DateRangeFilter

**Utilisé par:**
- Overview (Aurel)
- Fire Calendar (Aurel)
- Harmonization Lab - création expérience (Abdourahim)
- Data Catalogue (Abdourahim)

**Interface:**
```jsx
<DateRangeFilter
  startDate={startDate}
  endDate={endDate}
  onStartDateChange={(date) => setStartDate(date)}
  onEndDateChange={(date) => setEndDate(date)}
  minDate={minDate} // optionnel
  maxDate={maxDate} // optionnel
/>
```

**Fonctionnalités:**
- Sélecteur de date début
- Sélecteur de date fin
- Validation (début < fin)
- Format ISO 8601 (YYYY-MM-DD)

**Implémentation:**
- Utiliser `<input type="date">` natif ou librairie (ex: `react-datepicker`)
- Styles: `.controls`, `label`, `select`

**Responsabilités:**
- Ensemble: Définir l'interface
- Aurel: Implémentation (car utilisé dans Overview)

### 2.2 SatelliteSelector

**Utilisé par:**
- Overview (Aurel)
- Fire Calendar (Aurel)
- Harmonization Lab - création expérience (Abdourahim)
- Data Catalogue (Abdourahim)

**Interface:**
```jsx
<SatelliteSelector
  satellites={satellites} // ex: ['modis_terra', 'modis_aqua', 'viirs']
  selected={selectedSatellites}
  onChange={(selected) => setSelectedSatellites(selected)}
  multiple={true} // true pour multi-select, false pour single
/>
```

**Fonctionnalités:**
- Checkbox pour multi-select ou radio pour single-select
- Labels lisibles (ex: "MODIS Terra", "MODIS Aqua", "VIIRS")
- Affichage du nombre d'observations par satellite (si disponible)

**Implémentation:**
- Utiliser checkboxes ou radio buttons natifs
- Styles: `.controls`, `.pill` pour badges

**Responsabilités:**
- Ensemble: Définir l'interface
- Aurel: Implémentation (car utilisé dans Overview)

### 2.3 MapView

**Utilisé par:**
- Overview - carte des points chauds (Aurel)
- Harmonization Lab - carte des résultats (Abdourahim)

**Interface:**
```jsx
<MapView
  observations={observations} // array de { lat, lon, satellite, ... }
  center={center} // { lat, lon }
  zoom={zoom}
  onObservationClick={(obs) => handleObservationClick(obs)}
  filters={filters} // optionnel
  legend={legend} // optionnel
/>
```

**Fonctionnalités:**
- Affichage des points sur la carte
- Légende par satellite (couleurs)
- Info-bulle au clic/survol
- Filtres (si supporté)
- Clustering si volume important

**Implémentation:**
- Utiliser Leaflet ou MapLibre
- Styles CSS spécifiques pour la carte

**Responsabilités:**
- Ensemble: Définir l'interface
- Aurel: Implémentation (car utilisé dans Overview)
- Abdourahim: Utilisation pour résultats harmonisation

### 2.4 StatCard

**Utilisé par:**
- Overview (Aurel)
- Harmonization Lab - métriques (Abdourahim)
- Data Catalogue - statistiques (Abdourahim)

**Interface:**
```jsx
<StatCard
  title="Observations totales"
  value={123456}
  unit="observations"
  description="sur la période étudiée"
  trend={trend} // optionnel
/>
```

**Fonctionnalités:**
- Titre
- Valeur formatée avec `fmt()`
- Unité
- Description courte
- Trend (optionnel)

**Implémentation:**
- Adapter `.card` existant
- Utiliser `.k`, `.v`, `.d` pour le contenu

**Responsabilités:**
- Ensemble: Définir l'interface
- Aurel: Implémentation (car utilisé dans Overview)

### 2.5 DataTable

**Déjà existe (`table.data`)**

**Utilisé par:**
- Harmonization Lab - liste expériences (Abdourahim)
- Data Catalogue (Abdourahim)
- Overview - comparaison satellites (Aurel)

**Interface:**
```jsx
<DataTable
  columns={columns} // array de { key, label, format }
  data={data}
  onRowClick={(row) => handleRowClick(row)} // optionnel
  sortable={true} // optionnel
/>
```

**Fonctionnalités:**
- Affichage tableau
- Tri par colonne
- Hover sur ligne
- Pagination si nécessaire

**Implémentation:**
- Réutiliser `table.data` existant
- Ajouter logique de tri si nécessaire

**Responsabilités:**
- Ensemble: Définir l'interface
- Abdourahim: Implémentation (car utilisé dans Harmonization)

### 2.6 LoadingState

**Déjà existe (`.loading`)**

**Utilisé par:**
- Tous les modules

**Interface:**
```jsx
<LoadingState message="Chargement des données..." />
```

**Fonctionnalités:**
- Spinner ou animation
- Message optionnel

**Implémentation:**
- Réutiliser `.loading` existant
- Créer composant `LoadingState.jsx` si nécessaire

**Responsabilités:**
- Ensemble: Définir l'interface
- Aurel: Implémentation

### 2.7 EmptyState

**Déjà existe (message artefact indisponible)**

**Utilisé par:**
- Tous les modules

**Interface:**
```jsx
<EmptyState message="Aucun enregistrement pour cette période" />
```

**Fonctionnalités:**
- Message explicite
- Jamais "pas de feu"
- Icône ou illustration optionnelle

**Implémentation:**
- Réutiliser message existant
- Créer composant `EmptyState.jsx` si nécessaire

**Responsabilités:**
- Ensemble: Définir l'interface
- Aurel: Implémentation

### 2.8 ErrorState

**À améliorer**

**Utilisé par:**
- Tous les modules

**Interface:**
```jsx
<ErrorState
  error={error}
  onRetry={() => retry()}
  details={details} // optionnel
/>
```

**Fonctionnalités:**
- Message d'erreur clair
- Bouton retry
- Détails techniques optionnels (accordéon)

**Implémentation:**
- Créer `ErrorState.jsx`
- Utiliser `.banner.ref` pour le style

**Responsabilités:**
- Ensemble: Définir l'interface
- Abdourahim: Implémentation

---

## 3. Intégration API

### 3.1 Structure de data.js

**Principe:** Une seule couche d'accès aux données.

**Fonctions à ajouter/modifier:**

```javascript
// Fonction API générique
async function apiGet(path, params = {}) {
  if (!import.meta.env.VITE_API_BASE) {
    return null; // mode statique
  }
  const url = new URL(path, import.meta.env.VITE_API_BASE);
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.append(key, value);
  });
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

// Fonctions spécifiques
export async function loadObservations(params) {
  return apiGet('/observations', params);
}

export async function loadExperiments(params) {
  return apiGet('/experiments', params);
}

export async function createExperiment(data) {
  // POST request
}

export async function loadExperimentResult(jobId) {
  return apiGet(`/experiments/${jobId}/result`);
}

export async function loadCatalog(params) {
  return apiGet('/catalog', params);
}

export async function loadTemporalSeries(params) {
  return apiGet('/series/temporal', params);
}
```

### 3.2 Normalisation des réponses

**Principe:** Normaliser les réponses API dans `data.js`, jamais dans les vues.

**Cas `{ meta, rows }`:**
```javascript
export async function loadExperiments(params) {
  const response = await apiGet('/experiments', params);
  if (response && response.rows) {
    return response.rows; // extraire rows
  }
  return response;
}
```

### 3.3 Gestion des erreurs

**Principe:** Pousser les erreurs dans `data.errors[]`.

```javascript
export async function loadAll() {
  const results = await Promise.allSettled([
    loadExecution(),
    loadInventory(),
    loadAudit(),
    loadBaselines(),
    loadObservations(),
    loadExperiments(),
    loadCatalog(),
    loadTemporalSeries(),
  ]);
  
  const errors = results
    .filter(r => r.status === 'rejected')
    .map(r => r.reason);
  
  return {
    execution: results[0].value,
    inventory: results[1].value,
    audit: results[2].value,
    baselines: results[3].value,
    observations: results[4].value,
    experiments: results[5].value,
    catalog: results[6].value,
    temporalSeries: results[7].value,
    errors,
  };
}
```

### 3.4 Endpoints par module

**Overview (Aurel):**
- `GET /observations` - carte des points chauds
- `GET /summary` - statistiques générales

**Fire Calendar (Aurel):**
- `GET /series/temporal?resolution=day|week|month` - séries temporelles

**Harmonization Lab (Abdourahim):**
- `GET /experiments` - liste des expériences
- `POST /experiments` - création expérience
- `GET /experiments/{job_id}` - suivi statut
- `GET /experiments/{job_id}/result` - résultats

**Data & Methodology (Abdourahim):**
- `GET /catalog` - catalogue datasets
- `GET /catalog/{dataset_id}` - détail dataset
- `GET /methodology` - contenu méthodologique (si disponible)

### 3.5 Mode statique vs mode API

**Principe:** Mode statique préservé par défaut.

```javascript
// Dans data.js
const API_BASE = import.meta.env.VITE_API_BASE;

if (!API_BASE) {
  // Mode statique - lire depuis artefacts
  return {
    observations: await getJSON('/artifacts/observations.json'),
    experiments: await getJSON('/artifacts/experiments.json'),
    // ...
  };
} else {
  // Mode API - appeler endpoints
  return {
    observations: await loadObservations(params),
    experiments: await loadExperiments(params),
    // ...
  };
}
```

**Responsabilités:**
- Ensemble: Définir la structure de `data.js`
- Abdourahim: Implémentation (car plus d'endpoints)

---

## 4. Tests

### 4.1 Tests fonctionnels

**Parcours utilisateur:**
1. Landing → Overview → filtres → carte
2. Overview → Fire Calendar → agrégations → détail
3. Harmonization → création → lancement → suivi → résultats
4. Data → catalogue → détail dataset
5. Méthodologie → lecture sections

**Responsabilités:**
- Aurel: Tests parcours Overview et Fire Calendar
- Abdourahim: Tests parcours Harmonization et Data/Methodology
- Ensemble: Tests navigation entre modules

### 4.2 Tests d'intégration API

**Objectif:** Vérifier que les données affichées correspondent à l'API.

**Méthode:**
- Pour chaque vue, comparer les chiffres affichés avec `curl` direct sur l'endpoint
- Vérifier que `data_origin` et `generated_at` sont corrects

**Responsabilités:**
- Aurel: Tests Overview et Fire Calendar
- Abdourahim: Tests Harmonization et Data/Methodology

### 4.3 Tests responsive

**Objectif:** Vérifier que l'interface fonctionne ≤ 900px.

**Écrans à tester:**
- Landing
- Overview
- Fire Calendar
- Harmonization (liste, formulaire, détail)
- Data (catalogue, détail)
- Méthodologie

**Responsabilités:**
- Aurel: Tests Overview et Fire Calendar
- Abdourahim: Tests Harmonization et Data/Methodology
- Ensemble: Tests Landing et navigation

### 4.4 Tests mode statique

**Objectif:** Vérifier que l'application fonctionne sans API.

**Méthode:**
- `VITE_API_BASE` vide → app identique
- Artefacts manquants → état dégradé propre

**Responsabilités:**
- Ensemble: Tests conjoints

---

## 5. Coordination et communication

### 5.1 Points de synchronisation

**Synchronisation 1 - Début du projet:**
- Définir l'interface des composants partagés (DateRangeFilter, SatelliteSelector, MapView)
- Définir la structure de `data.js`
- Définir la navigation dans App.jsx

**Synchronisation 2 - Milieu du projet:**
- Review de code des composants partagés
- Tests d'intégration des routes et navigation
- Vérification de la cohérence du design system

**Synchronisation 3 - Fin du projet:**
- Tests bout-en-bout
- Validation globale
- Préparation démo hackathon

### 5.2 Fréquence de communication

**Daily standup (15 min):**
- Progression depuis hier
- Planification aujourd'hui
- Blocages et dépendances

**Review de code:**
- Avant merge de composants partagés
- Avant merge de modifications de `data.js`
- Avant merge de modifications de App.jsx

**Tests d'intégration:**
- Conjointement après chaque module majeur
- Final avant démo

### 5.3 Conventions de nommage

**Composants:**
- PascalCase: `MapView`, `DateRangeFilter`
- Fichiers: `MapView.jsx`, `DateRangeFilter.jsx`

**Fonctions:**
- camelCase: `loadObservations`, `createExperiment`

**Variables:**
- camelCase: `selectedSatellites`, `startDate`

**Constantes:**
- UPPER_SNAKE_CASE: `API_BASE`, `DEFAULT_ZOOM`

### 5.4 Conventions de style

**CSS:**
- Réutiliser les classes existantes du design system
- Ne pas dupliquer de classes
- Utiliser les jetons de thème (`--bg`, `--panel`, etc.)

**React:**
- Composants fonctionnels
- Hooks pour état local
- Props explicites avec JSDoc

**Code:**
- Commentaires pour la logique complexe
- Pas de code mort
- Pas de console.log en production

---

## 6. Checklist de validation commune

### Layout et navigation
- [ ] App.jsx mis à jour avec nouvelles routes
- [ ] Sidebar reflète les 4 modules
- [ ] Navigation fonctionne entre tous les modules
- [ ] Landing et Auth conservés
- [ ] Responsive ≤ 900px

### Composants partagés
- [ ] DateRangeFilter implémenté et testé
- [ ] SatelliteSelector implémenté et testé
- [ ] MapView implémenté et testé
- [ ] StatCard implémenté et testé
- [ ] DataTable réutilisé
- [ ] LoadingState réutilisé
- [ ] EmptyState réutilisé
- [ ] ErrorState amélioré

### Intégration API
- [ ] data.js mis à jour avec tous les endpoints
- [ ] Normalisation des réponses implémentée
- [ ] Gestion des erreurs implémentée
- [ ] Mode statique préservé
- [ ] Mode API fonctionnel

### Tests
- [ ] Tests fonctionnels passent
- [ ] Tests d'intégration API passent
- [ ] Tests responsive passent
- [ ] Tests mode statique passent

### Build
- [ ] `npm --prefix web run build` → exit 0
- [ ] Zéro erreur console
- [ ] Bundle size acceptable

---

## 7. Risques et mitigation

### 7.1 Risque: Composants partagés mal définis

**Mitigation:**
- Définir l'interface avant implémentation
- Review de code avant utilisation
- Tests unitaires pour chaque composant

### 7.2 Risque: Conflits dans App.jsx

**Mitigation:**
- Coordination avant modifications
- Review de code avant merge
- Tests de navigation après chaque modification

### 7.3 Risque: Incohérence du design system

**Mitigation:**
- Réutiliser uniquement les classes existantes
- Review de code pour vérifier l'utilisation des classes
- Tests visuels conjoints

### 7.4 Risque: API endpoints non implémentés

**Mitigation:**
- Vérifier avec le backend avant développement
- Mode statique comme fallback
- Communication régulière avec l'équipe backend

---

## 8. Livrables communs

1. **Code:**
   - `web/src/App.jsx` (mis à jour)
   - `web/src/data.js` (mis à jour)
   - `web/src/components/DateRangeFilter.jsx`
   - `web/src/components/SatelliteSelector.jsx`
   - `web/src/components/MapView.jsx`
   - `web/src/components/StatCard.jsx`
   - `web/src/components/LoadingState.jsx`
   - `web/src/components/EmptyState.jsx`
   - `web/src/components/ErrorState.jsx`

2. **Documentation:**
   - README des composants partagés
   - Guide d'intégration API
   - Conventions de nommage et style

3. **Tests:**
   - Tests unitaires composants partagés
   - Tests d'intégration navigation
   - Tests mode statique/API

---

**Document version:** 1.0  
**Dernière mise à jour:** 10 novembre 2026
