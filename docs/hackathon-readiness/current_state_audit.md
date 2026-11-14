# Audit technique et fonctionnel — état actuel de PyroLens

**Règle d'évaluation** : une fonctionnalité n'est considérée opérationnelle que si elle apparaît dans le code, les tests et les artefacts. Aucune maquette ou affirmation du README ne suffit.

## 1. Pipeline Python (`src/pyrolens/`)

### Modules présents et leurs statuts

| Module | Rôle | Statut | Preuve |
|---|---|---|---|
| `cli.py` | Point d'entrée Typer (geo, inventory, download, normalize, audit, baselines, observability, figures, report, run, web-artifacts, doctor) | Opérationnel | `src/pyrolens/cli.py` |
| `config.py` / `pipeline.yaml` | Configuration versionnée (région Cameroun, période 2013-2020, capteurs, grilles, fenêtres) | Opérationnel | `config/pipeline.yaml` |
| `download.py` | Acquisition géométrie, FIRMS API, granules Earthdata (sans contournement) | Opérationnel, partiellement bloqué | `src/pyrolens/download.py` |
| `normalize.py` | Fenêtres canoniques 5j, dédoublement strict | Opérationnel | `data/manifests/normalize.json` |
| `ingest.py` / `audit.py` | Parsing CSV, contrôle qualité, classification anomalies | Opérationnel, testé | `src/pyrolens/audit.py`, `audit.json` |
| `grids.py` | Clés d'ensemble (cellule, date)/(cellule, fenêtre) | Opérationnel | `src/pyrolens/grids.py` |
| `baselines.py` | Jaccard 24 configs, divergences mensuelles/journalières, spatial, régional | Opérationnel, données réelles | `src/pyrolens/baselines.py`, `baselines/summary.csv` |
| `observability.py` | 4 états d'observabilité | Opérationnel, état par défaut « inconnu » | `observability.json` |
| `figures.py` / `report.py` | Figures PNG, rapport Markdown + DOCX | Opérationnel | `figures/`, `reports/scientific_report.md` |
| `harmonization.py` | Catalogue H1-H6, aucun déclaré validé | Documenté, H4-H6 non exécutés | `src/pyrolens/harmonization.py` |

### Données réelles acquises (preuves)

- 1 170 fenêtres canoniques FIRMS (585 MODIS + 585 VIIRS), 2013-01-01 → 2020-12-31, 0 jour manquant (`data_inventory.md` §4).
- 9 802 requêtes FIRMS journalisées avec SHA-256, codes HTTP, horodatages (`data/manifests/downloads.json`).
- Normalisation : 5 017 580 lignes lues = 4 460 288 écrites + 557 292 doublons stricts supprimés (`data/manifests/normalize.json`).
- 2 634 697 lignes hors emprise tracées et exclues des ensembles (`limitations.md` §1.3).
- `data_origin = nasa_firms` sur tous les artefacts récents (18/10/2026). Le fixture synthétique (`data/fixture/`) n'est plus utilisé par les rapports publics.

### Données non acquises (blocage Earthdata)

- Granules standard MOD14/MYD14/VNP14IMG (HDF) : HTTP 302 → `urs.earthdata.nasa.gov` sans `EARTHDATA_*` (`download.py` `probe_granule_access`, `downloads.json`).
- Produits couverture/nuages MOD35_L2, MOD09GA et géométrie MOD03/MYD03 : même blocage → `coverage_products_acquired = false`.

## 2. API (`api/`)

| Fichier | Rôle | Statut |
|---|---|---|
| `api/app.py` | `create_app()`, FastAPI, CORS, montage `/api/v1` | Implémenté |
| `api/index.py` | Entrée production uvicorn | Implémenté |
| `api/settings.py` | `Settings` gelé, lit l'environnement, jamais les clés d'acquisition | Implémenté |
| `api/store.py` | `ArtifactStore`, lecture artefacts, cache par empreinte, ETag | Implémenté |
| `api/errors.py` | Enveloppe `{"error": {code, message}}`, handlers 400-500 | Implémenté |
| `api/security.py` | Bearer optionnel sur POST (`PYROLENS_API_TOKEN`) | Implémenté |
| `api/jobs.py` | File d'attente 1 thread, persistance JSON des résultats | Implémenté |
| `api/schemas.py` | Modèles de réponse | Implémenté |
| `api/routers/system.py` | `/health`, `/meta`, `/report` | Implémenté |
| `api/routers/baselines.py` | `/summary`, `/series/jaccard`, `/series/divergence`, `/spatial`, `/export` | Implémenté |
| `api/routers/catalog.py` | `/catalog`, `/catalog/{dataset}` | Implémenté |
| `api/routers/audit.py` | `/audit/summary` | Implémenté |
| `api/routers/validation.py` | `POST /datasets/validate` | Implémenté |
| `api/routers/experiments.py` | `POST /experiments`, `GET /experiments/{id}`, `GET /experiments/{id}/result`, `GET /experiments` | Implémenté |
| `api/services/experiments.py` | Moteur d'expérience (réutilise `pyrolens.grids`/`baselines`) | Implémenté |
| `api/services/queries.py` | Requêtes sur artefacts (filtres, séries) | Implémenté |
| `docs/openapi.json` | Spécification machine | Versionnée, à régénérer après changement |

