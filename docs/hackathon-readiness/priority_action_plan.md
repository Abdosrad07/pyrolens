# Plan de correction priorisé — PyroLens

**Règle** : ne pas ajouter de fonctionnalités décoratives. Travailler sur les vrais blocages (G1, G2) puis finir le MVP (S1). Aucun nouveau code scientifique tant que D4 et D5 ne sont pas tranchés.

## Phase 0 — Décisions (immédiat, avant toute correction)

| Action | Décision requise | Qui | Livrable |
|---|---|---|---|
| D4 Earthdata | Fournir les identifiants **OU** acter publiquement l'état "observabilité inconnue" | Utilisateur (clés jamais dans le chat) | `decisions_to_validate.md` D4 statué |
| D5 Référence H4/H6 | Fournir une référence externe **OU** publier la limite (split temporel/régional seul) | Utilisateur | `decisions_to_validate.md` D5 statué |
| D2 API statique vs serveur | Confirmer le statique pour le MVP (recommandé) | Équipe | `decisions_to_validate.md` D2 statué |
| D3 hébergement | Confirmer Freebuff natif | Équipe | `decisions_to_validate.md` D3 statué |
| D6 comptes | Confirmer public / lecture seule | Équipe | `decisions_to_validate.md` D6 statué |
| D7 emprise | Confirmer 110 m tant qu'aucun écart frontière n'est démontré | Équipe | `decisions_to_validate.md` D7 statué |

## Phase 1 — P0 : débloquer les fondements scientifiques

### 1.1 D4 — Earthdata (si clés fournies)
- Renseigner `EARTHDATA_USER` + `EARTHDATA_PASSWORD` (ou `EARTHDATA_TOKEN`) dans Settings → Environment (jamais dans le chat, jamais dans Git).
- Lancer `pyrolens download` pour les granules standard (MOD14/MYD14/VNP14IMG) sur une période pilote d'abord.
- Acquérir `MOD03/MYD03` (géométrie), `MOD09GA` (couverture), `MOD35_L2/MYD35_L2` (nuages).
- Mettre `coverage_products_acquired = true` dans `config/pipeline.yaml` uniquement si réellement acquis.
- **Critère** : `downloads.json` montre les granules acquis ; `observability.json` passe `coverage_products_acquired = true` ; toujours aucun état "pas de feu".

### 1.2 D5 — Référence externe H4/H6 (si disponible)
- Si un registre au sol, des données pyrométriques ou une autre agence satellite sont disponibles : les intégrer comme jeu de référence.
- Sinon : exécuter H6 en split temporel (2013-2016 développement / 2017-2020 évaluation) + split sud/nord, et publier l'écart développement/évaluation tel quel (y compris si > seuil = "non généralisable").
- **Critère** : `harmonization.py` H4/H6 statuts mis à jour ; le rapport indique explicitement "aucune méthode validée" ou présente les résultats du split avec la limite.

## Phase 2 — P1 : finir le MVP (lot S1)

Après D1 (déjà validée), exécuter les 7 tâches S1 dans l'ordre :

| # | Tâche | Livrable | Critère d'acceptation |
|---|---|---|---|
| 1.1 | `downloads_summary.json` (< 2 Mo) + chargement à la demande | artefact + `data.js` modifié | Chargement initial < 2 Mo ; manifeste complet sur disque |
| 1.2 | Table intégrale des 24 configurations | vue `Baselines` | Toutes les lignes de `summary.csv` affichées |
| 1.3 | Liens ancrés de configuration | `Baselines.jsx` | Recharger l'URL restaure la sélection |
| 1.4 | Export CSV/JSON de la vue active | bouton d'export | Fichier exporté = lignes affichées |
| 1.5 | Écran d'accueil décideur (4-5 chiffres) | `Landing.jsx` | 4-5 chiffres issus des artefacts + renvoi vers les vues |
| 1.6 | Nettoyage des 252 CSV d'anomalies orphelins | code + `reports/anomalies/` | 1 fichier/fenêtre avec anomalie, zéro orphelin |
| 1.7 | Tests front smoke (build + vues rendues) | script de validation | `npm --prefix web run build` = exit 0 ; check-list cochée |

**Condition de sortie S1** : `pytest` 31/31 ; build front exit 0 ; chiffres recalés sur `summary.csv` ; aucune phrase "pas de feu" ; `docs/` à jour.

## Phase 3 — Go/no-go D2 (fin S1)

- Si besoin concret de requêtes serveur : ajouter `api/index.py` (FastAPI), basculer `data.js` sur l'API, déployer (S2).
- Sinon : rester statique (recommandation actuelle).

## Phase 4 — P2 : finitions et cohérence (après S1)

- Corriger G8 (tests front), G6 (export), G7 (écran d'accueil), G5 (downloads_summary déjà fait en 1.1).
- Régénérer `docs/openapi.json` si l'API change.
- Vérifier qu'aucune valeur de phase 1 n'est republiée (D1).

## Phase 5 — P3 : secondaires (après soumission)

- Raffinement d'emprise (D7, 110 m → 50 m/10 m) avec rerun complet.
- Connexion front ↔ API si D2 = b.
- Hébergement externe (D3, si CI/CD souhaité).

## Definition of Done globale (avant soumission)

1. `pytest` 31/31 (ou plus).
2. `npm --prefix web run build` = exit 0.
3. Preview prêt (Freebuff).
4. Chiffres recalés aux artefacts (`validation_plan.md` §2).
5. Aucune affirmation d'absence de feu.
6. `docs/` à jour (y compris `decisions_to_validate.md` D1-D8 tranchées ou explicitement reportées).
7. G1 et G2 documentés (validés ou limités explicitement).
