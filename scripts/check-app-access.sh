#!/usr/bin/env bash
#
# check-app-access.sh — read-only report of which applications in authentik
# have a group/user/policy access restriction bound, and which are open to
# any authenticated user. Never modifies state.
#
# Requires an authentik API token with at least read access to
# core.view_application and policies.view_policybinding (see
# docs/authentik-manual.md, "Creating an API Token for Automation").
#
# Usage: scripts/check-app-access.sh
# Reads SSO_EXTERNAL_URL (or SSO_DOMAIN) and AUTHENTIK_BOOTSTRAP_TOKEN from .env.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || exit 1

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required but not installed." >&2
  exit 1
fi

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

TOKEN="${AUTHENTIK_BOOTSTRAP_TOKEN:-}"
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: AUTHENTIK_BOOTSTRAP_TOKEN is not set in .env." >&2
  echo "See docs/authentik-manual.md, \"Creating an API Token for Automation\"." >&2
  exit 1
fi

BASE_URL="${SSO_EXTERNAL_URL:-}"
if [[ -z "$BASE_URL" ]]; then
  if [[ -n "${SSO_DOMAIN:-}" ]]; then
    BASE_URL="https://${SSO_DOMAIN}"
  else
    echo "ERROR: neither SSO_EXTERNAL_URL nor SSO_DOMAIN is set in .env." >&2
    exit 1
  fi
fi
BASE_URL="${BASE_URL%/}"

api_get() {
  curl -fsS -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" "$BASE_URL$1"
}

if ! apps_json="$(api_get "/api/v3/core/applications/")" || [[ -z "$apps_json" ]]; then
  echo "ERROR: failed to reach $BASE_URL/api/v3/core/applications/ — check the token and URL." >&2
  exit 1
fi

echo "== Application access report ($BASE_URL) =="
echo ""

app_count="$(echo "$apps_json" | jq '.results | length')"
if [[ "$app_count" -eq 0 ]]; then
  echo "No applications found."
  exit 0
fi

echo "$apps_json" | jq -c '.results[]' | while read -r app; do
  pk="$(echo "$app" | jq -r '.pk')"
  name="$(echo "$app" | jq -r '.name')"
  slug="$(echo "$app" | jq -r '.slug')"

  if ! bindings_json="$(api_get "/api/v3/policies/bindings/?target=$pk")"; then
    echo "$name ($slug): ERROR fetching policy bindings"
    continue
  fi

  binding_count="$(echo "$bindings_json" | jq '.results | length')"
  if [[ "$binding_count" -eq 0 ]]; then
    echo "$name ($slug): OPEN — no policy binding, any authenticated user can access it"
    continue
  fi

  echo "$name ($slug): $binding_count binding(s)"
  echo "$bindings_json" | jq -r '.results[] | "    - " +
    (if .enabled then "enabled" else "DISABLED" end) +
    ", group=" + (.group_obj.name // "none") +
    ", user=" + (.user_obj.username // "none") +
    ", policy=" + (.policy_obj.name // "none")'
done

echo ""
echo "Note: a binding with no group/user/policy resolvable, or all bindings disabled, may still"
echo "leave an application effectively open — inspect the authentik UI (Applications ->"
echo "Applications -> <app> -> Access) if a result here looks ambiguous."
