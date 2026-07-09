#!/usr/bin/env bash
#
# backup-sso.sh — create a timestamped backup of SSO config/export areas.
#
# Non-destructive: only reads from the running stack and writes new files
# under SSO_BASE_PATH/backups. Never deletes prior backups.
#
# NOTE: this performs a `pg_dump` (a consistent logical backup taken while
# PostgreSQL is running) rather than copying data files directly, which is
# the safe way to back up a live database. Restoring is a manual, deliberate
# step — see scripts/restore-notes.md before relying on this in production.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

SSO_BASE_PATH="${SSO_BASE_PATH:-}"
if [[ -z "$SSO_BASE_PATH" ]]; then
  echo "ERROR: SSO_BASE_PATH is not set. Refusing to back up." >&2
  exit 1
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$SSO_BASE_PATH/backups/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "Backing up to: $BACKUP_DIR"

echo "== Database dump (pg_dump) =="
if docker inspect -f '{{.State.Running}}' sso-postgresql >/dev/null 2>&1; then
  docker exec sso-postgresql pg_dump -U "${POSTGRES_USER:-authentik}" "${POSTGRES_DB:-authentik}" \
    > "$BACKUP_DIR/postgres-dump.sql"
  echo "  wrote: $BACKUP_DIR/postgres-dump.sql"
else
  echo "  SKIPPED: sso-postgresql container is not running." >&2
fi

echo "== Media / custom templates / certs =="
for area in media custom-templates certs; do
  src="$SSO_BASE_PATH/authentik/$area"
  if [[ -d "$src" ]]; then
    dest="$BACKUP_DIR/authentik-$area"
    cp -R "$src" "$dest"
    echo "  copied: $src -> $dest"
  fi
done

echo "== .env.example (for reference; never back up real .env secrets here) =="
cp "$REPO_ROOT/.env.example" "$BACKUP_DIR/.env.example" 2>/dev/null || true

cat <<EOF

Backup complete: $BACKUP_DIR

Notes:
  - The database backup is a pg_dump logical export, not a raw data-directory
    copy — this is the safe way to back up a live PostgreSQL instance.
  - This script never deletes prior backups; prune old ones manually once
    you have a retention policy you trust.
  - Test restoring from a backup before relying on it — see
    scripts/restore-notes.md.
EOF
