# Conformité aux exigences du défi NASA Space Apps Challenge 2026

**Note méthodologique** : les critères de notation internes du jury ne sont pas publiés. Ce document évalue PyroLens contre la description du défi « Harmonization of MODIS and VIIRS Hot Spots » et contre les exigences déductibles de l'énoncé. Chaque écart est distingué entre « exigence officielle (déduite de l'énoncé) » et « recommandation de l'auditeur ».

## Matrice de conformité

| Critère | Attente | État actuel | Écart | Priorité | Action corrective |
|---|---|---|---|---|---|
| Compréhension du problème | Rapprocher MODIS Terra/Aqua et VIIRS S-NPP | Compris ; clés d'ensemble définies | Partiel (pas d'harmonisation validée) | P1 | Exécuter S3/S4 ou acter la limite |
| Pertinence de la solution | Approche d'harmonisation inter-capteurs | Baseline Jaccard 24 configs | Écart : pas de méthode validée | P1 | Valider H4/H6 ou publier la limite |
| Qualité des données | Données authentiques, provenance claire | FIRMS réelles 2013-2020, SHA-256 | Satisfait (partiel : Earthdata bloqué) | P0 | Fournir clés Earthdata (D4) |
| Solidité scientifique | Validation, reproductibilité, limites assumées | Limites assumées, mais H4-H6 non exécutés | Écart critique | P0 | D5 : référence externe ou split |
| Originalité de l'approche | Démarche d'harmonisation documentée | Catalogue H1-H6, aucun déclaré validé | Écart | P1 | H4/H6 ou documentation de la limite |
| Fonctionnement technique | Pipeline + API + frontend fonctionnels | Opérationnel (données réelles) | Satisfait | P2 | Finir S1 (frontend MVP) |
| Expérience utilisateur | 3 modules : Overview, Harmonization Lab, Fire Calendar | Overview uniquement | Écart : 2 modules absents | P1 | Implémenter UI expériences + calendrier |
| Qualité des visualisations | Figures, cartes, séries temporelles | 6 PNG + Recharts dans Baselines | Satisfait | P2 | — |
| Reproductibilité | Même commande → même résultat | `pyrolens run` + pytest, SHA-256 | Satisfait | P2 | — |
| Documentation | Méthodologie, API, limites | `docs/` complet + artefacts | Satisfait | P3 | — |
| Impact potentiel | Utilité pour la science des feux | Baseline inter-capteurs | Partiel | P2 | — |
| Qualité de la démonstration | Vidéo 4-5 min, parcours sans code | Blocages Earthdata, modules absents | Écrit | P0 | Démo sur données réelles acquises |

## Analyse par exigence

### Exigence 1 — Utiliser MODIS Terra, MODIS Aqua et VIIRS S-NPP
- **État** : satisfait. Les trois capteurs sont configurés dans `config/pipeline.yaml` et acquis via l'API FIRMS (`MODIS_SP`, `VIIRS_SNPP_SP`).
- **Preuve** : `data/manifests/downloads.json` (585 MODIS + 585 VIIRS), `baselines.json` `sensor_sizes`.

### Exigence 2 — Harmonisation spatiale et temporelle
- **État** : satisfait au niveau de la mesure (grilles 0,10/0,25/0,50°, fenêtres 1/4/8/16 j).
- **Écart** : pas de méthode d'harmonisation *validée* (H4-H6). La sensibilité est publiée mais aucun seuillage ni correction n'est calé.
- **Priorité** : P1.

### Exigence 3 — Données de qualité et provenance
- **État** : satisfait pour les détections FIRMS (SHA-256, inventaire CMR, audit qualité).
- **Écart** : granules standard et produits couverture/nuages bloqués (Earthdata).
- **Priorité** : P0 (bloquant pour H5 et l'observabilité réelle).

### Exigence 4 — Validation scientifique
- **État** : non satisfait. Aucune référence indépendante, pas de seuils H4, pas de validation externe H6.
- **Priorité** : P0.

### Exigence 5 — Démonstration fonctionnelle
- **État** : partiel. Le pipeline tourne, le frontend affiche les artefacts, mais Harmonization Lab et Fire Calendar n'ont pas d'UI.
- **Priorité** : P1.

## Ce qui est conforme (à garder)
- Provenance claire (`data_origin` sur chaque artefact).
- Aucune affirmation d'absence de feu (« aucun_enregistrement »).
- Règle D1 respectée (une seule source de chiffres).
- Limites assumées et documentées (`docs/limitations.md`).

## Ce qui doit être corrigé avant soumission
1. Fournir les identifiants Earthdata (D4) ou acter publiquement le blocage.
2. Fournir une référence externe (D5) ou publier la limite H4/H6.
3. Implémenter au minimum les vues Harmonization Lab et Fire Calendar (ou documenter leur absence comme périmètre MVP).
4. Régénérer `docs/openapi.json` si l'API évolue.
