#!/usr/bin/env bash
#
# create-folders.sh — create persistent folders under SSO_BASE_PATH.
#
# Idempotent and non-destructive: only creates missing directories, never
# deletes or overwrites anything. Never assumes a Synology volume path.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env if present (does not overwrite already-exported variables).
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

SSO_BASE_PATH="${SSO_BASE_PATH:-}"

if [[ -z "$SSO_BASE_PATH" ]]; then
  echo "ERROR: SSO_BASE_PATH is not set. Refusing to create folders." >&2
  echo "Set it in .env (see .env.example) or export it before running this script." >&2
  exit 1
fi

# Folders are always relative to SSO_BASE_PATH, never a fixed NAS volume.
FOLDERS=(
  "$SSO_BASE_PATH/postgres"
  "$SSO_BASE_PATH/redis"
  "$SSO_BASE_PATH/authentik/media"
  "$SSO_BASE_PATH/authentik/custom-templates"
  "$SSO_BASE_PATH/authentik/certs"
  "$SSO_BASE_PATH/backups"
  "$SSO_BASE_PATH/logs"
  "$SSO_BASE_PATH/exports"
  "$SSO_BASE_PATH/docs"
)

echo "Creating persistent folders under: $SSO_BASE_PATH"
for folder in "${FOLDERS[@]}"; do
  if [[ -d "$folder" ]]; then
    echo "  exists:  $folder"
  else
    mkdir -p "$folder"
    echo "  created: $folder"
  fi
done

echo "Done. No existing files or folders were modified or deleted."
