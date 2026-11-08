# Préparation de la démonstration — PyroLens

**Question centrale** : peut-on présenter une vidéo de 4 à 5 minutes, sans intervention manuelle dans le code, couvrant les 7 parcours demandés ?

## Parcours de démonstration requis vs réalité

| Parcours requis | État actuel | Bloquant ? |
|---|---|---|
| 1. Consultation des données | Oui : Overview affiche étapes, blocages, inventaire, manifeste | Non |
| 2. Sélection des capteurs | Oui : Baselines filtre par paire (terra__aqua, aqua__viirs_snpp) | Non |
| 3. Configuration d'une expérience | **Non** : pas d'Harmonization Lab (aucune vue UI) | **Oui** |
| 4. Lancement du traitement | **Non** : pas de bouton "lancer l'expérience" côté front | **Oui** |
| 5. Consultation des résultats | Oui : Baselines, Observability, Report, Figures affichent les artefacts | Non |
| 6. Comparaison entre capteurs | Oui : Baselines affiche Jaccard par paire et configuration | Non |
| 7. Analyse temporelle (Fire Calendar) | **Non** : pas de vue dédiée ; séries dans `baselines.json` uniquement | **Oui** |

## Blocages susceptibles de compromettre la vidéo

1. **Harmonization Lab absent** : impossible de démontrer « configurer et lancer une expérience d'harmonisation » depuis l'interface. L'API `POST /api/v1/experiments` existe mais n'a pas de bouton associé.
2. **Fire Calendar absent** : impossible de démontrer l'analyse temporelle quotidienne/hebdomadaire/mensuelle via une vue dédiée.
3. **Blocage Earthdata** : si la démo doit montrer l'acquisition des granules standard ou produits couverture/nuages, elle échouera (HTTP 302). La démo doit se cantonner aux données FIRMS déjà acquises.
4. **Build frontend non testable ici** : `npm run build` n'a pas pu être exécuté dans l'environnement d'audit (vite absent). À vérifier avant la vidéo.
5. **Chargement `downloads.json` (5,9 Mo)** au démarrage du frontend : peut ralentir le chargement initial de la démo (écart S1.1).

## Scénario de démonstration reproductible (données réellement disponibles)

**Durée cible** : 4-5 minutes. **Données** : artefacts déjà produits (FIRMS 2013-2020, `data_origin = nasa_firms`).

1. **(0:30) Accueil / provenance** : Landing affiche l'origine des données (`nasa_firms`), la période (2013-2020), le pilote Cameroun. Montrer la bannière d'origine.
2. **(1:00) Synthèse d'exécution** : Overview affiche les étapes du pipeline (geo, inventaire, download, normalize, audit, baselines, observability, figures, report) avec les statuts `ok` / `bloqué`. Montrer le blocage Earthdata documenté (honnêteté).
3. **(1:30) Audit des données** : Audit affiche les anomalies classées par catégorie, les gaps temporels (`aucun_enregistrement`), la distribution de confiance par capteur (MODIS 0-100 vs VIIRS low/nominal/high, non converties).
4. **(2:30) Baselines de concordance** : afficher la matrice de sensibilité 24 configs, Terra–Aqua et Aqua–VIIRS, Jaccard de 0,10 à 0,66. Expliquer que c'est un recouvrement d'ensembles, pas une précision. Filtrer par paire/grille/fenêtre.
5. **(3:30) Observabilité** : afficher les 4 états, avec `coverage_products_acquired = false` → état par défaut « observabilité inconnue », jamais « pas de feu ».
6. **(4:00) Rapport et figures** : afficher le rapport Markdown et les 6 figures (Jaccard sensitivity, observability states, spatial distribution, etc.).
7. **(4:30) Clôture** : rappeler la règle D1 (source unique `summary.csv`) et les limites (H4-H6 non exécutés, Earthdata bloqué).

**Ce qui ne peut pas être démontré** (à ne pas montrer ou à présenter comme "à venir") :
- Configuration et lancement d'une expérience d'harmonisation depuis l'UI (Harmonization Lab absent).
- Calendrier des feux (Fire Calendar absent).
- Acquisition en direct de granules Earthdata (bloqué sans identifiants).

## Recommandation pour la vidéo

Réaliser la démo sur les artefacts déjà produits (données FIRMS réelles, pas le fixture synthétique). Présenter honnêtement les blocages (Earthdata, H4-H6) comme partie du projet — cela renforce la crédibilité scientifique. Ne pas tenter de simuler l'Harmonization Lab ni le Fire Calendar.
