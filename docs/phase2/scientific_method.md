# Méthode scientifique — protocole d'harmonisation (phase 2)

**Rôle de ce document** : fixer le protocole — hypothèses, preuves exigées, règles de
décision — avant tout calcul supplémentaire. `docs/methodology.md` fait foi pour **comment**
les chiffres sont produits ; ce document fait foi pour **ce qu'on peut en conclure**.
Statut global : **aucune méthode d'harmonisation n'est annoncée comme validée** (§7).

---

## 1. Question de recherche et cadre

Question (inchangée, `docs/methodology.md` §1) : recouvrement spatial et temporel des
détections MODIS Terra, MODIS Aqua et VIIRS S-NPP 375 m sur le Cameroun 2013-2020, et
sensibilité de ce recouvrement aux paramètres d'analyse.

Ce que la phase 2 **n'est pas** : une démonstration d'équivalence physique des capteurs, ni la
validation d'un algorithme, ni un outil d'alerte (aucune sortie n'interprète une absence de
détection comme une absence de feu).

## 2. Chaîne de preuve

```
données brutes immuables (data/raw, SHA-256)
  → audit (comptabilité des lignes, anomalies tracées ligne à ligne)
    → ensembles (clés (cellule, date|fenêtre), grilles × fenêtres)
      → baselines (24 configurations publiées intégralement)
        → interprétation (soumise aux règles §5 et §6)
```

Chaque affirmation du rapport doit remonter à un artefact horodaté
(`reports/`, `baselines/`, `web/public/artifacts/`) — voir `docs/phase2/data_validation.md` §7
pour la liste des affirmations confirmées/infirmées.

## 3. Hypothèses du catalogue (`src/pyrolens/harmonization.py`)

| ID | Hypothèse | Données requises | Statut au 20/10/2026 |
|---|---|---|---|
| H1 | schéma commun de colonnes **sans conversion de sens** réduit les écarts de forme (pas de physique) | CSV réels des 3 capteurs | **exécuté sur données réelles** : 4 460 288 lignes bien formées, 0 perte non expliquée, 0 colonne de confiance fusionnée (`audit.json`) |
| H2 | le recouvrement dépend fortement de la maille ; une grille commune avec aire publiée rend la comparaison interprétable | baselines multi-grilles | **exécuté sur données réelles** : 24 configurations, sensibilité publiée (`baselines/summary.csv`) |
| H3 | les fenêtres multiples (1/4/8/16 j) captent l'effet des heures de passage différentes | séries temporelles multi-fenêtres | **exécuté sur données réelles** : séries journalière/mensuelle par paire (`jaccard_monthly.csv`, `monthly_divergence.csv`) |
| H4 | seuils par **classe native** (MODIS 0-100 / VIIRS l-n-h) sans échelle numérique commune | confiances réelles + références | **non exécuté** — données de confiance disponibles, jeu de référence absent |
| H5 | calibration du FRP conditionnée par la géométrie d'observation (pas de facteur constant) | FRP + angles/pixels | **non exécuté** — bloqué : géométrie d'observation non acquise (Earthdata) |
| H6 | une méthode n'est crédible que sur des observations non utilisées à l'ajustement | splits dév/éval | **non exécuté** — données réelles disponibles depuis le 18/10 ; exécution planifiée (S4) |

## 4. Séparation développement / évaluation (imposée avant tout réglage)

- **Split temporel** : développement 2013-2016, évaluation 2017-2020.
- **Split géographique complémentaire** : sud vs nord (terciles de latitude de l'emprise).
- Les métriques d'évaluation sont calculées sur le jeu d'évaluation **seul** ; le jeu de
  développement ne sert qu'à régler des paramètres.
- Toute fuite entre jeux (choix de seuil, de maille ou de fenêtre après coup sur le jeu
  d'évaluation) invalide le résultat.

## 5. Règles de décision

1. **Aucune sélection par valeur de Jaccard.** Toutes les configurations sont publiées ;
   on explique la sensibilité, on ne choisit pas la combinaison favorable.
2. **Aucune conversion numérique de confiance** MODIS ↔ VIIRS (H4 : classes natives only).
3. **Aucun facteur constant de correction du FRP** (H5 : covariables géométriques ou rien).
4. **Jamais « pas de feu »** : absence de détection = `aucun_enregistrement` ou
   `observabilité inconnue` tant que `coverage_products_acquired = false`.
5. **Aucune reconstruction de données** : `config/pipeline.yaml → reconstruction.rules`
   reste vide (0 ligne reconstruite) ; lat/lon invalides exclus, jamais « corrigés ».
6. **Pas de comparaison d'heures de passage** tant que la géométrie d'observation manque.
7. **Pas d'appariement événement-à-événement** : les comparaisons portent sur des ensembles
   de clés, jamais sur la prétention que deux lignes sont le même feu.

## 6. Ce qui compte comme validation (critères d'acceptation d'une approche)

Une entrée du catalogue passe à « exécutée » seulement si :

1. exécution **sur données réelles** (`data_origin = nasa_firms`) et artefact horodaté produit ;
2. comptabilité des lignes vérifiée (équation imposée par le code) ;
3. jeu d'évaluation **non touché** pendant le réglage (§4) ;
4. conditions d'échec de l'entrée respectées (sinon : échec assumé, publié tel quel) ;
5. résultats reportés intégralement (y compris les configurations défavorables) ;
6. reproductible par une commande unique documentée (`README.md` §2).

« Exécutée » ≠ « validée » : la validation complète exige en plus les données d'H4-H6
(références indépendantes, géométrie d'observation).

## 7. Statut au 20/10/2026

- **Faits établis** (données réelles, artefacts 18-19/10) : recouvrement très sensible à la
  maille et à la fenêtre (0,10 → 0,66 selon configuration, `data_validation.md` §6) ;
  observabilité inconnue pour la majorité des capteur-cellule-jours.
- **Non établi** : toute équivalence des capteurs, toute règle de seuil, toute calibration
  FRP, toute généralisation temporelle/régionale (H4-H6 non exécutés).
- Les statuts vivants sont ceux de `src/pyrolens/harmonization.py` (rendus dans le rapport
  §9) ; toute mise à jour de statut doit être accompagnée de la régénération du rapport
  (`pyrolens report && pyrolens web-artifacts`).
