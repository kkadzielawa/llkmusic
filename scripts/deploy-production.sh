#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/kkadzielawa/llkmusic}"
BRANCH="${BRANCH:-deploy}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "$APP_DIR"

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Neither 'docker compose' nor 'docker-compose' is available."
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
git pull --ff-only origin "$BRANCH"

echo "Building and restarting containers..."
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" build web
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d --remove-orphans

echo "Pruning old Docker build cache..."
docker builder prune -f

echo "Deployment complete."
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps
