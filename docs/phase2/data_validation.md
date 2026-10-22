# Rapport A — Validation des données réelles (provenance, fichiers, aberrations)

**Période de référence des chiffres** : artefacts du 18/10/2026 (audit 12:33, baselines 12:39,
observabilité 12:43), figures et rapport du 19/10 09:08 ; contrôles de disque refaits le 20/10/2026.
**Origine des données** : `data_origin = nasa_firms` (API FIRMS, jamais le fixture de démonstration).

Ce document fait foi pour citer un chiffre sur les données réelles. Toute valeur qui n'y figure
pas ni n'est présente dans les artefacts horodatés **ne doit pas être publiée**.

---

## 1. Provenance vérifiable

| Élément | Preuve | Où |
|---|---|---|
| Acquisition FIRMS (API `area/bbox`) | URL, code HTTP, octets, SHA-256, horodatage par requête — **9 802 requêtes** | `data/manifests/downloads.json` |
| Dédoublonnage / canonisation | entrées/sorties par source, comptabilité vérifiée par le code | `data/manifests/normalize.json` |
| Historique d'exécution (étapes, statuts, blocages) | append-only depuis le 16/10 | `web/public/artifacts/execution.json` |
| Inventaire CMR (versions de produits, granules) | API CMR publique, sans clé | `web/public/artifacts/inventory.json` |
| Statut des secrets | clés lues dans l'environnement, **jamais** versionnées | `freebuff-env list`, `config/pipeline.yaml` (aucun secret) |

Chronologie utile : blocage initial `FIRMS_MAP_KEY absent` (16/10) → acquisition réelle le
18/10 (quota de l'API géré par erreurs puis reprises idempotentes) → `normalize` (12:29) →
reprise `download` qui complète 10 fenêtres sans enregistrement (12:30) → `audit` (12:33) →
`baselines` (12:39) → `observability` (12:43) → figures/rapport (19/10 09:08).
Le blocage **Earthdata** (granules standard, produits de couverture/nuages) persiste : HTTP 302
vers Earthdata Login, sans `EARTHDATA_USER`/`EARTHDATA_PASSWORD` (ou `EARTHDATA_TOKEN`).

## 2. Inventaire des fichiers (contrôle direct sur disque, 20/10)

- **1 170 CSV canoniques** : 585 `modis_sp_*.csv` + 585 `viirs_snpp_sp_*.csv`,
  fenêtres de 5 jours alignées sur l'epoch (limite de l'API FIRMS : 5 jours par requête),
  période continue **2013-01-01 → 2020-12-31, 0 fenêtre manquante**.
- **4 461 458 lignes au total** = 4 460 288 lignes de données + 1 170 en-têtes.
- **10 fenêtres MODIS à en-tête seul** (la requête FIRMS est revenue vide → « aucun
  enregistrement », jamais « pas de feu ») : 2013-08-04, 2014-08-29, 2014-09-08, 2015-09-13,
  2016-07-14, 2016-07-19, 2017-08-18, 2019-08-08, 2019-08-23, 2020-08-17 (débuts de fenêtre).
- Sources d'API : `MODIS_SP` et `VIIRS_SNPP_SP` = « Standard Processing » (qualité science,
  **non NRT**) — voir `config/pipeline.yaml` et la doc API FIRMS v4.2.0.

## 3. Comptabilité de normalisation (vérifiée)

`data/manifests/normalize.json` (18/10 12:29) :

| Étape | MODIS | VIIRS | Total |
|---|---:|---:|---:|
| fichiers lus | 721 | 711 | **1 432** |
| fichiers écrits (canoniques) | 575 | 585 | **1 160** |
| fichiers supprimés (chevauchements de fenêtres) | 146 | 126 | **272** |
| lignes lues | 841 649 | 4 175 931 | **5 017 580** |
| lignes écrites | 718 897 | 3 741 391 | **4 460 288** |
| doublons stricts supprimés | 122 752 | 434 540 | **557 292** |

