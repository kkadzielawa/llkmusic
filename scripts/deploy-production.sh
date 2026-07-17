#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/kkadzielawa/llkmusic}"
BRANCH="${BRANCH:-deploy}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(basename "$APP_DIR")}"
COMPOSE_IS_LEGACY=0

cd "$APP_DIR"

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
  COMPOSE_IS_LEGACY=1
else
  echo "Neither 'docker compose' nor 'docker-compose' is available."
  exit 1
fi

cleanup_legacy_compose_containers() {
  local container_ids=()

  mapfile -t container_ids < <(docker ps -aq --filter "label=com.docker.compose.project=${PROJECT_NAME}")
  if ((${#container_ids[@]} == 0)); then
    return 0
  fi

  echo "Removing existing project containers before retry..."
  docker rm -f "${container_ids[@]}"
}

compose_up() {
  echo "Building and restarting containers..."
  "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" build web
  if "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d --remove-orphans; then
    return 0
  fi

  if ((COMPOSE_IS_LEGACY == 0)); then
    return 1
  fi

  echo "Legacy docker-compose retry after container cleanup..."
  cleanup_legacy_compose_containers
  "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d --build --remove-orphans
}

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

compose_up

echo "Pruning old Docker build cache..."
docker builder prune -f

echo "Deployment complete."
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" ps
