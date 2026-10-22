# Architecture backend — phase 2

**Principe directeur** : le pipeline Python (`src/pyrolens/`) est la **source de vérité** ;
le navigateur ne fait que **lire des artefacts horodatés**. Toute évolution doit préserver
cette séparation (aucun calcul scientifique côté client, aucun secret côté client).

---

## 1. État actuel (au 20/10/2026) — « pipeline + artefacts statiques »

```
config/pipeline.yaml ──┐
data/raw/firms/*.csv ──┼─▶ pyrolens (Typer) ──▶ artefacts horodatés ──▶ web/public/artifacts/
(manifests SHA-256)     │    doctor/geo/inventory/       reports/  baselines/  figures/      ▲
                        │    download/normalize/audit/   (MD + DOCX) (CSV/JSON)  (PNG)       │ fetch
                        │    baselines/observability/                                        │
                        │    figures/report/web-artifacts                                    │
                        └─────────────────────────────────────────────▶ web/ (Vite 5 + React 18 + recharts)
                                                                        serveur d'aperçu géré par Freebuff
```

- **Aucun serveur applicatif** : `web/src/data.js` fait `fetch('/artifacts/…')` sur des fichiers
  statiques. 6 vues, 7 fichiers JSON + 1 Markdown + 6 PNG.
- **Données lues** : `execution`, `inventory`, `downloads` (5,9 Mo), `audit`, `baselines`,
  `observability`, `scientific_report.md`.
- **Tests** : 31 tests sur le Python ; le frontend n'a pas de tests unitaires (couverture
  limitée par build + relecture, `validation_plan.md` §3).

## 2. Options

### Option A — statique pur (recommandée pour le MVP, = état actuel)

| | |
|---|---|
| Forces | zéro infrastructure, reproductible, hébergement any-statique, pas de runtime à maintenir, données cohérentes par construction (les artefacts sont générés ensemble) |
| Limites | poids total servi (~8 Mo) ; requêtes filtrées côté client ; recalcul nécessite de relancer le pipeline |
| Effort | ~0 (maintien) |

**Ajustements recommandés (P1)** : exclure `downloads.json` du chargement initial ou publier
une version agrégée ; `Cache-Control` sur `/artifacts` si le coût de rechargement gêne.

### Option B — API légère FastAPI (conditionnée à D2)

À activer **seulement** si un besoin de requêtes filtrées/paginées, d'agrégation à la volée
ou de réutilisation externe est établi.

```
web/ (statique)  ──fetch──▶  /api/v1/*  ──▶  api/index.py (FastAPI)
                                                  │
                                                  ├─ lecture des artefacts (cache en mémoire, TTL)
                                                  ├─ import de pyrolens pour filtres/agrégations
                                                  └─ plus tard : pipelines lancés côté serveur
```

- **Emplacement conforme à l'hébergement** : `api/index.py` + `requirements.txt` à la racine
  (l'installateur d'hébergement gère Python lui-même ; aucune étape Python dans les commandes
  d'install/build du frontend).
- **Entrée unique** : un seul module d'entrée type `app = FastAPI()` exporté, CORS restreint à
  l'origine du site, ETag sur les réponses dérivées d'artefacts (validité = `generated_at`).
- **Cache** : lecture des JSON une fois au démarrage + TTL ; invalide à redéploiement.
- **Aucun appel sortant vers FIRMS/Earthdata depuis l'API** : l'acquisition reste une opération
  du pipeline, en local, avec les clés d'environnement.
- **Coût** : un service à maintenir en plus ; le MVP n'en tire rien tant que P1-1 suffit.

### Option C — base de données (déconseillée tant que les données sont figées)

Les données changent uniquement par exécution du pipeline (2013-2020, figées) ; une base
ajouterait synchronisation, migration et point de défaillance sans gain. À revoir si une
nouvelle région/période ou des mises à jour continues arrivent (décision explicite requise).

## 3. Sécurité et secrets

- Clés (`FIRMS_MAP_KEY`, `EARTHDATA_*`) : **exclusivement** dans l'environnement du pipeline,
  jamais dans `config/pipeline.yaml`, jamais dans le bundle Vite (`validation_plan.md` §4.7).
- L'API (option B) n'expose que des données dérivées publiques ; aucun endpoint d'écriture,
  aucune authentification dans le MVP (D6).
- Toute valeur de production distincte passe par `freebuff-deploy env set` (les `.env` de
  sandbox sont des valeurs de développement).

## 4. Hébergement

| Voie | Statut |
|---|---|
| **Freebuff (par défaut)** : build `vite build` → `dist/`, aperçu géré, déploiement géré par la plateforme ; l'API optionnelle serait alors servie ailleurs | recommandée pour le MVP |
| **Hébergeur externe type Vercel** (statique + fonctions Python) : pertinente après connexion GitHub si l'équipe veut du CI/CD Git | alternative, décision D3 |
| **Serveur dédié Docker** | hors MVP (maintenance) |

Aucune de ces voies n'exige de changer le code aujourd'hui : l'option A est portable telle quelle.

## 5. Recommandation

1. **MVP : option A** (aucune modification d'architecture) + correctifs P1.
2. **Option B** : go/no-go à D2, lot S2 (`implementation_plan.md`) — seulement si un besoin
   concret de requêtes côté serveur est identifié pendant l'usage du MVP.
3. **Option C** : jamais sans nouvelle décision écrite.
