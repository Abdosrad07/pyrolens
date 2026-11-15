# PyroLens — Phase 2 (recherche & analyse MODIS / VIIRS, pilote Cameroun)

> **📖 Documentation complète** : [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)
> — architecture, données, API, frontend, **modèle de prédiction expliqué**,
> limites scientifiques et lancement.

Pipeline Python reproductible d'audit, de baselines de concordance et d'analyse
d'observabilité entre **MODIS Terra**, **MODIS Aqua** et **VIIRS Suomi-NPP 375 m**,
avec rapports scientifiques servis en web (Vite + React + Recharts).

> **Origine des données.** L'API FIRMS est acquise avec la clé `FIRMS_MAP_KEY` fournie :
> `data/raw/firms/` contient **1 170 fenêtres canoniques de 5 jours (585 MODIS + 585 VIIRS),
> 2013-01-01 → 2020-12-31, 0 jour manquant**, et tous les rapports récents portent
> `data_origin = nasa_firms`. Les archives **Earthdata Login** (granules standard,
> produits de couverture/nuages) restent **bloquées sans identifiants** (HTTP 302,
> `docs/data_inventory.md` §5) : sans ces produits, l'observabilité classe par défaut
> « observabilité inconnue » et **jamais** « pas de feu ». L'échantillon synthétique
> (`data/fixture/`, `synthetic_fixture`) reste utilisable pour la démo et les tests.

---

## 0. Démarrage rapide (interface + API)

Trois processus suffisent pour tout faire tourner en local :

```powershell
# 1) Clés (une seule fois) : copier le gabarit puis remplir
Copy-Item env.example .env.local   # FIRMS_MAP_KEY, EARTHDATA_*, PYROLENS_API_TOKEN…
#    .env.local est gitignoré — ne JAMAIS mettre de clé dans env.example (versionné)

# 2) Backend API FastAPI — port 8010 (8010 évite les conflits courants sur 8000)
python -m uvicorn api.index:app --host 127.0.0.1 --port 8010

# 3) Frontend Vite — port 5173, proxy /api → 8010
$env:PYROLENS_API_ORIGIN='http://127.0.0.1:8010'   # ou via web/.env.local
npm --prefix web run dev
```

| Interface | URL | Contenu |
| --- | --- | --- |
| **Fire Monitor** (recommandée) | `http://localhost:5173/fire-monitor.html` | Carte Leaflet + tuiles NASA GIBS, vues Aperçu / Calendrier / Expériences / Données / Méthodologie / Qualité, **analyse de zone FIRMS** : NRT ~5 j (clic carte → jauge → Jaccard) **et historique archive 2019→aujourd'hui** (CSV annuels par pays, cache `data/raw/archive/`) |
| React (historique) | `http://localhost:5173/` | Les 6 écrans de rapport + Harmonization Lab sur artefacts |
| API | `http://127.0.0.1:8010/api/v1` | Docs interactives : `/api/v1/docs` — OpenAPI : `/api/v1/openapi.json` |

**Sans backend** : les vues artefacts (Aperçu, Calendrier pipeline, Qualité) fonctionnent
en mode statique ; Expériences, Données, Méthodologie et l'analyse de zone affichent un
message « API requise ».

