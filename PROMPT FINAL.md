# MISSION TECHNIQUE — PYROLENS
## Extension du modèle prédictif et amélioration du chatbot

Tu interviens directement dans le dépôt `pyrolens`, projet développé pour le NASA Space Apps Challenge 2026.

Tu es un ingénieur logiciel et machine learning senior. Tu dois améliorer le modèle de prédiction et le chatbot existants, sans dégrader les fonctionnalités déjà opérationnelles.

**Règle de travail : inspecter, expliquer, planifier, exécuter, tester et documenter.**

Ne modifie jamais un composant important sans avoir compris son fonctionnement actuel.

---

# 1. CONTEXTE TECHNIQUE — ÉTAT INITIAL À PRÉSERVER

Les informations suivantes ont été vérifiées. Considère-les comme la référence initiale et ne les remets pas en cause sans preuve issue du dépôt.

### 1.1 Modèle de prédiction

- Module : `src/pyrolens/prediction.py`
- Commande : `pyrolens predict`
- Données : `data/raw/firms`
- Période : 2013-01-01 au 2020-12-31
- Volume : 1 171 fichiers canoniques.
- Origine : NASA FIRMS.
- Couverture actuelle : Cameroun.
- Artefact : `web/public/artifacts/fire_risk.json`
- Cellules : 1 215 cellules de 0,25°.
- `reference_date` : `2020-12-31`.
- `estimate_kind` : `historical_backtest`.

Métriques actuelles :

| Indicateur | Valeur |
|---|---:|
| Observations de test | 122 715 |
| Prévalence | 31,8 % |
| PR-AUC Random Forest | 0,926 |
| PR-AUC baseline fréquence | 0,875 |
| F1 | 0,841 |
| Recall | 0,844 |
| Brier Score | 0,072 |
| Calibration | Isotonic |
| Seuil | 0,42 |

Le protocole actuel utilise :
- un découpage chronologique ;
- une purge de 8 jours ;
- des variables calculées exclusivement à partir du passé ;
- une calibration isotonic sur validation.

**Ces protections contre les fuites temporelles sont obligatoires. Ne les supprime pas et ne les affaiblis pas.**

### 1.2 Archives FIRMS

Le projet possède déjà :
- `src/pyrolens/archive.py`
- `scripts/download_west_africa_archive.py`

Le téléchargement utilise un manifeste JSONL, permet la reprise et gère les erreurs temporaires et le throttling FIRMS.

La commande `predict --source` accepte déjà les CSV imbriqués grâce à `rglob("*.csv")`.

### 1.3 Chatbot

- Backend : `api/services/chat.py`
- Endpoint : `/api/v1/chat`
- Frontend : `frontend/src/components/AiPanel.jsx`
- Fonctionnement : réponses déterministes fondées sur les artefacts du projet.

Il n'y a actuellement aucun LLM intégré au produit.

**Ne remplace pas le chatbot par un LLM et n'ajoute aucune dépendance à un service externe.**

### 1.4 Environnement

- Frontend : React 18 + Vite.
- Dossier : `frontend/`.
- Port frontend : 5174.
- Backend : 8010.
- Tests : pytest.
- Build : `cd frontend && npm run build`.

Documentation :
- `docs/PROJECT_OVERVIEW.md`
- `docs/FIRE_RISK_PREDICTION.md`
- `docs/MODEL_TRAINING_COLLEAGUE.md`
- `docs/NASA_SUBMISSION_AUDIT.md`

---

# 2. MÉTHODE D'EXÉCUTION OBLIGATOIRE

Travaille en six phases.

Pour chaque phase :
1. Explique brièvement ce que tu vas faire et pourquoi.
2. Inspecte les fichiers concernés.
3. Présente les éventuels risques.
4. Exécute les modifications nécessaires.
5. Lance les tests correspondants.
6. Présente les résultats avant de passer à la phase suivante.

Ne demande pas de confirmation pour chaque opération technique normale.

