# Plan d'amélioration — PyroLens

> Rédigé le 2026-11-15 — Phase 1 du PROMPT FINAL.md

## 1. État actuel (vérifié)

| Composant | État | Détails |
|---|---|---|
| `prediction.py` | ✅ Fonctionnel | RF + baseline, split chrono 2013-16/17-18/19-20, purge 16j, calibration isotonic, 24 features |
| Artefact `fire_risk.json` | ✅ Présent | 1 215 cellules, PR-AUC 0.926, F1 0.841, Brier 0.072, seuil 0.42 |
| Chatbot `chat.py` | ⚠️ Partiel | 8 intentions (prediction, zone, historique, donnees, calendrier, jobs, qualite, aide) — manque ~10 intentions obligatoires |
| Frontend i18n | ✅ Complété | FR/EN, tous les composants migrés |
| Tests `test_prediction.py` | ⚠️ Bloqués | pytest non installé |
| `data/raw/firms/` | ❌ Vide | 0 fichier CSV — données d'entraînement manquantes |
| `data/raw/archive/` | ❌ Absent | Aucune archive pays téléchargée |
| `data/raw/cmr/` | ✅ Inventaire | CMR metadata 2013-2020, 3 capteurs |

## 2. Fichiers à modifier

### Backend
- `src/pyrolens/prediction.py` — enrichir `FEATURE_NAMES` avec variables supplémentaires (FRP max, jours actifs, densité historique) si bénéfique
- `api/services/chat.py` — ajouter les intentions manquantes (voir §5.2)
- `tests/test_prediction.py` — ajouter tests pour nouvelles intentions chatbot, provenance cellules, métriques régionales

### Scripts (nouveaux)
- `scripts/download_multi_region_archive.py` — téléchargement archives pays multi-régions avec manifeste JSONL

### Documentation
- `docs/IMPROVEMENT_PLAN.md` — ce fichier
- `docs/IMPROVEMENT_REPORT.md` — rapport final (Phase 6)
- `docs/FIRE_RISK_PREDICTION.md` — mise à jour si protocole change

## 3. Données nécessaires

### Phase 2 — Extension géographique
Pays cibles (période 2018-2020, 3 capteurs × 3 ans par pays) :

| Région | Pays | Fichiers estimés | Volume estimé |
|---|---|---|---|
| Afrique Centrale | Cameroun (déjà), RCA, Tchad, Gabon, Guinée Éq. | ~15 | ~150 Mo |
| Afrique de l'Est | Kenya, Tanzanie, Éthiopie | ~18 | ~180 Mo |
| Afrique Australe | Zimbabwe, Zambie, Mozambique | ~18 | ~180 Mo |
| Témoin Europe | France | ~9 | ~90 Mo |
| Témoin Amérique | Brésil | ~9 | ~90 Mo |
| Témoin Asie | Russie | ~9 | ~90 Mo |
| **Total** | | **~78 fichiers** | **~780 Mo** |

**Révision** : Le Cameroun étant déjà la zone pilote, l'extension prioritaire est l'Afrique de l'Ouest (script existant) + 2 témoins (France, Brésil). Estimation ajustée : ~50 fichiers, ~500 Mo.

## 4. Risques techniques et scientifiques

| Risque | Niveau | Mitigation |
|---|---|---|
| Téléchargement lent (300 Ko/s) | Moyen | ~30 min pour 500 Mo — reprise automatique via manifeste |
| Fuite spatiale | Élevé | Validation spatiale : entraîner sur pays A, tester sur pays B |
| Déséquilibre géographique | Moyen | Stratification par région dans les métriques |
| Modèle global vs régional | Décision | À évaluer après download — commencer par global |
| pytest non installé | Bloquant | `pip install pytest` avant Phase 6 |

## 5. Tests à ajouter

- `test_chat_intentions` — couverture de toutes les intentions obligatoires
- `test_chat_dynamic_metrics` — vérifier que les métriques sont lues depuis l'artefact, pas codées en dur
- `test_cell_provenance` — chaque cellule a `data_origin` et `reference_date`
- `test_regional_metrics` — métriques par région quand données disponibles
- `test_no_temporal_leakage` — vérifier que les features ne voient que le passé
- `test_chat_fallback` — question non reconnue → réponse honnête

## 6. Étapes d'exécution

### Phase 2 — Données (2-3 h)
1. Installer pytest
2. Lancer les tests existants (baseline)
3. Télécharger archives pays Afrique de l'Ouest + France + Brésil
4. Vérifier intégrit�� (SHA256, taille)
5. Mettre à jour l'inventaire

### Phase 3 — Modèle (3-4 h)
1. Reproduire métriques actuelles (vérification)
2. Étendre `FEATURE_NAMES` si bénéfice mesurable
3. Entraîner sur données multi-pays
4. Évaluer global + par région
5. Validation spatiale (cross-country)
6. Comparaison baseline vs RF sur même test

### Phase 4 — Artefacts (30 min)
1. Régénérer `fire_risk.json` avec nouvelles données
2. Synchroniser `frontend/public/artifacts/`
3. Vérifier le contrat de données

### Phase 5 — Chatbot (2 h)
1. Ajouter les ~10 intentions manquantes
2. Lectures dynamiques depuis artefacts
3. Suggestions de suivi
4. Tests backend + frontend

### Phase 6 — Tests et documentation (1-2 h)
1. Tous les tests pytest
2. Build frontend
3. Mise à jour docs
4. Rapport final

**Temps total estimé : 9-12 h de travail effectif.**
