# PyroLens — Spécification du Frontend

**Version :** 1.0  
**Projet :** NASA Space Apps Challenge 2026  
**Objet :** Répartir les pages et fonctionnalités frontend entre deux développeurs et définir les règles d'intégration avec le backend.

---

# 1. Objectif du document

Ce document définit les pages à développer, les fonctionnalités visibles par l'utilisateur, les composants communs, les priorités et la répartition du travail.

Le backend est développé séparément. Il gère les données, les traitements scientifiques, les calculs et expose une API documentée.

Le frontend consomme cette API et présente les résultats sous forme de cartes, graphiques, tableaux et indicateurs.

### Principes fondamentaux

- Ne jamais inventer les réponses de l'API.
- Ne jamais inventer les unités ou les paramètres scientifiques.
- Ne jamais coder en dur des résultats scientifiques.
- Ne jamais présenter des données fictives comme des résultats réels.
- Respecter le contrat API défini par le responsable backend.

---

# 2. Compréhension de PyroLens

PyroLens est une plateforme scientifique qui permet d'explorer, de comparer et d'harmoniser des observations de feux provenant de trois sources satellitaires :

- MODIS Terra ;
- MODIS Aqua ;
- VIIRS Suomi NPP.

Le Cameroun constitue la première zone d'étude.

Les satellites peuvent produire des observations différentes en raison de leurs caractéristiques et de leurs moments de passage.

PyroLens organise ces observations selon des références communes afin de faciliter leur comparaison.

La plateforme ne doit pas prétendre que l'absence de détection signifie l'absence de feu, ni que l'harmonisation garantit une meilleure précision de détection.

---

# 3. Architecture de navigation

L'application comporte quatre modules principaux :

1. **Overview** — Vue d'ensemble et exploration des données.
2. **Harmonization Lab** — Configuration et consultation des expériences.
3. **Fire Calendar** — Analyse temporelle de l'activité observée.
4. **Data & Methodology** — Sources, qualité des données et explication des méthodes.

## Routes proposées

| Route | Page | Objectif |
|---|---|---|
| `/` | Overview | Vue d'ensemble et exploration |
| `/harmonization` | Harmonization Lab | Liste des expériences |
| `/harmonization/new` | Nouvelle expérience | Configuration et lancement |
| `/harmonization/:id` | Détail d'expérience | Statut, paramètres et résultats |
| `/fire-calendar` | Fire Calendar | Analyse temporelle |
| `/data` | Data Catalog | Catalogue des jeux de données |
| `/data/:id` | Détail d'un jeu de données | Métadonnées et qualité |
| `/methodology` | Méthodologie | Explication des traitements |

Prévoir une navigation principale persistante, un en-tête, une zone de contenu et un système de notifications.

Ne pas créer de pages de connexion, de profil ou d'administration si le backend ne prend pas réellement ces fonctions en charge.

---

# 4. Spécification détaillée des pages

## PAGE 1 — Overview

**Route :** `/`

**Objectif :** permettre à un nouvel utilisateur de comprendre rapidement les données disponibles et les possibilités de PyroLens.

### A. Bandeau d'introduction

Afficher :
- Le nom et une présentation courte de PyroLens.
- La zone d'étude active.
- La période couverte par les données.

### B. Cartes statistiques

Afficher, selon les données fournies par l'API :

- Nombre total d'observations.
- Nombre d'observations par satellite.
- Nombre de jours couverts.
- Nombre de cellules géographiques actives.
- Indicateurs de FRP lorsque disponibles.

Chaque carte doit préciser :
- Le libellé.
- La valeur.
- L'unité éventuelle.
- Une explication courte.

### C. Carte des points chauds

Fonctionnalités :

- Affichage des observations géolocalisées.
- Légende distinguant les satellites.
- Info-bulle au clic ou au survol.
- Filtres temporels et géographiques.
- Activation ou désactivation de chaque source.
- Regroupement ou chargement adapté si le volume de points est important.

### D. Comparaison des satellites

Présenter :

- Une comparaison MODIS Terra, MODIS Aqua et VIIRS.
- Des graphiques ou tableaux.
- Des libellés et unités explicites.
- Une explication des indicateurs affichés.

### E. Accès rapide

Prévoir des liens ou boutons vers :

- Le lancement d'une expérience.
- Le calendrier des feux.
- Le catalogue des données.
- La méthodologie.

### Interactions

