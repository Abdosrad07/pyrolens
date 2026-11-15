# PyroLens — Rapport scientifique de la phase 2

- Généré le : 2026-10-20T07:19:00+00:00
- Origine des données analysées : `nasa_firms`
- Période cible : 2013-01-01 → 2020-12-31

## 1. Statut des étapes

| étape | statut | preuve |
|---|---|---|
| doctor | ok | environnement inspecté |
| geo | ok | polygone administratif acquis : ne_110m_admin_0_countries.geojson |
| fixture | ok | échantillon synthétique 2019-01-01 → 2019-12-31 (4 fichiers, graine 20260101) |
| inventory | ok | CMR : versions et granules par année vérifiés (35019 granules bbox cumulés) |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | bloqué | FIRMS_MAP_KEY absent : API FIRMS inaccessible sans clé |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| audit | ok | 3 fichiers audités, 598 anomalies, origine=synthetic_fixture |
| observability | ok | états classés (détection / observabilité inconnue / indéterminé) — aucun état « pas de feu » |
| figures | ok | 3 figures générées |
| report | ok | rapport généré (DOCX: oui) |
| fixture | ok | échantillon synthétique 2019-01-01 → 2019-12-31 (4 fichiers, graine 20260101) |
| audit | ok | 3 fichiers audités, 12 anomalies, origine=synthetic_fixture |
| baselines | ok | 24 configurations comparées, origine=synthetic_fixture |
| observability | ok | états classés (détection / observabilité inconnue / indéterminé) — aucun état « pas de feu » |
| figures | ok | 5 figures générées |
| report | ok | rapport généré (DOCX: oui) |
| figures | ok | 6 figures générées |
| fixture | ok | échantillon synthétique 2019-01-01 → 2019-12-31 (4 fichiers, graine 20260101) |
| audit | ok | 3 fichiers audités, 25 anomalies, origine=synthetic_fixture |
| baselines | ok | 24 configurations comparées, origine=synthetic_fixture |
| observability | ok | états classés (détection / observabilité inconnue / indéterminé) — aucun état « pas de feu » |
| figures | ok | 6 figures générées |
| report | ok | rapport généré (DOCX: oui) |
| report | ok | rapport généré (DOCX: oui) |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 0 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 0 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 0 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 0 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 0 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 6 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 6 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 38 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 74 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 74 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 71 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 74 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 74 fichiers FIRMS acquis |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | attention | 377 nouveaux fichiers ; 580 erreurs, 0 reportés (rejouer la commande reprend l'acquisition) |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | attention | 126 nouveaux fichiers ; 8 erreurs, 514 reportés (rejouer la commande reprend l'acquisition) |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | attention | 18 nouveaux fichiers ; 25 erreurs, 401 reportés (rejouer la commande reprend l'acquisition) |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | attention | 230 nouveaux fichiers ; 0 erreurs, 198 reportés (rejouer la commande reprend l'acquisition) |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | attention | 91 nouveaux fichiers ; 0 erreurs, 99 reportés (rejouer la commande reprend l'acquisition) |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | attention | 31 nouveaux fichiers ; 0 erreurs, 62 reportés (rejouer la commande reprend l'acquisition) |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 60 nouveaux fichiers FIRMS (total session 1111 déjà présents) |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| audit | ok | 1432 fichiers audités, 2954573 anomalies, origine=nasa_firms |
| normalize | ok | 1432 → 1160 fenêtres canoniques ; 557292 doublons supprimés (comptabilité vérifiée : 5017580 = 4460288 + doublons) |
| download:geo | ok | emprise acquise (ne_110m_admin_0_countries.geojson) |
| download:firms | ok | 10 nouveaux fichiers FIRMS (total session 1161 déjà présents) |
| download:earthdata | bloqué | Redirection vers Earthdata Login : granule standard non accessible sans authentification |
| audit | ok | 1170 fichiers audités, 2634700 anomalies, origine=nasa_firms |
| baselines | ok | 24 configurations comparées, origine=nasa_firms |
| observability | ok | états classés (détection / observabilité inconnue / indéterminé) — aucun état « pas de feu » |
| figures | ok | 6 figures générées |
| report | ok | rapport généré (DOCX: oui) |

