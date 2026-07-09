# Restore Notes

There is no automated restore script yet (tracked under `ENABLE_RESTORE_TESTING` in
[`../docs/future-flags.md`](../docs/future-flags.md)). Restoring is deliberately manual so a
backup is never applied by accident. This document is the procedure until that changes.

## Before You Start

- Restoring overwrites live data. Stop and think about whether you actually want to replace the
  current state, or whether you're recovering into a fresh environment.
- Take a fresh backup of the *current* state first if it has anything worth keeping
  (`scripts/backup-sso.sh`), even if it's broken — you may want to compare later.

## Restore Procedure (PostgreSQL)

1. Stop the stack so nothing writes to the database during restore:

   ```bash
   docker compose stop authentik-server authentik-worker
   ```

2. Restore the dump into the running `sso-postgresql` container (adjust the backup path):

   ```bash
   cat "$SSO_BASE_PATH/backups/<timestamp>/postgres-dump.sql" | \
     docker exec -i sso-postgresql psql -U "$POSTGRES_USER" "$POSTGRES_DB"
   ```

   If the target database already has conflicting data, you likely want to drop and recreate the
   database first — do this deliberately, not as a default:

   ```bash
   docker exec sso-postgresql dropdb -U "$POSTGRES_USER" "$POSTGRES_DB"
   docker exec sso-postgresql createdb -U "$POSTGRES_USER" -O "$POSTGRES_USER" "$POSTGRES_DB"
   ```

3. Restore media/custom-templates/certs by copying the backed-up folders back into
   `$SSO_BASE_PATH/authentik/...`, replacing only what you intend to replace.

4. Restart the stack:

   ```bash
   docker compose up -d
   ```

5. Verify with `scripts/health-check.sh` and by logging in.

## Caveats

- A `pg_dump` restore assumes the target PostgreSQL major version is compatible with the dump.
- Restoring does not automatically fix an expired/rotated `AUTHENTIK_SECRET_KEY` mismatch —
  keep that value stable across backup and restore, or some encrypted fields may become
  unreadable.
- Test this procedure at least once in a disposable environment before you need it for real. An
  untested backup is not a backup.
