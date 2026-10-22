# Spécifications d'écrans — tableau de bord PyroLens

Shell commun (tous écrans) : sidebar 250 px (marque, période, navigation 6
vues, pied avec `pipeline <version>` / `artefacts <generated_at>` / état des
erreurs) + zone principale (`max-width 1280 px`). Chargement initial :
« Chargement des artefacts du pipeline… » jusqu'à `loadAll()` résolu.

**Chiffres = artefacts (D1)** : `baselines/summary.csv` et artefacts horodatés
uniquement. Chaque écran qui affiche des chiffres porte le badge d'origine
(`data_origin`) et l'horodatage (`generated_at`).

---

## Écran 1 — « Synthèse d'exécution » (`Overview.jsx`)

- **Rôle** : dire en un écran ce qui a réellement été exécuté et ce qui est
  bloqué, sans interprétation.
- **Structure** :
  1. bandeau d'origine (`banner info` nasa_firms / `banner warn`
     synthetic_fixture) ;
  2. rangée de cartes (`cards`) : étapes exécutées `n / total`, blocages
     documentés (rouge si > 0), période cible `AAAA-MM-JJ → AAAA-MM-JJ`,
     origine des données, fichiers téléchargés (manifeste) ;
  3. panneau « Étapes » : table étape → statut (`pill ok|blocked|ref`) + artefact
     attestant ;
  4. panneau « Blocages documentés » (`.blocker`) : `what` / `detail` /
     `action` pour chaque blocage (Earthdata, etc.) ;
  5. panneau inventaire / manifeste : sources, compteurs, provenance.
- **Données** : `execution.json`, `inventory.json`, `downloads.json`,
  `audit.json` (`data_origin`).
- **États** : origine synthétique → `banner warn` obligatoire ; artefact absent
  → carte à « — » + entrée dans `data.errors[]` (pied de sidebar).
- **Acceptation** : aucun compte affiché sans origine visible ; blocages jamais
  présentés comme résolus.

## Écran 2 — « Audit des données » (`Audit.jsx`)

- **Rôle** : comptabilité des lignes et qualité, avec les libellés exacts du
  pipeline.
- **Structure** :
  1. cartes : fichiers audités, lignes bien formées, lignes analysables, hors
     emprise (« ambigu, exclu »), anomalies classées ;
  2. panneau comptabilité (`row_accounting`) : chaque ligne du décompte +
     rappel `4 572 + 1 272 = 5 844` capteur-jours le cas échéant ;
  3. graphique anomalies par catégorie (recharts, barres horizontales) ;
  4. graphiques distributions : FRP (histogramme), confiance par capteur,
     volumes mensuels (séries) ;
  5. panneau « Jours sans enregistrement » : négation explicite
     (« aucun_enregistrement — jamais “pas de feu” »), 200 entrées max.
- **Données** : `audit.json`.
- **Acceptation** : `grep` sur l'écran = uniquement des **négations** ;
  hors-emprise toujours présenté comme exclusion ambiguë, jamais comme erreur.

## Écran 3 — « Baselines de concordance » (`Baselines.jsx`)

- **Rôle** : explorateur des 24 configurations (2 paires × 3 grilles ×
  4 fenêtres), source unique des chiffres D1.
- **Structure** :
  1. filtres (`controls` + `select`) : paire, maille (0,1° / 0,25° / 0,5°),
     fenêtre (1 / 4 / 8 / 16 j) ;
  2. cartes de la configuration active : `n_a`, `n_b`, intersection, union,
     **Jaccard** (mono) ;
  3. table de toutes les configurations : `pair, grid, window, n_a, n_b, ∩, ∪,
     jaccard` — équation lisible `∪ = n_a + n_b − ∩` ;
  4. série mensuelle du Jaccard (recharts, ligne) pour la configuration
     active ;
  5. divergence jour/mois/région (configuration primaire) : tables + graph ;
  6. distribution spatiale : top cellules (comptages par capteur) ;
  7. note d'interprétation permanente : « Jaccard = |A ∩ B| / |A ∪ B| calculé
     par le pipeline ; aucune sélection par maximisation ».
- **Données** : `baselines.json` (+ `summary.csv` en amont).
- **Acceptation** : chaque Jaccard affiché recoupé ligne à ligne avec
  `summary.csv` ; aucune configuration mise en avant parce qu'elle maximise le
  Jaccard.

## Écran 4 — « Observabilité (4 états) » (`Observability.jsx`)

- **Rôle** : les 4 états du pipeline par capteur, sans jamais conclure à
  l'absence de feu.
- **Structure** : cartes par capteur (Terra / Aqua / VIIRS) avec les 4 états
  (`détection observée`, `conditions plausibles sans détection`,
  `observabilité inconnue`, `indéterminé`) ; barres empilées (recharts) ;
  bandeau expliquant `coverage_products_acquired = false` → l'état par défaut
  est « observabilité inconnue ».
- **Données** : `observability.json` (`states`, `state_labels`, `note`).
- **Acceptation** : aucun état « pas de feu » ; l'origine `coverage=false`
  est affichée dès que l'état « inconnu » domine.

## Écran 5 — « Rapport scientifique » (`Report.jsx`)

- **Rôle** : rendre le Markdown du rapport généré (rendu maison, aucune
  dépendance MD).
- **Structure** : `.md` (titres, tables, blocs de code, listes) + bandeau
  horodatage + lien/mention de `scientific_report.md`.
- **Données** : `scientific_report.md` (texte brut via `data.js`).
- **Acceptation** : aucune valeur du rapport altérée ; table §résumé =
  `summary.csv`.

## Écran 6 — « Figures » (`Figures.jsx`)

- **Rôle** : galerie des PNG produits par `pyrolens figures`.
- **Structure** : `.fig-grid` de `figure.fig` (image + `figcaption` mono) ;
  légendes fixes (mensuel, sensibilité, anomalies, volumes, spatial,
  observabilité).
- **Données** : fichiers PNG de `web/public/artifacts/figures/`.
- **Acceptation** : aucune image sans légende ; fond blanc des PNG assumé
  (`figure.fig img`).

---

## 7. Checklist d'acceptation (tout écran)

- [ ] `npm --prefix web run build` → exit 0
- [ ] aperçu (`freebuff-preview`) : écran visible, zéro erreur console
- [ ] chiffres recoupés avec l'artefact correspondant (D1)
- [ ] `data_origin` + `generated_at` visibles si chiffres affichés
- [ ] aucune affirmation d'absence de feu ; négations explicites préservées
- [ ] avertissements d'interprétation intacts
- [ ] aucun secret / URL d'acquisition / chemin local affiché
- [ ] écran fonctionnel avec un artefact manquant (état dégradé propre)
- [ ] responsive ≤ 900 px : sidebar empilée, tables scrollables
