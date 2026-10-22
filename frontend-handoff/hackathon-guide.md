# Guide hackathon — intégrer le backend et livrer la vraie interface

> Public : le/la frontend engineer qui reprend PyroLens pour (A) brancher
> l'API FastAPI sur l'interface, puis (B) produire l'interface web réelle du
> projet pour le hackathon. Ce document est le point d'entrée ; il ne remplace
> ni `docs/api.md` (contrat API), ni `design-system.md` (jetons), ni
> `screen-specifications.md` (écrans).

---

## 0. Référentiel en 30 secondes

| Besoin | Fichier |
|---|---|
| Contrat des endpoints (champs publiés) | `docs/api.md` |
| Structure machine (types, schémas) | `docs/openapi.json` → Swagger `/api/v1/docs` |
| Bascule statique → API pas à pas | `frontend-handoff/api-integration.md` |
| Jetons, classes CSS, responsive | `frontend-handoff/design-system.md` |
| Les 6 écrans + checklist §7 | `frontend-handoff/screen-specifications.md` |
| Maquette HTML cliquable | `frontend-handoff/mockups/index.html` |
| Règles éditoriales (contrat D1…) | `frontend-handoff/README.md` §3 |

**État du dépôt (oct. 2026)** : front statique Vite 5 + React 18 + Recharts,
CSS pur (aucun UI-kit), build `web/dist/` servi par un Worker Cloudflare
(`web/sites-worker.js`) — aperçu publié, dépôt GitHub `Abdosrad07/pyrolens`
(branche `main`). API FastAPI v1 en lecture seule (`api/`), 91 tests pytest
dont 60 API. **Le front est pleinement fonctionnel sans l'API** : c'est le
mode par défaut, à conserver.

**Fait important** : l'app réelle compte **8 écrans** — `views/Landing.jsx`
(page d'accueil), `Auth.jsx` (session simulée) et les 6 vues de rapports.
Le handoff documente les 6 vues seulement : les specs Landing/Auth sont à
produire (Mission B, B-0).

---

## 1. Démarrage (10 minutes)

```bash
# Front
npm --prefix web ci
npm --prefix web run build        # exit 0 obligatoire
npm --prefix web run dev          # Vite, PORT injecté par la plateforme

# API (porte 8000)
pip install -r requirements.txt
PYTHONPATH=src uvicorn api.index:app --host 0.0.0.0 --port 8000
# Swagger : http://localhost:8000/api/v1/docs

# Tests
python3 -m pytest                 # 91 tests (31 pipeline + 60 API)
python3 -m pytest tests/api -q    # API seule
```

Arborescence utile (tout est relatif à la racine du dépôt) :

```
web/src/
├── main.jsx          import "./index.css" — jamais retirer
├── App.jsx           shell : landing | auth | 6 vues (VIEWS), session, sidebar
├── data.js           UNIQUE couche d'accès aux données (loadAll, fmt, labels)
├── Auth.jsx          session simulée (sessionStorage) — branche réelle à venir
├── index.css         tous les jetons :root (ne pas dupliquer de classes)
└── views/            Landing, Overview, Audit, Baselines, Observability,
                      Report, Figures
api/                  FastAPI v1 — app.py (CORS, routes), settings.py (env)
```

---

## 2. Mission A — brancher le backend sur l'interface

### A-1. Principes (non négociables)

1. **Une seule couche d'accès** : tout passe par `web/src/data.js`. Les vues
   ne font jamais `fetch()` elles-mêmes ; elles reçoivent `data.*` en props.
   Remplacer l'implémentation de `loadAll()` suffit à basculer l'app.
2. **Base URL unique** : `VITE_API_BASE` (vide = mode statique, renseigné =
   mode API). Aucun autre fichier ne doit connaître l'URL.
3. **Mêmes clés de données** : l'API renvoie les mêmes artefacts ; les routes
   à lignes ajoutent `{ meta, rows }` → normaliser dans `data.js`, jamais dans
   une vue.
4. **Mode statique préservé** : `VITE_API_BASE` absent → l'app reste servable
   hors-ligne depuis `/artifacts`. Aucune dépendance réseau obligatoire à
   l'affichage.

### A-2. Étapes

**Étape 1 — configuration locale** (`.env.local`, jamais committé) :

```bash
# côté front (Vite lit .env.local)
VITE_API_BASE=http://localhost:8000

# côté API (lecture de l'env du processus uvicorn)
PYROLENS_CORS_ORIGINS=http://localhost:5173
```

⚠️ CORS côté API n'autorise que **GET** (`api/app.py`,
`allow_methods=["GET"]`). C'est largement suffisant pour Mission A (les GET
sont le cœur du dashboard) ; pour les deux POST (`/experiments`,
`/datasets/validate`) il faudra passer par un proxy même-origine ou élargir
`allow_methods` côté back — décision à prendre avec le backend, pas en
douce dans le front.

