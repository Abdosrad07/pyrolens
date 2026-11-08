# Couverture des fonctionnalités — PyroLens

**Cadre de référence** : la liste consolidée des fonctionnalités prévues (modules Overview, Harmonization Lab, Fire Calendar, Data & Methodology, complémentaires) transmise le 2026-11-08.

**Règle d'évaluation** : une fonctionnalité n'est considérée couverte que si elle apparaît dans le code, les tests et les artefacts du dépôt. Aucune maquette ou intention ne suffit.

## Tableau récapitulatif par module

| Module | Total IDs | Couvert (implémenté) | Partiel | Absent |
|---|---|---|---|---|
| Overview (OV-01 à OV-08) | 8 | 4 (OV-01, OV-02, OV-06, OV-07) | 1 (OV-08) | 3 (OV-03, OV-04, OV-05) |
| Harmonization Lab (HL-01 à HL-14) | 14 | 9 (backend HL-03..HL-09, HL-13, HL-14) | 1 (HL-11) | 4 (HL-01, HL-02, HL-10, HL-12) |
| Fire Calendar (FC-01 à FC-08) | 8 | 0 (données présentes, pas d'UI) | 0 | 8 |
| Data & Methodology (DM-01 à DM-08) | 8 | 8 | 0 | 0 |
| Complémentaires (EX-01 à EX-09) | 9 | 1 (EX-01 via API `/export`) | 0 | 8 |
| **Total** | **47** | **22** | **2** | **23** |

## 1. Module Overview — Tableau de bord

| ID | Fonctionnalité | État | Preuve dans le dépôt | Écart | Action nécessaire | Priorité |
|---|---|---|---|---|---|---|
| OV-01 | Vue d'ensemble | ✅ Couvert | `web/src/views/Overview.jsx` + `Landing.jsx` : synthèse d'exécution, étapes, origine des données | — | — | — |
| OV-02 | Statistiques générales | ✅ Couvert | `Overview.jsx` : cartes "Étapes exécutées", "Blocages documentés", "Fichiers téléchargés", "Période cible" | — | — | — |
| OV-03 | Carte des points chauds | ❌ Absent | Aucune carte géographique dans le frontend | Pas de visualisation géographique des détections | Implémenter une carte sur les détections FIRMS | P2 |
| OV-04 | Filtrage géographique | ❌ Absent | Aucun filtre géographique côté front ; le filtrage se fait côté pipeline (emprise polygonale) | L'utilisateur ne peut pas filtrer la zone à l'écran | Ajouter un sélecteur de zone / emprise dans Overview | P2 |
| OV-05 | Filtrage temporel | ❌ Absent | Aucun sélecteur de période côté front ; la période est fixée à 2013-2020 dans `pipeline.yaml` | L'utilisateur ne peut pas restreindre la période affichée | Ajouter un sélecteur de dates dans Overview | P2 |
| OV-06 | Comparaison des capteurs | ✅ Couvert | `web/src/views/Baselines.jsx` : filtre par paire (terra__aqua, aqua__viirs_snpp), Jaccard par paire | — | — | — |
| OV-07 | Informations sur les données | ✅ Couvert | `Overview.jsx` : inventaire FIRMS/CMR, manifeste SHA-256, période, origine `data_origin` | — | — | — |
| OV-08 | Indicateurs scientifiques | ⚠️ Partiel | `Baselines.jsx` affiche le Jaccard ; `Overview.jsx` affiche les comptages | Pas de tableau d'indicateurs scientifiques dédiés | Créer un bloc d'indicateurs clés sur l'accueil (S1.5) | P1 |

## 2. Module Harmonization Lab — Laboratoire d'harmonisation (partie 1)

| ID | Fonctionnalité | État | Preuve dans le dépôt | Écart | Action nécessaire | Priorité |
|---|---|---|---|---|---|---|
| HL-01 | Sélection des données | ❌ Absent | Aucune UI pour choisir les jeux de données ; le choix se fait par `source` paramètre de l'API | Pas d'interface de sélection | Créer une vue de sélection source (raw/fixture/auto) | P0 |
| HL-02 | Configuration des capteurs | ❌ Absent | Aucune UI pour sélectionner les capteurs à comparer ; fixé par `pair` dans l'API | Pas d'interface de configuration paire | Ajouter un sélecteur de paire (terra__aqua, aqua__viirs_snpp) | P0 |
| HL-03 | Nettoyage des données | ✅ Couvert (backend) | `src/pyrolens/audit.py` : détection anomalies, traçabilité ligne/colonne/valeur brute ; `audit.json` | Pas d'UI dédiée, mais le moteur existe | Exposer les résultats d'audit via l'UI Audit (déjà fait) | — |
| HL-04 | Normalisation | ✅ Couvert (backend) | `src/pyrolens/grids.py`, `src/pyrolens/baselines.py` : schéma commun, clés `(cellule, date)` / `(cellule, fenêtre)` | Pas d'UI dédiée | — | — |
| HL-05 | Harmonisation spatiale | ✅ Couvert (backend) | `grids.py` : grilles 0,10 / 0,25 / 0,50° ; `baselines.py` : sensibilité publiée | Pas d'UI dédiée | — | — |
| HL-06 | Harmonisation temporelle | ✅ Couvert (backend) | `grids.py` : fenêtres 1 / 4 / 8 / 16 jours alignées sur l'epoch | Pas d'UI dédiée | — | — |
| HL-07 | Agrégation | ✅ Couvert (backend) | `baselines.py` : ensembles de clés, intersection, union, Jaccard | Pas d'UI dédiée | — | — |
| HL-08 | Configuration expérimentale | ✅ Couvert (backend API) | `POST /api/v1/experiments` : `pair`, `grid_deg`, `window_days`, `source` | Pas d'UI de saisie | Créer un formulaire de configuration d'expérience | P0 |
| HL-09 | Exécution | ✅ Couvert (backend API) | `POST /api/v1/experiments` → job `queued` → `running` → `succeeded`/`failed` ; `api/jobs.py` | Pas d'UI de lancement | Ajouter un bouton "Lancer l'expérience" et suivi de statut | P0 |

| HL-10 | Comparaison avant/après | ❌ Absent | Aucune vue comparant observations originales vs harmonisées | Pas de visualisation avant/après | Implémenter une vue de comparaison des ensembles | P1 |
| HL-11 | Calcul des métriques | ⚠️ Partiel | `baselines.py` calcule Jaccard, n_a, n_b, intersection, union ; `api/services/experiments.py` réutilise le même moteur | Pas d'UI affichant les métriques d'une expérience lancée | Afficher `result.result.jaccard` dans l'UI Harmonization Lab | P1 |
| HL-12 | Visualisation des résultats | ❌ Absent | Aucune carte/graphique/tableau des résultats d'expérience dans le frontend | Pas de visualisation des résultats d'harmonisation | Créer des vues de résultats (cartes, graphiques, tableaux) | P1 |
| HL-13 | Historique des expériences | ✅ Couvert (backend) | `GET /api/v1/experiments` liste les tâches ; résultats persistés dans `PYROLENS_EXPERIMENTS_DIR` | Pas d'UI d'historique | Ajouter une liste des expériences passées | P2 |
| HL-14 | Traçabilité | ✅ Couvert (backend) | Chaque résultat d'expérience porte `params`, `data_origin`, `source.digest_sha256`, `software`, `started_at/finished_at` | Pas d'UI de traçabilité | Afficher la provenance dans la vue résultat | P2 |

## 3. Module Fire Calendar — Calendrier des feux

| ID | Fonctionnalité | État | Preuve dans le dépôt | Écart | Action nécessaire | Priorité |
|---|---|---|---|---|---|---|
| FC-01 | Calendrier quotidien | ❌ Absent | Les séries quotidiennes sont dans `baselines.json` (`daily`) mais sans vue dédiée | Pas de calendrier quotidien | Créer une vue Fire Calendar avec agrégation quotidienne | P1 |
| FC-02 | Calendrier hebdomadaire | ❌ Absent | Pas d'agrégation hebdomadaire dédiée ; seules les fenêtres 1/4/8/16 j existent | Pas de vue hebdomadaire | Ajouter une agrégation hebdomadaire dans Fire Calendar | P1 |
| FC-03 | Calendrier mensuel | ❌ Absent | `baselines.json` contient `jaccard_monthly` et `monthly_divergence` mais sans vue dédiée | Pas de vue mensuelle | Créer une vue mensuelle à partir des séries existantes | P1 |
| FC-04 | Identification des périodes actives | ❌ Absent | Aucune détection automatique de périodes d'activité forte | Pas d'alerte ou de surlignage de périodes actives | Ajouter un repérage des périodes à forte activité | P2 |
| FC-05 | Évolution temporelle | ❌ Absent | Les séries existent dans les artefacts mais sans visualisation dédiée | Pas de graphique d'évolution temporelle | Créer un graphique de tendance (Recharts) | P1 |
| FC-06 | Comparaison des capteurs | ❌ Absent | Les données par paire existent mais sans vue Fire Calendar dédiée | Pas de comparaison capteurs dans le calendrier | Ajouter un sélecteur de paire dans Fire Calendar | P1 |
| FC-07 | Visualisation observations originales vs harmonisées | ❌ Absent | Aucune vue distinguant données originales et harmonisées | Pas de distinction visuelle | Ajouter un toggle original/harmonisé | P2 |
| FC-08 | Analyse de la FRP | ❌ Absent | Le FRP est collecté dans l'audit mais sans analyse temporelle dédiée | Pas de vue FRP dans le calendrier | Ajouter un graphique d'évolution du FRP | P2 |

## 4. Module Data & Methodology — Données et méthodologie

| ID | Fonctionnalité | État | Preuve dans le dépôt | Écart | Action nécessaire | Priorité |
|---|---|---|---|---|---|---|
| DM-01 | Catalogue des données | ✅ Couvert | `GET /api/v1/catalog` ; `data/manifests/downloads.json` ; `inventory.json` | — | — | — |
| DM-02 | Sources des données | ✅ Couvert | `config/pipeline.yaml` (`sensors.terra`, `sensors.aqua`, `sensors.viirs_snpp`) ; `docs/data_inventory.md` | — | — | — |
| DM-03 | Métadonnées | ✅ Couvert | `audit.json` par fichier (header, n_records, date_min/max, sensor, version) | — | — | — |
| DM-04 | Qualité des données | ✅ Couvert | `src/pyrolens/audit.py` ; `audit.json` (anomalies par catégorie, gaps temporels) | — | — | — |
| DM-05 | Méthodologie | ✅ Couvert | `docs/methodology.md` : clés d'ensemble, ordre des analyses, métriques, reproductibilité | — | — | — |
| DM-06 | Documentation scientifique | ✅ Couvert | `docs/phase2/` (9 fichiers) ; `reports/scientific_report.md` | — | — | — |
| DM-07 | Limites scientifiques | ✅ Couvert | `docs/limitations.md` ; `docs/methodology.md` §10 | — | — | — |
| DM-08 | Reproductibilité | ✅ Couvert | `config/pipeline.yaml` versionné ; `data/raw` immuable (SHA-256) ; `python3 -m pytest` | — | — | — |

## 5. Fonctionnalités complémentaires

| ID | Fonctionnalité | État | Preuve dans le dépôt | Écart | Action nécessaire | Priorité |
|---|---|---|---|---|---|---|
| EX-01 | Export des résultats en CSV | ⚠️ Partiel | `GET /api/v1/export` existe (CSV/JSON) mais pas de bouton d'export dans l'UI | Pas de bouton d'export côté frontend | Ajouter un bouton d'export dans Baselines (S1.4) | P1 |
| EX-02 | Export des graphiques | ❌ Absent | Aucune fonction d'export des figures côté front | Pas d'export PNG depuis l'UI | Ajouter un téléchargement des figures | P2 |
| EX-03 | Génération de rapports d'expérience | ❌ Absent | Le rapport global existe (`pyrolens report`) mais pas par expérience | Pas de rapport par job d'expérience | Générer un rapport Markdown par expérience | P2 |
| EX-04 | Historique détaillé des analyses | ❌ Absent | L'API liste les jobs mais sans UI détaillée | Pas d'UI d'historique détaillé | Ajouter une page d'historique des expériences | P2 |
| EX-05 | Gestion de plusieurs utilisateurs | ❌ Absent | `Auth.jsx` simulé (sessionStorage) ; pas de backend comptes | Pas de multi-utilisateurs | À envisager post-MVP (D6) | Future |
| EX-06 | Ingestion automatique des données | ❌ Absent | `pyrolens download` est manuel ; pas d'ingestion planifiée | Pas d'automatisation | À envisager post-MVP (EX-06) | Future |
| EX-07 | Extension à d'autres pays | ❌ Absent | `pipeline.yaml` : seule la région Cameroun (ISO3 CMR) est configurée | Pas de sélecteur de pays | À envisager post-MVP (EX-07) | Future |
| EX-08 | Traitement de volumes plus importants | ❌ Absent | L'API est limitée (1 thread, cache 30 s, max 20 jobs) | Pas de montée en charge | À envisager post-MVP (EX-08) | Future |
| EX-09 | Validation externe des résultats | ❌ Absent | H4/H6 non exécutés (pas de référence indépendante) | Pas de validation externe | À traiter en S4 (D5 validée) | P0 |

## 6. Mapping fonctionnalités → lots de développement

| Lot | Fonctionnalités couvertes | Statut |
|---|---|---|
| **S0** (fait) | DM-01 à DM-08, HL-03 à HL-07 (moteur backend), D1, D8 | ✅ Terminé |
| **S1** (en cours) | OV-08 (indicateurs, S1.5), EX-01 (export, S1.4), OV-01/OV-02 (S1.5) | ⏳ 1.1 fait ; 1.2 à 1.7 restants |
| **S2** | D2 (API statique validée) ; bascule front↔API si besoin | ⏳ Go/no-go fin S1 |
| **S3** (après D4) | OV-03 (carte), OV-04 (filtre géo), OV-05 (filtre temporel) | ⏳ Bloqué par Earthdata |
| **S4** (après D5) | HL-01, HL-02 (UI sélection/config), HL-08/HL-09 (UI exécution), HL-10/HL-11/HL-12 (UI résultats), HL-13/HL-14 (UI historique/traçabilité), FC-01 à FC-08, EX-09 | ⏳ Bloqué par D4/D5 |

## 7. Conclusion : ce qui doit absolument fonctionner (scénario MVP)

Pour considérer PyroLens comme un MVP techniquement crédible, le scénario suivant doit être démontrable :

1. L'utilisateur accède aux données MODIS Terra, Aqua et VIIRS (OV-07, DM-01/DM-02 — ✅).
2. Il consulte leurs caractéristiques et leur qualité (OV-02, DM-04 — ✅).
3. Il sélectionne deux jeux de données à comparer (HL-01, HL-02 — ❌ UI manquante).
4. Il configure les paramètres spatiaux et temporels (HL-08 — ❌ UI manquante).
5. Il lance une expérience d'harmonisation (HL-09 — ❌ UI manquante).
6. Le backend traite réellement les données (HL-03 à HL-07 — ✅ backend prêt).
7. Le système calcule les métriques de comparaison (HL-11 — ✅ backend prêt, UI manquante).
8. L'utilisateur visualise les résultats avant et après harmonisation (HL-10, HL-12 — ❌ UI manquante).
9. Il consulte les résultats sur une carte et dans le Fire Calendar (OV-03, FC-01 à FC-08 — ❌ UI manquante).
10. Il peut retrouver la configuration et la provenance des résultats (HL-13, HL-14, DM-08 — ✅ backend prêt, UI partielle).

**Priorité absolue** : combler les écrans manquants du Harmonization Lab (HL-01, HL-02, HL-08, HL-09, HL-10, HL-11, HL-12) et du Fire Calendar (FC-01 à FC-08), car c'est le cœur scientifique du défi NASA. Le backend est déjà prêt ; il manque les interfaces.

**Ce document est le cadre de référence.** Aucune fonctionnalité de cette liste ne sera laissée de côté sans décision explicite.
