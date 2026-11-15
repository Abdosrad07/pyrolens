# Guide collègue — Entraîner le modèle de risque en local

> Objectif : reproduire `fire_risk.json` chez toi, puis l'améliorer avec
> plus de données. Tout est en CLI — pas besoin de l'API pour entraîner.

---

## 1. Setup (une fois)

```powershell
git clone https://github.com/Abdosrad07/pyrolens.git
cd pyrolens
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .            # ou PYTHONPATH=src partout

# Clés (téléchargements NRT seulement — l'archive pays n'en demande pas)
Copy-Item env.example .env.local   # remplir FIRMS_MAP_KEY
```

Vérification : `python -m pyrolens.cli doctor`

---

## 2. Télécharger les données

### 2a. Pipeline NRT — continuer au-delà de 2020 (recommandé en premier)

Nos 1 171 fichiers s'arrêtent à **2020-12-31**. L'API FIRMS NRT sert des
fenêtres de 5 jours pour **n'importe quelle date** — on peut donc absorber
2021→aujourd'hui :

```powershell
$env:PYTHONPATH='src'
python -m pyrolens.cli download --start 2021-01-01
```

- ~6 ans × 73 fenêtres × 2 capteurs ≈ **~870 fichiers** supplémentaires
- Reprenable : relancer la commande reprend où ça s'est arrêté
- Compter plusieurs heures ( débit ~50-60 fichiers / 150 s)
- `FIRMS_MAP_KEY` obligatoire

### 2b. Archive annuelle par pays — Afrique de l'Ouest (sans clé)

```powershell
python scripts/download_west_africa_archive.py
```

- 18 pays × MODIS+VIIRS-SNPP × 2013-2025 ≈ 468 fichiers (~3-5 Go)
- **Aucune clé** — endpoint ouvert `/data/country/{capteur}/{année}/`
- Reprenable via `data/raw/archive/` ; manifest
  `data/manifests/archive_bulk_west_africa.jsonl`
- ⚠️ Le serveur throttle les rafales : le script a une pause de politesse,
  compter ~2-3 h. Si tu coupes, relance = reprise.

### 2c. Options pour aller plus loin

| Donnée | Comment | Volume |
|---|---|---|
| VIIRS-NOAA20 (2ᵉ satellite, dès 2018) | adapter `SENSORS` dans le script → `viirs-noaa20` | ×~2 les VIIRS récents |
| Autres pays | ajouter des entrées dans `COUNTRIES` du script | au choix |
| MODIS Terra+Aqua séparés | déjà couverts (colonne `satellite`) | — |

---

## 3. Entraîner le modèle

```powershell
$env:PYTHONPATH='src'

# Modèle actuel (reproduit fire_risk.json de main)
python -m pyrolens.cli predict
# → 1215 cellules, test PR-AUC 0.926, F1 0.841 (données 2013-2020)

# Options utiles
python -m pyrolens.cli predict --grid 0.10 --window 8     # maille plus fine
python -m pyrolens.cli predict --window 16                # horizon 16 j
python -m pyrolens.cli predict --stride 3                 # échantillons plus denses
python -m pyrolens.cli predict --reference-date 2020-06-30
python -m pyrolens.cli predict --out data\fire_risk_v2.json
```

### Avec les données archive (plus performant)

Une fois 2b téléchargé :

```powershell
python -m pyrolens.cli predict --source data/raw/archive
```

- `--source` accepte maintenant les **sous-dossiers** (`rglob`) →
  `data/raw/archive/{viirs-snpp,modis}/` lus ensemble
- `data_origin` devient `firms_archive_sp` (standard processing —
  **meilleure qualité** que le NRT)
- La couverture passe de ~1 215 cellules (Cameroun) à toute
  l'Afrique de l'Ouest → carte plus riche, mais attention : les
  capteurs y sont moins denses hors axes

### Avec pipeline + archive combinés

Copie les CSV archive dans un dossier à plat avec les CSV pipeline
(ou inverse) et pointe `--source` dessus — les deux sources sont
compatibles (même schéma FIRMS, capteur lu dans la colonne `satellite`).

---

## 4. Servir le résultat

```powershell
# L'artefact par défaut atterrit dans web/public/artifacts/fire_risk.json
# → servi par GET /api/v1/fire-risk (backend) ou /artifacts/fire_risk.json (statique)

# Ou pour ton frontend React : copie dans frontend/public/artifacts/
Copy-Item web\public\artifacts\fire_risk.json frontend\public\artifacts\
```

Le frontend lit `cells[]` = `{cell_i, cell_j, lat, lon, prob, level}` —
aucun changement nécessaire côté React.

---

## 5. Ce qui rend le modèle « plus performant »

| Levier | Effet attendu | Coût |
|---|---|---|
| **+ Années** (2021+ via NRT) | le modèle apprend les feux récents, moins de dérive temporelle | ~870 fichiers, des heures |
| **+ Pays** (archive Ouest-africaine) | couverture spatiale ×18, patterns régionaux | ~468 fichiers, ~3-5 Go |
| **VIIRS-NOAA20** | 2ᵉ capteur VIIRS → meilleure observabilité diurne | modeste |
| **Fenêtres météo (ERA5)** | les vrais drivers (sécheresse, vent) — le saut qualitatif | ⚠️ nouveau pipeline, pas encore implémenté |
| `--window 16` | anticiper plus loin, plus incertain | test PR-AUC à comparer |
| `--grid 0.10` | maille fine, plus de cellules | ×4 les échantillons, +lent |

**Rappel honnêteté** : plus de données ≠ détection de feux réels — le
label reste « ≥1 détection FIRMS ». Les métriques (PR-AUC, F1, Brier)
devront être comparées sur **la même période test** pour être
interprétables ; ne change pas train/val/test sans le documenter.

---

## 6. En cas de souci

| Symptôme | Cause probable | Fix |
|---|---|---|
| `Aucun CSV dans …` | `--source` pointe un dossier vide | vérifie le chemin, `rglob` accepte les sous-dossiers |
| Téléchargement lent/bloqué | FIRMS throttle les rafales | relance le script — le cache reprend où il en était |
| `unresolved` en masse | sondes HEAD rejetées | réessaie plus tard ; `_probe` a un retry ×2 intégré |
| PR-AUC bas sur archive | moins de passages satellites hors Cameroun | normal — la couverture est hétérogène, documente-le |
| `data_origin` inattendu | `firms_archive_sp` = archive standard processing | normal et **préférable** au NRT |

Référence complète : `docs/FIRE_RISK_PREDICTION.md` (détail du modèle),
`docs/PROJECT_OVERVIEW.md` §7 (explication pédagogique).