## 2. Origine et provenance

- Inventaire produit/période : voir docs/data_inventory.md
- Références bibliographiques consultées : voir docs/references.md
- Sommes de contrôle SHA-256 : enregistrées dans `data/manifests/` pour tout fichier acquis.

## 3. Audit des données

- Fichiers audités : 1170
- Satellites : Aqua, N, Terra
- Anomalies totales : 2634700
- Jours avec enregistrements : 4572

| catégorie | occurrences |
|---|---:|
| outside_emprise | 2634697 |
| duplicate_key | 3 |

> Les trous temporels listent des jours SANS ENREGISTREMENT pour un capteur. Ils ne signifient pas absence de feu, et sans produit de couverture/nuages l'observabilité reste inconnue.

## 4. Baselines calculées

- Définition des clés : `(cellule, date)` (fenêtre 1 j) ; `(cellule, fenêtre) avec fenêtre = jours_depuis_1970 // W` (W > 1)
- Configurations testées : grilles [0.1, 0.25, 0.5]° × fenêtres [1, 4, 8, 16] jours
- Configuration primaire affichée : {'grid_deg': 0.25, 'window_days': 8}

| paire | grille | fenêtre | \|A\| | \|B\| | intersection | union | Jaccard |
|---|---:|---:|---:|---:|---:|---:|---:|
| terra__aqua | 0.1 | 1 j | 49596 | 138128 | 17486 | 170238 | 0.1027 |
| terra__aqua | 0.1 | 4 j | 44432 | 114810 | 22533 | 136709 | 0.1648 |
| terra__aqua | 0.1 | 8 j | 39961 | 93329 | 24847 | 108443 | 0.2291 |
| terra__aqua | 0.1 | 16 j | 33811 | 69733 | 24602 | 78942 | 0.3116 |
| terra__aqua | 0.25 | 1 j | 39271 | 84165 | 22632 | 100804 | 0.2245 |
| terra__aqua | 0.25 | 4 j | 29204 | 54978 | 22413 | 61769 | 0.3629 |
| terra__aqua | 0.25 | 8 j | 22344 | 36858 | 18756 | 40446 | 0.4637 |
| terra__aqua | 0.25 | 16 j | 15774 | 23320 | 13794 | 25300 | 0.5452 |
| terra__aqua | 0.5 | 1 j | 27263 | 45323 | 19446 | 53140 | 0.3659 |
| terra__aqua | 0.5 | 4 j | 16327 | 24089 | 14126 | 26290 | 0.5373 |
| terra__aqua | 0.5 | 8 j | 10908 | 14746 | 9676 | 15978 | 0.6056 |
| terra__aqua | 0.5 | 16 j | 6928 | 8856 | 6219 | 9565 | 0.6502 |
| aqua__viirs_snpp | 0.1 | 1 j | 138128 | 549116 | 103750 | 583494 | 0.1778 |
| aqua__viirs_snpp | 0.1 | 4 j | 114810 | 317931 | 103069 | 329672 | 0.3126 |
| aqua__viirs_snpp | 0.1 | 8 j | 93329 | 212320 | 87418 | 218231 | 0.4006 |
| aqua__viirs_snpp | 0.1 | 16 j | 69733 | 134546 | 67040 | 137239 | 0.4885 |
| aqua__viirs_snpp | 0.25 | 1 j | 84165 | 246024 | 74656 | 255533 | 0.2922 |
| aqua__viirs_snpp | 0.25 | 4 j | 54978 | 100846 | 52818 | 103006 | 0.5128 |
| aqua__viirs_snpp | 0.25 | 8 j | 36858 | 60172 | 35727 | 61303 | 0.5828 |
| aqua__viirs_snpp | 0.25 | 16 j | 23320 | 35624 | 22719 | 36225 | 0.6272 |
| aqua__viirs_snpp | 0.5 | 1 j | 45323 | 103783 | 42371 | 106735 | 0.3970 |
| aqua__viirs_snpp | 0.5 | 4 j | 24089 | 37947 | 23346 | 38690 | 0.6034 |
| aqua__viirs_snpp | 0.5 | 8 j | 14746 | 22014 | 14287 | 22473 | 0.6357 |
| aqua__viirs_snpp | 0.5 | 16 j | 8856 | 12732 | 8574 | 13014 | 0.6588 |

