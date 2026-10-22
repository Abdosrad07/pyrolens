# PyroLens — handoff frontend

Dossier destiné à qui reprend ou étend l'interface du tableau de bord
**PyroLens** (Vite + React + Recharts, CSS pur, `web/`). Il décrit **l'existant
livré** et la marche à suivre pour l'étendre sans casser le contrat éditorial.

> **Convention D1 (validée le 21/10/2026)** : tout chiffre affiché provient de
> `baselines/summary.csv` et des artefacts horodatés — jamais de valeur codée en
> dur, jamais d'ancienne valeur de phase 1.

---

## 1. Sommaire

| Fichier | Contenu |
|---|---|
| [`hackathon-guide.md`](hackathon-guide.md) | **point d'entrée frontend engineer** : brancher l'API v1 sur l'interface (Mission A) puis livrer la vraie interface web pour le hackathon (Mission B) — étapes, vérifications, contrat éditorial |
| [`screen-specifications.md`](screen-specifications.md) | les 6 écrans : rôle, structure, données affichées, états (chargement, artefact absent, origine), critères d'acceptation |
| [`design-system.md`](design-system.md) | jetons de thème, classes CSS existantes, composants réutilisables, typographie, responsive |
| [`user-flows.md`](user-flows.md) | parcours type : découverte, vérification d'un chiffre, lecture du rapport, gestion d'un blocage |
| [`api-integration.md`](api-integration.md) | branchement progressif sur l'API v1 (`docs/api.md`) : mapping endpoint ↔ artefact, without breaking change |
| [`mockups/index.html`](mockups/index.html) | maquette HTML statique cliquable des 6 écrans (jetons identiques à `web/src/index.css`) |
| [`assets/logo.svg`](assets/logo.svg) | marque PyroLens (SVG, sans dépendance externe) |

## 2. Où vit le code

```
web/
├── index.html            point d'entrée Vite (ne pas toucher au script racine)
├── vite.config.js        HMR désactivée par la plateforme → NE PAS MODIFIER
├── public/artifacts/     sortie de `pyrolens web-artifacts` (source des chiffres)
└── src/
    ├── main.jsx          createRoot + import "./index.css" (jamais retirer)
    ├── App.jsx           shell : sidebar, 6 vues (VIEWS), loadAll()
    ├── data.js           TOUS les accès artefacts + PAIR_LABELS/fmt()
    ├── index.css         jetons et classes (design-system.md)
    └── views/            1 fichier par écran (Overview, Audit, Baselines,
                          Observability, Report, Figures)
```

## 3. Règles non négociables (contrat éditorial)

1. **Aucune affirmation d'absence de feu** — libellés du pipeline à respecter :
   `aucun_enregistrement`, « observabilité inconnue ».
   `grep -ri "pas de feu" web/src` ne doit réserver qu'aux **négations explicites**.
2. **Provenance visible** sur tout écran affichant des chiffres :
   `data_origin` + `generated_at` (badge/banner) et le pied de sidebar.
3. **Chiffres = artefacts (D1)** : source unique `baselines/summary.csv` et ses
   dérivés ; formules d'affichage via `fmt()` ; aucune constante numérique dans
   les vues hors textes explicatifs.
4. **Avertissements d'interprétation conservés** : Jaccard ≠ précision ;
   recouvrement qui croît avec maille/fenêtre = effet mécanique ; hors-emprise =
   ambigu exclu.
5. **Aucun secret côté client** : pas de `FIRMS_MAP_KEY`/`EARTHDATA_*`, pas
   d'URL d'acquisition, aucun appel sortant vers FIRMS/Earthdata depuis le
   navigateur.

## 4. Démarrage

```bash
npm --prefix web ci
npm --prefix web run build     # exit 0 obligatoire
freebuff-preview start         # aperçu géré (jamais de serveur lancé à la main)
```

Checklist de validité d'une modification : `screen-specifications.md` §7 et
`docs/phase2/frontend_handoff.md` §5 (les deux se recoupent ; en cas d'écart,
ce dossier fait foi pour les écrans, `docs/phase2/` pour le pipeline).

## 5. Contrat à respecter si vous ajoutez un écran

Voir la procédure complète dans `docs/phase2/frontend_handoff.md` §2 :
nouveau composant → enregistrer dans `VIEWS` + `switch` de `App.jsx` → artefact
ajouté à `jsonNames` de `data.js` et produit côté Python → chiffres recoupés
avec l'artefact → badge d'origine et absence d'affirmation d'absence de feu
vérifiés → build + aperçu.
