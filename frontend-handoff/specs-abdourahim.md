# Spécifications de développement - Abdourahim

**Développeur:** Abdourahim  
**Modules:** Harmonization Lab + Data & Methodology  
**Estimation temps:** 24-30 heures

---

## Contexte

Ce document détaille les fonctionnalités à implémenter pour les modules **Harmonization Lab** et **Data & Methodology** de PyroLens. Ces modules permettent la configuration d'expériences d'harmonisation, la consultation des résultats, et l'accès transparent aux données et méthodes scientifiques.

**Références:**
- Spécifications générales: `Pyrolens_Specification_Frontend.md`
- Design system: `frontend-handoff/design-system.md`
- API contract: `docs/api.md`
- Intégration API: `frontend-handoff/api-integration.md`

---

## MODULE 1 - Harmonization Lab

**Routes:** `/harmonization`, `/harmonization/new`, `/harmonization/:id`  
**Objectif:** Permettre de créer, lancer, suivre et consulter les expériences d'harmonisation. C'est le parcours fonctionnel principal de PyroLens.

### 1.1 Liste des expériences (`/harmonization`)

#### A. Contenu du tableau

**Colonnes:**
- Nom de l'expérience
- Date de création
- Satellites sélectionnés (MODIS Terra, MODIS Aqua, VIIRS)
- Jeux de données sélectionnés
- Période analysée
- Résolution spatiale (ex: 0,25°)
- Fenêtre temporelle (ex: 8 jours)
- Statut
- Action pour consulter les détails

**Statuts possibles (selon contrat backend):**
- `PENDING` - En attente
- `RUNNING` - En cours
- `COMPLETED` - Terminé
- `FAILED` - Échoué
- `CANCELLED` - Annulé

#### B. Fonctionnalités

