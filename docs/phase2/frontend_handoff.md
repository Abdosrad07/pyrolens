# Handoff frontend — tableau de bord PyroLens

Public : reprise de code par un·e développeur·se front. Le backend n'existe pas (artefacts
statiques, `backend_architecture.md` §1) : tout ce qui est affiché vient de `/artifacts/`.

---

## 1. Structure

```
web/
├── index.html            # point d'entrée Vite
├── vite.config.js        # plugin React ; HMR désactivée par la plateforme → ne pas toucher
├── public/artifacts/     # sortie de `pyrolens web-artifacts` (copiée telle quelle)
└── src/
    ├── main.jsx          # createRoot + import "./index.css" (jamais retirer)
    ├── App.jsx           # navigation VIEWS + orchestration loadAll
    ├── data.js           # TOUS les accès aux artefacts passent par ici
    ├── index.css         # jetons de thème (voir §3)
    └── views/            # 6 vues, un fichier par écran
        ├── Overview.jsx       # Synthèse d'exécution (provenance, étapes, blocages)
        ├── Audit.jsx          # comptabilité, anomalies, distributions (recharts)
        ├── Baselines.jsx      # explorateur paire × grille × fenêtre (recharts)
        ├── Observability.jsx  # 4 états (recharts)
        ├── Report.jsx         # rendu Markdown maison (pas de dépendance MD)
        └── Figures.jsx        # grille des PNG
```

- **Chargement** : `loadAll()` = `Promise.allSettled` sur 6 JSON + 1 MD ; un échec isolé
  alimente `data.errors[]` et n'empêche pas les autres vues (affiché dans le pied de sidebar).
- **Libellés** : `PAIR_LABELS`, `SENSOR_LABELS`, `pairLabel()`, `fmt()` (nombre au format
  `fr-FR`) — réutilisés par toutes les vues, jamais recopiés à la main.
- **Graphiques** : `recharts` uniquement dans `Audit.jsx`, `Baselines.jsx`,
  `Observability.jsx` (aucune autre lib de charts autorisée sans D2).

## 2. Ajouter une vue (procédure type)

1. Créer `web/src/views/MaVue.jsx` : accepte `{ data }`, rend `<h2 className="page-title">…</h2>`
   puis des `<section className="panel">`.
2. L'enregistrer dans `VIEWS` (`App.jsx`) et dans le `switch` de rendu du `<main>`.
3. Si la vue a besoin d'un nouvel artefact : l'ajouter dans `jsonNames` de `data.js`,
   le produire côté Python (`pyrolens … && pyrolens web-artifacts`), puis **recoupler les
   chiffres** avec l'artefact (`validation_plan.md` §2).
4. Vérifier l'absence d'affirmation d'absence de feu et la présence du badge d'origine (§5).
5. `npm --prefix web run build` puis contrôle visuel sur l'aperçu (`freebuff-preview`).

## 3. Thème et styles

- Jetons dans `index.css → :root` : fonds `--bg`, `--bg-2` ; panneaux `--panel`, `--panel-2` ;
  trait `--line` ; texte `--text`, `--muted` ; accents `--ember` (principal), `--teal`,
  `--blue`, `--amber`, `--red`, `--green` ; `--mono` pour les valeurs numériques.
- Classes existantes (ne pas en recréer de parallèles) : `.panel`, `.card`, `.cards`,
  `.page-title`, `.page-sub`, `.hint`, `.muted`, `.small`, `.mono`, `.pill`, `.banner info|warn`,
  `.blocker`, `.table-wrap`, `.chart-box`, `.fig-grid`, `.legend-note`, `.loading`, `.banner`.
- Tailwind n'est **pas** utilisée dans ce projet : rester en CSS pur du fichier `index.css`.

## 4. Règles non négociables (contrat éditorial)

1. **Aucun texte « pas de feu »** (ou équivalent) — `grep -ri "pas de feu" web/src` doit
   rester à 0. Une absence de détection s'affiche avec les libellés du pipeline :
   « aucun_enregistrement », « observabilité inconnue ».
2. **Badge d'origine** : `data_origin` (`nasa_firms`) et horodatage `generated_at` visibles
   sur toute vue affichant des chiffres.
3. **Avertissement de lecture** conservé : hors-emprise = ambigu exclu des ensembles ;
   recouvrement qui croît avec la maille/fenêtre = effet mécanique, pas amélioration.
4. **Jamais de secret** ni d'URL d'API d'acquisition côté client ; aucun appel sortant
   vers FIRMS/Earthdata depuis le navigateur.
5. **Chiffres = artefacts** : aucune valeur codée en dur dans les vues (les formules
   d'affichage passent par `fmt()`), sauf textes explicatifs.

## 5. Checklist d'acceptation d'une modification front

- [ ] `npm --prefix web run build` → exit 0
- [ ] `freebuff-preview status` → ready, HTTP 200 ; vues chargées sans erreur console
- [ ] chiffres de l'écran recoupés avec l'artefact correspondant
- [ ] seules occurrences de « pas de feu » : les **négations explicites** de `Audit.jsx`
  (« jours sans enregistrement — jamais « pas de feu » ») et `Observability.jsx` ; aucun
  texte qui **affirme** une absence de feu
- [ ] badge `data_origin` présent ; aucune valeur de clé dans `web/dist` : les URL FIRMS n'y
  figurent qu'en gabarit `<FIRMS_MAP_KEY>` (redaction vérifiée le 20/10) ; aucun `.env` copié
- [ ] phrases d'avertissement d'interprétation intactes
- [ ] si `data.js` modifié : `api_contract.md` §1 mis à jour en même temps

## 6. Passage à une API (si D2 validée)

Remplacer l'implémentation de `getJSON`/`getText` dans `data.js` par des appels `/api/v1/*`
(**§2 de `api_contract.md`**) en conservant les mêmes noms d'objets exposés aux vues :
`data.audit`, `data.baselines`, `data.observability`, `data.execution`, `data.report`.
Les composants ne doivent nécessiter aucune modification ; si une modification s'avère
nécessaire, c'est une rupture de contrat à faire remonter avant de continuer.