En revanche, si une opération risque de consommer plusieurs dizaines de Go, de supprimer des données, de modifier une architecture fondamentale ou de nécessiter des ressources indisponibles, arrête-toi et présente une estimation avant de continuer.

Ne simule jamais une réussite.

---

# PHASE 1 — AUDIT ET PLAN D'EXÉCUTION

Avant toute modification :

1. Inspecte le pipeline de prédiction.
2. Inspecte les données disponibles et leurs manifestes.
3. Comprends précisément le protocole d'entraînement et de validation.
4. Inspecte le chatbot backend et son intégration frontend.
5. Identifie les tests existants.
6. Vérifie les espaces disque disponibles et estime les volumes des archives envisagées.

Produis un plan court dans `docs/IMPROVEMENT_PLAN.md` comprenant :
- les fichiers à modifier ;
- les nouvelles données nécessaires ;
- les risques techniques et scientifiques ;
- les tests à ajouter ;
- les étapes d'exécution.

Ne modifie aucun code pendant cette première phase.

---

# PHASE 2 — EXTENSION DES DONNÉES GÉOGRAPHIQUES

## 2.1 Objectif

Étendre les données d'entraînement au-delà du Cameroun pour évaluer la capacité du modèle à fonctionner dans différents contextes géographiques.

Pays et régions envisagés :

**Afrique :**
- Cameroun ;
- autres pays d'Afrique centrale ;
- Afrique de l'Est ;
- Afrique australe ;
- Afrique de l'Ouest si des données supplémentaires sont utiles.

**Témoins hors Afrique :**
- États-Unis ;
- France ;
- Russie ;
- Brésil ;
- Australie.

Le choix final doit être justifié par la disponibilité des données, leur volume et leur intérêt scientifique.

## 2.2 Stratégie de téléchargement

Utilise les archives FIRMS par pays, sans clé API.

Les fichiers sont annuels et organisés par capteur.

Avant de télécharger :
- vérifie les véritables slugs FIRMS ;
- identifie les années disponibles ;
- estime la taille des fichiers ;
- évite les doublons ;
- identifie les éventuels chevauchements géographiques.

Commence avec une période commune raisonnable, idéalement 2018–2020, si elle est disponible pour les pays sélectionnés.

Ne télécharge pas automatiquement plusieurs années de données mondiales.

Réutilise le mécanisme de téléchargement existant :
- manifeste JSONL ;
- reprise après interruption ;
- retry avec backoff ;
- gestion du throttling ;
- téléchargement séquentiel ;
- aucune parallélisation agressive ;
- aucun Range request.

Le débit FIRMS peut être limité à environ 300 KB/s.

Pour les pays très volumineux, notamment les États-Unis, la Russie, le Brésil et l'Australie, privilégie une stratégie de filtrage spatial en amont lorsque cela est techniquement possible.

Documente les choix concernant :
- France métropolitaine et territoires ultramarins ;
- alias de noms de pays ;
- filtres géographiques ;
- capteurs disponibles ;
- années réellement téléchargées.

## 2.3 Traçabilité

Chaque jeu de données doit conserver :
- pays ou région ;
- capteur ;
- période ;
- nombre de fichiers ;
- volume téléchargé ;
- source FIRMS ;
- statut de validation.

Ne mélange pas des données dont la provenance est inconnue.

---

# PHASE 3 — AMÉLIORATION SCIENTIFIQUE DU MODÈLE

## 3.1 Évaluer d'abord le modèle actuel

Avant de modifier les algorithmes, reproduis les métriques initiales.

Vérifie particulièrement :
- la PR-AUC ;
- la prévalence ;
- le F1 ;
- le Recall ;
- le Brier Score ;
- la calibration ;
- la PR-AUC de la baseline fréquence.

La comparaison Random Forest / baseline doit être effectuée sur exactement les mêmes observations de test.

La baseline doit être recalculée sur le test, et non comparée uniquement à sa valeur de validation.

Si les résultats initiaux ne sont pas reproductibles, identifie la cause avant de poursuivre.

## 3.2 Adapter les données au modèle

Étudie la meilleure stratégie :

**Option A : modèle global**

