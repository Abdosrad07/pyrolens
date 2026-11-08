# Évaluation globale de préparation — PyroLens

**Note importante** : ce diagnostic est interne. Il ne prédit pas le classement du jury NASA Space Apps Challenge. Certaines notes s'appuient sur des documents du dépôt (tests documentés verts) car Python/npm n'étaient pas disponibles dans l'environnement d'audit pour re-exécuter.

## Notes par dimension

| Dimension | Note /25 ou /15 ou /10 | Justification (éléments observables) |
|---|---|---|
| Pertinence par rapport au défi | 10 / 15 | Le projet s'attaque au bon problème (MODIS Terra/Aqua vs VIIRS S-NPP, Cameroun 2013-2020) avec des données authentiques. Cependant, aucune méthode d'harmonisation n'est validée et 2 des 3 modules annoncés (Harmonization Lab, Fire Calendar) n'ont pas d'UI. Preuves : `config/pipeline.yaml`, `baselines/summary.csv`, absence de vues dédiées. |
| Solidité scientifique | 8 / 25 | Rigueur réelle sur la mesure (Jaccard = recouvrement, jamais présenté comme précision ; confiances non converties ; aucune affirmation "pas de feu"). Mais H4-H6 non exécutés, pas de référence indépendante, pas de correction FRP (géométrie absente). Preuves : `harmonization.py`, `docs/methodology.md` §1 non-objectifs, `docs/limitations.md` §1.1. |
| Fonctionnalités opérationnelles | 14 / 20 | Pipeline Python complet et testé, 91 tests documentés verts, frontend 7 vues opérationnelles, API FastAPI lecture seule + expériences. Manquent : Harmonization Lab UI, Fire Calendar UI, produits Earthdata. Preuves : `src/pyrolens/`, `web/src/views/`, `api/`, `execution.json`. |
| Cohérence frontend/backend | 9 / 10 | Même source d'artefacts, mêmes conventions (dates, confiances, Jaccard), règle D1 respectée. Écart : front et API déconnectés à l'exécution (front lit des fichiers statiques, endpoints `/experiments` et `/series/*` orphelins côté UI). Preuves : `web/src/data.js`, `api/routers/`. |
| Expérience utilisateur et visualisations | 8 / 10 | Frontend propre (Vite + React + Recharts), 6 figures, bannières d'origine des données, gestion Loading/Success/Empty/Error. Écart : 2 modules annoncés absents, pas de liens ancrés ni d'export. Preuves : `web/src/views/`, `web/public/artifacts/figures/`. |
| Reproductibilité et documentation | 9 / 10 | Configuration versionnée, commandes documentées, `data/raw` immuable (SHA-256), artefacts horodatés, `docs/` complet. Limite : `data/raw/firms/` ignoré par git (>330 Mo), reproduction nécessite `pyrolens download` avec clés FIRMS. Preuves : `docs/technical.md`, `docs/methodology.md` §9, `tests/test_reproducibility.py`. |
| Qualité de la démonstration | 6 / 10 | Scénario 4-5 min réalisable sur données réelles acquises (FIRMS). Mais 3 des 7 parcours requis ne peuvent pas être démontrés depuis l'UI (configurer/lancer expérience, Fire Calendar, acquisition Earthdata). Preuves : `demo_readiness.md`. |
| **Total** | **64 / 100** | |

## Limites de l'évaluation

- Les tests (31 pipeline + 60 API) sont documentés comme verts dans le dépôt mais n'ont pas été re-exécutés dans l'environnement d'audit (Python/npm indisponibles). La note reflète les artefacts et documents, pas une re-exécution.
- Le build frontend `npm run build` n'a pas pu être testé (vite absent).
- Les critères de notation internes du jury NASA ne sont pas publiés ; cette évaluation est un diagnostic interne, pas une prédiction.

## Verdict

**Partiellement prêt, mais insuffisant scientifiquement pour une soumission sérieuse en l'état.**

Justification : le projet dispose d'une infrastructure solide et de données réelles authentiques, mais il ne démontre pas encore d'harmonisation validée (H4-H6), et deux des trois modules annoncés n'ont pas d'interface. Le score de 64/100 reflète un produit techniquement avancé mais scientifiquement inachevé au regard du défi.

## Conditions pour passer à "Prêt pour une démonstration"

1. D4 et D5 tranchées (clés Earthdata fournies OU limite actée publiquement).
2. Lot S1 terminé (notamment Harmonization Lab UI ou Fire Calendar UI au moins l'un des deux).
3. Démo réalisée sur données réelles acquises (pas le fixture synthétique).
4. Aucun chiffre de phase 1 republié (D1 respectée).

## Conditions pour passer à "Prêt pour la soumission"

En plus des conditions ci-dessus :
5. H4 et/ou H6 exécutés (ou la limite publiée explicitement avec le split dév/éval).
6. H5 exécuté OU documenté comme bloqué par Earthdata avec le plan pour y remédier.
7. Definition of Done globale satisfaite (91 tests, build front, docs à jour, D1-D8 tranchées).

Délivré le 2026-11-08. À valider avant toute modification du code.