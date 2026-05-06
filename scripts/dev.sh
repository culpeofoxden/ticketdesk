#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
COMMAND="${1:-ps}"

cd "$ROOT"

case "$COMMAND" in
  up)
    docker compose up --build -d
    ;;
  down)
    docker compose down
    ;;
  restart)
    docker compose down
    docker compose up --build -d
    ;;
  ps)
    docker compose ps
    ;;
  logs)
    docker compose logs --tail=120
    ;;
  backend-logs)
    docker compose logs backend --tail=120
    ;;
  frontend-logs)
    docker compose logs frontend --tail=120
    ;;
  db-logs)
    docker compose logs db --tail=120
    ;;
  build-frontend)
    docker compose exec -T frontend npm run build
    ;;
  smoke)
    sh "$ROOT/scripts/smoke.sh"
    ;;
  *)
    printf 'Usage: sh scripts/dev.sh [up|down|restart|ps|logs|backend-logs|frontend-logs|db-logs|build-frontend|smoke]\n' >&2
    exit 1
    ;;
esac
