# Parking Management Deployment

This project is prepared to run as an independent service and be exposed under `/parking` in a facility management portal.

## 1. Backend setup

1. Copy env template and set secure values:
   - `copy backend\.env.production.example backend\.env.production`
   - Replace `PARKING_SECRET_KEY`, `PARKING_API_KEY`, `PARKING_CONTEXT_SECRET`.
   - If integrated with ka-part: set `PARKING_LOCAL_LOGIN_ENABLED=0`.
2. Start backend:
   - `pwsh -File backend\run.ps1`
3. Direct health check:
   - `http://127.0.0.1:8011/health`
4. SSO check (integration mode):
   - `http://127.0.0.1:8011/sso?ctx=<signed-token>`

## 2. Nginx reverse proxy (Windows local)

1. Start backend + nginx stack:
   - `pwsh -File deploy\windows\start_stack.ps1`
   - If `backend/.env.production` does not exist, the script creates one with random keys.
2. Access:
   - `http://127.0.0.1:8080/parking/login` (standalone login mode)
   - `http://127.0.0.1:8080/parking/admin2` (SSO session after `/sso`)
3. Verify proxy:
   - `pwsh -File deploy\verify\verify_proxy.ps1 -ApiKey "<your api key>"`
4. Stop stack:
   - `pwsh -File deploy\windows\stop_stack.ps1`

Config file:
- `deploy/nginx/nginx.local.conf`

## 3. IIS reverse proxy

Prerequisites:
- IIS Web Server
- URL Rewrite module
- Application Request Routing (ARR), proxy enabled

Apply config:
- `pwsh -File deploy\iis\configure_iis.ps1 -SiteName "Default Web Site"`

Config file:
- `deploy/iis/web.config`

## 4. Windows Service deployment

1. Prepare venv and env file:
   - `pwsh -File backend\run.ps1` (Ctrl+C after startup confirms venv/install are complete)
2. Install service (admin shell required):
   - `pwsh -File deploy\windows\install_service.ps1`
3. Remove service:
   - `pwsh -File deploy\windows\uninstall_service.ps1`

Service runner:
- `deploy/windows/service_runner.ps1`

## 5. Docker deployment

1. Create production env file:
   - `copy backend\.env.production.example backend\.env.production`
2. Start:
   - `docker compose up -d --build`
3. Verify:
   - `http://127.0.0.1:8080/parking/health`
4. Stop:
   - `docker compose down`

Files:
- `backend/Dockerfile`
- `docker-compose.yml`
- `deploy/nginx/docker-nginx.conf`

## 6. Data backup

Persist and back up:
- DB: `backend/app/data/parking.db` (or Docker volume `parking_data`)
- Uploads: `backend/app/uploads/` (or Docker volume `parking_uploads`)

## 7. Render deployment

Recommended settings:

1. Root Directory: `backend`
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

For full Render environment variable order, see:
- `docs/RENDER_ENV_CHECKLIST.md`

To generate strong random values for Render variables:
- `pwsh -File deploy\render\generate_render_env.ps1`