Équation imposée par le code (`ValueError` sinon) et recoupée ici :
`5 017 580 = 4 460 288 + 557 292` ✓ et `1 432 = 1 160 + 272` ✓.
Les **10 fenêtres MODIS vierges** ont été créées par la reprise `download` de 12:30
(fichiers à en-tête seul) : `1 160 + 10 = 1 170` fichiers finaux ✓.

## 4. Aberrations (audit du 18/10 12:33, 1 170 fichiers)

Comptabilité des lignes (`row_accounting` dans `audit.json`) :

| Catégorie | Nombre | Signification |
|---|---:|---|
| lignes bien formées (lues) | 4 460 288 | 100 % des lignes de données |
| **lignes mal formées** | **0** | aucune ligne tronquée/ininterprétable |
| analysables dans l'emprise | 1 825 588 | utilisées pour les ensembles |
| hors emprise, conservées | 2 634 697 | tracées, exclues des ensembles |
| exclues non interprétables | 0 | aucune |

Anomalies classées : `outside_emprise` **2 634 697** + `duplicate_key` **3** = **2 634 700**,
toutes classées *ambiguës*. **Aucune** anomalie de type `invalid_latitude`, `invalid_longitude`,
`invalid_date`, `invalid_time`, `invalid_frp`, `invalid_confidence`, `missing_value`,
`duplicate_row` (colonnes manquantes : `{}`).

Interprétation des trois résidus :

1. **Hors emprise (99,99 % des anomalies)** : la bbox de requête `[8.4, 4.1, 16.4, 13.2]`
   englobe le polygone administratif Natural Earth 110 m ; les détections du bassin côtier,
   du lac Tchad et des pays voisins sont donc téléchargées puis écartées par le filtre
   polygonal. Comportement attendu, jamais « corrigé ».
2. **3 `duplicate_key`** : même `(lat, lon, date, heure, satellite)` avec FRP/confiance
   différents — conservées en trace, exclues des ensembles.
3. **10 fenêtres MODIS sans aucune ligne** (§2).

## 5. Contenu physique constaté

- **Capteurs/satellites** : `Terra`, `Aqua`, `N` uniquement (S-NPP). Aucun NOAA-20 (`1`) ni
  NOAA-21 (`2`) : la règle d'exclusion du pilote ne s'applique donc à rien — vérifié.
- **Versions** : `6.03` (MODIS, archive Collection 6.1 — cohérent avec `inventory.json`
  CMR `061` pour MOD14/MYD14) et `2` (VIIRS, Collection 2 — `002` pour VNP14IMG).
- **Confiance (jamais convertie)** : VIIRS `n` 2 942 087 / `l` 646 577 / `h` 152 727
  (somme = 3 741 391 = lignes VIIRS après normalize ✓) ; MODIS entiers de 44 à 100
  (somme = 718 897 = lignes MODIS ✓).
