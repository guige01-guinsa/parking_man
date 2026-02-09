# Parking Enforcer OPS

- Run: backend/run.ps1
- Login: http://SERVER:8011/login
- Admin: http://SERVER:8011/admin2
- SSO: http://SERVER:8011/sso?ctx=<signed-token>
- Deployment details: docs/DEPLOYMENT.md

Backup:
- backend/app/data/parking.db
- backend/app/uploads/

Security:
- Change PARKING_SECRET_KEY
- Change PARKING_CONTEXT_SECRET (same value as facility portal)
- Change default passwords
- Set PARKING_ROOT_PATH=/parking when reverse-proxied under facility portal path
- Set PARKING_LOCAL_LOGIN_ENABLED=0 for integration-only operation