L'utilisateur doit pouvoir :

- Filtrer par période.
- Filtrer par zone si l'API le permet.
- Sélectionner un ou plusieurs satellites.
- Actualiser les statistiques et la carte selon les filtres.
- Ouvrir les détails d'un jeu de données ou d'une expérience.

### Critères de validation

- Toutes les valeurs proviennent de l'API.
- Les filtres ont un effet réel.
- La légende distingue les satellites.
- Une absence de résultat affiche un état vide explicite.
- Les unités et périodes sont visibles.

---

## PAGE 2 — Harmonization Lab

**Routes :**
- `/harmonization`
- `/harmonization/new`
- `/harmonization/:id`

**Objectif :** permettre de créer, lancer, suivre et consulter les expériences d'harmonisation.

C'est le parcours fonctionnel principal de PyroLens.

### A. Liste des expériences

Afficher :

- Nom de l'expérience.
- Date de création.
- Satellites et jeux de données sélectionnés.
- Période analysée.
- Résolution spatiale.
- Fenêtre temporelle.
- Statut.
- Action pour consulter les détails.

Prévoir :

- Recherche par nom si supportée.
- Filtres par statut et période.
- Pagination si nécessaire.
- Bouton de création d'une expérience.

Statuts possibles, selon le contrat backend :

- `PENDING`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

### B. Création d'une expérience

**Route :** `/harmonization/new`

Présenter un formulaire en étapes ou en sections clairement identifiées.

#### Étape 1 — Informations générales

- Nom de l'expérience.
- Description facultative.
- Zone d'étude.
- Date de début.
- Date de fin.

#### Étape 2 — Sélection des données

- Choix des jeux de données disponibles.
- Sélection des satellites :
  - MODIS Terra ;
  - MODIS Aqua ;
  - VIIRS Suomi NPP.
- Présentation des périodes couvertes.
- Affichage des métadonnées utiles.
- Avertissement si les périodes ne sont pas compatibles.

#### Étape 3 — Paramètres spatiaux

Proposer les valeurs prises en charge par le backend :

- 0,10° ;
- 0,25° ;
- 0,50° ;
- Valeur personnalisée uniquement si acceptée par le backend.

Expliquer simplement qu'il s'agit de la taille des cellules géographiques utilisées pour regrouper les observations.

#### Étape 4 — Paramètres temporels

Proposer les fenêtres prises en charge :

- 1 jour ;
- 4 jours ;
- 8 jours ;
- 16 jours ;
- Valeur personnalisée uniquement si acceptée par le backend.

Expliquer qu'il s'agit de la durée utilisée pour regrouper les observations dans le temps.

#### Étape 5 — Récapitulatif et lancement

Avant l'envoi :

- Récapituler les jeux de données.
- Afficher la période.
- Afficher les paramètres spatiaux et temporels.
- Permettre de modifier la configuration.
- Demander confirmation avant le lancement.

### C. Suivi de l'exécution

Après le lancement :

- Afficher le statut de l'expérience.
- Actualiser le statut via l'API.
- Afficher une progression uniquement si le backend en fournit une.
- Présenter les erreurs de manière compréhensible.
- Ne pas simuler une progression si aucune information réelle n'est disponible.

### D. Détail et résultats d'une expérience

**Route :** `/harmonization/:id`

Afficher les sections suivantes :

1. Informations générales.
2. Données sources.
3. Paramètres expérimentaux.
4. Statut et informations d'exécution.
5. Résultats avant harmonisation.
6. Résultats après harmonisation.
7. Comparaison des satellites.
8. Métriques scientifiques.
9. Carte des résultats.
10. Tableaux et séries temporelles.
11. Anomalies et avertissements.
12. Provenance et reproductibilité.
13. Actions d'export si disponibles.

Les métriques doivent avoir une définition accessible.

Un indice de Jaccard mesure un chevauchement entre ensembles d'observations. Il ne constitue pas, à lui seul, une mesure de précision des satellites.

### Critères de validation

- Une expérience peut être créée avec des paramètres valides.
- Les erreurs de formulaire sont affichées clairement.
- Les statuts correspondent à ceux du backend.
- Les résultats ne sont présentés comme définitifs qu'après confirmation du backend.
- Les paramètres et la provenance restent consultables.
- Les résultats affichés correspondent bien à l'identifiant demandé.

---

## PAGE 3 — Fire Calendar

**Route :** `/fire-calendar`