**Variables utiles** (`.env.local`, lues par le pipeline ET l'API) :
`FIRMS_MAP_KEY` (analyse de zone + `pyrolens download`), `EARTHDATA_*` (granules),
`PYROLENS_API_TOKEN` (protège les POST), `PYROLENS_CORS_ORIGINS`, `PYROLENS_SOURCE_DIR`,
`PYROLENS_ARCHIVE_DIR` (cache des CSV annuels archive, défaut `data/raw/archive`).

**Historique par zone** : la section « Historique archive » du panneau zone
(`/firms/history`) couvre n'importe quelle bbox via les fichiers annuels
`/data/country/{sensor}/{year}/{Pays}.csv` de FIRMS — **sans clé**, qualité
standard processing (VIIRS-SNPP dès 2012, MODIS dès 2000). Les pays sont
résolus par intersection bbox/polygones Natural Earth ; chaque fichier est
téléchargé une fois (parallèle par plages HTTP) puis filtré sur la bbox.
Le serveur archive est lent (~Ko/s par connexion) : le premier appel peut
durer longtemps, les suivants sont servis depuis le cache.

---

## 1. Installation

```bash
pip install -r requirements.txt     # Python 3.10+ (constaté : 3.10.12)
python3 -m pytest                   # 91 tests (31 pipeline + 60 API)
python3 -m pyrolens.cli doctor      # état de l'environnement (noms de clés, jamais de valeurs)
```

Les commandes s'exécutent avec `PYTHONPATH=src python3 -m pyrolens.cli …`
(abrégé `pyrolens` ci-dessous).

## 2. Commandes

| Commande | Rôle |
|---|---|
| `pyrolens doctor` | versions, bibliothèques, présence des clés (noms uniquement) |
| `pyrolens geo` | télécharge la géométrie d'emprise documentée (Natural Earth) |
| `pyrolens inventory` | inventaire **réel** produits/périodes via l'API CMR (sans clé) |
| `pyrolens download` | emprise + API FIRMS + probe de granule standard ; enregistre succès **et** échecs |
| `pyrolens fixture` | génère l'échantillon **synthétique** déterministe (démo/tests) |
| `pyrolens audit [--source DIR]` | audit qualité → `reports/`, CSV d'anomalies, journal |
| `pyrolens baselines` | baselines A/B/C → `baselines/` + artefacts JSON |
| `pyrolens observability` | classification en 4 états d'observabilité |
| `pyrolens figures` | figures PNG → `figures/` (+ artefacts web) |
| `pyrolens report` | `reports/scientific_report.md` **et** `.docx` |
| `pyrolens run` | séquence complète (geo → inventaire → acquisition → audit → baselines → figures → rapport) |
| `pyrolens web-artifacts` | vérifie les JSON consommés par le frontend |

Reproduction intégrale :

```bash
PYTHONPATH=src python3 -m pyrolens.cli run
python3 -m pytest
```

## 3. Accès aux données NASA (à fournir par vous, jamais dans le chat)

| Variable d'environnement | Usage | Où l'obtenir |
|---|---|---|
| `FIRMS_MAP_KEY` | API FIRMS (CSV par emprise, ≤ 5 jours/requête) | https://firms.modaps.eosdis.nasa.gov/api/map_key/ (gratuit, envoyé par e-mail) |
| `EARTHDATA_USER` + `EARTHDATA_PASSWORD` **ou** `EARTHDATA_TOKEN` | granules standard MOD14 / MYD14 / VNP14IMG et produits d'observabilité | https://www.earthdata.nasa.gov/data/earthdata-login (gratuit) — alternative : un `~/.netrc` avec `urs.earthdata.nasa.gov` |

Renseignez-les dans **Settings → Environment** (ou `.env.local`) : le pipeline les lit via
`os.environ`, aucun secret n'est écrit dans Git ni affiché. Aucun mécanisme
d'authentification n'est contourné.

Une fois les clés fournies :

```bash
PYTHONPATH=src python3 -m pyrolens.cli download
PYTHONPATH=src python3 -m pyrolens.cli run --source data/raw/firms
```

Les CSV réels sont alors prioritaires sur `data/fixture` (détection automatique).

## 4. Rapports web

Deux interfaces coexistent :

- **`web/public/fire-monitor.html`** — interface « Fire Monitor » (socle maquette
  `fire-monitor-aurel.html`) : carte + toutes les vues métier + analyse de zone
  FIRMS (`POST /api/v1/firms/analyze`, voir `docs/phase2/api_contract.md`).
- **`web/` (Vite + React + Recharts)** — les 6 écrans de rapport + Harmonization Lab.

Les deux lisent les artefacts statiques JSON/PNG (`web/public/artifacts/`) : aucune
base de données, aucun calcul côté client. Une **API FastAPI** (`api/`, contrat
`docs/api.md`, OpenAPI `docs/openapi.json`) sert les mêmes artefacts en JSON —
exports, validation de fichiers téléversés, expériences de comparaison et analyses
de zone en tâche de fond. Les fronts restent fonctionnels sans elle (mode statique).
Commandes depuis la racine du projet :

```bash
npm --prefix web install   # installation des dépendances du frontend
npm --prefix web run dev   # serveur de développement (0.0.0.0, port injecté par Freebuff)
npm --prefix web run build # build statique -> web/dist/
```

Les commandes enregistrées pour Freebuff sont exactement ces trois-là (`freebuff-preview
set-install` / `set` / `set-build`).

Après toute exécution du pipeline : `pyrolens figures` et `pyrolens report` rafraîchissent
les artefacts consommés par l'interface.

## 5. Comparer avec l'exploratoire v0.3

Les chiffres v0.3 (grille 0,25°, fenêtres 1 j / 8 j / 1 mois) **ne sont pas fournis dans
cet environnement** : le dépôt ne contient aucun résultat antérieur. Ils ne sont ni repris
ni recalculés (`reports/scientific_report.md` §11 les liste comme « valeurs de référence »).
Pour une comparaison : déposer les CSV v0.3 et les documenter dans `docs/` — puis confronter
`baselines/summary.csv` (configurations 0,25° × {1, 8} j) aux valeurs de référence, en
conservant l'étiquetage calculé/référence.

## 6. Structure du dépôt

```
config/pipeline.yaml     paramètres de traitement versionnés (aucun secret)
src/pyrolens/            modules : cmr, download, ingest, audit, grids, baselines,
                         observability, harmonization, figures, report, fixture, cli
tests/                   91 tests pytest — 31 pipeline (audit, grilles, Jaccard,
                         observabilité, immuabilité de data/raw, rapport/DOCX)
                         + 60 API (dossier tests/api/)
api/                     API FastAPI v1 (lecture seule + jobs) — docs/api.md
docs/                    index README.md, methodology.md, data_inventory.md,
                         references.md, technical.md, api.md, openapi.json,
                         limitations.md
docs/phase2/             dossier de phase 2 : validation des données (rapport A),
                         méthode scientifique, plan de validation, périmètre MVP,
                         architecture/API/frontend, décisions à valider, plan de lot
frontend-handoff/        handoff UI : écrans, design system, parcours, mockups
data/                    raw/ (brut, immuable), fixture/ (synthétique), manifests/ (SHA-256)
reports/                 audit Markdown, anomalies CSV, journaux, rapport .md/.docx
baselines/               CSV des baselines et sensibilités
figures/                 PNG
web/                     frontend Vite + React + Recharts
```

## 7. Ce qui a réellement été exécuté (octobre 2026)

- inventaire CMR **réel** : 35 019 granules dans la bbox 2013-2020 (MOD14 10 878,
  MYD14 11 083, VNP14IMG 13 058) — voir `docs/data_inventory.md` §3 ;
- emprise Natural Earth réelle (SHA-256 documenté) ;
- **acquisition FIRMS réelle** (clé `FIRMS_MAP_KEY`, 9 802 requêtes journalisées dans
  `data/manifests/downloads.json`) : 1 170 fenêtres canoniques, 0 jour manquant,
  aucun échec résiduel ; fermeture Earthdata toujours bloquée (sans identifiants) ;
- **normalisation** : 1 432 fichiers → 1 170 fenêtres canoniques dédoublonnées —
  557 292 doublons stricts supprimés (5 017 580 → 4 460 288 lignes, comptabilité
  vérifiée, `data/manifests/normalize.json`) ;
- audit **sur données réelles** (1 170 fichiers, 2 634 700 anomalies classées),
  24 configurations de baselines, observabilité (4 états, aucun « pas de feu »),
  6 figures, rapport MD + DOCX, **91 tests verts** — `data_origin = nasa_firms`.

## 8. État, décisions et suite

- **D1 validée (21/10/2026)** : source unique des chiffres = `baselines/summary.csv`
  (aucune valeur de phase 1 republicée) — `docs/phase2/decisions_to_validate.md`.
- **API v1 livrée** : `api/` (lecture seule + expériences), contrat `docs/api.md`,
  spécification `docs/openapi.json`, 60 tests dédiés.
- **Reste à trancher** : D2-D8 (`docs/phase2/decisions_to_validate.md`) puis lots S1-S4
  (`docs/phase2/implementation_plan.md`). Point de blocage scientifique principal :
  `EARTHDATA_USER`/`EARTHDATA_PASSWORD` (ou `EARTHDATA_TOKEN`) dans **Settings →
  Environment** pour les granules standard et les produits de couverture/nuages (D4),
  faute de quoi l'observabilité reste par défaut en « observabilité inconnue ».
- L'état actuel est intégralement reproductible avec `pyrolens run` +
  `python3 -m pytest` ; la documentation est indexée dans `docs/README.md`.
