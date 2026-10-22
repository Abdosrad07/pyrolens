# Contribuer à PyroLens

Merci d'intégrer le projet ! Ce guide résume la mise en place, les vérifications
obligatoires et les règles éditoriales **non négociables** (contrat de lecture).
Le code est publié sous licence **MIT** (`LICENSE`), dépôt destiné à la
**visibilité publique**.

---

## 1. Mise en place

```bash
# Pipeline + API (Python 3.10+)
pip install -r requirements.txt

# Frontend (Vite + React + Recharts)
npm --prefix web ci

# Vérifier l'environnement (noms de clés, jamais de valeurs)
PYTHONPATH=src python3 -m pyrolens.cli doctor
```

Configuration : `cp env.example .env.local` puis renseigner uniquement ce dont
vous avez besoin (`.env.local` est ignoré par git ; ne jamais committer de clé).
Les clés d'acquisition (`FIRMS_MAP_KEY`, `EARTHDATA_*`) restent locales : elles
ne sont lues que par le pipeline, jamais par l'API ni par le navigateur.

## 2. Vérifications avant toute PR

```bash
python3 -m pytest                 # suite complète (pipeline + API)
npm --prefix web run build        # build frontend, doit ressortir exit 0
```

Points d'attention :

- `data/raw/firms/` (> 330 Mo) est ignoré par git : sa présence n'est pas
  requise pour la majorité de la suite, mais `pyrolens download` est nécessaire
  pour rejouer l'acquisition et pour `tests/test_reproducibility.py` complet.
  La géométrie d'emprise (`data/raw/geo/`) et l'inventaire CMR sont versionnés.
- `reports/anomalies/` (474 Mo) et `reports/experiments/` sont des sorties
  régénérables : ne **jamais** les committer.
- Après modification d'un artefact publié, régénérer et recoupler :
  `PYTHONPATH=src python3 -m pyrolens.cli run` puis
  `PYTHONPATH=src python3 -m pyrolens.cli web-artifacts`.

## 3. Règles éditoriales (contrat de lecture)

1. **D1 — une seule source de chiffres** : toute valeur Jaccard/volume publiée
   provient de `baselines/summary.csv` (et des artefacts qui en dérivent),
   horodatée et reproductible. Les anciens chiffres de phase 1 sont retirés de
   partout ; ne pas en recopier ailleurs (décision validée, voir
   `docs/phase2/decisions_to_validate.md`).
2. **Jamais d'affirmation d'absence de feu** : une absence de détection s'affiche
   « aucun_enregistrement » / « observabilité inconnue ».
   `grep -ri "pas de feu" web/src docs src` ne doit réserver qu'aux négations explicites.
3. **Provenance visible** : toute vue ou section affichant des chiffres porte
   `data_origin` et `generated_at`.
4. **Jaccard ≠ précision** : conserver les avertissements d'interprétation
   (recouvrement d'ensembles, effet mécanique de la maille/fenêtre,
   hors-emprise = ambigu exclu).
5. **Aucun secret côté client** : pas de clé ni d'URL d'acquisition dans `web/`,
   `docs/` ou les artefacts ; l'API ne lit jamais `FIRMS_MAP_KEY` / `EARTHDATA_*`.

## 4. API (`api/`)

- L'API est **en lecture seule** sur artefacts ; seuls `POST /api/v1/experiments`
  et `POST /api/v1/datasets/validate` écrivent (tâches et fichiers temporaires).
- Tests dédiés : `python3 -m pytest tests/api`.
- Contrat OpenAPI : après tout changement de route,
  régénérer la spécification (voir `docs/api.md` §« Spécification OpenAPI »).
- Les endpoints POST exigent `Authorization: Bearer $PYROLENS_API_TOKEN`
  lorsque la variable est définie.

## 5. Frontend (`web/`)

- Ne pas toucher à `web/vite.config.js` (HMR désactivée par la plateforme).
- Tous les accès aux artefacts passent par `web/src/data.js` ; aucune valeur
  codée en dur dans les vues.
- Une vue affiche `data.errors[]` en cas d'artefact manquant sans bloquer les autres.
- Checklist de validité : voir `docs/phase2/frontend_handoff.md` §5 et
  `frontend-handoff/README.md`.

## 6. Style

- Python 3.10+, docstrings et commentaires en français, style compatible
  `ruff`/`black` sans configuration exotique ; pas de dépendance ajoutée sans accord.
- React fonctionnel, hooks uniquement depuis `react` ; CSS pur via les jetons de
  `web/src/index.css` (pas de Tailwind dans ce projet).
- Commits : messages explicites en français ou anglais, une intention par commit,
  jamais de fichier de données volumineux ni d'environnement.

## 7. Checklist d'une PR

- [ ] `python3 -m pytest` vert ; `npm --prefix web run build` exit 0
- [ ] chiffres recoupés avec `baselines/summary.csv` (D1)
- [ ] aucune affirmation d'absence de feu ; provenance affichée
- [ ] aucun secret / chemin local / URL d'acquisition commité
- [ ] artefacts et (si routes modifiées) `docs/openapi.json` régénérés
- [ ] documentation mise à jour (`docs/`, `README.md`) si comportement changé
