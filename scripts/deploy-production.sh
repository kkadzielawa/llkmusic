#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/kkadzielawa/llkmusic}"
BRANCH="${BRANCH:-deploy}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "$APP_DIR"

if ! docker compose version >/dev/null 2>&1; then
  echo "'docker compose' is required on the production host."
  exit 1
fi

echo "Validating deployment directory..."
test -f .env
test -f "$COMPOSE_FILE"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Refusing to deploy: working tree has uncommitted changes."
  exit 1
fi

echo "Fetching latest code..."
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "Building and restarting containers..."
docker compose -f "$COMPOSE_FILE" build web
docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans

echo "Pruning old Docker build cache..."
docker builder prune -f

echo "Deployment complete."
docker compose -f "$COMPOSE_FILE" ps
