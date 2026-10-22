# Parcours utilisateurs — tableau de bord PyroLens

Public : équipe projet, relecteur scientifique, développeur front reprenant le
code. Aucun compte, aucun état serveur côté front (D6 : MVP public) : le
« parcours » = navigation entre les 6 vues et vérification des chiffres.

---

## Parcours 1 — Découverte (première visite)

1. **Arrivée sur `/`** : écran « Chargement des artefacts du pipeline… » puis
   vue **Synthèse d'exécution**.
2. Le bandeau d'origine dit immédiatement quelles données sont servies
   (`nasa_firms` ou `synthetic_fixture` + avertissement).
3. Cartes de haut niveau : étapes exécutées, blocages, période, origine,
   fichiers téléchargés.
4. La sidebar donne la période, la version du pipeline et l'horodatage des
   artefacts — repères de fraîcheur avant toute lecture de chiffre.
5. **Suite naturelle** : Audit (qualité) → Baselines (chiffres) →
   Observabilité (états) → Rapport (récit) → Figures (preuves visuelles).

**Critère** : sans aucun clic, l'utilisateur sait d'où viennent les données et
ce qui est bloqué.

## Parcours 2 — Vérifier un chiffre (relecture scientifique)

1. Depuis **Baselines**, lire le badge `data_origin` + `generated_at` (pied de
   sidebar et panneaux).
2. Choisir paire / maille / fenêtre (`controls`) ; relever `n_a`, `n_b`, ∩, ∪,
   Jaccard dans les cartes.
3. **Recoupement hors-interface** : ouvrir `baselines/summary.csv` et vérifier
   la ligne correspondante — l'équation `∪ = n_a + n_b − ∩` est visible dans
   la table (contrat D1 : `summary.csv` est l'unique source).
4. Contrôler la note d'interprétation : le Jaccard est un recouvrement
   d'ensembles, pas une précision ; aucune configuration n'est mise en avant
   par sa valeur.
5. Optionnel : même configuration via l'API
   (`GET /api/v1/summary?pair=…&grid_deg=…&window_days=…`, `docs/api.md`) pour
   un contrôle automatisé — mêmes champs.

**Critère** : tout chiffre affiché est recoupable en une ouverture de fichier.

## Parcours 3 — Lire le rapport scientifique

1. Vue **Rapport** : Markdown rendu localement (aucune dépendance).
2. Balayage des sections : résumé (table = `summary.csv`), méthodes (clés,
   fenêtres), résultats, limites (H4-H6 non exécutés).
3. Les figures évoquées sont consultables en un clic dans la vue **Figures**.
4. Revenir à **Baselines** pour explorer les valeurs derrière la table.

**Critère** : rapport, figures et explorateur se citent sans contradiction
(même `generated_at`).

## Parcours 4 — Un blocage est affiché (état dégradé)

1. **Synthèse** montre `.blocker` (ex. Earthdata non acquis) : `what` = ce qui
   est bloqué, `detail` = la preuve (code HTTP), `action` = le correctif
   (fournir `EARTHDATA_USER`/`EARTHDATA_PASSWORD` ou `EARTHDATA_TOKEN` dans
   Settings → Environment).
2. Pied de sidebar : « N artefact(s) indisponible(s) » si un JSON manque —
   les autres vues restent utilisables (chargement `Promise.allSettled`).
3. Écran dégradé : cartes à « — » (`fmt()` gère `null`), jamais de fausse
   valeur.
4. Après correction : régénérer (`pyrolens run && pyrolens web-artifacts`) et
   recharger — l'horodatage du pied de sidebar doit avoir bougé.

**Critère** : un manque de données se voit et ne se remplit jamais d'une
valeur inventée.

## Parcours 5 — Développeur front : étendre le tableau de bord

1. Lire `README.md` (règles D1) puis `screen-specifications.md` (écrans).
2. Reproduire un écran existant (procédure `docs/phase2/frontend_handoff.md`
   §2) : composant → `VIEWS` + `switch` dans `App.jsx` → artefact ajouté à
   `jsonNames` de `data.js` et produit côté Python.
3. Recouper chaque chiffre avec l'artefact ; ajouter le badge d'origine.
4. `npm --prefix web run build` (exit 0) puis `freebuff-preview start` :
   contrôle visuel + console.
5. Checklist complète : `screen-specifications.md` §7.

**Critère** : la PR se relit sans étonnement — mêmes classes, mêmes jetons,
mêmes libellés de provenance.

---

## Règles transverses à chaque parcours

- Jamais d'affirmation d'absence de feu (`aucun_enregistrement`,
  « observabilité inconnue »).
- Jamais de secret ni d'URL d'acquisition côté client.
- Tout chiffre affiché porte sa provenance ; toute formule d'affichage passe
  par `fmt()`.
