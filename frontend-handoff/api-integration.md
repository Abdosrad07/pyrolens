# Intégration API — brancher le front sur l'API v1

Le front est **statique par défaut** (artefacts servis depuis `/artifacts`) et
reste pleinement fonctionnel sans backend. L'API v1 (`docs/api.md`,
`docs/openapi.json`) offre les mêmes données en JSON avec filtrage, exports et
expériences. Ce document décrit le passage de l'un à l'autre **sans rupture de
contrat** : les vues ne doivent pas changer.

---

## 1. Principes

1. **Une seule couche d'accès** : `web/src/data.js` (`getJSON`/`getText`).
   Remplacer l'implémentation de `loadAll()` suffit ; les composants de vues
   reçoivent toujours `{ data.audit, data.baselines, data.observability,
   data.execution, data.report, data.errors }`.
2. **Base URL configurable** :
   `const API_BASE = import.meta.env.VITE_API_BASE || "" ;` — vide = mode
   statique (`/artifacts/...`), renseigné = mode API (`${API_BASE}/api/v1/...`).
   Aucun autre fichier ne doit connaître l'URL.
3. **Mêmes noms de données** : l'API renvoie les artefacts décompressés aux
   mêmes clés ; les routes à lignes ajoutent une enveloppe `{ meta, rows }` —
   normaliser dans `data.js` (`.rows`) plutôt que dans les vues.
4. **D1 inchangé** : l'API sert `baselines.json` dérivé de `summary.csv` ;
   aucune valeur nouvelle n'apparaît en changeant de source.

## 2. Mapping artefact ↔ endpoint

