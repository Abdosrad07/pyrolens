# Contrat d'API PyroLens — v1

Base URL : `/api/v1`. Réponses JSON UTF-8 (`application/json; charset=utf-8`),
sauf `/report` (`text/markdown`) et `/export` (`text/csv` ou JSON en
téléchargement). Spécification machine : `docs/openapi.json` (export de
`/api/v1/openapi.json`), interactive sur `/api/v1/docs` (Swagger) et
`/api/v1/redoc`.

> **Lecture seule** : seuls `POST /api/v1/experiments` et
> `POST /api/v1/datasets/validate` sont admis en écriture (cf. §6).
> **D1 — source unique des chiffres** : toute valeur Jaccard publiée provient
> de `baselines/summary.csv` (`/api/v1/summary`, `dataset=summary` de
> `/export`), horodatée et reproductible ; l'API ne recalcule jamais ces
> valeurs.

---

## 1. Enveloppes et en-têtes

Réponse succès : l'objet métier lui-même (aucun wrapper), avec les champs de
provenance `generated_at` et/ou `data_origin` selon les routes.

Réponse d'erreur :

```json
{ "error": { "code": "404", "message": "Jeu de données inconnu : xyz." } }
```

| Code | Quand |
|---|---|
| 400 | paramètre inconnu/invalide, colonnes obligatoires absentes, fichier vide, nom ≠ `.csv` |
| 401 | `Authorization: Bearer <jeton>` attendu (jeton configuré) |
| 403 | expériences désactivées (`PYROLENS_JOBS_ENABLED=0`) |
| 404 | route, filtre, dataset, job ou export inconnu |
| 405 | méthode non autorisée |
| 409 | source indisponible, job non terminé/échoué |
| 413 | upload > `PYROLENS_MAX_UPLOAD_BYTES` (10 Mo) |
| 415 | type de contenu d'upload refusé |
| 500 | artefact absent/illisible (« exécuter le pipeline ») ou erreur interne |

**Paramètres inconnus** : tout query-paramètre non documenté → 400 (jamais
d'ignorance silencieuse).

**Cache HTTP** : `ETag` faible (empreinte des artefacts) +
`Cache-Control: public, max-age=60` ; renvoyer `If-None-Match` → `304` sans
corps. L'ETag change dès qu'un artefact est régénéré.

**Pagination** : uniquement `/spatial` (`limit` ≤ 5000, `offset`) ; les autres
routes retournent l'intégralité des lignes publiées.

---

## 2. Système

### `GET /health`

Réponse immédiate, sans lecture d'artefact :

```json
{ "status": "ok", "generated_at": "2026-10-18T12:00:00+00:00",
  "data_origin": "nasa_firms", "project_version": "0.2.0" }
```

### `GET /meta`

Période, configuration primaire, grilles/fenêtres/paires publiées, définitions
des clés, état de l'observabilité, note d'interprétation (Jaccard ≠ précision).

### `GET /report`

Rapport scientifique Markdown horodaté (`Content-Type: text/markdown;
charset=utf-8`), même contenu que `reports/scientific_report.md`.

---

## 3. Catalogue et qualité

### `GET /catalog`

```bash
curl -s https://<hôte>/api/v1/catalog
```

- `datasets[]` : jeux **source** (`firms_modis`, `firms_viirs` — fichiers,
  enregistrements, lignes analysables, hors-emprise, anomalies, période) et
  jeux **dérivé** (`audit`, `baselines`, `observability`, `scientific_report`
  avec `artifact`, `generated_at`, `data_origin`, `available`).
- `provenance` : manifeste d'acquisition (`downloads.json`, statuts agrégés ;
  URL en gabarit `<FIRMS_MAP_KEY>`, jamais la clé).
- Noms de fichiers relatifs uniquement — aucun chemin local.

### `GET /catalog/{dataset_id}`

Fichier par fichier pour les sources (`files[]` avec comptes, anomalies,
`date_min`/`date_max`) ; métadonnées pour les dérivés. 404 si inconnu.

### `GET /audit/summary?detail=0|1`

