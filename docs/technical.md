# Documentation technique — PyroLens

Architecture, installation, déploiement, gestion des erreurs et des logs,
sécurité. Les limites connues ont leur propre document : `docs/limitations.md`.
Le contrat d'interface est dans `docs/api.md` (+ `docs/openapi.json`).

---

## 1. Architecture

### 1.1 Vue d'ensemble

```
┌──────────────────── pipeline Python (src/pyrolens) ─────────────────────┐
│ download/geo/inventory → normalize → audit → baselines → observability │
│ → figures → report → web-artifacts                                     │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ écrit (horodaté, reproductible)
                               ▼
                 web/public/artifacts/*.json|md|png   ← source de vérité
                 baselines/*.csv                      ← référentiel des chiffres (D1)
                               │
          ┌────────────────────┴────────────────────┐
          ▼                                         ▼
   web/ (Vite + React)                     api/ (FastAPI, lecture seule)
   data.js charge les artefacts            sert les mêmes artefacts en JSON,
   6 vues, aucun calcul scientifique       + exports, + jobs d'expériences
```

Deux consommateurs, **une seule source** : les artefacts écrits par le pipeline.
Ni le front ni l'API ne recalculent les chiffres publiés ; seules les expériences
(`POST /api/v1/experiments`) exécutent du calcul, avec la même bibliothèque
`pyrolens.grids`/`pyrolens.baselines` et une provenance complète.

### 1.2 Structure de l'API (`api/`)

| Fichier | Rôle |
|---|---|
| `api/app.py` | `create_app()` : FastAPI, lifespan, CORS optionnel, montage des routeurs sous `/api/v1` |
| `api/index.py` | point d'entrée production (`uvicorn api.index:app`) |
| `api/settings.py` | `Settings` gelé lu dans l'environnement (`.env.example`) ; ne lit **jamais** `FIRMS_MAP_KEY`/`EARTHDATA_*` |
| `api/store.py` | `ArtifactStore` : lecture artefacts, cache mémoire par empreinte (mtime+taille), ETag faibles |
| `api/errors.py` | enveloppe `{"error": {code, message}}`, handlers 400/401/403/404/405/409/413/415/500 |
| `api/security.py` | Bearer optionnel sur les POST (`PYROLENS_API_TOKEN`) |
| `api/jobs.py` | file d'attente en mémoire, 1 thread, persistance des résultats JSON |
| `api/schemas.py` | modèles de réponse (compatibles par ajout de champ) |
| `api/services/` | métier : `catalog`, `queries`, `validation`, `experiments` |
| `api/routers/` | HTTP uniquement : `system`, `catalog`, `audit`, `baselines`, `validation`, `experiments` |

Règle : la couche HTTP ne contient **aucune** logique métier ; tout calcul vit
dans `src/pyrolens/` (partagé avec la CLI).

### 1.3 Frontend (`web/`)

Vite + React + Recharts, CSS pur (`web/src/index.css`), HMR désactivée par la
plateforme (`vite.config.js` : ne pas toucher). Tous les accès artefacts passent
par `web/src/data.js`. Handoff complet : `frontend-handoff/`.

---

## 2. Installation et mise en service

```bash
# Python 3.10+ (constaté : 3.10.12)
pip install -r requirements.txt        # pipeline + API (fastapi, uvicorn, polars, …)

# Frontend
npm --prefix web ci                    # ou npm --prefix web install

# Contrôles
PYTHONPATH=src python3 -m pyrolens.cli doctor   # noms de clés, jamais de valeurs
python3 -m pytest                               # pipeline + API
npm --prefix web run build                      # build statique → web/dist
```

Configuration : `cp env.example .env.local` puis renseigner. Toutes les
variables sont documentées dans `env.example` ; `.env.local` écrase `.env`.

### Lancer en local

```bash
# API (port 8000 par défaut)
PYTHONPATH=src uvicorn api.index:app --host 0.0.0.0 --port 8000
# ou
PYTHONPATH=src python3 -m api.index

# Front (via la plateforme)
freebuff-preview set "npm --prefix web run dev" 5173   # déjà enregistré
freebuff-preview start
```

Régénérer les artefacts après changement de pipeline :

```bash
PYTHONPATH=src python3 -m pyrolens.cli run          # séquence complète
PYTHONPATH=src python3 -m pyrolens.cli web-artifacts
```

---

## 3. Déploiement (Freebuff)

- **Front** : commande de build `vite build` (voir `web/package.json`) →
  `web/dist/` statique ; l'install est `npm ci`. Aucune étape Python dans
  l'install/build (l'image d'hébergement est Node.js only).
- **API** : `api/*.py` + `requirements.txt` à la racine — l'hébergeur installe
  les dépendances Python lui-même ; l'entrée est `api/index.py` (`app`).
- Vérifier ce que l'hébergeur exécutera réellement :

```bash
freebuff-deploy check      # commandes + problèmes éventuels, sans dépenser un build
freebuff-deploy status     # état, framework, temps de build
freebuff-deploy logs       # erreurs de build d'un déploiement
freebuff-deploy start      # redéployer après correction
```

