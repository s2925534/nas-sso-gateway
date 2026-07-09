#!/usr/bin/env bash
#
# health-check.sh — read-only checks of the SSO stack. Never modifies state.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS=0
FAIL=0

check() {
  local desc="$1"
  local status="$2" # 0 = pass, non-zero = fail
  if [[ "$status" -eq 0 ]]; then
    echo "  [PASS] $desc"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] $desc"
    FAIL=$((FAIL + 1))
  fi
}

echo "== Docker =="
docker info >/dev/null 2>&1
check "Docker daemon is reachable" $?

echo "== Docker Compose =="
docker compose version >/dev/null 2>&1
check "Docker Compose plugin is available" $?

echo "== .env =="
if [[ -f ".env" ]]; then
  check ".env file exists" 0
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
else
  check ".env file exists (copy .env.example to .env)" 1
fi

echo "== Containers =="
for svc in sso-postgresql sso-redis sso-authentik-server sso-authentik-worker; do
  state="$(docker inspect -f '{{.State.Running}}' "$svc" 2>/dev/null)"
  [[ "$state" == "true" ]]
  check "container $svc is running" $?
done

echo "== Authentik web endpoint =="
BASE_URL="http://localhost:${SSO_HTTP_PORT:-9000}"
curl -fsS "$BASE_URL/-/health/ready/" >/dev/null 2>&1
check "authentik web endpoint responds at $BASE_URL" $?

echo "== Persistent folders =="
SSO_BASE_PATH="${SSO_BASE_PATH:-./data/sso}"
for folder in postgres redis authentik/media authentik/custom-templates authentik/certs backups logs exports docs; do
  [[ -d "$SSO_BASE_PATH/$folder" ]]
  check "folder exists: $SSO_BASE_PATH/$folder" $?
done

echo ""
echo "== Summary =="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"

if [[ "$FAIL" -gt 0 ]]; then
  echo ""
  echo "See docs/troubleshooting.md for common causes."
  exit 1
fi

echo "All checks passed."