- Recherche par nom (si supportée par l'API)
- Filtres par statut
- Filtres par période
- Pagination si nécessaire
- Bouton de création d'une nouvelle expérience

#### C. Implémentation

**Composant à créer:**
- `ExperimentList` - Tableau avec filtres et pagination

**Structure:**
- Utiliser `.panel` pour le conteneur
- Utiliser `table.data` pour le tableau
- Utiliser `.controls` pour les filtres
- Utiliser `.pill` pour les statuts (`.ok`, `.blocked`, `.ref`)

**Intégration API:**
- Endpoint: `GET /experiments?status&start_date&end_date&search`
- Mode statique: lire depuis artefact JSON si disponible

### 1.2 Création d'une expérience (`/harmonization/new`)

#### A. Formulaire en 5 étapes

**Étape 1 - Informations générales**
- Nom de l'expérience (text, requis)
- Description facultative (textarea)
- Zone d'étude (select ou text)
- Date de début (date picker)
- Date de fin (date picker)

**Étape 2 - Sélection des données**
- Choix des jeux de données disponibles (multi-select checkboxes)
- Sélection des satellites (checkboxes):
  - MODIS Terra
  - MODIS Aqua
  - VIIRS Suomi NPP
- Présentation des périodes couvertes par chaque dataset
- Affichage des métadonnées utiles (nombre d'observations, etc.)
- Avertissement si les périodes ne sont pas compatibles

**Étape 3 - Paramètres spatiaux**
- Sélection de la résolution spatiale (select):
  - 0,10°
  - 0,25°
  - 0,50°
- Valeur personnalisée (input number) uniquement si acceptée par le backend
- Explication simple: "Taille des cellules géographiques utilisées pour regrouper les observations"

**Étape 4 - Paramètres temporels**
- Sélection de la fenêtre temporelle (select):
  - 1 jour
  - 4 jours
  - 8 jours
  - 16 jours
- Valeur personnalisée (input number) uniquement si acceptée par le backend
- Explication: "Durée utilisée pour regrouper les observations dans le temps"

**Étape 5 - Récapitulatif et lancement**
- Récapitulatif des jeux de données sélectionnés
- Affichage de la période
- Affichage des paramètres spatiaux et temporels
- Permettre de modifier la configuration (retour aux étapes précédentes)
- Demander confirmation avant le lancement
- Bouton "Lancer l'expérience"

#### B. Implémentation

**Composant à créer:**
- `ExperimentForm` - Formulaire multi-étapes avec wizard

**Sous-composants:**
- `DatasetSelector` - Sélection des jeux de données
- `SpatialParamSelector` - Sélection résolution spatiale
- `TemporalParamSelector` - Sélection fenêtre temporelle

**Validation:**
- Champs requis validés
- Dates cohérentes (début < fin)
- Au moins un satellite et un dataset sélectionnés
- Avertissements affichés pour incompatibilités

**Intégration API:**
- Endpoint: `POST /experiments`
- Corps: `{ name, description, study_area, start_date, end_date, datasets, satellites, spatial_resolution, temporal_window }`
- Réponse: `{ job_id, status }`

### 1.3 Suivi de l'exécution

#### A. Affichage du statut

- Afficher le statut de l'expérience (PENDING/RUNNING/COMPLETED/FAILED/CANCELLED)
- Actualiser le statut via l'API (polling toutes les 1-2 secondes)
- Afficher une progression uniquement si le backend en fournit une
- Présenter les erreurs de manière compréhensible
- Ne pas simuler une progression si aucune information réelle n'est disponible

#### B. Implémentation

**Composant à créer:**
- `ExperimentStatus` - Composant de suivi avec polling

**Fonctionnalités:**
- `useEffect` pour polling
- Affichage spinner si RUNNING
- Message d'erreur si FAILED
- Bouton pour annuler (si supporté)

**Intégration API:**
- Endpoint: `GET /experiments/{job_id}`
- Polling jusqu'à `status === "COMPLETED"` ou `"FAILED"`

### 1.4 Détail et résultats d'une expérience (`/harmonization/:id`)

#### A. 13 sections à afficher

1. **Informations générales**
   - Nom, description, créateur, date de création

2. **Données sources**
   - Satellites utilisés
   - Jeux de données sélectionnés
   - Période analysée

3. **Paramètres expérimentaux**
   - Résolution spatiale
   - Fenêtre temporelle
   - Autres paramètres

4. **Statut et informations d'exécution**
   - Statut final
   - Durée d'exécution
   - Horodatage de début et fin

5. **Résultats avant harmonisation**
   - Statistiques par satellite original
   - Tableau des observations brutes

6. **Résultats après harmonisation**
   - Statistiques harmonisées
   - Tableau des observations harmonisées

7. **Comparaison des satellites**
   - Graphiques comparatifs
   - Tableaux de concordance

8. **Métriques scientifiques**
   - Jaccard (avec définition)
   - Autres métriques (si disponibles)
   - Définitions accessibles (tooltips ou notes)

9. **Carte des résultats**
   - Carte des observations harmonisées
   - Légende par satellite
   - Filtres

10. **Tableaux et séries temporelles**
    - Tableaux détaillés
    - Séries temporelles par satellite

11. **Anomalies et avertissements**
    - Liste des anomalies détectées
    - Avertissements d'interprétation

12. **Provenance et reproductibilité**
    - `data_origin`
    - `generated_at`
    - `digest_sha256` (si disponible)
    - `elapsed_s` (temps de calcul)

13. **Actions d'export**
    - Bouton exporter CSV (si disponible)
    - Bouton exporter JSON (si disponible)

#### B. Implémentation

**Composant à créer:**
- `ExperimentDetail` - Page de détail avec 13 sections

**Sous-composants:**
- `MetricCard` - Affichage des métriques
- `ResultTable` - Tableau des résultats
- `ResultMap` - Carte des résultats (réutiliser MapView d'Aurel)
- `ExportButton` - Bouton d'export

**Intégration API:**
- Endpoint: `GET /experiments/{job_id}/result`
- Endpoint: `GET /export?experiment_id&format=csv|json`

#### C. Note importante sur Jaccard

- L'indice de Jaccard mesure un chevauchement entre ensembles d'observations
- Il ne constitue pas, à lui seul, une mesure de précision des satellites
- Toujours afficher cette note explicite

### 1.5 Critères de validation

- [ ] Une expérience peut être créée avec des paramètres valides
- [ ] Les erreurs de formulaire sont affichées clairement
- [ ] Les statuts correspondent à ceux du backend
- [ ] Les résultats ne sont présentés comme définitifs qu'après confirmation du backend
- [ ] Les paramètres et la provenance restent consultables
- [ ] Les résultats affichés correspondent bien à l'identifiant demandé
- [ ] Le polling fonctionne correctement
- [ ] Mode statique et mode API fonctionnent

### 1.6 Composants à créer

| Composant | Description | Priorité |
|-----------|-------------|----------|
| `ExperimentList` | Tableau avec filtres et pagination | P0 |
| `ExperimentForm` | Formulaire multi-étapes (wizard) | P0 |
| `ExperimentStatus` | Suivi avec polling | P0 |
| `ExperimentDetail` - Page de détail 13 sections | P0 |
| `DatasetSelector` - Sélection datasets | P0 |
| `SpatialParamSelector` - Sélection résolution | P0 |
| `TemporalParamSelector` - Sélection fenêtre | P0 |
| `MetricCard` - Affichage métriques | P0 |
| `ResultTable` - Tableau résultats | P0 |
| `ResultMap` - Carte résultats (réutiliser MapView) | P1 |
| `ExportButton` - Bouton export | P1 |

### 1.7 Estimation temps

- Liste des expériences: 3h
- Formulaire création (5 étapes): 6-8h
- Suivi d'exécution (polling): 2h
- Détail et résultats (13 sections): 8-10h
- Tests et validation: 3h
- **Total: 22-26h**

---

## MODULE 2 - Data & Methodology

**Routes:** `/data`, `/data/:id`, `/methodology`  
**Objectif:** Rendre les données, leur qualité et les méthodes transparentes.

### 2.1 Catalogue des données (`/data`)

#### A. Contenu du tableau

**Colonnes:**
- Nom du jeu de données
- Satellite (MODIS Terra, MODIS Aqua, VIIRS)
- Source d'origine (NASA FIRMS, etc.)
- Période couverte
- Format (CSV, NetCDF, etc.)
- Nombre d'observations
- Statut de validation
- Date d'importation (si disponible)

#### B. Fonctionnalités

- Rechercher un jeu de données (par nom)
- Filtrer par satellite
- Filtrer par période
- Ouvrir le détail d'un jeu de données (clic sur ligne)

#### C. Implémentation

**Composant à créer:**
- `DatasetCatalog` - Tableau avec filtres

**Structure:**
- Utiliser `.panel` pour le conteneur
- Utiliser `table.data` pour le tableau
- Utiliser `.controls` pour les filtres

**Intégration API:**
- Endpoint: `GET /catalog` (déjà utilisé pour inventory)
- Mode statique: lire depuis `inventory.json`

### 2.2 Détail d'un jeu de données (`/data/:id`)

#### A. Contenu

- Informations générales (nom, description)
- Satellite et source
- Période couverte
- Champs disponibles et unités
- Nombre d'observations
- Rapport de qualité
- Anomalies détectées
- Historique et provenance (si disponibles)

#### B. Implémentation

**Composant à créer:**
- `DatasetDetail` - Page de détail dataset

**Structure:**
- Utiliser `.panel` pour chaque section
- Utiliser `.card` pour les métriques
- Utiliser `table.data` pour les champs et anomalies

**Important:**
- Ne pas masquer les anomalies ou les limites du jeu de données
- Afficher les avertissements de manière claire

**Intégration API:**
- Endpoint: `GET /catalog/{dataset_id}`
- Mode statique: lire depuis artefact JSON

### 2.3 Méthodologie (`/methodology`)

#### A. 10 sections pédagogiques

1. **Origine des données**
   - Sources satellitaires (MODIS, VIIRS)
   - API FIRMS
   - Archives Earthdata

2. **Différences générales entre les sources satellitaires**
   - Résolution spatiale
   - Fréquence de passage
   - Caractéristiques techniques

3. **Importation et validation**
   - Processus d'acquisition
   - Validation des fichiers
   - Gestion des erreurs

4. **Nettoyage et normalisation**
   - Schéma commun
   - Unités alignées
   - Seuils normalisés

5. **Harmonisation spatiale**
   - Grilles géographiques
   - Résolutions
   - Agrégation spatiale

6. **Harmonisation temporelle**
   - Fenêtres temporelles
   - Agrégation temporelle
   - Alignement des timestamps

7. **Agrégation**
   - Méthodes d'agrégation
   - Somme, moyenne, etc.

8. **Calcul des métriques**
   - Jaccard
   - Autres métriques
   - Formules

9. **Interprétation des résultats**
   - Ce que les métriques signifient
   - Limites d'interprétation
   - Pièges à éviter

10. **Limites scientifiques**
    - Ce que l'approche ne peut pas faire
    - Biais potentiels
    - Incertitudes

#### B. Implémentation

**Composant à créer:**
- `MethodologyContent` - Contenu méthodologique

**Structure:**
- Utiliser `.panel` pour chaque section
- Utiliser `.md` pour le rendu Markdown (réutiliser existant)
- Ajouter des schémas/diagrammes si disponibles (images)

**Important:**
- Utiliser des textes courts et accessibles
- Ne pas inventer de détails méthodologiques
- S'appuyer sur la documentation scientifique validée par le responsable backend

**Intégration API:**
- Endpoint: `GET /methodology` (si disponible)
- Mode statique: contenu Markdown statique (comme Report)

### 2.4 Critères de validation

- [ ] Les informations proviennent de l'API ou de la documentation validée
- [ ] Les sources, unités et limites sont explicites
- [ ] Le vocabulaire est compréhensible pour un non-spécialiste
- [ ] Les anomalies sont affichées sans être masquées
- [ ] La méthodologie est pédagogique et accessible
- [ ] Mode statique et mode API fonctionnent

### 2.5 Composants à créer

| Composant | Description | Priorité |
|-----------|-------------|----------|
| `DatasetCatalog` - Tableau avec filtres | P0 |
| `DatasetDetail` - Page de détail dataset | P0 |
| `MethodologyContent` - Contenu méthodologique | P0 |

### 2.6 Estimation temps

- Catalogue des données: 3h
- Détail d'un dataset: 3h
- Méthodologie: 4-5h
- Tests et validation: 2h
- **Total: 12-13h**

---

## TRAVAIL COMMUN (avec Aurel)

### Layout et navigation

**À coordonner:**
- Adapter `App.jsx` pour nouvelles routes (`/harmonization`, `/harmonization/new`, `/harmonization/:id`, `/data`, `/data/:id`, `/methodology`)
- Mettre à jour sidebar avec les 4 modules
- Navigation principale persistante

**Responsabilités partagées:**
- Aurel: routes Overview et Fire Calendar
- Abdourahim: routes Harmonization et Data/Methodology
- Ensemble: layout général et navigation

### Composants partagés

**Composants à créer ensemble:**
- `DateRangeFilter` - Utilisé par Harmonization (création) et Data (catalogue)
- `SatelliteSelector` - Utilisé par Harmonization et Data
- `MapView` - Utilisé par Overview (Aurel) et Harmonization résultats (Abdourahim)

**Coordination:**
- Définir l'interface des composants partagés
- Implémentation conjointe ou répartition claire
- Tests d'intégration

### Intégration API

**À coordonner:**
- Brancher tous les endpoints sur `data.js`
- Gérer états loading/success/empty/error de manière cohérente
- Normaliser les réponses API

**Endpoints spécifiques Abdourahim:**
- `GET /experiments` - liste des expériences
- `POST /experiments` - création expérience
- `GET /experiments/{job_id}` - suivi statut
- `GET /experiments/{job_id}/result` - résultats
- `GET /catalog` - catalogue datasets (déjà partiellement utilisé)
- `GET /catalog/{dataset_id}` - détail dataset
- `GET /export` - export résultats

### Tests

**Tests fonctionnels à rédiger:**
- Parcours utilisateur: Harmonization → création → lancement → suivi → résultats
- Parcours utilisateur: Data → catalogue → détail dataset
- Parcours utilisateur: Méthodologie → lecture sections
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

### Harmonization Lab
- [ ] Liste des expériences fonctionnelle
- [ ] Formulaire création (5 étapes) opérationnel
- [ ] Suivi d'exécution avec polling
- [ ] Détail expérience (13 sections) complet
- [ ] Carte des résultats fonctionnelle
- [ ] Export disponible
- [ ] Mode statique et mode API fonctionnent
- [ ] Contrat éditorial respecté

### Data & Methodology
- [ ] Catalogue des données fonctionnel
- [ ] Détail dataset complet
- [ ] Méthodologie pédagogique
- [ ] Anomalies affichées
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

**À installer (si nécessaire):**
- Aucune nouvelle dépendance majeure attendue
- Réutiliser Recharts pour graphiques
- Réutiliser MapView d'Aurel pour carte résultats

**Librairies de formulaires (optionnelles):**
- `react-hook-form` pour gestion formulaire complexe
- `yup` ou `zod` pour validation schema
- `react-step-wizard` pour wizard multi-étapes

**Commandes (si utilisées ):**
```bash
npm --prefix web install react-hook-form yup
npm --prefix web install react-step-wizard
```

**CSS additionnel:**
- Styles personnalisés pour wizard multi-étapes
- Styles pour composants de métriques

---

## Points de blocage potentiels

1. **API endpoints POST non implémentés**
   - Solution: Mode statique avec simulation ou attendre backend

2. **Polling complexe à implémenter**
   - Solution: Utiliser `useInterval` ou librairie `react-use`

3. **Formulaire multi-étapes complexe**
   - Solution: Utiliser librairie existante (react-step-wizard)

4. **Carte résultats non disponible**
   - Solution: Réutiliser MapView d'Aurel ou mode dégradé

5. **Contenu méthodologique non disponible**
   - Solution: Contenu Markdown statique ou placeholder

---

## Livrables

1. **Code:**
   - `web/src/views/HarmonizationList.jsx` (nouveau)
   - `web/src/views/HarmonizationNew.jsx` (nouveau)
   - `web/src/views/HarmonizationDetail.jsx` (nouveau)
   - `web/src/views/DataCatalog.jsx` (nouveau)
   - `web/src/views/DatasetDetail.jsx` (nouveau)
   - `web/src/views/Methodology.jsx` (nouveau)
   - `web/src/components/ExperimentList.jsx` (nouveau)
   - `web/src/components/ExperimentForm.jsx` (nouveau)
   - `web/src/components/ExperimentStatus.jsx` (nouveau)
   - `web/src/components/ExperimentDetail.jsx` (nouveau)
   - `web/src/components/DatasetSelector.jsx` (nouveau)
   - `web/src/components/SpatialParamSelector.jsx` (nouveau)
   - `web/src/components/TemporalParamSelector.jsx` (nouveau)
   - `web/src/components/MetricCard.jsx` (nouveau)
   - `web/src/components/ResultTable.jsx` (nouveau)
   - `web/src/components/ExportButton.jsx` (nouveau)
   - `web/src/components/DatasetCatalog.jsx` (nouveau)
   - `web/src/components/DatasetDetail.jsx` (nouveau)
   - `web/src/components/MethodologyContent.jsx` (nouveau)
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

## Communication avec Aurel

**À coordonner:**
- Interface des composants partagés (props, callbacks)
- Conventions de nommage
- Structure des données API
- Planification des reviews de code

**Fréquence:**
- Daily standup (15 min)
- Review de code avant merge
- Tests d'intégration conjoints

**Points de synchronisation:**
1. Début: Interface des composants partagés (DateRangeFilter, SatelliteSelector, MapView)
2. Milieu: Tests d'intégration des routes et navigation
3. Fin: Tests bout-en-bout et validation globale

---

## Questions en attente

1. **API POST:** Endpoints `/experiments` et `/datasets/validate` sont-ils implémentés?
2. **Polling:** Fréquence recommandée pour le polling de statut?
3. **Export:** Format d'export supporté par le backend (CSV, JSON, les deux)?
4. **Méthodologie:** Contenu disponible en Markdown où à créer?
5. **Formulaire wizard:** Utiliser librairie existante ou implémentation from scratch?

---

## Notes spécifiques pour Harmonization Lab

### Gestion des erreurs

- Erreur de création: Afficher message clair, permettre correction
- Erreur d'exécution: Afficher détails, permettre relance
- Timeout: Afficher avertissement, proposer réessayer

### UX du formulaire

- Progress indicator (étapes 1/5, 2/5, etc.)
- Possibilité de sauvegarder en brouillon (si supporté)
- Validation à chaque étape avant de passer à la suivante
- Récapitulatif final avant soumission

### UX du suivi

- Animation de chargement pendant RUNNING
- Message explicite si l'exécution prend du temps
- Bouton "Annuler" si supporté par l'API

### UX des résultats

- Organisation claire des 13 sections (accordéon ou onglets)
- Possibilité de télécharger les résultats
- Lien vers la méthodologie pour comprendre les métriques

---

## Notes spécifiques pour Data & Methodology

### Catalogue des données

- Tri par défaut pertinent (ex: par date d'importation)
- Recherche en temps réel (debounce)
- Affichage rapide des métadonnées clés

### Détail dataset

- Onglets pour organiser les sections (général, qualité, anomalies)
- Visualisation des anomalies (graphique si possible)
- Lien vers la source originale (NASA FIRMS, etc.)

### Méthodologie

- Navigation rapide entre sections (table des matières)
- Glossaire des termes techniques
- Liens vers les références scientifiques

---

**Document version:** 1.0  
**Dernière mise à jour:** 10 novembre 2026