- **Variables de production** : `freebuff-deploy env list` / `freebuff-deploy
  env set '{"KEY":"value"}'` — les valeurs `.env` du sandbox sont des valeurs de
  dev. En production, définir si besoin `PYROLENS_API_TOKEN`,
  `PYROLENS_CORS_ORIGINS` ; ne **jamais** fournir `FIRMS_MAP_KEY`/`EARTHDATA_*`
  à l'API de production (acquisition = pipeline local).
- Après changement des commandes : re-passer par `freebuff-preview set-install`
  / `set-build` puis `freebuff-deploy check`.

---

## 4. Erreurs et logs

### 4.1 Enveloppe d'erreur

Toute réponse non-2xx est du JSON UTF-8 :

```json
{ "error": { "code": "404", "message": "Route inconnue." } }
```

| Code | Signification |
|---|---|
| 400 | paramètre/fichier invalide (validation requête, colonnes absentes, fichier vide, nom ≠ .csv) |
| 401 | `Authorization: Bearer` attendu (`PYROLENS_API_TOKEN` défini) |
| 403 | expériences désactivées (`PYROLENS_JOBS_ENABLED=0`) |
| 404 | ressource inconnue (artefact-filtre inexistant, job, dataset) |
| 405 | méthode non autorisée (l'API est en lecture seule hors 2 POST) |
| 409 | source indisponible / job non terminé ou échoué |
| 413 | upload trop volumineux (`PYROLENS_MAX_UPLOAD_BYTES`) |
| 415 | type de contenu d'upload refusé |
| 500 | artefact indisponible/illisible ou erreur interne (détail uniquement côté serveur) |

Aucun message ne contient de pile d'exception ni de chemin serveur.

### 4.2 Journalisation

- Logger racine `pyrolens.api` (+ `pyrolens.api.jobs` pour les tâches) :
  erreurs internes avec pile (`logger.exception`), échecs d'expériences,
  démarrage (répertoires, jobs activés ou non).
- Niveau par défaut `WARNING` ; rendre visible avec `LOG_LEVEL=INFO`/`DEBUG`
  si besoin (`logging.basicConfig` côté serveur).
- Lecture des logs :
  - aperçu local : `freebuff-preview logs`
  - production : `freebuff-deploy logs`
- Côté pipeline : `reports/logs/` (journal d'exécution `pyrolens run`).

---

## 5. Sécurité

1. **Lecture seule** : seuls `POST /api/v1/experiments` et
   `POST /api/v1/datasets/validate` modifient de l'état (file de tâches,
   fichiers temporaires supprimés). Aucune écriture dans `data/raw`.
2. **Auth optionnelle** : les 2 POST exigent `Authorization: Bearer
   $PYROLENS_API_TOKEN` si la variable est définie ; sans elle, API ouverte
   (choix D6 : MVP public). Jeton comparé en temps constant simple, jamais stocké.
3. **CORS strict** : désactivé par défaut ; `PYROLENS_CORS_ORIGINS` (CSV) et
   méthodes limitées à `GET`.
4. **Secrets** : l'API ne lit jamais `FIRMS_MAP_KEY` ni `EARTHDATA_*` ;
   aucune clé dans `web/`, les artefacts ou les réponses ; `.env*` ignoré par
   git, `env.example` ne contient que des valeurs vides. Vérification :
   `grep -rniE "(map_key|earthdata_token|bearer [A-Za-z0-9])" web/dist docs/openapi.json`.
5. **Upload** : streaming par blocs de 1 Mo avec plafond, écrit dans un
   répertoire temporaire système (`pyrolens-upload-*`) supprimé après analyse ;
   nom de fichier réduit à son nom de base ; aucun chemin exposé en réponse.
6. **Limitation des ressources** : 1 thread de calcul, `PYROLENS_MAX_JOBS`
   résultats conservés (évacuation FIFO), cache mémoire plafonné par empreinte
   fichier, TTL négatif de 30 s pour artefacts absents.
7. **Transparence** : chaque réponse porte `data_origin`/`generated_at` ; rien
   n'affirme une absence de feu (contrat éditorial, `CONTRIBUTING.md` §3).

---

## 6. Continuité de service et reproductibilité

- Les artefacts sont écrits de façon **atomique-compatible** (lecture par
  empreinte mtime+taille) : une régénération pendant une requête ne sert que des
  versions complètes ; l'ETag change dès que l'artefact change.
- `Cache-Control: public, max-age=60` + `ETag` faible ; `If-None-Match` → 304.
- Les résultats d'expériences sont persistés dans
  `PYROLENS_EXPERIMENTS_DIR` : ils survivent au redémarrage (relecture disque),
  pas les tâches en cours (voir `docs/limitations.md`).
- Reproduction intégrale des chiffres : `pyrolens run` + `pytest`, mêmes
  entrées → mêmes artefacts (horodatage `generated_at` mis à jour).
