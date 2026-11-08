# Audit de cohérence frontend/backend — PyroLens

## Architecture observée

Le pipeline Python écrit des artefacts dans `web/public/artifacts/` et `baselines/`. Le frontend (`web/`, Vite + React) et l'API (`api/`, FastAPI) lisent ces mêmes artefacts sans recalcul. Règle documentée dans `docs/technical.md` §1.1 : deux consommateurs, une seule source.

## Correspondance composant → endpoint

| Vue frontend | Fichier | Données consommées | Endpoint/backend correspondant | Statut |
|---|---|---|---|---|
| Landing | `Landing.jsx` | `execution`, `audit.data_origin` | `/api/v1/meta`, `/health` | Cohérent |
| Overview | `Overview.jsx` | `execution`, `inventory`, `downloads` | `/api/v1/meta`, `/catalog` | Cohérent |
| Audit | `Audit.jsx` | `audit` | `/api/v1/audit/summary` | Cohérent |
| Baselines | `Baselines.jsx` | `baselines` | `/api/v1/summary`, `/series/jaccard`, `/series/divergence`, `/spatial`, `/export` | Cohérent |
| Observability | `Observability.jsx` | `observability` | `/api/v1/observability` | Cohérent |
| Report | `Report.jsx` | `scientific_report.md` | `/api/v1/report` | Cohérent |
| Figures | `Figures.jsx` | Fichiers PNG statiques | `/artifacts/figures/` (direct) | Cohérent |
| (absent) Harmonization Lab | — | — | `POST /api/v1/experiments`, `GET /experiments/{id}/result` | **Backend oui, frontend non** |
| (absent) Fire Calendar | — | — | `/series/jaccard`, `/series/divergence` (données présentes, pas de vue) | **Backend oui, frontend non** |

## Vérification des structures JSON

- `baselines.json` : contient `summary`, `monthly`, `daily`, `regions`, `spatial`, `primary`, `grids_deg`, `window_days`, `key_definitions`, `sensor_sizes`, `generated_at`, `data_origin`. Le frontend `Baselines.jsx` consomme `b.summary`, `b.jaccard_monthly`, `b.regions`, `b.spatial`, `b.primary`, `b.grids_deg`, `b.window_days`. Cohérent.
- `observability.json` : `states`, `coverage_products_acquired`, `state_labels`, `note`, `grid_deg`, `generated_at`, `data_origin`. Le frontend consomme `o.states`, `o.coverage_products_acquired`, `o.note`, `o.state_labels`, `o.grid_deg`. Cohérent.
- `audit.json` : `n_files`, `files[]` (chaque fichier avec `n_records`, `n_rows_analysable`, `n_anomalies`, `date_min`, `date_max`...), `row_accounting`, `anomalies_by_category`, `temporal_gaps`, `volumes_by_month`, `confidence_distribution_by_sensor`. Le frontend consomme `a.anomalies_by_category`, `a.row_accounting`, `a.temporal_gaps.entries`, `a.volumes_by_month`, `a.confidence_distribution_by_sensor`, `a.data_origin`, `a.n_files`. Cohérent.
- `execution.json` : `steps[]`, `blockers[]`, `period_start`, `period_end`, `project_version`. Le frontend consomme `exec.steps`, `exec.blockers`, `exec.period_start`, `exec.period_end`, `exec.project_version`. Cohérent.

## Endpoints utilisés vs existants

Le frontend charge uniquement des fichiers statiques via `fetch(`${BASE}/${name}.json`)` dans `data.js` (`BASE = "/artifacts"`). Il n'appelle **pas** les endpoints API (`/api/v1/*`). L'API et le frontend sont donc **déconnectés à l'exécution** : ils partagent les mêmes artefacts mais n'interagissent pas. C'est un choix architectural (statique pour le MVP, D2), pas une incohérence.

Cependant :
- Le frontend ne consomme pas `POST /api/v1/experiments` (pas d'Harmonization Lab).
- Le frontend n'a pas de vue qui appelle `/series/jaccard` ou `/series/divergence` avec filtres (pas de Fire Calendar).
- L'API expose ces endpoints mais ils sont orphelins côté interface.

## États Loading / Success / Empty / Error

| État | Gestion frontend | Preuve |
|---|---|---|
| Loading | `if (!data) return <div>Chargement…</div>` dans `App.jsx` ; `<div className="loading">` dans chaque vue | `App.jsx` L80-88, `Audit.jsx` L36 |
| Success | Rendu des données avec `fmt()` et tableaux | Toutes les vues |
| Empty | `if (!b) return <div>Artefact indisponible.</div>` ; messages "Aucune ligne régionale" | `Baselines.jsx` L91, L287 |
| Error | `Promise.allSettled` dans `loadAll()`, erreurs collectées dans `out.errors` ; `onError` sur `` dans `Figures.jsx` | `data.js` L28-43, `Figures.jsx` L25-28 |

**Écart** : pas de message d'erreur global si tous les artefacts échouent ; `data.js` ne propage pas les erreurs vers l'UI (seulement `out.errors` non affiché). Mineur.

## Unités et conventions

- Dates : `AAAA-MM-JJ` UTC, `acq_time` HHMM sans zéro de tête (21 = 00:21) — documenté dans `docs/references.md` §1.5 et appliqué dans `src/pyrolens/audit.py` `_parse_time`.
- Confiance : MODIS 0-100 vs VIIRS low/nominal/high, **jamais converties** (`docs/methodology.md` §7, `Audit.jsx` L333-337).
- Coordonnées : WGS84 décimales, bbox `[ouest, sud, est, nord]`.
- Jaccard : |A ∩ B| / |A ∪ B|, 0 si union vide.

Cohérent entre backend (`baselines.py`, `grids.py`) et frontend (`Baselines.jsx` calcule le Jaccard local de la même façon pour les régions).

## Données fictives présentées comme réelles

**Aucune** n'a été détectée. Chaque artefact porte `data_origin` (`nasa_firms` ou `synthetic_fixture`). Le frontend `Landing.jsx` et `Overview.jsx` affichent une bannière d'avertissement quand l'origine est `synthetic_fixture`. Le rapport et la documentation distinguent explicitement les deux.

## Conclusion de cohérence

Frontend et backend sont cohérents sur les données partagées (mêmes artefacts, mêmes conventions, mêmes avertissements). Le principal écart fonctionnel est l'absence d'UI pour les deux modules annoncés (Harmonization Lab, Fire Calendar), alors que le backend expose les endpoints correspondants (`/api/v1/experiments`, `/series/*`).