**Étape 2 — `data.js`** : ajouter `apiGet(path, params)` (modèle complet dans
`api-integration.md` §3) puis brancher `loadAll()` sur les endpoints suivants
en cas de `API_BASE` sinon comportement actuel :

| `loadAll()` actuel (statique) | Endpoint API v1 |
|---|---|
| `execution.json` | — (aucun équivalent : garder l'artefact) |
| `inventory.json` / `downloads.json` | `GET /catalog` |
| `audit.json` | `GET /audit/summary?detail=1` |
| `baselines.json` | `GET /summary` + `GET /series/jaccard?pair=…` |
| `observability.json` | `GET /observability` |
| `scientific_report.md` | `GET /report` (`text/markdown`) |
| PNG `figures/` | — (rester statique) |

**Étape 3 — normalisation et erreurs** dans `data.js` :

- `{ meta, rows }` → exposer `rows` sous la clé attendue par les vues ;
- erreur HTTP → `throw` → poussée dans `data.errors[]` (canal déjà présent,
  affiché tel quel) ; l'enveloppe d'erreur est `{ error: { code, message } }` ;
- `304` (ETag) → retourner l'état en mémoire, ne pas effacer l'écran ;
  les GET envoient `ETag` + `Cache-Control: max-age=60`.

**Étape 4 — vérification écran par écran** : pour chacune des 6 vues,
comparer le nombre affiché et sa provenance (`data_origin`, `generated_at`)
avec `curl` direct sur l'endpoint. Aucun écart ne doit subsister : D1 impose
que l'API **recalcule jamais** les valeurs publiées (source unique
`baselines/summary.csv`).

**Étape 5 — étendre sans casser** (optionnel, cf. `api-integration.md` §4) :
bouton d'export CSV (`GET /export?dataset=summary&format=csv`), écran
« Expériences » (POST → polling 1 s → `/result`), validation de fichier
(`POST /datasets/validate`).

### A-3. Garde-fous sécurité

- **Jeton `PYROLENS_API_TOKEN` jamais dans le bundle** : toute variable
  `VITE_*` est publique. Les POST sont protégés côté serveur ; pour un front
  protégé : proxy même-origine ou saisie utilisateur, jamais `VITE_`.
- Aucun appel sortant vers FIRMS/Earthdata depuis le navigateur.
- Aucun chemin local ni URL d'acquisition affiché (l'API ne renvoie que des
  noms relatifs, gabarit `<FIRMS_MAP_KEY>`).

### A-4. Critères de fin de Mission A

- [ ] `VITE_API_BASE` vide → app identique à aujourd'hui (régression zéro)
- [ ] `VITE_API_BASE` renseignée → les 6 vues affichent les mêmes chiffres
      que le mode statique (comparaison curl/vue, écran par écran)
- [ ] API coupée → écran dégradé propre (message via `data.errors[]`,
      pas de blanc, pas de crash)
- [ ] `npm --prefix web run build` → exit 0 ; `python3 -m pytest` → 91 verts
- [ ] Zéro jeton/URL/acquisition dans le bundle (`grep` sur `web/dist/`)

---

## 3. Mission B — produire la véritable interface (hackathon)

Le socle existant est bon (maquette fidèle, contrat éditorial respecté,
données réelles). Le travail n'est pas « refaire » mais **compléter et
durcir**. Ordre de priorité :

### B-0. Resynchroniser handoff et code (bloquant pour qui reprend)