Un modèle commun entraîné sur plusieurs régions, avec des variables permettant de tenir compte des différences géographiques.

**Option B : modèles régionaux**

Des modèles distincts par région, avec fusion des prédictions dans un artefact commun.

**Option C : modèle global avec évaluation régionale**

Un modèle commun et des métriques détaillées par pays ou région.

Choisis l'approche la plus défendable scientifiquement. Ne multiplie pas les modèles sans justification.

Le résultat doit permettre d'identifier les performances du modèle au Cameroun, en Afrique et hors Afrique.

## 3.3 Variables supplémentaires

Évalue les possibilités suivantes :

- densité historique des détections par cellule ;
- historique des détections sur plusieurs fenêtres ;
- FRP moyen et maximal ;
- nombre de jours avec détections ;
- mois et saison ;
- coordonnées géographiques ;
- indicateur d'hémisphère ;
- variables saisonnières adaptées à chaque hémisphère ;
- informations disponibles sur les capteurs.

Attention : les saisons ne sont pas directement transférables entre hémisphères.

Ne conserve une nouvelle variable que si elle apporte un intérêt mesurable et ne provoque aucune fuite temporelle.

## 3.4 Comparaison des algorithmes

Évalue, si les ressources le permettent :

- Random Forest actuel ;
- Random Forest avec réglages optimisés ;
- `class_weight` ;
- Gradient Boosting ou un autre modèle pertinent.

Ne multiplie pas les expérimentations inutilement.

Règle de sélection :

Un modèle candidat ne peut être retenu que si sa PR-AUC de validation dépasse celle de la baseline fréquence d'au moins 5 % en relatif.

La sélection se fait sur validation uniquement.

Le test final reste indépendant et n'est utilisé qu'après sélection du modèle.

Ne choisis jamais un modèle simplement parce qu'il produit un score plus élevé sur le test.

## 3.5 Prévention des fuites

Exigences absolues :

- split chronologique ;
- purge temporelle de 8 jours minimum ;
- variables exclusivement calculées à partir du passé ;
- aucune information issue de la fenêtre cible dans les features ;
- calibration exclusivement sur validation ;
- test final indépendant ;
- vérification des doublons entre partitions ;
- vérification des cellules et périodes communes.

Évalue également le risque de fuite spatiale et la capacité du modèle à généraliser à des régions inconnues.

Si une validation spatiale indépendante est réalisable, ajoute-la comme expérience complémentaire.

## 3.6 Interprétation des résultats

Les métriques doivent être produites :
- globalement ;
- par région ;
- par pays lorsque l'échantillon est suffisant.

Ne présente pas une métrique régionale lorsque le nombre d'observations est insuffisant.

Documente les limites de généralisation.

---

# PHASE 4 — ARTEFACTS ET INTÉGRATION

Régénère :

`web/public/artifacts/fire_risk.json`

Synchronise également :

`frontend/public/artifacts/fire_risk.json`

Le frontend doit toujours disposer de l'artefact attendu.

Chaque artefact doit inclure, lorsque pertinent :

- `generated_at` ;
- `reference_date` ;
- `prediction_horizon_days` ;
- `estimate_kind` ;
- `data_origin` ;
- période des données ;
- pays et régions couverts ;
- capteurs utilisés ;
- version du modèle ;
- métriques globales ;
- métriques régionales ;
- informations de calibration ;
- provenance de chaque cellule.

Chaque cellule doit être traçable.

Aucune cellule ne doit être présentée sans provenance.

Conserve une distinction explicite entre :

1. Historical Monitoring ;
2. Near-Real-Time Monitoring ;
3. Historical Prediction Backtest.

Le modèle ne doit jamais être présenté comme une prévision opérationnelle actuelle si ses données d'entraînement s'arrêtent en 2020.

N'utilise pas `reference_date` comme synonyme de date actuelle.

---

# PHASE 5 — AMÉLIORATION DU CHATBOT

Le chatbot doit rester déterministe et fonctionner à partir des données réellement disponibles.

Fichier backend :

