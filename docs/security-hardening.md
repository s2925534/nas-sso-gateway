# Security Hardening (Phase 6)

Moves the deployment from "works" to "safe to depend on." Each item below expands on the
corresponding rule in [`docs/security.md`](security.md) with a concrete procedure. Do this before
any app in Phase 4/5 becomes something you'd be upset to lose access to.

## MFA Enforcement

Scope: passkey (WebAuthn) is the only MFA method in use. TOTP-authenticator-app and SMS are
deferred until asked for again — the steps below should only ever bind/require a passkey stage,
not a generic "any authenticator" stage.

1. **Directory → Policies → Create → Password Policy / Authenticator Validation Policy**, or use
   authentik's per-flow MFA stage binding, scoped to WebAuthn/passkey specifically.
2. Bind a passkey-required stage to your default authentication flow, or scope it to specific
   groups first (e.g. `admins`) before rolling out to everyone.
3. Test with a non-admin test account before enforcing broadly, so you don't lock yourself out.
4. Blanket enforcement is tracked as `ENABLE_MFA_ENFORCEMENT` in
   [`docs/future-flags.md`](future-flags.md); passkey itself is active scope, not a future flag —
   see ADR-012 in [`docs/decision-log.md`](decision-log.md).

## Admin Account Separation

- Confirm the admin/bootstrap account is not a member of any `app-*-users` group (see
  [`docs/multi-app-rollout.md`](multi-app-rollout.md)) — admin access to authentik itself should
  not imply access to every downstream app.
- Confirm your day-to-day account (Phase 3, Step 2) is not a superuser.
- Periodically review **Directory → Users** for any account with superuser rights beyond what you
  expect.

## Backup and Restore Test

1. Run `scripts/backup-sso.sh` against a real running stack.
2. Follow [`scripts/restore-notes.md`](../scripts/restore-notes.md) to restore that backup into a
   **disposable** test environment (a second, throwaway `SSO_BASE_PATH` / Postgres instance) — not
   your live one.
3. Confirm you can log in with the restored admin account and that app/provider configuration
   came back intact.
4. Only after this succeeds once should you trust the backup process for the real deployment.
5. Tracked as `ENABLE_RESTORE_TESTING` in [`docs/future-flags.md`](future-flags.md).

## Emergency Access Plan

- Write down (outside of Git — a password manager note is fine) the exact steps to:
  1. Reach the Docker host directly (SSH/console) if `auth.example.com` is unreachable.
  2. Restart the stack (`docker compose up -d` from this repo) without needing the web UI first.
  3. Reset the admin password via authentik's management command if locked out (see
     [`docs/troubleshooting.md`](troubleshooting.md) — "Lost Admin Password").
  4. Disable forward-auth enforcement for a specific app if authentik itself is down (see the
     per-app rollback step recorded in Phase 4/5).
- Review this plan whenever the deployment topology changes (new host, new reverse proxy, etc.).

## Audit Logging

- **Directory/Events → Logs** (authentik's built-in event log) — review periodically for:
  - Failed login attempts, especially against the admin account.
  - New application/provider creation you don't recognize.
  - Group membership changes.
- Decide a review cadence (e.g. monthly) and put it in your own calendar/reminder system — this
  repo does not automate log review. Tracked as `ENABLE_AUDIT_LOG_REVIEW` in
  [`docs/future-flags.md`](future-flags.md).

## Session Lifetime Review

1. **Flows & Stages → Stages → (your session/user-login stage) → Session duration.**
2. Balance convenience vs. exposure: shorter sessions reduce the window a stolen/lost device
   session is usable, longer sessions reduce login friction.
3. Consider shorter sessions for the admin account specifically (a separate flow/stage binding)
   than for day-to-day users.

## Password Policy Review

1. **Directory → Policies → Password Policy** — review minimum length/complexity requirements.
2. Prefer requiring long passphrases over complex-but-short passwords, and rely on MFA as the
   primary defense rather than password complexity alone.

## Recovery Codes

- Confirm every MFA-enrolled account (starting with admin) has generated and safely stored
  recovery codes — **Directory → Users → (user) → MFA Authenticators** shows enrollment status.
- Store recovery codes in a password manager, not in this repo, not in plaintext notes synced
  anywhere public.
- Re-generate and re-store recovery codes if you ever suspect they were exposed.

## Image Upgrade Procedure

`docker-compose.yml` pins exact `authentik`/PostgreSQL/Redis versions rather than floating tags
(`latest`, `16-alpine`, `7-alpine`), so upgrades are a deliberate, reviewed step rather than
something that happens silently on a routine `docker compose pull`.

1. Run `scripts/backup-sso.sh` first — see "Backup and Restore Test" above. Never upgrade against
   a database you have no working restore path for.
2. Check the release notes for the specific version jump:
   - authentik: <https://docs.goauthentik.io/releases/> — read every version between your current
     pin and the target, not just the target's notes; breaking changes and required migration
     steps are called out per release.
   - PostgreSQL/Redis: bump patch versions within the same major freely; treat a major version
     bump (e.g. `16.x` → `17.x`) as its own separate, planned migration.
3. Update the pin:
   - `AUTHENTIK_TAG` in your `.env` (or the default in `.env.example` if you're updating the
     project baseline), matching the exact tag from
     <https://github.com/goauthentik/authentik/pkgs/container/server>.
   - The `image:` lines in `docker-compose.yml` for `postgresql`/`redis`, matching exact tags from
     Docker Hub (`postgres`, `redis` official images).
4. `docker compose pull && docker compose up -d`, then `scripts/health-check.sh`.
5. Smoke-test: log in as your normal user (Phase 3, Step 2) and confirm at least one existing
   OIDC/proxy-provider app still authenticates correctly before considering the upgrade done.
6. If anything breaks, roll back by restoring the pinned tags and redeploying, then restore the
   pre-upgrade backup from Step 1 if the database was already migrated.