**Objectif :** explorer l'évolution temporelle des observations.

### A. Filtres

Prévoir :

- Période de début et de fin.
- Satellite ou groupe de satellites.
- Zone géographique.
- Type de données : originales ou harmonisées, si disponible.

### B. Calendrier

Afficher :

- Une vue quotidienne.
- Une intensité visuelle fondée sur une mesure explicitement définie.
- Une légende.
- La possibilité de sélectionner un jour pour afficher ses détails.

### C. Agrégations temporelles

Prévoir :

- Vue quotidienne.
- Vue hebdomadaire.
- Vue mensuelle.

### D. Graphiques

Afficher :

- Évolution du nombre d'observations.
- Évolution du nombre de cellules actives.
- Évolution de la FRP lorsque disponible.
- Comparaison entre satellites.
- Comparaison des données originales et harmonisées lorsque les résultats existent.

### E. Détail d'une période

Au clic sur un jour, une semaine ou un mois :

- Afficher les statistiques correspondantes.
- Afficher les satellites concernés.
- Afficher les observations ou cellules concernées.
- Permettre d'accéder à la carte si les données sont disponibles.

### Critères de validation

- Les agrégations correspondent aux données de l'API.
- La période sélectionnée est visible.
- Les graphiques précisent leurs unités.
- Les données originales et harmonisées sont différenciées.
- Une période sans observation n'est jamais présentée comme une période sans feu.

---

## PAGE 4 — Data & Methodology

**Routes :**
- `/data`
- `/data/:id`
- `/methodology`

**Objectif :** rendre les données, leur qualité et les méthodes transparentes.

### A. Catalogue des données — `/data`

Afficher :

- Nom du jeu de données.
- Satellite.
- Source d'origine.
- Période couverte.
- Format.
- Nombre d'observations.
- Statut de validation.
- Date d'importation si disponible.

Interactions :

- Rechercher un jeu de données.
- Filtrer par satellite.
- Filtrer par période.
- Ouvrir le détail d'un jeu de données.

### B. Détail d'un jeu de données — `/data/:id`

Afficher :

- Informations générales.
- Satellite et source.
- Période couverte.
- Champs disponibles et unités.
- Nombre d'observations.
- Rapport de qualité.
- Anomalies détectées.
- Historique et provenance si disponibles.

Ne pas masquer les anomalies ou les limites du jeu de données.

### C. Méthodologie — `/methodology`

Présenter de manière pédagogique :

1. Origine des données.
2. Différences générales entre les sources satellitaires.
3. Importation et validation.
4. Nettoyage et normalisation.
5. Harmonisation spatiale.
6. Harmonisation temporelle.
7. Agrégation.
8. Calcul des métriques.
9. Interprétation des résultats.
10. Limites scientifiques.

Utiliser des textes courts, des schémas et des définitions accessibles.

Ne pas inventer de détails méthodologiques : s'appuyer sur la documentation scientifique validée par le responsable backend.

### Critères de validation

- Les informations proviennent de l'API ou de la documentation validée.
- Les sources, unités et limites sont explicites.
- Le vocabulaire est compréhensible pour un non-spécialiste.

---

# 5. Composants frontend partagés

Construire une bibliothèque commune pour éviter les duplications.

| Composant | Fonction |
|---|---|
| `AppLayout` | Structure générale |
| `Sidebar` / `MainNavigation` | Navigation |
| `PageHeader` | Titre et description |
| `StatCard` | Indicateur statistique |
| `DateRangeFilter` | Filtre de période |
| `SatelliteSelector` | Sélection des satellites |
| `DatasetSelector` | Sélection des jeux de données |
| `MapView` | Carte géographique |
| `ChartCard` | Conteneur de graphique |
| `DataTable` | Tableau |
| `StatusBadge` | Statut |
| `LoadingState` | Chargement |
| `EmptyState` | Aucun résultat |
| `ErrorState` | Erreur |
| `ConfirmDialog` | Confirmation |
| `TooltipInfo` | Explication d'un terme |
| `ExportButton` | Export si disponible |
| `Notification` | Retour après action |

Les composants doivent être réutilisables, accessibles et visuellement cohérents.

---

# 6. Règles d'intégration avec le backend

Le backend est la source de vérité pour les données, les calculs et les statuts.

### Consommation de l'API

