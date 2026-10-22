# Limites connues — PyroLens

Périmètre assumé, jamais caché. Chaque limite indique son **impact** et la
**marche à suivre** si elle devient bloquante. Le reste de la documentation :
`docs/technical.md` (architecture, déploiement), `docs/methodology.md` (chiffres),
`docs/phase2/decisions_to_validate.md` (arbitrages ouverts).

---

## 1. Scientifiques (méthode)

1. **Aucune méthode validée** : le Jaccard mesure un recouvrement d'ensembles,
   pas une précision. H4 (seuils de confiance) et H6 (validation externe) sont
   non exécutables faute de référence indépendante (D5) : aucun registre au sol,
   aucune pyrométrie. « Exécuté » ≠ « validé ».
2. **Absence de détection ≠ absence de feu** : les jours vides sont libellés
   `aucun_enregistrement` ; l'observabilité par défaut est « observabilité
   inconnue » (produits de couverture/nuages bloqués sans identifiants
   Earthdata, D4).
3. **Hors-emprise = ambigu exclu** : filtre bbox + polygon Natural Earth 110 m
   (frontières simplifiées, D7) ; 2 634 697 lignes tracées hors emprise et
   exclues des ensembles.
4. **Effet mécanique de la maille/fenêtre** : un recouvrement qui croît quand la
   maille grossit ou la fenêtre s'allonge n'est pas une amélioration — comparer
   uniquement à paramètres égaux.
5. **Confiances MODIS/VIIRS non converties** et **FRP non corrigé** : aucune
   échelle commune n'est proposée par conception.
6. **Terciles de latitude** pour les régions : découpage documenté et arbitraire
   (pas une frontière administrative).

## 2. Données

1. **Acquisition FIRMS conditionnée à `FIRMS_MAP_KEY`** (≤ 5 jours/requête,
   2013-01-01 → 2020-12-31 pour les fenêtres canoniques). Sans clé, `pyrolens
   download` échoue proprement (raison enregistrée au manifeste).
2. **Archives Earthdata bloquées** (HTTP 302 sans identifiants) : granules
   standard et produits de couverture/nuages absents → états d'observabilité
   par défaut « inconnue », H5 impossible (D4).
3. **`data/raw/firms/` ignoré par git** (> 330 Mo) : reproduction par
   `pyrolens download`, pas par clonage. `reports/anomalies/` (474 Mo) idem :
   régénérable par `pyrolens audit`.
4. **Un seul pilote géographique** (Cameroun, `region.iso3: CMR`) : aucun
   résultat national d'un autre pays sans rerun complet.

## 3. API et exécution

1. **Processus unique, mémoire vive** : file de tâches `ThreadPoolExecutor(1)`
   — exécution séquentielle, pas de distribuição ni de reprise après crash
   d'une tâche en cours (les tâches « succeeded » persistées sont relues au
   démarrage).
2. **Registre des jobs en mémoire** : au redémarrage, seuls les **résultats**
   persistés sont retrouvés ; les tâches `queued`/`running` disparaissent.
3. **Cache positif par empreinte** (mtime+taille) : une régénération
   d'artefact est vue à la requête suivante ; un artefact **absent** est
   mémorisé comme absent pendant `PYROLENS_CACHE_TTL_SECONDS` (30 s).
4. **`/series/divergence` et `/spatial` limités à la configuration primaire** :
   l'artefact ne persiste pas les 24 configurations × jour/mois/région.
5. **Upload jamais intégré** : `POST /datasets/validate` audite en mémoire et
   oublie — aucune persistance côté API, aucun pipeline déclenché sur un
   téléversement.
6. **Pas d'authentification côté lecture** (D6 : MVP public) ; les POST ne sont
   protégés que si `PYROLENS_API_TOKEN` est défini.
7. **CORS fermé par défaut** : ajouter `PYROLENS_CORS_ORIGINS` avant tout
   appel cross-origin.

## 4. Frontend

1. **Artefacts statiques** : sans régénération (`pyrolens run`), l'affichage
   vieillit ; `generated_at` est la seule horloge visible.
2. **Aucune pagination serveur** : `/spatial` sert jusqu'à 5 000 cellules par
   requête ; le front n'affiche que le top publié.
3. **Rendu Markdown maison** (`Report.jsx`) : pas de table de bord, ni de
   rendu d'extensions GFM hors familles présentes dans le rapport généré.

## 5. Si une limite devient bloquante

1. Citer la section dans une issue avec le cas d'usage.
2. Vérifier l'arbitrage correspondant dans `docs/phase2/decisions_to_validate.md`
   (D4 → clés Earthdata ; D5 → références H4/H6 ; D2 → périmètre API).
3. Toute évolution de la **définition des ensembles** (emprise, maille,
   fenêtre) impose un rerun complet et une comparaison documentée des
   chiffres — jamais de valeur publiée modifiée en silence (D1).