> La configuration au Jaccard maximal **n'est pas** retenue : l'agrégation grossière augmente le recouvrement tout en masquant les divergences. Toutes les configurations sont publiées (`baselines/summary.csv`).

### Divergences mensuelles (configuration primaire)

| paire | mois | A seul | B seul | commune |
|---|---|---:|---:|---:|
| terra__aqua | 2012-12 | 18 | 104 | 184 |
| terra__aqua | 2013-01 | 87 | 467 | 742 |
| terra__aqua | 2013-02 | 108 | 479 | 360 |
| terra__aqua | 2013-03 | 87 | 413 | 84 |
| terra__aqua | 2013-04 | 45 | 95 | 14 |
| terra__aqua | 2013-05 | 15 | 19 | 4 |
| terra__aqua | 2013-06 | 3 | 5 | 0 |
| terra__aqua | 2013-07 | 5 | 11 | 1 |
| terra__aqua | 2013-08 | 2 | 14 | 0 |
| terra__aqua | 2013-09 | 6 | 11 | 0 |
| terra__aqua | 2013-10 | 22 | 81 | 36 |
| terra__aqua | 2013-11 | 41 | 193 | 253 |
| terra__aqua | 2013-12 | 50 | 400 | 609 |
| terra__aqua | 2014-01 | 82 | 537 | 646 |
| terra__aqua | 2014-02 | 101 | 640 | 484 |
| terra__aqua | 2014-03 | 75 | 439 | 145 |
| terra__aqua | 2014-04 | 27 | 54 | 5 |
| terra__aqua | 2014-05 | 14 | 17 | 5 |
| terra__aqua | 2014-06 | 6 | 5 | 2 |
| terra__aqua | 2014-07 | 8 | 10 | 1 |
| terra__aqua | 2014-08 | 4 | 4 | 0 |
| terra__aqua | 2014-09 | 5 | 4 | 0 |
| terra__aqua | 2014-10 | 25 | 37 | 18 |
| terra__aqua | 2014-11 | 48 | 201 | 214 |
| terra__aqua | 2014-12 | 59 | 386 | 695 |
| terra__aqua | 2015-01 | 78 | 499 | 795 |
| terra__aqua | 2015-02 | 69 | 494 | 284 |
| terra__aqua | 2015-03 | 82 | 563 | 121 |
| terra__aqua | 2015-04 | 67 | 165 | 25 |
| terra__aqua | 2015-05 | 15 | 26 | 6 |
| terra__aqua | 2015-06 | 6 | 4 | 0 |
| terra__aqua | 2015-07 | 2 | 16 | 1 |
| terra__aqua | 2015-08 | 3 | 14 | 1 |
| terra__aqua | 2015-09 | 6 | 3 | 0 |
| terra__aqua | 2015-10 | 12 | 40 | 27 |
| terra__aqua | 2015-11 | 60 | 212 | 201 |
| terra__aqua | 2015-12 | 55 | 421 | 755 |
| terra__aqua | 2016-01 | 56 | 404 | 607 |
| terra__aqua | 2016-02 | 50 | 846 | 536 |
| terra__aqua | 2016-03 | 56 | 258 | 57 |

### Divergences régionales (terciles de latitude de la bbox — proxy documenté)

