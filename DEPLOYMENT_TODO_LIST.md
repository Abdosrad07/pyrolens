# PyroLens Hybrid Deployment - Todo List

## Infra & Bicep

- [ ] Create `infra/main.bicep`: Linux B1 plan, Python 3.12 Web App, Azure Storage + Azure Files mount (archive + models), appCommandLine, app settings (non-secret)
- [ ] Configure App Service settings:
  - [ ] `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
  - [ ] Startup command: `python -m uvicorn api.index:app --host 0.0.0.0 --port 8000`
  - [ ] `PYROLENS_ARCHIVE_DIR`, `PYROLENS_ARTIFACTS_DIR`
  - [ ] `PYROLENS_CORS_ORIGINS=https://votredomaine`
  - [ ] `PYROLENS_ALLOWED_POSTS=chat,firms/analyze,firms/history`
  - [ ] `PYROLENS_JOBS_ENABLED=true`
  - [ ] `PYROLENS_API_TOKEN` (if needed)
  - [ ] `FIRMS_MAP_KEY` (optional, for NRT)

## Startup Script

- [ ] Create `startup.sh`: uvicorn on `$PORT` / `WEBSITES_PORT` (default 8000)
- [ ] **No downloading** in startup or lifespan
- [ ] **No predict training** in startup or lifespan

## Frontend Configuration

- [ ] Rewrite `frontend/.htaccess`: SPA rewrite to index.html, en-têtes, cache, **no** `[P]` flag
- [ ] Copy `.htaccess` to `frontend/dist/` (Vite doesn't publish it automatically)
- [ ] Update `frontend/src/services/api.js`: VITE_API_BASE prefix for `/api/v1/*`
- [ ] Update `frontend/src/services/fireRisk.js`: **Priority**: `/api/v1/fire-risk` first, then `/artifacts/fire_risk.json`
- [ ] Build frontend: `VITE_API_BASE=https://<app>.azurewebsites.net npm run build` (no trailing slash)

## API Configuration

- [ ] Verify `api/index.py` entry point: `uvicorn api.index:app`
- [ ] CORS: set `PYROLENS_CORS_ORIGINS` in App Service (WITHOUT it, no headers → GoDaddy SPA fails)
- [ ] Set `PYROLENS_ALLOWED_POSTS=chat,firms/analyze,firms/history` (keep predict/experiments closed without token)
- [ ] `FIRMS_MAP_KEY`: only if NRT analysis needed; history works without key if CSV on disk (but gitignored)

## Data & Model Deployment

- [ ] **DO NOT** preload global archive in startup (exceeds B1 RAM ~1.75Go and 230s timeout)
- [ ] Azure Files mounting via Bicep: `PYROLENS_ARCHIVE_DIR` and `models/` persist across redeploys
- [ ] Without persistent disk: cache and `.joblib` lost on redeploy

## GitHub Workflows

- [ ] **Replace `.github/workflows/deploy.yml`** (trigger: after CI green on main):
  - [ ] `npm ci` + `npm run build` in `frontend/` with `VITE_API_BASE=${{ vars.VITE_API_BASE }}`
  - [ ] Copy `.htaccess` into `dist/`
  - [ ] Deploy API: `azure/webapps-deploy` with `AZURE_WEBAPP_PUBLISH_PROFILE` secret + app-name variable
  - [ ] FTP deploy of `dist/` to GoDaddy: secrets `GODADDY_FTP_SERVER`, `GODADDY_FTP_USERNAME`, `GODADDY_FTP_PASSWORD`, `GODADDY_FTP_DIR=public_html`

- [ ] **Create `.github/workflows/bootstrap-data.yml`** (trigger: `workflow_dispatch` only):
  - [ ] Mount/sync Azure Files share
  - [ ] Run Afrique download (list from `scripts/download_west_africa_archive.py`): Ouest + Cameroun + Tchad (18 countries × 2 × 13 = 468 files, 0.2s pause)
  - [ ] Resume on existing files
  - [ ] Run `pyrolens predict --source <archive>` → publish `fire_risk.json` + `.joblib` to shared dir (NOT repo)
  - [ ] CLI accepts archive tree (`rglob`, `origin firms_archive_sp`)

## GoDaddy Configuration

- [ ] `.htaccess` in `dist/` rewrites SPA to index.html, no `RewriteRule [P]`
- [ ] FTP deploy `dist/` → GoDaddy `public_html`
- [ ] Domain: `www` + apex → GoDaddy; API on `*.azurewebsites.net` or `api.<domain>`

## DNS & Domain

- [ ] `www.votredomaine.com` → GoDaddy shared hosting
- [ ] `api.votredomaine.com` → Azure App Service (optional, later) or keep on `*.azurewebsites.net`

## Security & Secrets

- [ ] **Never commit** to git: `FIRMS_MAP_KEY`, `PYROLENS_API_TOKEN`, FTP secrets, `AZURE_WEBAPP_PUBLISH_PROFILE`
- [ ] Add app settings in portal or via Bicep with `secureOnLinux` for secrets

## Testing & Validation

- [ ] Cold start: API responds immediately; first zone-history call per country is slow (cache miss), subsequent are fast
- [ ] GoDaddy SPA loads and calls `/api/v1/*` with CORS
- [ ] `/chat` works (deterministic, no LLM)
- [ ] `/firms/analyze` with key works (NRT)
- [ ] `/firms/history` works for cached countries
- [ ] Fire risk shows trained model (Afrique de l'Ouest + Centre, PR-AUC 0,926; not global)
- [ ] Non-whitelist POSTs blocked without `PYROLENS_API_TOKEN`
- [ ] Whitelist routes work without token

## Timeline & Notes

- [ ] **Phase 1**: Infra + API deployment (Bicep + Azure Files)
- [ ] **Phase 2**: Frontend build + GoDaddy deploy
- [ ] **Phase 3**: Bootstrap data job (Africa prewarming + training)
- [ ] **Phase 4**: DNS finalization and functional tests

- [ ] **Cold start (Basic, 1 instance)**: API responds immediately; regional model only (AO + Centre)
- [ ] **Global immediately**: Zone analysis at first click (no worldwide dump needed)
- [ ] **What remains regional**: Risk layer trained on Afrique de l'Ouest + Centre only
- [ ] **Archive awareness**: Full world = ~200 countries × 2 sensors × 13 years; prewarm once via GitHub job, then serve from disk