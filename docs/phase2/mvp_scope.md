# Périmètre MVP — tableau de bord PyroLens

**Produit** : tableau de bord web d'exploration de l'étude MODIS/VIIRS (Cameroun 2013-2020),
alimenté exclusivement par les artefacts horodatés du pipeline Python.
**Utilisateurs** : (R) chercheur/relecteur de l'étude, (D) décideur qui veut les chiffres
clés sans lire le rapport, (I) intégrateur qui reprendra le code.

---

## 1. Dans le périmètre (P0 — MVP)

| # | Besoin | Utilisateur | État actuel |
|---|---|---|---|
| P0-1 | Synthèse d'exécution : origine `nasa_firms`, période, provenance, statut des étapes et blocages | D, R | ✅ `Overview.jsx` |
| P0-2 | Audit : comptabilité des lignes, anomalies par catégorie, distributions (confiance, FRP, mois), trous temporels avec libellé « aucun_enregistrement » | R | ✅ `Audit.jsx` |
| P0-3 | Explorateur de configurations : paire × grille × fenêtre → Jaccard, tailles d'ensembles, séries mensuelles, carte de distribution spatiale, régions | R | ✅ `Baselines.jsx` (3 sélecteurs, 24 configurations) |
| P0-4 | Observabilité : 4 états, compteurs par capteur, avertissement explicite tant que la couverture n'est pas acquise | D, R | ✅ `Observability.jsx` |
| P0-5 | Rapport scientifique intégral (Markdown rendu) + figures PNG téléchargeables | R | ✅ `Report.jsx`, `Figures.jsx` |
| P0-6 | Lecture honnête : badge d'origine des données, horodatage des artefacts, « artefact indisponible » si un fichier manque (jamais d'écran blanc) | tous | ✅ (`data.js` → `errors[]`) |
| P0-7 | Aucune affirmation d'absence de feu nulle part dans l'interface | tous | ✅ (à re-vérifier à chaque vue ajoutée) |
| P0-8 | Build statique reproductible et aperçu prêt : `npm --prefix web run build`, `freebuff-preview` | I | ✅ 20/10 |

## 2. P1 — avant ou juste après la première mise en ligne

| # | Besoin | Justification |
|---|---|---|
| P1-1 | Alléger le chargement initial : `downloads.json` (5,9 Mo) n'est pas affiché dans les vues → l'exclure du `loadAll` ou publier une version agrégée (nombre de requêtes, SHA-256 de synthèse) | temps de chargement, poids du build |
| P1-2 | Export CSV/JSON de la configuration affichée (summary + séries) | reproductibilité pour R |
| P1-3 | Lien ancré vers la configuration (URL `?pair=&grid=&window=`) | citation, partage |
| P1-4 | Table des 24 configurations complète en une vue (aujourd'hui filtrée par sélecteurs) | exigence « publiées intégralement » |
| P1-5 | Écran d'accueil orienté D : 4-5 chiffres clés + renvoi vers les vues | adoption décideurs |

## 3. Hors périmètre (et pourquoi)

- **Comptes utilisateurs / authentification** : le produit est public et en lecture seule
  (à revoir seulement si D6 est activé).
- **Calcul d'harmonisation « validée », alerte incendie, prédiction** : non établi
  scientifiquement (`scientific_method.md` §7).
- **Toute interface affichant « pas de feu »** : interdit par conception (test + relecture).
- **Édition ou import de données côté client** : la source de vérité reste le pipeline Python.
- **Application mobile native, temps réel, notifications** : sans objet (données 2013-2020).
- **Cartographie tuilée en ligne (tiles externes)** : ajouterait une dépendance réseau externe
  sans besoin établi ; la distribution spatiale est déjà publiée en points par cellule.

## 4. Critères d'acceptation du MVP

1. `npm --prefix web run build` → exit 0 ; `freebuff-preview status` → ready, HTTP 200.
2. Les 6 vues affichent des chiffres identiques aux artefacts horodatés (recoupement §2 du
   `validation_plan.md`).
3. Aucun écran blanc si un artefact manque ; le champ `errors[]` reste visible.
4. Badge `data_origin` et horodatage des artefacts présents sur toutes les vues de données.
5. Aucune formulation qui **affirme** une absence de feu ; les seules occurrences de
   « pas de feu » dans `web/src` sont des négations explicites d'avertissement (contrôle
   `grep -ri "pas de feu" web/src` → 3 lignes, toutes des négations — Audit.jsx,
   Observability.jsx).
6. Aucune valeur de secret dans `web/dist/` : URL FIRMS en gabarit `<FIRMS_MAP_KEY>` uniquement.
7. Chargement initial < 2 Mo après P1-1 (aujourd'hui ~8 Mo, dont 5,9 Mo inutilisés).

## 5. Contraintes de plateforme (Freebuff)

- Serveur d'aperçu géré : commande enregistrée via `freebuff-preview set`, liaison 0.0.0.0,
  port injecté ; **ne jamais** le relancer depuis un shell.
- Build de production = `vite build` (statique dans `dist/`), sans étape Python à l'install
  ni au build (l'hébergeur n'est pas un environnement Python) — voir `backend_architecture.md`.
- HMR désactivée dans la config du projet : préserver `server.hmr: false`.
- Les dépendances restent `react`, `react-dom`, `recharts` (aucune nouvelle lib sans D2).

## 6. Dépendances de décisions

- **D2** (API FastAPI oui/non) : si validée, le P1-1 est remplacé par un endpoint agrégé et
  la couche `data.js` devient un client API (`api_contract.md`, `frontend_handoff.md`).
- **D3** (hébergement) : conditionne la mise en ligne, pas le développement.
- **D4/D5** (Earthdata, références) : conditionnent les vues d'observabilité réelle (H4-H6),
  pas le MVP.