Comptabilité des lignes (`row_accounting`, `rows_by_classification`),
anomalies par catégorie, distributions FRP/confiance/volumes mensuels, trous
temporels. `detail=1` inclut les `entries` des trous (200 max) ; `detail=0`
(`défaut`) renvoie `n_entries` sans entrées.

> Les jours sans enregistrement sont libellés `aucun_enregistrement` côté
> pipeline — jamais « pas de feu ».

---

## 4. Comparaisons inter-capteurs (chiffres D1)

Toutes ces routes lisent `baselines.json` et renvoient `{"meta", "rows"}` ;
`meta` porte `generated_at`, `data_origin`, `artifact`, `filters`.

### `GET /summary`

24 configurations (2 paires × 3 grilles × 4 fenêtres), filtres facultatifs
`pair`, `grid_deg`, `window_days` (combinaison inexistante → 404).

Champs d'une ligne : `pair`, `sensor_a`, `sensor_b`, `grid_deg`,
`window_days`, `key_definition`, `n_a`, `n_b`, `intersection`, `union`,
`jaccard`.

```bash
curl -s 'https://<hôte>/api/v1/summary?pair=terra__aqua&grid_deg=0.25&window_days=8'
# équation vérifiable : union == n_a + n_b - intersection
```

### `GET /series/jaccard?pair=…[&grid_deg][&window_days]`

Série mensuelle : `month`, `a_only`, `b_only`, `both`, `jaccard`.
`pair` requis ; une configuration inexistante → 404.

### `GET /series/divergence?pair=…&resolution=day|month|region`

Configuration **primaire uniquement** (0,25° / 8 j) : `day` → `date`,
`month` → `month`, `region` → `region` (terciles de latitude documentés),
avec `a_only`, `b_only`, `both`.

### `GET /spatial?pair=…[&grid_deg][&window_days][&limit][&offset]`

```json
{ "meta": {…}, "total": 1523, "offset": 0, "limit": 1000,
  "rows": [ { "cell_i": 780, "cell_j": 300, "lon": 195.125, "lat": 75.125,
              "a_count": 4, "b_count": 3 } ] }
```

### `GET /observability[?grid_deg=…]`

4 états du pipeline par capteur (`grid_deg` doit correspondre à la maille
publiée sinon 404). Aucun état n'affirme une absence de feu.

### `GET /export?dataset=…[&pair][&grid_deg][&window_days][&format=csv|json]`

```bash
curl -sOJ 'https://<hôte>/api/v1/export?dataset=summary&format=csv'
```

`dataset` ∈ `summary` | `jaccard_monthly` | `daily` | `monthly` | `regions` |
`spatial` (404 sinon) ; `pair` requis hors `summary` (400 sinon). En-têtes CSV
= champs de l'artefact (reproductibilité) ; `Content-Disposition: attachment`
(`pyrolens_<fichier>`).

---

## 5. Early Warning — détection d'anomalies d'activité de feu

Trois routes en lecture seule qui comparent l'activité récente (défaut 14 j)
à une baseline historique par cellule de grille (défaut 730 j). **Toutes les
réponses portent `estimate_kind: "historical_backtest"`** : les données FIRMS
sont des archives/NRT avec latence — aucune affirmation temps réel, et une
cellule sans détection n'implique jamais l'absence de feu.