`api/services/chat.py`

Fichier frontend :

`frontend/src/components/AiPanel.jsx`

## 5.1 Intentions obligatoires

Le chatbot doit comprendre et traiter au minimum les questions suivantes :

**Modèle :**
- Quelle est la PR-AUC ?
- Quel est le F1 ?
- Quelle est la date de référence ?
- Quel est le modèle utilisé ?
- Quelle est la période d'entraînement ?
- Quels pays sont couverts ?

**Interprétation :**
- Que signifie une probabilité de 0,7 ?
- Comment interpréter la PR-AUC ?
- Quelle est la différence entre PR-AUC et F1 ?
- Que signifie le Brier Score ?

**Données et satellites :**
- Quelles données sont utilisées ?
- Quelle est la différence entre MODIS et VIIRS ?
- Quelle est la différence entre Terra et Aqua ?
- Qu'est-ce que NASA FIRMS ?

**Harmonisation :**
- Qu'est-ce que le Jaccard ?
- Comment fonctionne la comparaison des capteurs ?
- Pourquoi utiliser une grille de 0,25° ?

**Utilisation :**
- Comment analyser une zone ?
- Comment consulter les données historiques ?
- Comment lancer un téléchargement ?

**Limites :**
- Quelles sont les limites du modèle ?
- Le modèle prédit-il réellement les incendies ?
- Les résultats ont-ils été validés sur le terrain ?
- Le modèle fonctionne-t-il en temps réel ?

**Documentation :**
- Comment citer PyroLens ?
- Quelles sont les licences utilisées ?
- Quelles sont les sources des données ?

## 5.2 Exactitude des réponses

Les métriques doivent être lues dynamiquement dans les artefacts JSON.

Interdictions :
- valeurs statistiques codées en dur ;
- chiffres inventés ;
- réponses affirmant une couverture géographique non disponible ;
- présentation du backtest comme une prévision actuelle.

Le chatbot doit rappeler que la probabilité représente :

**P(au moins une détection FIRMS dans une cellule pendant les 8 prochains jours, selon le protocole du modèle).**

Elle ne représente pas la probabilité qu'un incendie réel se produise.

Pour le Jaccard, utiliser exclusivement les termes :
- set overlap ;
- recouvrement des ensembles ;
- similarité entre détections.

Ne jamais parler d'accuracy pour désigner le Jaccard.

## 5.3 Suggestions de suivi

Après chaque réponse, proposer deux ou trois questions pertinentes.

Exemple :

Question : « Que signifie une probabilité de 0,7 ? »

Réponse : expliquer l'interprétation statistique et les limites.

Suggestions :
- Comment cette probabilité est-elle calculée ?
- Quelle est la performance du modèle ?
- Sur quelles données le modèle a-t-il été entraîné ?

Prévoir un fallback honnête lorsque la question n'est pas reconnue.

## 5.4 Frontend

Vérifie :
- affichage des réponses longues ;
- lisibilité des tableaux et paragraphes ;
- suggestions cliquables ;
- état de chargement ;
- gestion des erreurs ;
- polling correct du job asynchrone ;
- conservation de l'historique de conversation pendant la session.

Ne casse pas le fonctionnement actuel de `/api/v1/chat`.

## 5.5 Architecture future facultative

Tu peux étudier une interface `ChatProvider` avec :

- `DeterministicChat` comme fournisseur par défaut ;
- un futur `LLMChat` optionnel ;
- variable `PYROLENS_CHAT_PROVIDER`.

Mais aucun LLM ne doit être activé ou ajouté dans cette mission.

Le mode déterministe doit rester autonome.

---

# PHASE 6 — TESTS, DOCUMENTATION ET RAPPORT FINAL

## 6.1 Tests

Exécute :

`pytest tests/test_prediction.py`

Puis :

`pytest`

Enfin :

`cd frontend && npm run build`

Ajoute des tests couvrant :
- nouvelles données ;
- provenance des cellules ;
- métriques régionales ;
- absence de fuite temporelle ;
- réponses dynamiques du chatbot ;
- intentions obligatoires ;
- fallback ;
- suggestions ;
- erreurs de lecture des artefacts ;
- intégration frontend/backend.