- Spécifier `Landing.jsx` (hero + modules + PIPELINE) et `Auth.jsx` dans
  `screen-specifications.md` (écrans 0), et les ajouter à la maquette
  `mockups/index.html` — aujourd'hui 6 écrans documentés pour 8 réels.
- Ajouter `landing`/`auth` au `VIEWS`-documentaire du README du handoff.

### B-1. États réels de l'interface (visibilité jury)

L'app gère déjà l'artefact absent (`« Artefact … indisponible »` dans Audit,
Baselines, Observability, Report) mais **pas l'état d'erreur réseau** et la
maquette n'illustre aucun état dégradé. À faire :

- état `loading` (existant, `.loading`) + état `erreur` (`data.errors[]`)
  rendus visibles dans l'UI, pas seulement en props ;
- banner d'origine systématique quand `generated_at` change (rafraîchissement
  après nouvelle exécution du pipeline) ;
- illustrations des 3 états dans la maquette (nominal / chargement / absent).

### B-2. Auth réelle

`Auth.jsx` valide l'e-mail **côté client uniquement** (session `sessionStorage`,
documenté en clair dans l'écran). Pour le hackathon, deux voies :

1. **Démo honnête (recommandée si le temps manque)** : garder la session
   simulée, libellé explicite déjà présent — ne jamais laisser croire à une
   authentification réelle.
2. **Branche API** : exiger `Authorization: Bearer` côté proxy/back sur les
   écritures, brancher `Auth.jsx` sur le point d'entrée correspondant **sans
   changer le markup** (c'est l'intention du fichier, cf. son docstring).

### B-3. Finitions interface

- **Code-splitting** : le bundle fait 575 ko minifié (165 ko gzip, avertissement
  Vite) → `React.lazy()` sur les vues lourdes (`Audit`, `Baselines` avec
  Recharts) pour un premier rendu rapide en démo.
- **Figures** : l'app affiche les vrais PNG (`/artifacts/figures/…`) ; la
  maquette affiche des placeholders — les remplacer par les PNG réels pour
  que la maquette reste un miroir honnête.
- **Responsive ≤ 900 px** : vérifier les 8 écrans (checklist §7), en
  particulier Landing (hero) et les tables de Baselines.
- **Contrôles Baselines** : dans l'app ils sont fonctionnels (`useState` +
  `onChange`) ; ne pas « réparer » la maquette statique en y ajoutant du JS,
  sauf à documenter qu'elle n'est plus autonome.

### B-4. Exigences de démo (le jour J)

1. Build + aperçu : `npm --prefix web run build` exit 0, zéro erreur console.
2. Pipeline exécuté à jour (`pyrolens run` ou `figures` + `report`) pour que
   les `generated_at` soient récents.
3. Les 4 parcours du handoff passent : découverte (Landing), vérification
   d'un chiffre (Baselines, curl ↔ écran), lecture du rapport, gestion d'un
   blocage (Overview → banner Earthdata).
4. Checklists finales : `screen-specifications.md` §7 **et**
   `docs/phase2/frontend_handoff.md` §5 (en cas d'écart, le handoff fait foi
   pour les écrans, `docs/phase2/` pour le pipeline).

---

## 4. Contrat éditorial — cinq lignes rouges

1. **Jamais d'affirmation d'absence de feu** : libellés du pipeline imposés
   (`aucun_enregistrement`, « observabilité inconnue »).
   `grep -ri "pas de feu" web/src` → uniquement des négations explicites.
2. **Provenance visible** sur tout écran chiffré : `data_origin` +
   `generated_at` (banner) + pied de sidebar.
3. **Chiffres = artefacts (D1)** : source unique `baselines/summary.csv`,
   formatage via `fmt()` ; aucune constante numérique dans les vues.
4. **Avertissements d'interprétation intacts** : Jaccard ≠ précision ;
   croissance du recouvrement avec maille/fenêtre = effet mécanique ;
   hors-emprise = ambigu exclu.
5. **Aucun secret côté client** : ni `FIRMS_MAP_KEY`/`EARTHDATA_*`, ni URL
   d'acquisition, ni chemin local, ni jeton dans le bundle.

Toute violation = régression bloquante, quelle que soit la beauté de l'écran.
