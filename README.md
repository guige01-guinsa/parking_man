# Parking Management

Parking enforcement backend designed to run independently and integrate into a facility management system.

## Quick Start

1. Copy env template:
   - `copy backend\.env.production.example backend\.env.production`
2. Start backend:
   - `pwsh -File backend\run.ps1`
3. Optional local reverse proxy:
   - `pwsh -File deploy\windows\start_stack.ps1`

Documentation:
- `docs/DEPLOYMENT.md`
- `docs/OPS.md`

SSO integration (ka-part):
- Entry endpoint: `/sso?ctx=<signed-token>`
- Shared claims: `site_code`, `permission_level`
- For integrated production use, set:
  - `PARKING_LOCAL_LOGIN_ENABLED=0`
  - `PARKING_CONTEXT_SECRET` (must match ka-part)