| paire | région | A seul | B seul | commune |
|---|---|---:|---:|---:|
| terra__aqua | centre | 1549 | 3823 | 7878 |
| terra__aqua | nord | 671 | 1199 | 1065 |
| terra__aqua | sud | 1368 | 13080 | 9813 |
| aqua__viirs_snpp | centre | 140 | 8267 | 11585 |
| aqua__viirs_snpp | nord | 88 | 4361 | 2174 |
| aqua__viirs_snpp | sud | 903 | 11817 | 21968 |

## 5. Observabilité

- Grille : 0.25°
- Produits de couverture/nuages acquis : **False**

- **terra** : absence d'observation ou observabilité inconnue = 220382, détection observée = 39271
- **aqua** : détection observée = 84165, absence d'observation ou observabilité inconnue = 175488
- **viirs_snpp** : détection observée = 246024, absence d'observation ou observabilité inconnue = 13629

> Sans produit de couverture/nuages acquis, une cellule/jour sans détection est classée 'observabilité inconnue' et jamais 'pas de feu'.
>
> **Rappel d'interprétation** : une cellule/jour sans détection n'implique jamais l'absence de feu — seule une couverture d'observation documentée permettrait d'évoquer des conditions d'observation plausibles.

## 6. Comparaison A — Terra / Aqua

Voir tableau §4 (paire `terra__aqua`). Les deux capteurs partagent l'instrument, la résolution nominale 1 km et la famille de produit, mais diffèrent par l'heure de passage (~10 h 30 vs ~13 h 30 locales) : la comparaison journalière n'est donc pas une observation simultanée.

## 7. Comparaison B — Aqua / VIIRS Suomi-NPP 375 m

Voir tableau §4 (paire `aqua__viirs_snpp`). Différences à documenter avec les chiffres : résolution 1 km vs 375 m, géométrie de balayage (pixel scan/track variable), définition de champ (un pixel VIIRS ≠ un pixel MODIS), sémantique de confiance distincte (numérique 0-100 vs catégories low/nominal/high — non converties ici).

## 8. Sensibilité des paramètres

Grilles 0,10 / 0,25 / 0,50° et fenêtres 1 / 4 / 8 / 16 jours : intégralement publiées dans `baselines/summary.csv` et `baselines/jaccard_monthly.csv`, et visualisées dans `figures/jaccard_sensitivity.png`. Aucune fenêtre horaire n'est analysée : les champs disponibles (date + heure d'acquisition UTC par détection) ne documentent pas une couverture horaire interprétable par cellule.

## 9. Approches d'harmonisation candidates

> Statut : **aucune méthode n'est annoncée comme validée**. H1-H3 sont exécutés sur données réelles (18/10/2026) ; H4-H6 restent non exécutés (prérequis manquants, §10) — « exécuté » ≠ « validé » (docs/phase2/scientific_method.md §6).

### H1-representation — Schéma commun de colonnes normalisées (sans conversion de sens)
- **Catégorie** : harmonisation de la représentation des données
- **Hypothèse** : Une partie des écarts observés provient de différences de nommage, de formats de date/heure et d'unités explicites, pas de différences physiques.
- **Variables d'entrée** : CSV FIRMS bruts des trois capteurs, en-têtes et métadonnées de version.
- **Méthode** : Normalisation des noms de colonnes, formatage AAAA-MM-JJ + HHMM UTC, conservation des valeurs brutes de confiance et de FRP dans des colonnes distinctes.
- **Critères d'évaluation** : Taux de lignes analysables avant/après ; zéro perte non expliquée ; aucune colonne de confiance fusionnée.
- **Données de validation nécessaires** : Échantillon de fichiers réels par capteur et par année.
- **Risques de biais** : Cacher des différences réelles derrière une normalisation trop agressive.
- **Conditions d'échec** : Perte de lignes ou modification des valeurs brutes.
- **Statut des tests** : EXÉCUTÉ sur données réelles (audit du 18/10/2026, data_origin=nasa_firms) : 4 460 288 lignes bien formées, 0 ligne malformée, 0 perte non expliquée, 0 colonne de confiance fusionnée (audit.json).

