param(
    [string]$ComposeFile = "docker-compose.prod.yml"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $ComposeFile)) {
    throw "Compose file not found: $ComposeFile"
}

docker compose -f $ComposeFile pull
docker compose -f $ComposeFile up -d
docker compose -f $ComposeFile ps
