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

## 4. Ajouts progressifs possibles sans toucher aux vues

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