### H2-spatial — Agrégation sur grille commune avec aire de cellule explicite
- **Catégorie** : harmonisation spatiale
- **Hypothèse** : Le recouvrement mesuré dépend fortement de la taille de cellule ; une grille commune avec aire documentée rend les comparaisons interpretables.
- **Variables d'entrée** : Détections lat/lon, grilles 0,10 / 0,25 / 0,50°, emprise polygonale.
- **Méthode** : Appartenance de cellule par index entier d'origine -180/-90 ; publication de l'aire des cellules et de la densité de détections par aire.
- **Critères d'évaluation** : Sensibilité du Jaccard à la maille ; stabilité des divergences régionales ; distribution spatiale des cellules actives.
- **Données de validation nécessaires** : Baselines Terra-Aqua et Aqua-VIIRS sur la période complète.
- **Risques de biais** : L'agrégation grossière augmente artificiellement le recouvrement.
- **Conditions d'échec** : Écarts qui disparaissent avec la maille sans explication géophysique.
- **Statut des tests** : EXÉCUTÉ sur données réelles (baselines du 18/10/2026) : 24 configurations publiées intégralement, sensibilité de 0,102715 à 0,658829 selon la maille et la fenêtre (baselines/summary.csv).

### H3-temporal — Fenêtres alignées (cellule, fenêtre) avec fenêtres multiples
- **Catégorie** : harmonisation temporelle
- **Hypothèse** : Les heures de passage différentes (Terra ~10h30, Aqua/S-NPP ~13h30 locales) rendent la simultanéité journalière trop stricte.
- **Variables d'entrée** : Dates d'acquisition UTC, fenêtres 1 / 4 / 8 / 16 jours alignées sur l'epoch.
- **Méthode** : Clés (cellule, fenêtre) ; comparaison des séries de Jaccard par fenêtre ; aucune fenêtre horaire tant que la documentation ne permet pas de l'interpréter.
- **Critères d'évaluation** : Décroissance attendue des divergences avec l'agrégation, quantifiée, sans sélection de la configuration maximisant le Jaccard.
- **Données de validation nécessaires** : Séries journalière/mensuelle par paire et par configuration.
- **Risques de biais** : Masker des divergences réelles par agrégation temporelle.
- **Conditions d'échec** : Écart qui croît avec la fenêtre (signe d'un biais de couverture).
- **Statut des tests** : EXÉCUTÉ sur données réelles (18/10/2026) : séries journalière et mensuelle par paire et par configuration (jaccard_monthly.csv, monthly_divergence.csv, daily_divergence.csv) ; croissance mécanique du recouvrement avec W quantifiée.

### H4-confidence — Règles de sélection par classe, SANS échelle numérique commune
- **Catégorie** : harmonisation de la confiance
- **Hypothèse** : Des seuils de sélection par classe (MODIS 0-100 / VIIRS low-nominal-high) produisent des ensembles comparables sans conversion numérique.
- **Variables d'entrée** : Colonnes confidence brutes par capteur, FRP brut, daynight.
- **Méthode** : Définition de sous-ensembles par classe native de chaque capteur, comparaison des métriques d'ensemble pour chaque combinaison de seuils.
- **Critères d'évaluation** : Stabilité du Jaccard entre combinaisons de seuils ; interprétabilité.
- **Données de validation nécessaires** : Fichiers réels avec confiance complète ; idéalement références indépendantes.
- **Risques de biais** : Étalonner les seuils sur la métrique elle-même (sur-ajustement).
- **Conditions d'échec** : Toute table de conversion numérique confiance→confiance.
- **Statut des tests** : NON EXÉCUTÉ — les confiances réelles des trois capteurs sont disponibles, mais aucune table de conversion n'est implémentée (par conception) et aucun jeu de référence indépendant n'est disponible (voir docs/phase2/decisions_to_validate.md, D5).

