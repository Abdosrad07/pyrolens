Tu interviens dans le dépôt PyroLens pour une dernière session de stabilisation avant soumission NASA.

**OBJECTIF : corriger les problèmes UX existants avant 15 h. Aucune nouvelle fonctionnalité majeure.**

### 1. Carte d'aperçu — P0
Diagnostique pourquoi la carte n'est pas visible dans l'aperçu. Vérifie Leaflet, les dimensions CSS, l'initialisation et les erreurs JavaScript. Corrige sans modifier inutilement les autres cartes.

Critère : carte visible et fonctionnelle dès l'ouverture.

### 2. Jobs — P0
Corrige le comportement visuel du polling asynchrone :
- aucun rechargement permanent ;
- aucune réinitialisation visuelle à chaque polling ;
- progression stable ;
- gestion claire des états attente, exécution, succès et erreur ;
- aucune requête dupliquée.

Remplace l'affichage brut des paramètres JSON par des libellés et valeurs compréhensibles. Conserve les informations techniques utiles dans une section secondaire si nécessaire.

### 3. Navigation — P1
Ajoute un bouton retour cohérent aux pages concernées. Respecte l'historique de navigation et conserve la navigation principale.

Vérifie également le bouton d'accès au chatbot : il doit être visible, accessible et fonctionnel depuis les pages concernées.

### 4. Fonctionnalités à préserver
Ne modifie pas inutilement :
- Calendrier et ses données 2013–2020 ;
- Chronologie ;
- Qualité ;
- Risque ;
- logique et réponses du chatbot ;
- moteur d'harmonisation ;
- modèle prédictif.

### 5. Vérifications
Après les corrections :
- teste chaque fonctionnalité concernée ;
- exécute `pytest` ;
- exécute `cd frontend && npm run build` ;
- corrige les régressions éventuelles.

Travaille dans une branche dédiée. Ne pousse pas directement des modifications non vérifiées en production.

### 6. Méthode pédagogique
Avant chaque correction, explique brièvement :
1. le problème identifié ;
2. sa cause ;
3. le fichier concerné ;
4. la correction envisagée.

Après chaque correction, indique comment la vérifier dans le navigateur.

**Règle de priorité :** termine d'abord la carte et Jobs, ensuite la navigation, puis les tests. Si le temps manque, ne sacrifie pas la stabilité pour des améliorations esthétiques.

À la fin, fournis un tableau : problème, cause, fichiers modifiés, correction, test et statut.

Commence par l'inspection. Ne modifie rien avant d'avoir identifié les causes.