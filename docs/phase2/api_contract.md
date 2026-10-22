# Contrat de données / API — phase 2

Deux contrats : **v1 (en vigueur)** = les artefacts statiques servis sous `/artifacts/` ;
**v2 (conditionnelle à D2)** = une éventuelle API REST. Toute évolution du contrat v1 qui
casse un champ consommé par `web/src/` est une **rupture** : elle exige un bump de version et
la mise à jour simultanée de `frontend_handoff.md`.

---

## 1. Contrat v1 — artefacts statiques (en vigueur)

Base : `web/public/artifacts/` (servi en `/artifacts/`). Producteur : `pyrolens web-artifacts`.

| Fichier | Rôle | Structure (champs racine) |
|---|---|---|
| `execution.json` | journal append-only des étapes, blocages, commandes | `{steps[{at, step, status, detail}], blockers[{what, detail, http_status, action, at}], commands[{cmd, status, at}], period_start, period_end, project_version}` |
| `inventory.json` | inventaire CMR (versions produits, granules) | `{generated_at, source, base_url, bbox_note, period, sensors{terra, aqua, viirs_snpp}}` |
| `downloads.json` | manifeste complet d'acquisition | `{generated_at, entry_count, entries[{url, dataset, status, http_status, path, bytes, sha256, acquired, downloaded_at}]}` — **5,9 Mo ; hors chargement initial après P1-1** |
| `audit.json` | audit de qualité | `{generated_at, data_origin, n_files, files[1170], anomalies_by_category, rows_by_classification, row_accounting, missing_values_by_column, satellites, versions, frp_stats, confidence_distribution_by_sensor, volumes_by_month, n_distinct_days_with_records, temporal_gaps{n_entries, entries[200]}, interpretation_warning}` |
| `baselines.json` | résultats d'harmonisation | `{generated_at, data_origin, key_definitions, grids_deg, window_days, primary, sensor_sizes, summary[24], monthly, daily, regions, jaccard_monthly, spatial}` |
| `observability.json` | états d'observabilité | `{generated_at, data_origin, grid_deg, coverage_products_acquired, states{terra, aqua, viirs_snpp}, state_labels, note}` |
| `scientific_report.md` | rapport complet (rendu par `Report.jsx`) | Markdown UTF-8 |
| `figures/*.png` | 6 figures | binaires |
| `generated_at.txt` | horodatage de synchronisation | ISO-8601 |

### Schémas courants

- **Ligne `summary`** : `{pair, sensor_a, sensor_b, grid_deg, window_days, key_definition, n_a, n_b, intersection, union, jaccard}`
- **Ligne divergente** (`monthly`, `daily`, `regions`, `jaccard_monthly`) :
  `{pair, month|date|region, a_only, b_only, both[, jaccard]}`
- **Ligne spatiale** : `{pair, grid_deg, window_days, cell_i, cell_j, lon, lat, a_count, b_count}`

### Invariants v1

1. `generated_at` (ISO-8601) présent sur chaque JSON ; `data_origin` sur chaque JSON de
   résultats (`nasa_firms` aujourd'hui, `synthetic_fixture` pour le fixture de démonstration).
2. `execution.json` est **append-only** ; l'historique n'est jamais réécrit.
3. Les identifiants (`pair` = `terra__aqua` | `aqua__viirs_snpp`, capteurs `terra|aqua|viirs_snpp`,
   grilles en degrés, fenêtres en jours) sont stables ; `web/src/data.js → PAIR_LABELS`
   référence les libellés affichables.
4. Valeurs nulles = `null` (jamais `0` substitué) ; les compteurs sont des entiers ;
   `jaccard` est un flottant [0, 1] arrondi à 6 décimales.
5. Un artefact absent doit rester gérable côté client (`errors[]`, jamais d'écran blanc).
6. **P1** : ne pas publier de chemins absolus locaux dans les artefacts agrégés
   (`downloads.json → entries[].path` en expose aujourd'hui — sans secret, mais non portable).

## 2. Contrat v2 — API REST (conditionné à D2, lot S2)

Base : `/api/v1`. Réponses : `application/json; charset=utf-8`, `Cache-Control` + `ETag`
dérivés de `generated_at` (les données ne changent qu'au déploiement d'artefacts).

| Endpoint | Paramètres | Réponse |
|---|---|---|
| `GET /api/v1/meta` | — | `{generated_at, data_origin, primary, period, grids_deg, window_days, pairs, coverage_products_acquired}` |
| `GET /api/v1/summary` | `pair?, grid_deg?, window_days?` | `{meta, rows: [ligne summary]}` |
| `GET /api/v1/series/jaccard` | `pair` (requis), `grid_deg?, window_days?` | `{meta, rows: [{month, jaccard, a_only, b_only, both}]}` |
| `GET /api/v1/series/divergence` | `pair` (requis), `resolution: day|month|region` | `{meta, rows: [...]}` |
| `GET /api/v1/spatial` | `pair`, `grid_deg`, `window_days` | `{meta, rows: [ligne spatiale]}` (pagination `limit/offset` au-delà de 50 000 lignes) |
| `GET /api/v1/observability` | `grid_deg?` | `{meta, states, state_labels, note}` |
| `GET /api/v1/audit/summary` | — | `row_accounting`, `anomalies_by_category`, `temporal_gaps.n_entries` (sans les 200 entrées détaillées : `?detail=1`) |
| `GET /api/v1/report` | — | Markdown (`text/markdown`) |
| `GET /api/v1/health` | — | `{status, generated_at}` |

**Erreurs** (enveloppe unique) : `{error: {code, message}}` avec codes `400` (paramètre
inconnu), `404` (paire/configuration inexistante), `500` (artefact illisible) ;
aucune pile d'exposition, aucun chemin serveur dans le message.

**Versioning** : `/api/v1` fixe ; ajout de champ = compatible, suppression/renommage = `/v2`.
**Génération** : OpenAPI exporté par FastAPI (`/api/v1/openapi.json`), servi comme contrat
de référence aux clients.
**Interdits v2** : aucun endpoint écrivant, aucun paramètre qui interprète une absence de
détection (jamais de filtre « feu absent »), aucun secret ni chemin local en réponse.

## 3. Passation v1 → v2

Si D2 est validée : `web/src/data.js` devient la seule couche à remplacer (mêmes noms de
données en retour), les composants de vues ne changent pas — voir `frontend_handoff.md` §4.
Tant que D2 n'est pas tranchée, **le contrat v1 est le contrat**.
