#!/usr/bin/env sh
set -eu

API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"
SMOKE_EMAIL="${SMOKE_EMAIL:-admin@example.com}"
SMOKE_PASSWORD="${SMOKE_PASSWORD:-password}"
export SMOKE_EMAIL SMOKE_PASSWORD

API_URL="${API_URL%/}"
FRONTEND_URL="${FRONTEND_URL%/}"

step() {
  printf '==> %s\n' "$1"
}

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

need curl
need python3

step "Checking backend health at $API_URL/health"
health="$(curl -fsS "$API_URL/health")"
printf '%s' "$health" | python3 -c "import json,sys; assert json.load(sys.stdin).get('status') == 'ok'"

step "Checking frontend at $FRONTEND_URL"
curl -fsSI "$FRONTEND_URL" >/dev/null

step "Logging in as $SMOKE_EMAIL"
login_payload="$(python3 -c 'import json,os; print(json.dumps({"email": os.environ["SMOKE_EMAIL"], "password": os.environ["SMOKE_PASSWORD"]}))')"
login_response="$(curl -fsS -H 'Content-Type: application/json' -d "$login_payload" "$API_URL/auth/login")"
token="$(printf '%s' "$login_response" | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token') or '')")"
if [ -z "$token" ]; then
  printf 'Login did not return an access token.\n' >&2
  exit 1
fi

step "Checking current user"
me_response="$(curl -fsS -H "Authorization: Bearer $token" "$API_URL/auth/me")"
printf '%s' "$me_response" | python3 -c "import json,os,sys; assert json.load(sys.stdin).get('email') == os.environ['SMOKE_EMAIL']"

step "Checking ticket list"
curl -fsS -H "Authorization: Bearer $token" "$API_URL/tickets" >/dev/null

printf 'Smoke checks passed.\n'
