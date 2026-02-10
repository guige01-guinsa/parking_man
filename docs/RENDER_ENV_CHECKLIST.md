# Render Environment Checklist

This checklist is for running `parking_man` as an independent Render service and connecting from `ka-part.com`.

## 1. parking_man Render service

Recommended Render service settings:

1. `Environment`: `Python 3`
2. `Root Directory`: `backend`
3. `Build Command`: `pip install -r requirements.txt`
4. `Start Command`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. `Auto-Deploy`: `On Commit`

If your Render service uses repo root as Root Directory:

1. `Build Command`: `pip install -r backend/requirements.txt`
2. `Start Command`: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

Do not use `gunicorn ... app:app` with this repository layout.

Environment variables input order:

1. `PARKING_API_KEY=<strong-random-string>`
2. `PARKING_SECRET_KEY=<strong-random-string>`
3. `PARKING_CONTEXT_SECRET=<strong-random-string>` (must match ka-part)
4. `PARKING_LOCAL_LOGIN_ENABLED=0`
5. `PARKING_CONTEXT_MAX_AGE=300`
6. `PARKING_DEFAULT_SITE_CODE=COMMON`
7. `PARKING_PORTAL_URL=https://www.ka-part.com/pwa/`
8. `PARKING_ROOT_PATH=`
9. `PARKING_SESSION_MAX_AGE=43200`

`PARKING_ROOT_PATH` rules:

- Use empty value for standalone domain mode (for example `https://parking-man.onrender.com`).
- Use `/parking` only when traffic is reverse-proxied under `/parking`.

Optional persistent storage values (if Render Disk is attached, mount path `/var/data`):

1. `PARKING_DB_PATH=/var/data/parking.db`
2. `PARKING_UPLOAD_DIR=/var/data/uploads`

## 2. ka-part Render service (gateway mode to parking_man)

Environment variables input order:

1. `ENABLE_PARKING_EMBED=0`
2. `PARKING_BASE_URL=https://<parking-man-domain>`
3. `PARKING_SSO_PATH=/sso`
4. `PARKING_CONTEXT_SECRET=<same value as parking_man>`
5. `PARKING_CONTEXT_MAX_AGE=300`

`PARKING_SSO_PATH` rules:

- Use `/sso` when `parking_man` is served at domain root.
- Use `/parking/sso` only when `parking_man` itself is mounted under `/parking`.

## 3. Validation after deploy

1. `https://www.ka-part.com/api/health` returns `200`.
2. `https://www.ka-part.com/parking/health` returns `200` (embed mode) or handoff page `200` (gateway mode).
3. `https://www.ka-part.com/parking/admin2` returns `200` and routes to the parking service.
4. Parking service direct health URL returns `200`:
   - `https://<parking-man-domain>/health`
