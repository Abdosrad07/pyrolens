# Méthodologie — PyroLens phase 2

Ce document définit **comment** les chiffres sont produits, avant de les interpréter.
Il fait foi pour relire les sorties de `baselines/`, `reports/` et `figures/`.

---

## 1. Question de recherche et non-objectifs

**Question** : dans quelle mesure les détections de points chauds de MODIS Terra,
MODIS Aqua et VIIRS Suomi-NPP 375 m se recouvrent-elles spatialement et temporellement
sur le Cameroun 2013-2020, et comment ce recouvrement dépend-il des paramètres
d'analyse ?

**Non-objectifs (interdits par conception)** :
- démontrer l'équivalence physique des capteurs ;
- valider un algorithme d'harmonisation (aucune méthode n'est annoncée validée) ;
- conclure « absence de feu » à partir d'une absence de détection ;
- choisir la configuration qui maximise le Jaccard ;
- convertir les niveaux de confiance MODIS et VIIRS sur une échelle numérique commune ;
- appliquer un facteur constant de correction du FRP ;
- comparer naïvement des lignes individuelles comme observations simultanées d'un même feu.

## 2. Clés d'ensemble (définitions exactes)

Implémentation : `src/pyrolens/grids.py`.

- **Cellule** : index entier `i = floor(round((lon + 180)/g, 9))`,
  `j = floor(round((lat + 90)/g, 9))`, origine `(-180, -90)`, maille `g ∈ {0,10° ; 0,25° ; 0,50°}`.
  L'arrondi à 1e-9 neutralise l'erreur binaire : sans lui, un point exactement sur une
  frontière de cellule changerait de cellule selon la représentation du pas.
  Représentation de la clé : `i:j`.
