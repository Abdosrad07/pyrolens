# Plan d'implémentation — phase 2

Lots ordonnés, chaque tâche avec **livrable**, **critère d'acceptation**
(`validation_plan.md`) et **commande de vérification**. Un lot ne démarre que si les
décisions qui le conditionnent sont tranchées (`decisions_to_validate.md`).

---

## S0 — Documentation et sincérité des livrables (20/10/2026)

| Tâche | Livrable | Critère d'acceptation |
|---|---|---|
| Vérification des annonces de phase 1 | `docs/phase2/data_validation.md` §7 | 31/31 tests confirmés ; « 12 lignes malformées » et Jaccard 0,263/0,777/0,310/0,789 infirmés et remplacés par les artefacts réels |
| Rapport A (provenance, fichiers, aberrations) | idem, §1-§6 | comptes recalculés sur disque et conformes aux manifests |
| Dossier complet phase 2 | 9 fichiers dans `docs/phase2/` | chacun référencé depuis les autres sans contradiction |
| Statuts H1-H3 alignés sur l'exécution réelle | `src/pyrolens/harmonization.py` + rapport régénéré + `web-artifacts` | le rapport §9 ne dit plus « NON EXÉCUTÉ sur données réelles » pour H1-H3 ; `pytest` 31/31 ; build OK |
| Recoupement docs ↔ artefacts | README, `docs/*.md` vs JSON horodatés | aucune valeur orpheline restante |

**Commandes** : `python3 -m pytest` · `PYTHONPATH=src python3 -m pyrolens report` ·
`PYTHONPATH=src python3 -m pyrolens web-artifacts` · `npm --prefix web run build`.

## S1 — MVP (après validation de D1 ; D2 tranchée en fin de lot)

| # | Tâche | Livrable | Critère d'acceptation |
|---|---|---|---|
| 1.1 | Exclure `downloads.json` (5,9 Mo) du chargement initial, publier un agrégat `downloads_summary.json` (nb requêtes, octets, statuts, SHA-256 de synthèse — **sans chemins absolus**) | artefact + `data.js` | chargement initial < 2 Mo ; manifeste complet reste disponible sur disque |
| 1.2 | Table intégrale des 24 configurations (P1-4) | vue `Baselines` | toutes les lignes de `summary.csv` affichées, aucun filtre imposé |
| 1.3 | Liens ancrés de configuration (P1-3) | `Baselines.jsx` | recharger l'URL restaure la sélection |
| 1.4 | Export CSV/JSON de la vue active (P1-2) | bouton d'export | fichier exporté = lignes affichées (recoupement) |
| 1.5 | Écran d'accueil décideur (P1-5) | vue d'accueil | 4-5 chiffres = artefacts, renvoi vers les vues |
| 1.6 | Nettoyage des 252 CSV d'anomalies orphelins (restes de l'audit pré-normalisation) + purge du répertoire avant écriture dans `pyrolens audit` | code + `reports/anomalies/` | 1 fichier d'anomalie par fenêtre canonique au moins une anomalie, aucun orphelin |
| 1.7 | Tests de non-régression front minimaux (smoke : build + vues rendues) | script `validation_plan.md` §3 | check-list §5 du `frontend_handoff.md` cochée |

**Condition** : D1 validée. D2 statutée en fin de lot (go/no-go API).

## S2 — API légère (uniquement si D2 = b)

| Tâche | Livrable | Critère d'acceptation |
|---|---|---|
| 2.1 | `api/index.py` (FastAPI) + `requirements.txt` à la racine | endpoints `/api/v1/*` de `api_contract.md` §2 |
| 2.2 | Cache artefacts + ETag, CORS restreint, enveloppe d'erreur unique | tests d'intégration API ; aucun chemin serveur en réponse |
| 2.3 | `data.js` basculé sur l'API (§6 du handoff) | vues inchangées, mêmes chiffres qu'avec les statiques |
| 2.4 | Déploiement de l'API (hébergement conforme D3) | `freebuff-deploy check` sans erreur ; santé `GET /api/v1/health` |

## S3 — Observabilité réelle (conditionné à D4)

| Tâche | Livrable | Critère d'acceptation |
|---|---|---|
| 3.1 | Acquisition `MOD03/MYD03` (géométrie, période pilote d'abord) | manifests SHA-256, `data/raw/` toujours immuable |
| 3.2 | Acquisition `MOD09GA` (couverture) + `MOD35_L2/MYD35_L2` (nuages) ; masques VIIRS traités comme variables **séparées** | `coverage_products_acquired = true` seulement si réellement acquis |
| 3.3 | Passage de l'état par défaut à `no_detection_plausible_conditions` là où justifié | `pytest tests/test_observability.py` vert ; **toujours** aucun « pas de feu » |
| 3.4 | Mise à jour du rapport/figures observabilité + vue web | chiffres et avertissements cohérents |

## S4 — Validation scientifique H4-H6 (conditionné à D5 pour H4/H6)

| Tâche | Livrable | Critère d'acceptation |
|---|---|---|
| 4.1 | Split dév/éval exécuté (2013-2016 / 2017-2020 + sud/nord) | métriques calculées sur le jeu d'évaluation seul, reportées séparément |
| 4.2 | H4 : sous-ensembles par classe native, combinaisons de seuils publiées | **aucune** table de conversion numérique ; sur-ajustement détecté = échec publié |
| 4.3 | H5 : calibration FRP avec covariables géométriques (si S3-1 acquis) | comparaison à la ligne de base constante ; gain hors échantillon mesuré |
| 4.4 | H6 : écart dév/évalu vs seuil fixé **avant** tout test | écart > seuil = « non généralisable » publié tel quel |
| 4.5 | Mise à jour `harmonization.py` statuts + rapport | « exécuté » ≠ « validé » conservé tant que la référence externe manque |

## Dépendances et risques

```
S0 ─▶ S1 ─▶ (S2 si D2)          D1 requis pour S0.ferme ; D3 requis pour mise en ligne
S3 (D4) ─▶ S4.3 (H5)            D5 requis pour S4.2/S4.4
S1.6 indépendant                 D7 (emprise) = rerun complet si activé → impacte S1 et S4
```

- **Risque principal** : faux sentiment de validation — mitigué par `scientific_method.md` §6
  (« exécuté » ≠ « validé ») et par les statuts du catalogue.
- **Risque de dette** : artefacts servis bruts (poids, chemins locaux) — traité en S1.1.
- **Risque d'exécution** : quotas FIRMS et blocage Earthdata — journaliser chaque tentative
  dans `execution.json` (déjà fait), ne jamais contourner une erreur de quota.

## Definition of Done (globale)

1. `python3 -m pytest` = 31/31 (ou plus) ; 2. `npm --prefix web run build` = exit 0 ;
3. `freebuff-preview status` = ready ; 4. chiffres recoupés aux artefacts
   (`validation_plan.md` §2) ; 5. aucune phrase d'absence de feu ; 6. `docs/` à jour ;
7. décisions D1-D8 tranchées ou explicitement reportées.
