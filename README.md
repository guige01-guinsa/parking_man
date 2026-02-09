# Parking Management

Parking enforcement backend designed to run independently and integrate into a facility management system.

## Quick start

1. Copy env template:
   - `copy backend\.env.production.example backend\.env.production`
2. Start backend:
   - `pwsh -File backend\run.ps1`
3. Optional local reverse proxy:
   - `pwsh -File deploy\windows\start_stack.ps1`

Documentation:
- `docs/DEPLOYMENT.md`
- `docs/OPS.md`
