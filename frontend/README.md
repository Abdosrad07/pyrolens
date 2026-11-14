# Fire Monitor — Frontend React (PyroLens)

Interface modulaire Fire Monitor : carte Leaflet (tuiles NASA GIBS), vues Aperçu/Calendrier/Jobs/Qualité/Risque, panneau de prédiction de risque, assistant IA.

## Prérequis

- Node.js >= 18
- npm >= 9

## Installation

```bash
cd frontend
npm install
```

## Lancement dev

```bash
npm run dev
```

Le serveur démarre sur **http://localhost:5174** (port dédié pour ne pas entrer en conflit avec `web/` sur 5173).

Le proxy Vite relaye automatiquement `/api/*` vers le backend FastAPI (`http://127.0.0.1:8010` par défaut).

## Build production

```bash
npm run build
```

Résultat dans `frontend/dist/`.

## Architecture

```
frontend/
├── package.json
├── vite.config.js            # port 5174, proxy /api → FastAPI
├── index.html
├── .env.local.example        # variables d'environnement
├── public/
│   └── artifacts/            # copier de web/public/artifacts si existants
└── src/
    ├── main.jsx              # point d'entrée
    ├── App.jsx               # état global, routing vues
    ├── styles/
    │   └── globals.css       # design system + tous les styles
    ├── components/
    │   ├── TopBar.jsx        # barre du haut (marque, recherche, actions)
    │   ├── MapView.jsx       # carte Leaflet via react-leaflet + tuiles GIBS
    │   ├── DockNav.jsx       # barre de navigation centrale
    │   ├── RiskSphere.jsx    # bouton flottant sphère
    │   ├── RiskPanel.jsx     # panneau latéral configuration risque
    │   ├── AiPanel.jsx       # panneau assistant IA
    │   ├── Toast.jsx         # notifications toast
    │   └── icons.jsx         # composant SVG réutilisable
    ├── views/
    │   ├── OverviewView.jsx  # Aperçu des observations
    │   ├── CalendarView.jsx  # Calendrier des feux
    │   ├── JobsView.jsx      # Jobs Slurm
    │   ├── DqView.jsx        # Rapport de qualité des données
    │   └── RiskView.jsx      # Vue pleine page Risque
    ├── hooks/
    │   ├── useMap.js         # manipulation carte (flyTo, ref)
    │   ├── useRiskData.js    # chargement fire_risk.json
    │   └── useApi.js         # fetch API /api/v1/*
    ├── services/
    │   ├── api.js            # apiGet / apiPost (VITE_API_BASE)
    │   └── fireRisk.js       # fetchFireRisk()
    └── data/
        └── constants.js      # RISK_LEVELS, CAM_BBOX, JOBS, DQ_BASE
```

## Variables d'environnement

Copier `.env.local.example` en `.env.local` :

| Variable | Défaut | Description |
|---|---|---|
| `VITE_API_ORIGIN` | `http://127.0.0.1:8010` | Backend FastAPI |
| `VITE_API_BASE` | `""` (proxy) | Base URL API (vide = proxy Vite) |

Exemple `.env.local` :

```env
VITE_API_ORIGIN=http://127.0.0.1:8010
```

## Connexion au backend FastAPI

Le proxy Vite (`vite.config.js`) relaye automatiquement `/api/*` vers le backend défini par `VITE_API_ORIGIN`.

Endpoints consommés :

- `GET /artifacts/fire_risk.json` — données de risque
- `GET /api/v1/fire-risk` — idem (fallback)
- `POST /api/v1/chat` — assistant IA
- Recherche Nominatim : `https://nominatim.openstreetmap.org/search`

## Design System

Le design system est conservé tel quel depuis le fichier HTML source :

- **Couleurs** : canopy (#0E2A25), ash (#F2F6F4), ember (#F2541B), sulphur (#FFC83D), lagoon (#168F80)
- **Polices** : Bricolage Grotesque (display), Instrument Sans (UI)
- **Variables CSS** : toutes les variables `:root` sont dans `globals.css`

## Lien vers le projet PyroLens

- Backend : `C:\Users\USER\Desktop\Pyrolens\pyrolens\`
- Web app existante : `C:\Users\USER\Desktop\Pyrolens\pyrolens\web\`
- Fire Monitor React : `C:\Users\USER\Desktop\Pyrolens\pyrolens\frontend\`

## Licence

PyroLens — étude de faisabilité.