### Endpoints réellement fonctionnels (lecture)

- `GET /api/v1/health`, `/meta`, `/report`
- `GET /api/v1/catalog`, `/catalog/{dataset_id}`
- `GET /api/v1/summary`, `/series/jaccard`, `/series/divergence`, `/spatial`, `/export`
- `GET /api/v1/audit/summary`
- `GET /api/v1/observability`
- `POST /api/v1/experiments` (calcul réel via `api/services/experiments.py`)
- `GET /api/v1/experiments/{job_id}`, `/result`, liste

**Limite documentée** : exécution séquentielle (1 thread), pas de reprise après crash d'une tâche en cours, CORS fermé par défaut, pas d'auth lecture (D6 : MVP public).

## 3. Frontend (`web/`)

| Vue | Fichier | Statut | Données réelles ou synthétiques |
|---|---|---|---|
| Landing (accueil) | `web/src/views/Landing.jsx` | Opérationnel | Affiche `data_origin` |
| Overview (synthèse) | `web/src/views/Overview.jsx` | Opérationnel | Étapes, blocages, inventaire, manifeste |
| Audit | `web/src/views/Audit.jsx` | Opérationnel | Anomalies, gaps temporels, confiance |
| Baselines | `web/src/views/Baselines.jsx` | Opérationnel | 24 configs, Jaccard, régions, spatial top 30 |
| Observability | `web/src/views/Observability.jsx` | Opérationnel | 4 états, `coverage_products_acquired = false` |
| Report | `web/src/views/Report.jsx` | Opérationnel | Rendu Markdown du rapport |
| Figures | `web/src/views/Figures.jsx` | Opérationnel | 6 PNG |
| Auth | `web/src/Auth.jsx` | Simulé (sessionStorage, aucun backend comptes) | Démonstration uniquement |

**Ce qui manque** par rapport aux 3 modules annoncés (Overview, Harmonization Lab, Fire Calendar) :
- **Harmonization Lab** : absent. Il n'existe aucune vue de configuration/exécution d'expériences d'harmonisation côté front. L'API `POST /api/v1/experiments` existe mais n'a pas d'interface utilisateur dédiée.
- **Fire Calendar** : absent. Aucune vue d'agrégation temporelle quotidienne/hebdomadaire/mensuelle dédiée. Les séries existent dans `baselines.json` (`jaccard_monthly`, `daily`) mais sans vue calendrier.

### Chargement des données frontend

`web/src/data.js` charge 7 artefacts statiques depuis `/artifacts` (`execution`, `inventory`, `downloads`, `audit`, `baselines`, `observability`, `scientific_report.md`). Aucun calcul côté interface. `downloads.json` (5,9 Mo) est chargé en totalité au démarrage — voir écart S1.1.

## 4. Tests

| Suite | Fichiers | Statut | Preuve |
|---|---|---|---|
| Pipeline (31 tests) | `tests/` | Verts (documentés) | `README.md` §7, `data_validation.md` §7 |
| API (60 tests) | `tests/api/` | Verts (documentés) | `README.md` §7 |
| Reproductibilité | `tests/test_reproducibility.py` | Immuabilité `data/raw` vérifiée | Test cité dans `data_validation.md` |

**Limite** : Python et npm non disponibles dans l'environnement d'audit actuel, les tests n'ont pas pu être re-exécutés ici ; les statuts proviennent des artefacts et documents du dépôt (constat d'outil, pas re-exécution).

## 5. Déploiement et configuration

- `requirements.txt` : polars, pandas, numpy, pyarrow, shapely, pyproj, matplotlib, typer, pyyaml, httpx, pytest, python-docx, fastapi, uvicorn, pydantic.
- `vite.config.js` : build Vite, port via variable d'environnement `PORT` (Freebuff), HMR désactivé.
- `sites-manifest.json`, `sites-worker.js` : présence d'articles liés à Freebuff (hébergement statique).
- Aucun secret commité (vérifié : `FIRMS_MAP_KEY`, `EARTHDATA_*` absents de Git, lus via `os.environ`).

## 6. Cohérence observée

Le pipeline écrit des artefacts JSON/CSV/PNG dans `web/public/artifacts/` et `baselines/`. Le frontend et l'API lisent ces mêmes artefacts sans recalcul. La règle D1 (une seule source de chiffres = `baselines/summary.csv`) est respectée dans le code (`api/routers/baselines.py`, `docs/api.md`).

## 7. Ce qui n'est PAS opérationnel (non ambigu)

| Élément | Reason |
|---|---|
| Granules standard Earthdata (MOD14/MYD14/VNP14IMG) | HTTP 302 sans identifiants (`download.py`, `downloads.json`) |
| Produits couverture/nuages (MOD35_L2, MOD09GA) | Même blocage |
| H5 (géométrie d'observation MOD03/MYD03, correction FRP) | Dépend des granules ci-dessus |
| H4 (seuils de confiance) | Pas de référence indépendante (D5) |
| H6 (validation externe) | Pas de référence au sol / autre agence (D5) |
| Harmonization Lab (UI) | Aucune vue frontend dédiée |
| Fire Calendar (UI) | Aucune vue dédiée ; séries uniquement dans artefacts JSON |
| Build frontend `npm run build` | Non testable ici (vite non installé dans l'environnement d'audit) |