### H5-frp — Calibration du FRP conditionnée par la géométrie d'observation
- **Catégorie** : calibration éventuelle du FRP
- **Hypothèse** : Les écarts de FRP MODIS-VIIRS dépendent de l'angle de vue, de la taille de pixel et de l'échelle d'agrégation (Li et al., 2018), pas d'un facteur constant.
- **Variables d'entrée** : FRP brut, scan/track, angles de vue si disponibles, taille de pixel, échelle.
- **Méthode** : Modèle de régression avec covariables géométriques, entraîné sur une période et évalué sur une période distincte (séparation temporelle stricte).
- **Critères d'évaluation** : Erreur hors échantillon ; comparaison à la ligne de base constante (attendu : meilleure).
- **Données de validation nécessaires** : FRP + géométrie d'observation ; idéalement référence indépendante (pyrométrie, GT).
- **Risques de biais** : Confoundement entre taille de feu et géométrie ; saturation I4 (VIIRS).
- **Conditions d'échec** : Gain non significatif hors échantillon ou biais résiduel par angle de vue.
- **Statut des tests** : NON EXÉCUTÉ — le FRP réel est acquis, mais la géométrie d'observation (MOD03/MYD03) ne l'est pas : blocage Earthdata persistent (voir docs/phase2/decisions_to_validate.md, D4).

### H6-external-validation — Validation croisée par séparation géographique et temporelle
- **Catégorie** : validation contre références indépendantes
- **Hypothèse** : Une méthode d'harmonisation n'est crédible que si elle est évaluée sur des observations non utilisées pour l'ajustement.
- **Variables d'entrée** : Jeu de développement (années ou sous-régions) vs jeu d'évaluation.
- **Méthode** : Split temporel (ex. 2013-2016 développement / 2017-2020 évaluation) et split sud/nord de l'emprise ; rapport des métriques sur les deux jeux.
- **Critères d'évaluation** : Écart développement/évaluation < seuil défini avant tout test.
- **Données de validation nécessaires** : Données réelles multiannuelles ; références indépendantes si disponibles.
- **Risques de biais** : Fuite d'information entre jeux ; saisonnalité non représentée.
- **Conditions d'échec** : Écart important entre jeux = méthode non généralisable.
- **Statut des tests** : NON EXÉCUTÉ — les données réelles multiannuelles sont acquises depuis le 18/10/2026 ; le split développement/évaluation reste à exécuter (voir docs/phase2/implementation_plan.md, lot S4).

## 10. Blocages et accès aux données

- **FIRMS API (CSV par emprise)** — FIRMS_MAP_KEY absent : API FIRMS inaccessible sans clé (statut HTTP None, action attendue : fournir FIRMS_MAP_KEY via Settings → Environment (clé gratuite FIRMS))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))
- **Archives standard (MOD14/MYD14/VNP14IMG)** — Redirection vers Earthdata Login : granule standard non accessible sans authentification (statut HTTP 302, action attendue : fournir EARTHDATA_USER+EARTHDATA_PASSWORD ou EARTHDATA_TOKEN (ou ~/.netrc))

## 11. Valeurs de référence v0.3 (non recalculées)

- Les statistiques de concordance de l'exploratoire v0.3 (grille 0,25°, fenêtres 1 j / 8 j / 1 mois) **ne sont pas fournies dans cet environnement** : le dépôt est vide de résultats antérieurs. Elles ne sont donc **ni reprises ni recalculées** ici ; pour les comparer, fournir les CSV v0.3 (voir README §« Comparer avec v0.3 »).
- La tendance annoncée (recouvrement spatial croissant avec l'agrégation temporelle) reste **une observation exploratoire**, non une démonstration d'équivalence physique des capteurs ni la validation d'un algorithme d'harmonisation.

## 12. Limites

- Données d'exécution non réelles tant que les credentials ne sont pas fournis.
- Aucun produit de couverture/nuages acquis : l'état « absence de détection en conditions d'observation plausibles » n'est **jamais** attribué.
- Aucune conversion de confiance MODIS↔VIIRS, aucune calibration FRP constante.
- Découpage régional = terciles de latitude de la bbox (proxy), pas des limites administratives.