- Centraliser les appels HTTP dans une couche API.
- Centraliser l'URL de base dans une variable d'environnement.
- Consulter `api_contract.md`, `api_reference.md`, `data_dictionary.md` et OpenAPI.
- Définir les types TypeScript à partir du contrat API.
- Uniformiser les formats de date, coordonnées, unités, identifiants et erreurs.
- Ne pas disperser les appels API dans les composants.
- Ne pas coder en dur des résultats scientifiques.
- Si un endpoint ou un champ manque, le signaler au responsable backend au lieu d'inventer une convention.

### États obligatoires

Chaque zone dépendant de l'API doit gérer :

- **Loading :** récupération en cours.
- **Success :** données disponibles.
- **Empty :** requête réussie, aucun résultat.
- **Error :** requête échouée.
- **Processing :** traitement en cours, lorsque cela s'applique.

Ne pas confondre une liste vide avec une erreur.

### Données de démonstration

Les données fictives temporaires doivent :

- Être clairement identifiées.
- Être isolées des données réelles.
- Être faciles à retirer.
- Ne jamais être présentées comme des résultats scientifiques réels.

---

# 7. Répartition entre les deux développeurs frontend

## Développeur A — Overview et Fire Calendar

### Pages

- Overview (`/`).
- Fire Calendar (`/fire-calendar`).

### Responsabilités

- Tableau de bord et cartes statistiques.
- Carte des points chauds.
- Filtres géographiques et temporels.
- Comparaison des satellites.
- Calendrier quotidien, hebdomadaire et mensuel.
- Graphiques temporels et FRP.
- États de chargement, vide et erreur.
- Connexion aux endpoints correspondants.

### Livrables

- Pages responsive.
- Visualisations réutilisables.
- Parcours fonctionnels connectés à l'API.
- Tests fonctionnels.

## Développeur B — Harmonization Lab et Data & Methodology

### Pages

- Liste des expériences.
- Création d'expérience.
- Détail et résultats d'expérience.
- Catalogue des données.
- Détail d'un jeu de données.
- Méthodologie.

### Responsabilités

- Historique des expériences.
- Formulaire de configuration.
- Sélection des données et satellites.
- Paramètres spatiaux et temporels.
- Confirmation et lancement.
- Suivi du statut.
- Présentation des résultats et métriques.
- Provenance.
- Catalogue, qualité et documentation méthodologique.
- Connexion aux endpoints correspondants.

### Livrables

- Parcours complet de création et consultation d'expérience.
- Pages données et méthodologie.
- Connexion API.
- Tests fonctionnels.

## Travail commun

Les deux développeurs coordonnent :

- Identité visuelle.
- Layout et navigation.
- Composants partagés.
- Conventions de nommage.
- Types TypeScript.
- Gestion des erreurs.
- Responsive design.
- Tests d'intégration.
- Revue finale.

**Important :** le moteur d'harmonisation et les calculs restent exclusivement du ressort du backend. Le frontend configure les expériences et présente les résultats.

---

# 8. Organisation indicative du code

Adapter à la technologie déjà utilisée dans le dépôt.

```text
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── router/
│   │   └── providers/
│   ├── assets/
│   ├── components/
│   │   ├── layout/
│   │   ├── maps/
│   │   ├── charts/
│   │   ├── tables/
│   │   ├── filters/
│   │   └── feedback/
│   ├── features/
│   │   ├── overview/
│   │   ├── harmonization/
│   │   ├── fire-calendar/
│   │   ├── datasets/
│   │   └── methodology/
│   ├── services/
│   │   ├── api/
│   │   └── endpoints/
│   ├── hooks/
│   ├── types/
│   ├── utils/
│   └── styles/
├── .env.example
└── README.md
```

Ne pas dupliquer les clients API ou les types de données dans chaque module.

---

# 9. Direction UX et design

Le design doit faciliter la compréhension des données scientifiques.

Principes :

- Interface sobre et professionnelle.
- Hiérarchie visuelle claire.
- Navigation prévisible.
- Textes courts et explicatifs.
- Graphiques lisibles.
- Couleurs cohérentes entre satellites.
- Légendes systématiques.
- Unités visibles.
- Contraste suffisant.
- Interface responsive.
- Animations décoratives limitées.

Définir une seule fois les couleurs des satellites dans le thème de l'application et les réutiliser sur toutes les pages.

Ne pas utiliser la couleur comme seul moyen de distinction : ajouter des libellés ou des symboles.

