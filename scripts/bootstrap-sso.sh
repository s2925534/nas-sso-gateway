#!/usr/bin/env bash
#
# bootstrap-sso.sh — bring up the local/LAN SSO stack for the first time.
#
# Does not delete anything. Public exposure (if any) is handled by whatever
# external tooling you choose — this script only starts the local Docker
# Compose stack.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f ".env" ]]; then
  echo "ERROR: .env not found. Copy .env.example to .env and fill in real secrets first:" >&2
  echo "  cp .env.example .env" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

echo "== Step 1/3: create persistent folders =="
"$SCRIPT_DIR/create-folders.sh"

echo "== Step 2/3: start Docker Compose =="
docker compose up -d

echo "== Step 3/3: wait for authentik-server to respond =="
# 0.0.0.0 means "listen on all interfaces" — it isn't itself a reachable
# address to curl, so probe localhost in that case instead.
SSO_HTTP_PORT="${SSO_HTTP_PORT:-9000}"
if [[ "${SSO_BIND_HOST:-0.0.0.0}" == "0.0.0.0" ]]; then
  BASE_URL="http://localhost:${SSO_HTTP_PORT}"
else
  BASE_URL="http://${SSO_BIND_HOST}:${SSO_HTTP_PORT}"
fi

ATTEMPTS=30
until curl -fsS "$BASE_URL/-/health/ready/" >/dev/null 2>&1; do
  ATTEMPTS=$((ATTEMPTS - 1))
  if [[ "$ATTEMPTS" -le 0 ]]; then
    echo "authentik did not report healthy in time. Check: docker compose logs authentik-server" >&2
    exit 1
  fi
  sleep 5
done

cat <<EOF

SSO stack is up.

  Access URL (local):    $BASE_URL
  Access URL (external): ${SSO_EXTERNAL_URL:-<not set>}

Reminders:
  - Public exposure of this service is handled by whatever external
    reverse-proxy/tunnel/deployer tooling you choose (if any), not this
    script. Keep PUBLIC_EXPOSURE=false in .env until that is wired up.
  - Change the bootstrap admin credentials as soon as you log in, and enable
    MFA before relying on this beyond local testing. See docs/security.md.
  - This script created folders and started containers only — it never
    deletes anything.
EOF