Paramètres communs (query) : `source` (`auto` | `fixture` | `raw`, défaut
`auto`), `grid_deg` (défaut 0,25 ; (0, 2]), `recent_days` (défaut 14 ;
[1, 365]), `baseline_days` (défaut 730 ; ≥ `recent_days`, ≤ 3650),
`reference_date` (`AAAA-MM-JJ`, défaut = dernière détection des données ;
les données postérieures n'influencent jamais le résultat). Paramètre inconnu
→ 400 ; combinaison invalide → 400 ; source vide → 409.

Le calcul est mis en cache (indexé sur l'empreinte SHA-256 de la source +
paramètres) ; les filtres de présentation (`severity`, `min_score`, `limit`)
sont appliqués après coup et ne modifient jamais les métriques.

### `GET /early-warning/summary`

Compteurs par sévérité + métadonnées :

```json
{ "generated_at": "…", "estimate_kind": "historical_backtest",
  "data_origin": "synthetic_fixture",
  "params": { "grid_deg": 0.25, "recent_days": 14, "baseline_days": 730,
              "thresholds": {"watch": 0.55, "moderate": 0.72, "high": 0.88},
              "min_detections": {"watch": 3, "moderate": 6, "high": 12} },
  "period": { "data_start": "…", "data_end": "…", "recent_start": "…",
              "recent_end": "…", "baseline_end": "…" },
  "summary": { "n_cells_evaluated": 264, "n_cells_total": 357,
               "n_alerts": 11,
               "by_severity": {"NORMAL": 253, "WATCH": 11,
                               "MODERATE": 0, "HIGH": 0} },
  "source": { "n_files": 3, "digest_sha256": "…", "source_dir_kind": "fixture" },
  "notes": "…", "elapsed_s": 0.93 }
```

Filtres optionnels : `severity` (`NORMAL|WATCH|MODERATE|HIGH`), `min_score`
([0, 1]), `limit` (≤ 5000).

### `GET /early-warning/alerts`

Liste des cellules évaluées, tri : sévérité décroissante puis score
décroissant. Chaque alerte :

```json
{ "cell_id": "765:385", "cell_i": 765, "cell_j": 385,
  "lon": 11.375, "lat": 6.375, "severity": "WATCH", "score": 0.85,
  "ratio": 26.571,
  "recent": { "days": 14, "detections": 3, "daily_mean": 0.214 },
  "baseline": { "median_daily": 0.0081, "q90_daily": 0.0286,
                "level": "region", "sufficient": false,
                "n_days_with_detection": 4 },
  "reasons": ["ratio_26.6x", "baseline_insuffisante"] }
```

- `cell_id` = `ci:cj` (index de grille, origine −180°/−90°).
- `baseline.level` ∈ `cell` | `region` | `global` (lissage hiérarchique) ;
  `baseline.sufficient` = historique ≥ 30 jours avec détection.
- `severity` ∈ `NORMAL` | `WATCH` | `MODERATE` | `HIGH` — seuils de score
  **et** planchers de détections absolues (voir `params`).
- `score` ∈ [0, 1] : force statistique d'excès d'activité (Poisson
  sur-dispersé + ratio robuste) — **pas une probabilité d'incendie**.
- `reasons` : explications lisibles (`ratio_Xx`, `baseline_insuffisante`, …).

Mêmes filtres que `/summary` + `limit`. Réponse : `{ generated_at,
estimate_kind, data_origin, params, period, summary, filters, alerts[],
notes, source }`.

### `GET /early-warning/alerts/{cell_id}`

Détail d'une cellule (`ci:cj`, ex. `720:360`). 400 si format invalide, 404 si
la cellule n'a pas été évaluée. Mêmes paramètres de calcul que `/alerts`
(sans les filtres de présentation).

```bash
curl -s 'https://<hôte>/api/v1/early-warning/summary?source=fixture'
curl -s 'https://<hôte>/api/v1/early-warning/alerts?severity=HIGH&limit=20'
curl -s 'https://<hôte>/api/v1/early-warning/alerts/765:385'
```

Exemples de réponses réelles : `docs/fixtures/early_warning/*.json`.
Méthodologie complète : `docs/EARLY_WARNING_BACKEND.md`.

---

## 6. Upload (validation, jamais d'intégration)

### `POST /datasets/validate`

`multipart/form-data`, champ `file` (`.csv`, UTF-8) ; `Content-Type` accepté :
`text/csv`, `application/csv`, `text/plain`, `application/octet-stream`,
`application/vnd.ms-excel`. Colonnes obligatoires : `latitude`, `longitude`,
`acq_date`, `acq_time`, `satellite`.

```bash
curl -s -X POST https://<hôte>/api/v1/datasets/validate \
  -H 'Content-Type: multipart/form-data' -F 'file=@mon_fichier.csv'
```

Réponse 200 (audité, **jamais intégré**, `integrated: false`,
`data_origin: "uploaded_file"`) :

- `dataset` : nom du fichier, capteur déduit, satellites/versions observés ;
- `counts` : `n_records`, `n_rows_analysable`, `n_anomalies`,
  `n_anomalies_sampled` ;
- `period` : bornes `acq_date` des lignes analysables ;
- `anomalies_by_category` + `anomalies_sample[]` (`line_number`, `column`,
  `raw_value`, `category`, `reason`, `classification`) : valeurs brutes
  tracées, **jamais corrigées** ;
- `note` : politique (aucune correction, aucune intégration, absence de
  détection ≠ absence de feu).

Erreurs : 400 (nom/vide/colonnes), 413 (taille), 415 (type), 401 (jeton).

---

## 7. Expériences (jobs)

### `POST /experiments` → `202`

```bash
curl -s -X POST https://<hôte>/api/v1/experiments \
  -H 'Content-Type: application/json' ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
  -d '{"pair":"terra__aqua","grid_deg":0.25,"window_days":8,"source":"auto"}'
# → { "job_id": "3fa4856e12ab", "status": "queued",
#     "links": { "self": "…/experiments/3fa4856e12ab", "result": "…/result" } }
```

Corps : `pair` (`terra__aqua` | `aqua__viirs_snpp`), `grid_deg`
(0.1 | 0.25 | 0.5), `window_days` (1 | 4 | 8 | 16), `source`
(`auto` | `fixture` | `raw`, défaut `auto`). Valeur hors configuration → 400
listant les valeurs admises. En-tête `Location` = URL de suivi.

### `GET /experiments/{job_id}` → suivi

`status` : `queued` → `running` → `succeeded` | `failed` ; champs
`created_at`, `started_at`, `finished_at`, `error` (message, jamais de pile),
`params`, `links`. 404 si inconnu (id = 12 hex).

### `GET /experiments/{job_id}/result`

200 quand `succeeded` ; **409** tant que non terminé (« Réessayer plus tard »)
ou si échoué. Le champ `result` contient l'enveloppe complète de provenance :
`started_at`, `finished_at`, `elapsed_s`, `params`, `data_origin`,
`source` (`n_files`, `n_rows_*`, `digest_sha256`), `software`, `warning`, et
les métriques sous `result.result` : `n_a`, `n_b`, `intersection`, `union`,
`jaccard`, `monthly[]`, `spatial_top[]`.

```bash
curl -s https://<hôte>/api/v1/experiments/$JOB/result | jq '.result.result.jaccard'
```

### `GET /experiments`

Liste des tâches connues du processus (`count`, `items[]` = vues de tâche),
plus les résultats persistés relus depuis `PYROLENS_EXPERIMENTS_DIR`.

Comportement : exécution séquentielle (1 thread), `PYROLENS_MAX_JOBS` tâches
conservées (évacuation de la plus ancienne), `PYROLENS_JOBS_ENABLED=0` → 403.
Détails et limites : `docs/limitations.md` §3.

---

## 8. Authentification

Lecture ouverte (choix D6 : MVP public). Si `PYROLENS_API_TOKEN` est défini,
les deux POST exigent :

```
Authorization: Bearer <jeton>
```

sinon → 401. CORS : désactivé par défaut ; `PYROLENS_CORS_ORIGINS` (CSV)
n'autorise que `GET`. Aucun secret n'est stocké côté API ; l'API ne lit jamais
`FIRMS_MAP_KEY` ni `EARTHDATA_*`.

---

## 9. Spécification OpenAPI

- Servie à `/api/v1/openapi.json` (Swagger UI : `/api/v1/docs`, ReDoc :
  `/api/v1/redoc`).
- Export de référence versionné : **`docs/openapi.json`** — à régénérer après
  tout changement de route :

```bash
python3 -c 'import json; from api.app import app; \
  open("docs/openapi.json","w",encoding="utf-8").write( \
  json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n")'
python3 -m pytest tests/api -q   # les tests vérifient le document exporté
```

- Les réponses à lignes (`meta` + `rows`) et les objets de lignes sont libres
  par conception (ajout de champs possible) : ce fichier décrit la **structure**,
  `docs/api.md` les **champs publiés**.
