#!/usr/bin/env sh
set -eu

COMPOSE_FILE="${1:-docker-compose.prod.yml}"

docker compose -f "$COMPOSE_FILE" pull
docker compose -f "$COMPOSE_FILE" up -d
docker compose -f "$COMPOSE_FILE" ps
