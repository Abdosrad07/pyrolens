# Early Warning Backend — Détection d'anomalies d'activité de feu

## 1. Vue d'ensemble

Service backend « early warning » pour PyroLens : détection statistique
d'anomalies d'activité de feu par cellule de grille, exposée via trois
endpoints FastAPI en lecture seule.

| Endpoint | Rôle |
|---|---|
| `GET /api/v1/early-warning/summary` | Compteurs par sévérité + métadonnées |
| `GET /api/v1/early-warning/alerts` | Liste des cellules évaluées (filtres) |
| `GET /api/v1/early-warning/alerts/{cell_id}` | Détail d'une cellule |

**Garde-fou central** : toutes les réponses portent
`estimate_kind = "historical_backtest"`. Les données FIRMS sont des archives /
NRT avec latence documentée — le service ne prétend **jamais** faire du
suivi temps réel, et une cellule sans détection n'implique jamais l'absence
de feu.

## 2. Modules livrés

| Fichier | Rôle |
|---|---|
| `src/pyrolens/anomaly_detection.py` | Moteur statistique (agrégation, baseline, score, sévérité) |
| `api/services/early_warning.py` | Service API : résolution source, cache, filtres, vues |
| `api/routers/early_warning.py` | Router FastAPI (3 GET) |
| `api/app.py` | Enregistrement du router (modifié, additif uniquement) |
| `tests/test_anomaly_detection.py` | 29 tests unitaires du moteur |
| `tests/api/test_early_warning.py` | 25 tests d'intégration API |
| `docs/fixtures/early_warning/*.json` | Exemples de réponses pour le frontend |

Aucun module de prédiction ni aucun autre backend existant n'a été modifié.

## 3. Méthodologie statistique

### 3.1 Agrégation

Les CSV FIRMS sont agrégés en **compteurs journaliers par cellule**
(`latitude`, `longitude`, `acq_date`, `frp`). Maillage par défaut 0,25°
(origine −180°/−90°, cohérente avec `pyrolens.grids`). Les lignes non
interprétables (date/coordonnées invalides) sont ignorées — cohérent avec
l'audit qui les isole sans correction.

### 3.2 Baseline robuste

Par cellule, sur une fenêtre de référence glissante (défaut 730 jours,
plafonnée à `recent_start − 1`) :

- **médiane** et **q90** des comptes journaliers (zéros inclus) ;
- **lissage hiérarchique** cellule → bande de latitude 5° → global, pour les
  cellules à historique insuffisant (`n_days_with_detection < 30`) ;
- la moyenne n'est jamais utilisée seule (dominée par les pics).

### 3.3 Score d'anomalie ∈ [0, 1]

Combine deux composantes :

1. **Score de comptage** : `1 − P(X ≥ recent_total)` sous
   `Poisson(λ = baseline_médiane × recent_days × dispersion)`, où la
   dispersion (q90/médiane, bornée [1, 8]) approxime la sur-dispersion des
   données zéro-lourdes. Calcul de la queue de Poisson par récurrence stable.
2. **Score de ratio** : `log1p(mean_recent / baseline_médiane) / log1p(10)`
   (ratio 10× ≈ 1,0), pondéré à 35 %.

Score final = `0,65 × comptage + 0,35 × ratio`, borné [0, 1], avec pénalité
× 0,85 si la baseline est insuffisante. **Ce n'est pas une probabilité
d'incendie** : c'est une force statistique d'excès d'activité détectée.

### 3.4 Sévérité

`NORMAL / WATCH / MODERATE / HIGH` via seuils configurables **et** un plancher
d'activité absolue (évite d'alerter sur 0→1 détection dans une cellule vide) :

| Sévérité | Score ≥ | Détections récentes ≥ |
|---|---|---|
| WATCH | 0,55 | 3 |
| MODERATE | 0,72 | 6 |
| HIGH | 0,88 | 12 |

Seuils et planchers exposés dans `params` de chaque réponse.

### 3.5 Persistance et capteurs

Chaque alerte porte deux champs additionnels :

- **`persistence`** : nombre de jours consécutifs en fin de fenêtre récente
  dont le compte journalier dépasse la médiane de la baseline (baseline nulle
  → tout jour avec ≥1 détection compte). Mesure la *durée* de l'écart, pas
  seulement son amplitude.
- **`sensors`** : capteurs actifs sur la fenêtre récente, normalisés depuis
  les colonnes `satellite` / `instrument` du CSV FIRMS
  (`modis` | `viirs-snpp` | `viirs-noaa` | `unknown`). Permet de distinguer
  une détection confirmée par plusieurs instruments d'un artefact isolé.

### 3.6 Fenêtres temporelles

- `recent_days` (défaut 14) : fenêtre « récente » comparée à la baseline.
- `baseline_days` (défaut 730) : profondeur de la référence.
- `reference_date` (optionnel, AAAA-MM-JJ) : borne la fin de la fenêtre
  récente ; sans elle, la fenêtre se termine à la dernière détection des
  données. Les données postérieures à `reference_date` n'influencent jamais
  le résultat.

## 4. Contrat API

Paramètres communs (query) : `source` (`auto|fixture|raw`), `grid_deg`,
`recent_days`, `baseline_days`, `reference_date`, plus filtres de
présentation `severity`, `min_score`, `limit` (summary/alerts).