Tous les tests doivent être verts.

Si un test échoue, identifie la cause et corrige-la sans masquer l'échec.

## 6.2 Documentation

Mets à jour :

- `docs/FIRE_RISK_PREDICTION.md`
- `docs/PROJECT_OVERVIEW.md`
- `docs/MODEL_TRAINING_COLLEAGUE.md`, si la procédure change.

Ajoute une documentation du chatbot si nécessaire.

Documente :
- pays ajoutés ;
- périodes ;
- capteurs ;
- volumes ;
- méthodes de téléchargement ;
- méthode d'entraînement ;
- métriques avant/après ;
- résultats régionaux ;
- limites ;
- procédure de reproduction.

## 6.3 Rapport final

Produis un rapport :

`docs/IMPROVEMENT_REPORT.md`

Il doit contenir :

**A. Données**
- pays et régions ajoutés ;
- années ;
- nombre de fichiers ;
- volumes téléchargés ;
- erreurs et données manquantes.

**B. Modèle**
- métriques initiales ;
- métriques finales ;
- baseline sur le même test ;
- comparaison des algorithmes ;
- résultats régionaux ;
- validation temporelle et spatiale ;
- limites restantes.

**C. Chatbot**
- intentions implémentées ;
- exemples de questions testées ;
- fonctionnement des suggestions ;
- tests frontend/backend.

**D. Qualité**
- résultats pytest ;
- résultat du build frontend ;
- fichiers modifiés ;
- éventuelles régressions.

**E. Limites**
- ce qui n'a pas pu être réalisé ;
- pourquoi ;
- ce qui nécessiterait davantage de données ou de ressources.

---

# 7. CONTRAINTES ABSOLUES

1. Ne jamais écrire que PyroLens prédit avec certitude des incendies réels.
2. Utiliser « detected fire activity » pour désigner la cible du modèle.
3. Utiliser « historical backtest » pour les résultats historiques.
4. Ne jamais qualifier le Jaccard d'accuracy.
5. Ne jamais inventer une métrique ou une donnée.
6. Ne jamais cacher une régression par rapport à la baseline.
7. Ne jamais introduire de fuite temporelle.
8. Ne jamais exposer de clé API ou de secret dans Git.
9. `FIRMS_MAP_KEY` n'est pas nécessaire pour les archives pays.
10. Ne pas modifier inutilement le moteur d'harmonisation.
11. Ne pas supprimer les fonctionnalités existantes.
12. Ne pas introduire de LLM obligatoire.
13. Ne pas télécharger massivement sans estimation préalable.
14. Ne pas paralléliser agressivement les téléchargements FIRMS.
15. Respecter le style existant : code compact, docstrings françaises et tests pytest.
16. Utiliser des commits conventionnels (`feat:`, `fix:`, `docs:`, `test:`...) avec le trailer Devin attendu par le dépôt.

---

# 8. CRITÈRE FINAL DE RÉUSSITE

La mission est terminée uniquement si :

- les nouvelles données sont réellement téléchargées et documentées ;
- le modèle est entraîné et évalué sans fuite ;
- la baseline et le modèle sont comparés sur le même test ;
- les résultats régionaux sont disponibles lorsque les données le permettent ;
- les artefacts sont régénérés et synchronisés ;
- le chatbot répond correctement aux intentions obligatoires ;
- le frontend affiche correctement les réponses ;
- les tests backend passent ;
- le build frontend passe ;
- la documentation reflète réellement l'état du projet ;
- le rapport final distingue clairement les réussites, les échecs et les limites.

**Instruction finale : privilégie la validité scientifique à l'amélioration artificielle des scores. Un modèle légèrement moins performant mais correctement évalué vaut mieux qu'un modèle affichant d'excellentes métriques obtenues avec une méthodologie fragile.**

Commence par la PHASE 1. Ne passe pas directement aux téléchargements ou aux modifications du modèle.