# Design system — tableau de bord PyroLens

CSS pur, **aucune** Tailwind/UI-kit : tout vit dans `web/src/index.css`
(jetons `:root`). Ne jamais recréer une classe parallèle à une classe
existante ; étendre les jetons plutôt que les contourner.

---

## 1. Jetons de thème (`:root`)

| Jeton | Valeur | Usage |
|---|---|---|
| `--bg` | `#0b0f14` | fond d'application |
| `--bg-2` | `#10161d` | sidebar, dégradés |
| `--panel` | `#131b24` | panneaux, cartes |
| `--panel-2` | `#182231` | en-têtes de table, fonds secondaires |
| `--line` | `#23303f` | bordures, séparations |
| `--text` | `#dce6f2` | texte principal |
| `--muted` | `#8ba0b8` | texte secondaire, libellés |
| `--ember` | `#ff7a33` | accent principal (marque, navigation active) |
| `--ember-soft` | `#ffb27a` | accent clair (titre marque, h2 du rapport) |
| `--teal` | `#35c8c0` | valeurs **calculées** (`pill calc`) |
| `--blue` | `#5aa7ff` | bandeau d'information (`banner info`) |
| `--amber` | `#f5c542` | avertissements, références (`banner warn`, `pill ref`) |
| `--red` | `#ff5f6d` | blocages, états bloqués (`blocker`, `pill blocked`) |
| `--green` | `#47d18a` | états OK (`pill ok`) |
| `--mono` | ui-monospace / SF Mono / Menlo / Consolas | **toutes** les valeurs numériques |

Fond : deux radial-gradients (ember 10 % en haut à droite, teal 7 % à gauche)
au-dessus de `--bg` — conserver.

## 2. Typographie

- Corps : `"Inter", "Segoe UI", system-ui, sans-serif`, 14,5 px, interligne
  1,55.
- Titre d'écran : `.page-title` 26 px + `.page-sub` (muted, 78 ch max).
- Libellés de carte : 11,5 px, majuscules, interlettrage 1 px.
- Chiffres : toujours `font-family: var(--mono)` + `font-variant-numeric:
  tabular-nums` (dans `table.data`) — formats `fr-FR` via `fmt()`
  (espaces fines, virgule décimale).

## 3. Composants CSS existants (réutiliser, ne pas dupliquer)

| Classe | Rôle |
|---|---|
| `.app`, `.sidebar`, `.main` | shell : flex, sidebar sticky 250 px, main max 1280 px |
| `.brand`, `.nav button(.active)`, `.nav-group`, `.foot` | navigation et pied de sidebar |
| `.cards` / `.card` (+ `.k`, `.v`, `.d`) | rangée de indicateurs (min 190 px, auto-fill) |
| `.panel` (+ `h3 .hint`) | bloc de contenu principal (radius 12, padding 18/20) |
| `.banner .info \| .warn` | bandeau d'origine / avertissement |
| `.blocker` (+ `.what`, `.detail`, `.action`) | blocage documenté, liseré rouge |
| `.pill .ok \| .blocked \| .ref \| .calc` | étiquettes d'état/calculation |
| `.table-wrap` + `table.data` | tables mono, en-têtes muted majuscules, hover |
| `.controls` + `select` | filtres d'écran (label muted + select mono) |
| `.chart-box` (320 px) / `.chart-box.tall` (420 px) | conteneurs recharts |
| `.legend-note` | note sous un graphique |
| `.cal-head`, `.cal-grid`, `.cal-dow`, `.cal-day` (+ `.out`, `.sel`), `.cal-legend` | calendrier quotidien (Fire Calendar) — intensité via `color-mix` sur `--ember` |
| `.seg` (+ `button.on`) | bascule segmentée jour/semaine/mois |
| `.fig-grid` + `figure.fig` | galerie de PNG (img fond blanc, figcaption mono) |
| `.md` | rendu Markdown du rapport (h1/h2 ember-soft, tables, code, pre) |
| `.loading` | état de chargement initial |
| `.mono`, `.muted`, `.small` | utilitaires ponctuels |

Pills : `ok` = vert (exécuté), `blocked` = rouge (bloqué), `ref` = ambre
(référence/autre), `calc` = teal (« calculé par le pipeline » — utiliser pour
toute valeur issue d'un artefact).

## 4. Graphiques (Recharts)

- Autorisés : `Audit.jsx`, `Baselines.jsx`, `Observability.jsx`,
  `FireCalendar.jsx` et `Overview.jsx` (arbitrage : `specs-aurel.md` modules 1
  et 2 prescrivent Recharts ; même lib, aucune nouvelle dépendance). Toute
  autre vue : arbitrage requis.
- Palette : `--teal`, `--blue`, `--amber`, `--ember`, `--red`, `--green` —
  toujours une légende `.legend-note` expliquant ce qui est mesuré.
- Axes : grille `--line`, texte `--muted`, formatage `fmt()`.

## 5. Motion

Transitions courtes (0,15 s ease) sur hover/focus uniquement (nav, boutons,
lignes de table). **Pas d'animation décorative** : l'écran doit rester lisible
sans mouvement (accessibilité et cohérence « instrument de mesure »).

## 6. Responsive

`@media (max-width: 900px)` : `.app` en colonne, sidebar pleine largeur non
sticky, main padding 20/16. Tables : `.table-wrap` (scroll horizontal).
Cartes : auto-fill min 190 px (déjà fluide). Graphiques : largeur 100 %.

## 7. Ajouter un composant visuel

1. Chercher la classe existante correspondante (tableau §3).
2. Si elle n'existe pas : ajouter dans `index.css` en **réutilisant les
   jetons** (pas de couleur hexadécimale en dur hors `:root`).
3. Documenter la classe ici et dans `docs/phase2/frontend_handoff.md` §3.
4. Vérifier contrastes : texte `--text`/`--muted` sur `--panel` ; jamais
   d'information portée par la seule couleur (toujours un libellé).
