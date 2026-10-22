# Documentation PyroLens — index

Toute la documentation du projet, par famille. **Convention D1 (validée le
21/10/2026)** : la source unique des chiffres publiés est
`baselines/summary.csv` (et ses dérivés horodatés) — aucune valeur de phase 1
n'est republicée.

---

## 1. Scientifique (comment les chiffres sont produits et ce qu'ils valent)

| Document | Contenu |
|---|---|
| [`methodology.md`](methodology.md) | question de recherche, non-objectifs, clés d'ensemble (cellule/fenêtre), filtres, métriques, interdits d'interprétation |
| [`data_validation.md`](phase2/data_validation.md) | rapport A : comptabilité des lignes, anomalies, résultats quantitatifs de référence (résumés depuis `summary.csv`), vérification des annonces de phase 1 (§7) |
| [`phase2/scientific_method.md`](phase2/scientific_method.md) | statuts H1-H6, distinction « exécuté » ≠ « validé », règles de citation |
| [`phase2/validation_plan.md`](phase2/validation_plan.md) | plans de vérification : chiffres, écrans, régression, publication |
| [`data_inventory.md`](data_inventory.md) | inventaire réel des sources (CMR, FIRMS, Earthdata), état d'acquisition |
| [`references.md`](references.md) | références scientifiques et états HTTP des API consultées |
| [`limitations.md`](limitations.md) | limites assumées : scientifiques, données, API, frontend, et quoi faire si l'une bloque |

## 2. Technique (construire, déployer, exploiter)

| Document | Contenu |
|---|---|
| [`technical.md`](technical.md) | architecture (pipeline → artefacts → front + API), installation, déploiement Freebuff, erreurs/logs, sécurité |
| [`api.md`](api.md) | contrat d'API v1 : enveloppes, codes d'erreur, chaque endpoint avec exemples curl, auth, export OpenAPI |
| [`openapi.json`](openapi.json) | spécification machine exportée depuis `/api/v1/openapi.json` (regénérée à chaque changement de route) |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | mise en place contributeur, vérifications, règles éditoriales, checklist PR |
| [`../env.example`](../env.example) | gabarit de variables d'environnement (pipeline + API), sans secret |

## 3. Phase 2 — cadrage produit (`phase2/`)

| Document | Contenu |
|---|---|
| [`phase2/mvp_scope.md`](phase2/mvp_scope.md) | périmètre MVP, user stories, critères d'acceptation |
| [`phase2/implementation_plan.md`](phase2/implementation_plan.md) | lots S0-S4, état d'avancement |
| [`phase2/decisions_to_validate.md`](phase2/decisions_to_validate.md) | décisions D1-D8 (D1 **validée** : uniquement `summary.csv`) |
| [`phase2/backend_architecture.md`](phase2/backend_architecture.md) | options statique vs API, sources de vérité |
| [`phase2/api_contract.md`](phase2/api_contract.md) | contrat v1 des données artefacts (champs partagés front/API) |
| [`phase2/frontend_handoff.md`](phase2/frontend_handoff.md) | handoff technique du front existant (structure, thème, procédures) |
| [`phase2/data_validation.md`](phase2/data_validation.md) | voir §1 (rapport A) |
| [`phase2/scientific_method.md`](phase2/scientific_method.md) / [`validation_plan.md`](phase2/validation_plan.md) | voir §1 |

## 4. Autres entrées

- Racine : [`../README.md`](../README.md) (installation, commandes, état
  d'exécution), [`../CONTRIBUTING.md`](../CONTRIBUTING.md) (règles D1),
  [`../LICENSE`](../LICENSE) (MIT).
- Handoff UI détaillé (écrans, design system, parcours, mockups) :
  [`../frontend-handoff/`](../frontend-handoff/README.md).
- Artefacts publiés (source de vérité des chiffres) :
  `../web/public/artifacts/` et `../baselines/summary.csv`.

---

**Rappels non négociables** : aucune affirmation d'absence de feu ; provenance
(`data_origin`, `generated_at`) visible partout ; Jaccard = recouvrement
d'ensembles, pas une précision ; aucun secret côté client ni dans les
artefacts.