Réponse type (alerts) :

```json
{
  "generated_at": "...",
  "estimate_kind": "historical_backtest",
  "data_origin": "synthetic_fixture",
  "params": {"grid_deg": 0.25, "recent_days": 14, "baseline_days": 730,
             "thresholds": {...}, "min_detections": {...}},
  "period": {"data_start": "...", "data_end": "...",
             "recent_start": "...", "recent_end": "...", "baseline_end": "..."},
  "summary": {"n_cells_evaluated": 264, "n_cells_total": 357,
              "n_alerts": 11, "by_severity": {"NORMAL": 253, "WATCH": 11,
              "MODERATE": 0, "HIGH": 0}},
  "filters": {"severity": null, "min_score": null, "limit": null,
              "cell_id": null, "matched": 264},
  "alerts": [
    {"cell_id": "765:385", "cell_i": 765, "cell_j": 385,
     "lon": 11.375, "lat": 6.375, "severity": "WATCH", "score": 0.85,
     "ratio": 26.571,
     "recent": {"days": 14, "detections": 3, "daily_mean": 0.214},
     "baseline": {"median_daily": 0.0081, "q90_daily": 0.0286,
                  "level": "region", "sufficient": false,
                  "n_days_with_detection": 4},
     "persistence": 9,
     "sensors": ["modis", "viirs-snpp"],
     "reasons": ["ratio_26.6x", "baseline_insuffisante"]}
  ],
  "notes": "...",
  "source": {"n_files": 3, "digest_sha256": "...", "source_dir_kind": "fixture"}
}
```

- `cell_id` = `ci:cj` (index de grille, origine −180°/−90°) ; le endpoint
  `/alerts/{cell_id}` accepte aussi le format `ci_cj` utilisé par le frontend.
- Tri : sévérité décroissante puis score décroissant.
- 404 si la cellule n'a pas été évaluée ; 400 sur paramètre invalide ;
  409 si la source est vide.
- Aucun chemin local exposé ; `data_origin` ∈ `nasa_firms | synthetic_fixture | custom_source`.

#### Couche de compatibilité Early Warning Center

`summary_view` et `alerts_view` exposent **additivement** les champs attendus
par `frontend/src/services/earlyWarning.js` (sans toucher au contrat
canonique) :

- `/summary` : `n_cells_monitored`, `n_anomalies`, `n_high_priority`,
  `n_increasing_zones`, `data_period`, `recent_window`, `historical_backtest`.
- `/alerts` : `items[]` (cellules non-NORMAL, sévérité `low|moderate|high`,
  `cell_id` en `ci_cj`, `recent_detections`, `historical_baseline`,
  `activity_change`, `persistence`, `sensors`, `observation_period`,
  `anomaly_score`, `reason`, `limitations`) et `meta` (résumé frontend).

## 5. Cache et performance

Le calcul est protégé par un cache en mémoire indexé sur
`(source_dir, digest_sha256(source), grid_deg, recent_days, baseline_days,
reference_date)`. Les filtres de présentation sont appliqués après coup et ne
modifient jamais les métriques. Borné à 8 configurations.

Performance mesurée :
- fixture (3 CSV) : ~1 s ;
- archive FIRMS complète (1 170 CSV, ~4,4 M lignes) : ~70 s au premier appel
  (chargement I/O), ensuite servi depuis le cache.

## 6. Fixtures frontend

`docs/fixtures/early_warning/` : `summary.json`, `alerts.json` (50 premières),
`cell.json` — générées depuis la source synthétique (`data_origin =
synthetic_fixture`), prêtes pour l'intégration frontend.

## 7. Tests

- **Unitaires** (`tests/test_anomaly_detection.py`, 29 tests) : agrégation,
  baseline (cellule/région/global), score (pic, normal, baseline nulle,
  insuffisante), sévérité (seuils + planchers + personnalisés), persistance,
  capteurs (labels + suivi par jour), fenêtre `reference_date`, tri,
  provenance, entrées invalides.
- **API** (`tests/api/test_early_warning.py`, 25 tests) : les 3 endpoints,
  filtres, tri, 400/404/409, cache, OpenAPI, absence de chemin local,
  compatibilité frontend (champs `items`/`meta`, sévérité `low|moderate|high`,
  `cell_id` `ci_cj`).

Suite complète : **173 tests, tous verts** (`pytest tests -q` → EXIT=0).

## 8. Limites connues

- **Pas de temps réel** : latence FIRMS (NRT ~3 h, archive quotidienne) ; le
  service est un *backtest historique*, pas un système d'alerte opérationnel.
- **Observabilité** : les jours sans enregistrement ne sont pas distingués
  d'une absence de feu quand la couverture satellite n'est pas documentée ;
  la baseline traite les zéros comme « activité détectée nulle ».
- **Sur-dispersion** : approximée par q90/médiane (proxy), pas par un
  estimateur de variance dédié.
- **Échelle** : maille 0,25° par défaut ; les résultats ne sont pas
  comparables entre mailles sans recalcul.
- **Source unique** : un seul répertoire CSV par calcul ; pas de fusion
  multi-source.
- **Première exécution coûteuse** sur la pleine archive (~70 s) ; le cache
  amortit les appels suivants.
