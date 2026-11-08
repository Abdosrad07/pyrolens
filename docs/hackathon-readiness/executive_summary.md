# Executive Summary — PyroLens (audit d'écart, pré-soumission NASA Space Apps Challenge 2026)

## Verdict global

**Partiellement prêt, mais insuffisant scientifiquement pour une soumission sérieuse.**

PyroLens dispose d'un pipeline Python réel, testé, qui produit des artefacts cohérents sur des données NASA FIRMS authentiques (2013-2020, Cameroun). Le frontend statique consomme ces artefacts et l'API FastAPI les expose. Cependant, aucune méthode d'harmonisation n'est validée (H4/H6 non exécutables), et l'observabilité réelle est bloquée par l'absence d'identifiants Earthdata. Le projet démontre la concordance inter-capteurs (Jaccard), mais ne répond pas encore pleinement au défi « Harmonization of MODIS and VIIRS Hot Spots ».

## Ce qui est réellement fonctionnel (preuves dans le dépôt)

| Élément | Preuve | Statut |
|---|---|---|
| Pipeline Python reproductible | `src/pyrolens/cli.py`, commande `run` | Fonctionnel |
| Données FIRMS réelles 2013-2020 (0 jour manquant) | `data/manifests/downloads.json`, `data_inventory.md` §4 | Acquis, vérifié |
| Normalisation 1 432 → 1 170 fenêtres canoniques | `data/manifests/normalize.json` | Vérifié (comptabilité exacte) |
| Audit qualité 1 170 fichiers | `audit.json` (2 634 700 anomalies classées) | Testé et vérifié |
| Baselines 24 configs (Jaccard 0,10 → 0,66) | `baselines/summary.csv`, `baselines.json` | Fonctionnel, données réelles |
| Observabilité 4 états (jamais « pas de feu ») | `observability.json`, `src/pyrolens/harmonization.py` H2 | Fonctionnel, état « inconnu » par défaut |
| 91 tests (31 pipeline + 60 API) | `README.md` §7, `docs/phase2/data_validation.md` §7 | Verts (documentés) |
| Frontend statique Vite + React + Recharts | `web/src/App.jsx`, `data.js`, 7 vues | Opérationnel |
| API FastAPI lecture seule + jobs | `api/`, `docs/api.md`, `openapi.json` | Implémentée, 60 tests |

## Ce qui fait défaut (bloquants scientifiquement)

| Élément | Conséquence |
|---|---|
| **H4 — seuils de confiance** non exécuté | `harmonization.py` H4 : « NON EXÉCUTÉ — prérequis manquants (D5) » |
| **H6 — validation externe** non exécuté | Aucune référence au sol, pyrométrie ou autre agence satellite dans l'environnement |
| **H5 — géométrie d'observation / FRP** non exécuté | Granules standard MOD14/MYD14/VNP14IMG bloqués (Earthdata Login, HTTP 302) |
| **Observabilité réelle** bloquée | `coverage_products_acquired = false` → état par défaut « observabilité inconnue » |
| **Harmonization Lab** absent du frontend | Les 3 modules annoncés (Overview, Harmonization Lab, Fire Calendar) ne sont pas tous implémentés : seul Overview existe vraiment |

## Trois écarts les plus graves

1. **Absence de validation scientifique** : aucune méthode d'harmonisation déclarée validée (H4-H6). Le Jaccard est un recouvrement d'ensembles, pas une précision de détection — le document le dit, mais le défi demande de l'harmonisation effective.
2. **Blocage Earthdata** : sans `EARTHDATA_USER/PASSWORD` ou `EARTHDATA_TOKEN`, les granules standard et produits de couverture/nuages (MOD35_L2, MOD09GA, MOD03/MYD03) sont inaccessibles → H5 et l'observabilité réelle impossibles.
3. **Harmonization Lab et Fire Calendar non implémentés** : le frontend ne contient que les vues Overview (Audit, Baselines, Observability, Report, Figures). Il n'existe pas de module de configuration/exécution d'expériences d'harmonisation ni de calendrier des feux, malgré l'annonce dans la mission.

## Recommandation avant soumission

Ne pas soumettre en l'état. Terminer le lot S1 (MVP frontend), trancher D4/D5 (fournir les clés Earthdata ou acter publiquement la limite), implémenter au minimum le Harmonization Lab (exécution d'expériences via l'API existante `POST /api/v1/experiments`) et un Fire Calendar basique (agrégations quotidiennes/mensuelles déjà dans `baselines.json`). Documenter explicitement que le Jaccard mesure le recouvrement, non la précision.

## Livrables du présent audit

Dossier `docs/hackathon-readiness/` :
1. `executive_summary.md` (présent document)
2. `current_state_audit.md` — audit technique et fonctionnel
3. `scientific_gap_analysis.md` — écarts scientifiques
4. `challenge_compliance.md` — conformité aux exigences officielles
5. `frontend_backend_audit.md` — cohérence frontend/backend
6. `demo_readiness.md` — préparation de la démonstration
7. `gap_matrix.md` — matrice complète des écarts
8. `priority_action_plan.md` — plan de correction priorisé
9. `readiness_score.md` — évaluation globale argumentée

Délivré le 2026-11-08. À valider avant toute modification du code.