| `data.js` (statique) | Endpoint API v1 | Note |
|---|---|---|
| `execution.json` | — (pas d'équivalent) | garder l'artefact (ou exposer via `/health` + `meta`) |
| `inventory.json` | `GET /catalog` (`provenance`) | catalogue agrège audit + inventaire |
| `downloads.json` | `GET /catalog` (`provenance.manifest`) | URLs en gabarit `<FIRMS_MAP_KEY>` |
| `audit.json` | `GET /audit/summary?detail=1` | détail des trous optionnel |
| `baselines.json` → `summary` | `GET /summary?pair&grid_deg&window_days` | `{ meta, rows }` |
| `baselines.json` → série mensuelle | `GET /series/jaccard?pair&…` | pair requis, 404 si config inexistante |
| `baselines.json` → jour/mois/région | `GET /series/divergence?pair&resolution=day\|month\|region` | configuration primaire |
| `baselines.json` → spatial | `GET /spatial?pair&…&limit&offset` | pagination |
| `observability.json` | `GET /observability?grid_deg` | 404 si maille ≠ publiée |
| `scientific_report.md` | `GET /report` | `text/markdown` |
| PNG `figures/` | — (rester statique) | fichiers servis par le front |
| — | `GET /meta`, `GET /health` | provenance agrégée / supervision |
| — | `GET /export?dataset=…` | téléchargement CSV/JSON (bouton « Exporter ») |
| — | `POST /datasets/validate` | validation de fichier (Jeton si configuré) |
| — | `POST /experiments` → suivi → `/result` | calcul à la demande (202 → polling) |
| — | `GET /early-warning/summary` | compteurs d'alertes par sévérité |
| — | `GET /early-warning/alerts?severity&min_score&limit` | liste des cellules évaluées |
| — | `GET /early-warning/alerts/{cell_id}` | détail d'une cellule (`ci:cj`) |

## 3. Exemple de bascule (data.js)

```js
const API_BASE = import.meta.env.VITE_API_BASE || "";
const HEADERS = {}; // + Authorization si PYROLENS_API_TOKEN côté back, jamais côté client

async function apiGet(path, params) {
  const url = new URL(`${API_BASE}/api/v1${path}`, window.location.origin);
  Object.entries(params || {}).forEach(([k, v]) => v != null && url.searchParams.set(k, v));
  const res = await fetch(url, { headers: HEADERS });
  if (res.status === 304) return null; // cache local : conserver le dernier état
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`); // enveloppe { error }
  return res.json();
}
```

- Les réponses d'erreur ont la forme `{ error: { code, message } }` : afficher
  `message` dans `data.errors[]` (même canal que le mode statique).
- Les GET renvoient `ETag` + `Cache-Control: max-age=60` : un
  `If-None-Match: <etag>` retourne 304 sans corps — réutiliser l'état en mémoire.

## 4. Early Warning — détection d'anomalies

Trois GET en lecture seule, calculées à la demande puis mises en cache
(indexé sur l'empreinte de la source + paramètres). **Première exécution
coûteuse sur la pleine archive (~70 s) ; les suivantes sont servies depuis le
cache** — prévoir un état de chargement côté UI.

| Besoin UI | Endpoint | Paramètres utiles |
|---|---|---|
| Bandeau « X alertes » | `GET /early-warning/summary` | `source`, `grid_deg`, `recent_days`, `baseline_days`, `reference_date` |
| Liste/carte des alertes | `GET /early-warning/alerts` | + `severity` (`NORMAL\|WATCH\|MODERATE\|HIGH`), `min_score` ([0,1]), `limit` (≤5000) |
| Fiche cellule | `GET /early-warning/alerts/{cell_id}` | `cell_id` = `ci:cj` (ex. `765:385`) ; mêmes paramètres de calcul, pas de filtres |

Champs clés d'une alerte : `cell_id`, `lon`, `lat`, `severity`, `score` ∈
[0,1], `ratio`, `recent` (détections, moyenne journalière), `baseline`
(médiane/q90, `level` ∈ `cell|region|global`, `sufficient`), `reasons[]`
(explications lisibles).

**Garde-fous éditoriaux (non négociables)** :

- `estimate_kind` vaut toujours `"historical_backtest"` — afficher la mention
  « backtest historique, pas d'alerte temps réel » près des scores.
- `score` est une **force statistique d'excès d'activité**, pas une
  probabilité d'incendie : ne jamais l'afficher comme « % de risque ».
- Une cellule absente de la liste n'implique **pas** l'absence de feu.
- `data_origin` ∈ `nasa_firms | synthetic_fixture | custom_source` :
  l'afficher comme les autres écrans (provenance visible).
- Erreurs : 400 (paramètre invalide), 404 (cellule non évaluée), 409 (source
  vide) — même canal `data.errors[]`.

Exemples de réponses réelles pour le mode statique / tests :
`docs/fixtures/early_warning/{summary,alerts,cell}.json` — utilisables comme
fixtures de repli si l'API est coupée (mode dégradé propre).

## 5. Ajouts progressifs possibles sans toucher aux vues

1. **Bouton d'export** sur l'écran Baselines : lien direct
   `GET /export?dataset=summary&format=csv` (téléchargement, en-têtes = champs
   de `summary.csv`).
2. **Écran « Expériences »** : POST `/experiments` (corps
   `pair/grid_deg/window_days/source`) → poll `GET /experiments/{job_id}`
   toutes ~1 s jusqu'à `succeeded|failed` → afficher `result.result` avec
   provenance (`data_origin`, `digest_sha256`, `elapsed_s`). En cas d'échec :
   message `error` (jamais de pile).
3. **Validation de fichier** : `POST /datasets/validate` (multipart, champ
   `file`) → restituer `counts`, `period`, `anomalies_sample` avec la mention
   `integrated: false` (« audité, jamais intégré »).

## 5. Garde-fous

- Ne jamais mettre de jeton dans le bundle (`VITE_*` est public) : l'auth des
  POST est gérée côté serveur (`PYROLENS_API_TOKEN`) — pour un front protégé,
  passer par un proxy ou une saisie utilisateur, pas par une variable `VITE_`.
- Aucun appel sortant vers FIRMS/Earthdata depuis le navigateur.
- Le mode statique reste le mode par défaut du build (pas de dépendance
  réseau obligatoire à l'affichage).
- Contrat : `docs/api.md` (champs) + `docs/openapi.json` (structure) ;
  changement de forme = rupture → mettre à jour `data.js` uniquement.