- **Fenêtre de 1 jour** → clé = **`(cellule, date)`**, format `i:j|AAAA-MM-JJ`.
- **Fenêtre de W jours (W ∈ {4, 8, 16})** → clé = **`(cellule, fenêtre)`**, format `i:j|wK`,
  avec `K = jours_depuis_1970 // W` (alignement sur l'epoch, **pas** sur le mois).
  L'alignement est explicite car il décale les bornes des fenêtres par rapport aux mois
  calendaires ; `window_start()` reverse la clé en date pour l'affichage.
- **Ensemble d'un capteur** = ensemble **sans doublon** des clés pour lesquelles le capteur
  possède au moins une détection dans l'emprise.

Conséquence : une même cellule et deux dates d'une même fenêtre produisent une clé unique ;
le recouvrement augmente donc mécaniquement avec W — c'est **exactement** l'effet à
quantifier (et à ne pas prendre pour une amélioration de la mesure).

## 3. Ordre des analyses (imposé)

1. **A. Terra – Aqua** : même instrument, même résolution nominale (1 km), mêmes familles
   de produit ; divergences d'heure de passage (~10 h 30 vs ~13 h 30 locales) documentées.
2. **B. Aqua – VIIRS S-NPP** : ajoute les différences de résolution (1 km vs 375 m),
   de géométrie de balayage (scan/track variables), de définition de champ et de
   sémantique de confiance.
3. **C. Sensibilité des paramètres** : grilles × fenêtres, publiées intégralement.

Paires définies dans `config/pipeline.yaml` (`analysis.pairs`), sélecteur de lignes :
`kind` (`modis`/`viirs`) **et** `satellite` (`Terra` / `Aqua` / `N` — le pilote exclut
NOAA-20 `1` et NOAA-21 `2`, explicitement).

## 4. Métriques calculées

Pour chaque paire et chaque configuration `(g, W)` — implémentation `src/pyrolens/baselines.py` :

| Métrique | Définition |
|---|---|
| `n_a`, `n_b` | tailles des ensembles A et B |
| `intersection` | `|A ∩ B|` |
| `union` | `|A ∪ B|` |
| `jaccard` | `|A ∩ B| / |A ∪ B|`, 0 si union vide |
| divergence mensuelle | clés A seulement, B seulement, communes, regroupées par mois (via `window_start` pour W > 1) |
| divergence journalière | même chose en `(cellule, date)` (fenêtre 1 jour) |
| distribution spatiale | effectifs A/B par cellule (centres de cellule fournis) |
| divergence régionale | terciles de latitude de la bbox : sud / centre / nord |

Sorties : `baselines/summary.csv` (24 configurations = 2 paires × 3 grilles × 4 fenêtres),
`jaccard_monthly.csv`, `daily_divergence.csv`, `monthly_divergence.csv`,
`spatial_distribution.csv`, `regional_divergence.csv`, `baselines.json`.

**Régions** : les terciles de latitude de la bbox sont un **proxy documenté**, pas des
limites administratives. Elles servent à localiser les divergences, pas à les expliquer.

**Sélection** : aucune configuration n'est retenue sur la valeur du Jaccard. La figure
`figures/jaccard_sensitivity.png` et `baselines/summary.csv` publient la totalité des
combinaisons, croissances comprises.

**Fenêtres horaires** : **non analysées**. Les champs disponibles (`acq_date`, `acq_time`
en UTC par détection) ne documentent pas une couverture horaire par cellule : comparer des
heures de passage reviendrait à comparer des instants d'overpass différents sans info de
couverture. Une telle analyse exige d'abord des produits d'observation (MOD09GA/MOD03).

## 5. Observabilité : stratégie à 4 états

Implémentation `src/pyrolens/observability.py`.

| État | Condition | Disponible aujourd'hui ? |
|---|---|---|
| `detection_observed` | ≥ 1 détection du capteur pour (cellule, jour) | oui |
| `no_detection_plausible_conditions` | aucune détection **et** produit de couverture documentant une observation avec ciel exploitable | **non** (aucun produit de couverture acquis) |
| `unknown_observability` | aucune détection **et** aucune information de couverture → **état par défaut** | oui (par défaut) |
| `indeterminate` | couverture présente mais état d'observation ambigu (nuage/incertitude) | non |

Règles :
- l'état par défaut est `unknown_observability` tant que
  `observability.coverage_products_acquired = false` dans la configuration ;
- aucun état, libellé ou texte de sortie ne contient « pas de feu » (test
  `tests/test_observability.py`) ;
- le rapport répète le mémorandum : *une cellule/jour sans détection n'implique jamais
  l'absence de feu*.

## 6. Plan d'acquisition des produits d'observabilité (non encore acquis)

Par tuiles/périodes, pour limiter le poids, avec les mêmes manifestes SHA-256 :

1. **Géométrie d'observation** : `MOD03` / `MYD03` (angles soleil/satellite, géolocalisation)
   — période restreinte d'abord (ex. un an pilote), car conditionne l'interprétation du FRP.
2. **Couverture d'observation** : `MOD09GA` (observation coverage/number, QA) par jour,
   extrait sur la bbox uniquement.
3. **Nuages** : `MOD35_L2` / `MYD35_L2` (confiance ciel clair).
4. **Côté VIIRS** : les masques/qualité VIIRS proviennent d'un produit **différent**
   (bandes VIIRS, définitions distinctes) : **ils ne sont pas interchangeables** avec
   `MOD35_L2` ; les deux doivent être portés comme variables séparées avec leur propre
   sémantique, jamais fusionnés en un « masque de nuages unique ».

Tant que (1)-(3) ne sont pas acquis, la colonne de couverture reste vide et l'état par
défaut demeure `unknown_observability`.

## 7. Audit de données : politiques

Implémentations `src/pyrolens/ingest.py`, `src/pyrolens/audit.py`.

- **Conservation du brut** : les lignes ne sont jamais réécrites ; chaque anomalie conserve
  fichier, numéro de ligne physique, colonne, valeur brute, catégorie, motif, classe.
- **Coordonnées** : une latitude/longitude non numérique ou hors plage est **exclue**,
  jamais « corrigée » parce qu'une autre valeur paraîtrait plus plausible.
  Un point valide mais hors emprise est classé *ambigu* : conservé, tracé, exclu des ensembles.
- **Reconstruction** : table de règles vide par défaut (`config/pipeline.yaml → reconstruction.rules`).
  Toute reconstruction doit être démontrable (fichier, colonne, motif, justification) ;
  à ce stade, **0 ligne reconstruite**.
- **Déduplication** : pour les ensembles uniquement, en conservant la première occurrence ;
  les doublons restent tracés (`duplicate_row`, `duplicate_key`).
- **FRP** : valeur négative ou non numérique → anomalie, `frp = None` (jamais remplacée).
- **Confiance** : validée par sémantique de capteur (MODIS 0-100 ou classes legacy ;
  VIIRS low/nominal/high), **jamais convertie**.
- **Trous temporels** : jours sans enregistrement dans la plage couverte du capteur,
  libellés `aucun_enregistrement`, jamais « pas de feu ».
- **Immuabilité de `data/raw`** : vérifiée par test (SHA-256 avant/après exécution complète,
  `tests/test_reproducibility.py`).

## 8. Séparation développement / évaluation (pour la phase d'harmonisation)

À appliquer **avant** tout ajustement d'une méthode candidate :

- **split temporel** : développement 2013-2016, évaluation 2017-2020 ;
- **split géographique complémentaire** : sud vs nord du polygon (terciles de latitude),
  pour détecter un biais régional ;
- les métriques d'évaluation sont calculées sur le jeu d'évaluation **seul**, et le jeu de
  développement ne sert qu'à régler les paramètres ;
- tout écart important entre les deux jeux = condition d'échec déclarée (voir
  `harmonization.py`, entrées H4-H6).

## 9. Reproductibilité

- configuration versionnée : `config/pipeline.yaml` (aucun secret) ;
- graine déterministe du fixture : `20260101` (testé : bits identiques) ;
- commandes : voir `README.md` ;
- journaux : `reports/logs/*.log` ; historique d'exécution :
  `web/public/artifacts/execution.json` (étapes, statuts, blocages, codes HTTP) ;
- provenance : `data/manifests/*.json` (URL, code HTTP, octets, SHA-256, horodatage) ;
- tests : `python3 -m pytest` (31 tests) ;
- environnement : `requirements.txt`, Python 3.10.12 constaté (cible 3.10+).

## 10. Limites méthodologiques actuelles

1. Détections FIRMS réelles acquises (2013-2020, `data_origin = nasa_firms`) ; les
   sorties de démonstration restent identifiables par `data_origin = synthetic_fixture`.
2. Aucun produit d'observabilité → impossibilité d'attribuer l'état
   « absence de détection en conditions d'observation plausibles ».
3. Emprise 110 m (frontières simplifiées).
4. Comparaisons ensembles/clés : aucune mise en correspondance événement-à-événement
   (non demandée à ce stade, et non justifiable sans géométrie d'observation).
5. Pas de référence indépendante (registres au sol, autres capteurs) dans l'environnement :
   la validation externe (H6) reste conditionnée à l'acquisition de telles données.
