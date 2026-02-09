# Parking Enforcer OPS

- Run: backend/run.ps1
- Login: http://SERVER:8011/login
- Admin: http://SERVER:8011/admin2
- Deployment details: docs/DEPLOYMENT.md

Backup:
- backend/app/data/parking.db
- backend/app/uploads/

Security:
- Change PARKING_SECRET_KEY
- Change default passwords
- Set PARKING_ROOT_PATH=/parking when reverse-proxied under facility portal path
