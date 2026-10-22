# Décisions à valider — phase 2

À trancher avant les lots concernés (`implementation_plan.md`). Chaque décision indique sa
recommandation, son échéance et l'impact d'un report. **D1 a été tranchée le 21/10/2026**
(choix utilisateur) ; les autres restent soumises à validation explicite.

---

## D1 — Publication des chiffres Jaccard de phase 1

- **Contexte** : les valeurs 0,263 / 0,777 / 0,310 / 0,789 (et « 310.82791 ») annoncées en
  phase 1 sont **introuvables** dans les artefacts actuels ; elles datent probablement de
  l'époque du fixture synthétique. Le référentiel réel est `baselines/summary.csv` (24
  configurations, `nasa_firms`, 18/10). Vérification détaillée :
  `data_validation.md` §7.
- **Options** : (a) remplacer les anciennes valeurs par celles de `summary.csv` partout ;
  (b) publier les deux en signalant l'origine synthétique des anciennes.
- **Recommandation** : **(a)** — une seule source de chiffres, horodatée, reproductible.
- **Décision (21/10/2026)** : **(a) retenue — « Uniquement summary.csv »** : une seule
  source de chiffres (`baselines/summary.csv` et ses dérivés horodatés), retirée de
  toutes les communications ; aucune valeur de phase 1 n'est republicée. Appliquée dans
  `README.md`, `docs/`, le rapport, l'API (`docs/api.md`) et le frontend (D1).
- **Échéance** : immédiate (toute citation externe).
- **Si reportée** : risque de contradictions entre documents.

## D2 — Architecture : statique (A) ou API FastAPI (B)

- **Contexte** : le MVP fonctionne sans backend (`backend_architecture.md`) ; l'option B
  n'apporte que filtrage/pagination serveur et réutilisation externe.
- **Options** : (a) rester statique + correctifs P1 ; (b) ajouter `api/index.py` (FastAPI)
  dès le lot S1.
- **Recommandation** : **(a)** pour le MVP ; (b) seulement si un besoin concret de requêtes
  serveur apparaît (go/no-go revu en fin de S1).
- **Échéance** : fin du lot S1.
- **Si reportée** : aucun impact (l'option B n'exclut rien rétroactivivement).

## D3 — Hébergement de mise en ligne

- **Options** : (a) **Freebuff** (défaut) : build `vite build` → `dist/`, aperçu et
  déploiement gérés, aucun service externe ; (b) hébergeur externe type **Vercel**
  (lien de configuration fourni dans le résumé de l'étape), pertinent surtout après
  connexion GitHub avec CI/CD ; (c) serveur dédié (hors MVP).
- **Recommandation** : **(a)** dès que le MVP est accepté ; (b) seulement si l'équipe veut
  du déploiement Git automatisé.
- **Échéance** : avant toute mise en ligne.
- **Si reportée** : le produit reste accessible en aperçu local.

## D4 — Identifiants Earthdata (produits d'observabilité et granules)

- **Contexte** : sans eux, `download:earthdata` reste bloqué (HTTP 302), la couverture/nuages
  n'est pas acquise, l'observabilité reste par défaut « inconnue » et H5 (géométrie
  d'observation) est impossible.
- **Clés à fournir** (Settings → Environment, **jamais dans le chat**) :
  `EARTHDATA_USER` + `EARTHDATA_PASSWORD` **ou** `EARTHDATA_TOKEN`.
- **Recommandation** : fournir les clés si (et seulement si) l'état « conditions
  d'observation plausibles » est attendu pour la suite de l'étude.
- **Échéance** : avant le lot S3.
- **Si reportée** : aucun changement côté MVP ; les 4 états restent déséquilibrés par défaut
  (c'est le comportement honnête actuel).

## D5 — Références indépendantes pour H4 et H6

- **Contexte** : aucun registre au sol, aucune pyrométrie, aucune autre source de vérité
  n'existe dans l'environnement ; sans elles, H4 (seuils de confiance) et H6 (validation
  externe) restent non exécutables et **aucune méthode ne pourra être déclarée validée**.
- **Options** : (a) fournir un jeu de référence (registre incendies Cameroun, produits
  satellitaires d'autres agences, données de terrain) ; (b) exécuter H6 en split
  temporel/régional seul et publier la limite explicitement.
- **Recommandation** : **(a) si disponible, sinon (b)** — jamais un silence sur l'absence
  de validation externe.
- **Échéance** : avant le lot S4.
- **Si reportée** : le rapport continue d'annoncer « aucune méthode validée » (statut actuel
  acceptable).

## D6 — Comptes utilisateurs / authentification

- **Contexte** : le tableau de bord est public et en lecture seule ; `mvp_scope.md` le met
  hors périmètre.
- **Options** : (a) garder public ; (b) ajouter une auth pour réserver l'accès.
- **Recommandation** : **(a)** pour le MVP ; (b) seulement avec un besoin d'usage avéré.
- **Échéance** : avant toute ouverture multi-utilisateurs.

## D7 — Résolution de l'emprise

- **Contexte** : polygone Natural Earth **110 m** (frontières simplifiées) ; filtre déjà
  opérationnel (2 634 697 lignes hors emprise tracées).
- **Options** : (a) conserver 110 m ; (b) passer à une géométrie plus fine
  (ex. admin_0 50 m / frontières nationales) — nouvelle emprise = redéfinition des ensembles
  = **recomptage intégral** des baselines.
- **Recommandation** : **(a)** tant qu'aucun écart lié aux frontières n'est démontré ;
  (b) avec rerun complet et comparaison documentée (S1 possible).
- **Échéance** : avant toute publication de résultats régionaux affinés.

## D8 — Mise à jour des statuts H1-H3 dans le catalogue et le rapport

- **Contexte** : `src/pyrolens/harmonization.py` indiquait « NON EXÉCUTÉ sur données
  réelles » pour H1-H3 alors que l'audit et les baselines **tournent sur données réelles
  depuis le 18/10**. Le rapport §9 en reprenait les statuts (affirmation devenue fausse).
- **Action effectuée** (lot S0) : statuts H1-H3 alignés sur l'exécution réelle, H4-H6
  reformulés (données disponibles vs prérequis manquants), rapport et artefacts régénérés.
- **Recommandation** : **valider la formulation** et rappeler que « exécuté » ≠ « validé »
  (`scientific_method.md` §6-§7).
- **Échéance** : immédiate (fait, à relire).

## Synthèse

| Décision | Recommandation | Échéance | Statut |
|---|---|---|---|
| D1 chiffres Jaccard | retenir `summary.csv` | immédiate | **validée (21/10) — uniquement `summary.csv`** |
| D2 API | statique pour le MVP | fin S1 | à valider |
| D3 hébergement | Freebuff natif | avant mise en ligne | à valider |
| D4 Earthdata | fournir clés si besoin réel | avant S3 | à valider |
| D5 références H4/H6 | fournir ou assumer la limite | avant S4 | à valider |
| D6 comptes | public | avant multi-utilisateurs | à valider |
| D7 emprise | conserver 110 m | avant résultats régionaux fins | à valider |
| D8 statuts H1-H3 | valider la formulation | immédiate | fait, à relire |