- **FRP** (MW) sur les lignes analysables : n = 1 825 588, min 0.0, max 2 015.7, moyenne 10.709.
- **Jours** : 4 572 capteur-jours avec ≥ 1 détection analysable ; **1 272 capteur-jours sans
  aucun enregistrement** dans la plage couverte du capteur (+2 lignes de synthèse = 1 274
  entrées dans `temporal_gaps`, 200 détaillées dans l'artefact) ;
  `4 572 + 1 272 = 5 844 = 2 × 2 922 jours` ✓.
  Lecture brute (toutes lignes, hors filtre d'emprise) : 5 270 capteur-jours avec enregistrements
  (MODIS 2 438, VIIRS 2 832), 574 sans aucun.
  Libellé imposé : **`aucun_enregistrement`**, jamais « pas de feu ».

## 6. Résultats quantitatifs de référence

**Baselines (24 configurations = 2 paires × 3 grilles × 4 fenêtres, `baselines/summary.csv`) :**

| Paire | Jaccard min | Jaccard max | Primaire (0,25° / 8 j) |
|---|---:|---:|---:|
| Terra – Aqua | 0,102715 (0,10° / 1 j) | 0,650183 (0,50° / 16 j) | **0,463729** |
| Aqua – VIIRS S-NPP | 0,177808 (0,10° / 1 j) | 0,658829 (0,50° / 16 j) | **0,582794** |

À la configuration primaire : Terra–Aqua `n_a` 22 344, `n_b` 36 858, ∩ 18 756, ∪ 40 446 ;
Aqua–VIIRS `n_a` 36 858, `n_b` 60 172, ∩ 35 727, ∪ 61 303. La croissance du Jaccard avec la
maille et la fenêtre est l'effet mécanique à quantifier, **pas** une amélioration de la mesure
(`docs/methodology.md` §2 et §4).

**Observabilité (0,25°, `coverage_products_acquired = false`) :** par capteur, 259 653
capteur-cellule-jours au total — Terra 39 271 détections / 220 382 « observabilité inconnue » ;
Aqua 84 165 / 175 488 ; VIIRS 246 024 / 13 629. **Aucun état « pas de feu » n'existe**.

**Divergence régionale (primaire 0,25° / 8 j, terciles de latitude = proxy documenté)** :
voir `baselines/regional_divergence.csv` (sud/centre/nord par paire).

## 7. Vérification des résultats annoncés en phase 1

| Annonce de phase 1 | Verdict | Preuve |
|---|---|---|
| 31 tests verts | **confirmé** (`31 passed`) | `python3 -m pytest` (exit 0) |
| « 12 lignes malformées » | **non transposable** : sur données réelles `lignes_mal_formées = 0` ; le décompte 12 provient de l'audit du fixture synthétique du 16/10 (« 3 fichiers audités, 12 anomalies », `execution.json`) | `audit.json → row_accounting` |
| Jaccard 0,263 / 0,777 / 0,310 / 0,789 | **non reproduits** : aucune occurrence dans les artefacts actuels ; valeurs probables de l'époque synthétique | recherche exhaustive du dépôt + `baselines/summary.csv` (§6) |
| valeur « 310.82791 » | **introuvable** dans le dépôt | recherche exhaustive |

**Décision associée (D1, `decisions_to_validate.md`) — validée le 21/10/2026 : « uniquement
summary.csv »** : les valeurs de phase 1 sont retirées des communications ; le référentiel
unique est `baselines/summary.csv` et `audit.json` horodatés du 18/10.

## 8. Limites (renvoi)

Produits de couverture/nuages non acquis → observabilité par défaut inconnue ; emprise
Natural Earth 110 m ; aucune référence indépendante au sol ; comparaisons ensembles/clés sans
mise en correspondance événement-à-événement. Détail : `docs/methodology.md` §10 et
`docs/data_inventory.md` §5.

## 9. Reproductibilité

```bash
python3 -m pytest                                  # 31 tests
PYTHONPATH=src python3 -m pyrolens audit           # recalcule l'audit
PYTHONPATH=src python3 -m pyrolens baselines       # 24 configurations
PYTHONPATH=src python3 -m pyrolens observability   # 4 états
```
`data/raw/` est immuable (SHA-256 avant/après, `tests/test_reproducibility.py`).

## 10. Références documentaires consultées (19/10)

- Attributs MODIS/VIIRS : https://www.earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs
- FAQ FIRMS : https://www.earthdata.nasa.gov/data/tools/firms/faq
- API area/bbox (noms de sources, limites 5 jours/requête, quotas) : https://firms.modaps.eosdis.nasa.gov/api/area/
- Conventions appliquées et testées dans le code : `acq_time` HHMM **UTC** sans zéro de tête
  (`21` = 00:21, `136` = 01:36 — `src/pyrolens/audit.py`), confiance MODIS 0-100 vs VIIRS
  `l/n/h` (`src/pyrolens/schema.py`), brightness en K, FRP en MW, `daynight` D/N, dates UTC,
  coordonnées WGS84 décimales, bbox `[ouest, sud, est, nord]`.