Expliquer les termes techniques comme FRP, résolution spatiale et cellule active avec des infobulles ou des définitions courtes.

---

# 10. Priorités de développement

## P0 — Indispensable au MVP

- Layout et navigation.
- Overview fonctionnel.
- Création d'une expérience.
- Suivi de l'exécution.
- Consultation des résultats.
- Carte des observations.
- Comparaison des satellites.
- États Loading, Success, Empty et Error.
- Connexion réelle à l'API.
- Responsive des parcours principaux.

## P1 — Important

- Fire Calendar complet.
- Catalogue et détail des données.
- Rapports de qualité.
- Méthodologie.
- Historique des expériences.
- Provenance détaillée.
- Comparaison de plusieurs expériences.

## P2 — Complémentaire

- Interface d'export avancée.
- Consultation de rapports.
- Filtres avancés.
- Améliorations de confort.
- Administration uniquement si elle est prise en charge par le backend.

Ne pas développer P2 avant que les parcours P0 soient opérationnels.

---

# 11. Parcours de validation de bout en bout

Le frontend doit permettre à un utilisateur de :

1. Ouvrir PyroLens et comprendre le tableau de bord.
2. Consulter les observations sur la carte.
3. Ouvrir Harmonization Lab.
4. Sélectionner deux jeux de données satellitaires.
5. Définir une période.
6. Choisir une résolution spatiale et une fenêtre temporelle.
7. Vérifier le récapitulatif.
8. Lancer l'expérience.
9. Consulter son statut.
10. Ouvrir les résultats après la fin du traitement.
11. Comparer les observations originales et harmonisées.
12. Consulter les métriques.
13. Explorer les visualisations temporelles lorsque disponibles.
14. Consulter les sources et la méthodologie.

Ce parcours doit utiliser les données réelles disponibles dans le backend.

---

# 12. Tableau de suivi du développement

| Page / Fonctionnalité | Responsable | Priorité | Statut initial | Dépendance API | Testé |
|---|---|---|---|---|---|
| Layout et navigation | Commun | P0 | À faire | Non | Non |
| Overview — statistiques | A | P0 | À faire | Oui | Non |
| Overview — carte | A | P0 | À faire | Oui | Non |
| Overview — filtres | A | P0 | À faire | Oui | Non |
| Harmonization — liste | B | P0 | À faire | Oui | Non |
| Harmonization — formulaire | B | P0 | À faire | Oui | Non |
| Harmonization — suivi | B | P0 | À faire | Oui | Non |
| Harmonization — résultats | B | P0 | À faire | Oui | Non |
| Fire Calendar | A | P1 | À faire | Oui | Non |
| Catalogue des données | B | P1 | À faire | Oui | Non |
| Détail d'un dataset | B | P1 | À faire | Oui | Non |
| Méthodologie | B | P1 | À faire | Selon contenu | Non |
| Exports | Commun | P2 | À faire | Oui | Non |
| Intégration globale | Commun | P0 | À faire | Oui | Non |

### Statuts à utiliser

- À faire.
- En cours.
- En revue.
- Bloqué.
- Terminé.
- Testé et validé.

---

# 13. Conditions de réception du frontend

Le frontend est prêt pour la démonstration lorsque :

- Toutes les pages P0 sont accessibles.
- Les parcours principaux fonctionnent.
- Les données affichées proviennent du backend.
- Les filtres ont un effet réel.
- Les statuts d'expérience sont exacts.
- Les erreurs sont compréhensibles.
- Les résultats vides sont correctement traités.
- Les unités et légendes sont présentes.
- Les observations originales et harmonisées sont distinguées.
- Aucun résultat fictif n'est présenté comme réel.
- L'application fonctionne sur les tailles d'écran ciblées.
- Le parcours complet a été testé par les deux développeurs.

---

# 14. Règle finale de collaboration

Le backend définit les données disponibles, les paramètres acceptés, les calculs et les résultats.

Le frontend définit la manière dont l'utilisateur interagit avec ces fonctions et comprend les résultats.

L'inspecteur teste l'application du point de vue de l'utilisateur, relève les anomalies et conseille l'équipe sur la qualité du parcours.

Toute divergence entre l'interface et le contrat API doit être discutée avant correction.

Aucun développeur ne doit inventer seul une structure de données ou une règle scientifique.

**Priorité commune : livrer une application cohérente, utilisable et scientifiquement honnête, pas simplement un ensemble de pages visuellement abouties.**