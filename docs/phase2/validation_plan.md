# Plan de validation — phase 2

**Objet** : lister chaque contrôle qui garantit l'intégrité scientifique et technique du
produit, son état au 20/10/2026, et la procédure de rejeu. Toute tâche d'implémentation
(`implementation_plan.md`) doit passer par ce plan avant d'être déclarée terminée.

---

## 1. Contrôles automatisés (pytest — 31 tests, exit 0)

| Zone | Tests | Ce qu'ils garantissent |
|---|---|---|
| `test_ingest.py` (5) | lignes bonnes conservées, ligne malfaisante tracée avec son numéro de ligne, alias d'en-tête, détection du capteur, **confiance jamais convertie** | le parseur ne réécrit jamais le brut |
| `test_audit.py` (7) | comptage, lat hors plage **exclue jamais corrigée**, date/heure invalides signalées, FRP négatif = ambigu non réparé, doublons, hors emprise = ambigu, trous temporels sans affirmation de feu | politique d'audit (`methodology.md` §7) |
| `test_emprise.py` (4) | bbox conforme à la config, masque bbox ≠ polygone, polygone réel strict, terciles documentés | l'emprise est celle déclarée |
| `test_grids_baselines.py` (6) | origine/arrondi des cellules, alignement des fenêtres sur l'epoch, définitions de clés, ensembles, **Jaccard sur valeurs connues**, sélecteur `kind`/`satellite` | les clés et métriques sont exactes |
| `test_observability.py` (3) | sans couverture → seulement détecté/observabilité inconnue, avec couverture → conditions plausibles, **aucun état interprété comme « pas de feu »** | stratégie à 4 états |
| `test_report.py` (3) | le rapport distingue calculé vs référence, ne crash pas sans artefacts, DOCX généré | rapport fidèle |
| `test_reproducibility.py` (3) | **`data/raw` immuable (SHA-256 avant/après)**, artefacts réécrits et parse-ables, fixture déterministe | reproductibilité |

**État : 31/31 verts (exit 0), dernier passage le 20/10/2026.**

## 2. Contrôles de données (par exécution du pipeline)

| Contrôle | Méthode | État (18-20/10) |
|---|---|---|
| Comptabilité normalize | `rows_in = rows_out + doublons` et `files_in = files_out + files_removed`, levées par le code (`ValueError`) | ✓ 5 017 580 = 4 460 288 + 557 292 ; 1 432 = 1 160 + 272 |
| Comptabilité audit | `analysables + hors emprise + doublons = lignes bien formées` | ✓ 1 825 588 + 2 634 697 + 3 = 4 460 288 |
| Couverture temporelle | fenêtres de 5 j continues 2013-01-01 → 2020-12-31 | ✓ 0 fenêtre manquante (10 fenêtres sans enregistrement, tracées) |
| Cohérence ensembles ↔ observabilité | `n_a` (grille primaire, 1 j) = `detection_observed` du capteur | ✓ Terra 39 271 ; Aqua 84 165 ; VIIRS 246 024 |
| Aucun « pas de feu » | test + relecture des sorties (libellés FR) | ✓ aucun état, libellé ou texte |
| Provenance | manifests SHA-256 + `execution.json` append-only | ✓ 9 802 requêtes journalisées |
| Chiffres publiés vs artefacts | recoupement README/`docs/` ↔ JSON horodatés | ✓ fait le 20/10 (`data_validation.md` §7) |

## 3. Contrôles de livraison (frontend)

| Contrôle | Commande / observation | État |
|---|---|---|
| Typecheck/build | `npm --prefix web run build` → exit 0 (`web/dist/`) | ✓ 20/10 |
| Aperçu prêt | `freebuff-preview status` → running, HTTP 200 | ✓ 20/10 |
| Modules servis | index + 6 vues + artefacts en 200 | ✓ 20/10 |
| Cohérence affichée | badge `data_origin = nasa_firms`, périodes, chiffres = artefacts | ✓ (à re-vérifier après toute modif de vue) |

## 4. Ce qui ne peut pas encore être validé (et pourquoi)

| À valider | Blocage | Débloque avec |
|---|---|---|
| H4 : seuils par classe native | aucun jeu de référence indépendant | D5 (références au sol) |
| H5 : calibration FRP | géométrie d'observation non acquise | D4 (identifiants Earthdata) |
| H6 : généralisation dév/éval | exécution non encore faite (données disponibles) | lot S4 |
| État « conditions d'observation plausibles » | produits de couverture/nuages non acquis | D4 |
| Validation externe (registres incendies) | aucune source dans l'environnement | D5 |

## 5. Procédure de rejeu (contre-vérification indépendante)

```bash
python3 -m pytest                                  # doit rester à 31/31
PYTHONPATH=src python3 -m pyrolens doctor          # environnement
PYTHONPATH=src python3 -m pyrolens run             # séquence complète journalisée
PYTHONPATH=src python3 -m pyrolens web-artifacts   # synchronisation web
npm --prefix web run build                         # build statique
```
Points de comparaison : `data/manifests/*.json` (SHA-256 inchangés sur `data/raw/`),
`baselines/summary.csv` (24 lignes, valeurs identiques à ±0),
`audit.json → row_accounting` (comptes identiques), `execution.json` (étapes appendées,
nouveau statut sans réécriture de l'historique).

**Critère de non-régression** : toute différence inexpliquée entre deux exécutions = incident
bloquant (aucune publication tant qu'elle n'est pas expliquée).

## 6. Fréquence

- **Avant chaque publication de chiffre** : §1 + §2.
- **Après toute modification de vue ou d'artefact** : §3.
- **Après toute modification du pipeline** : §5 complet.
