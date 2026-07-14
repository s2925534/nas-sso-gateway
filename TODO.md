# TODO

Status legend: `[ ]` not done, `[x]` done. See [`docs/phase-plan.md`](docs/phase-plan.md) for the
full description of each phase.

## Phase 0: Planning and Documentation Foundation

- [x] Create README
- [x] Create architecture document
- [x] Create phase plan
- [x] Create decision log
- [x] Create security document
- [x] Create authentik manual
- [x] Create deployer integration notes
- [x] Create reverse proxy/domain notes
- [x] Create app integration patterns
- [x] Create OIDC integration notes
- [x] Create proxy-auth integration notes
- [x] Create troubleshooting guide
- [x] Create future flags
- [x] Create TODO with phases and checkboxes
- [x] Validate docs
- [x] Commit and push

## Phase 1: Authentik MVP Foundation

- [x] `.env.example`
- [x] `.gitignore`
- [x] Docker Compose for authentik, PostgreSQL, and Redis
- [x] Folder creation script
- [x] Bootstrap script
- [x] Health check script
- [x] Backup script
- [x] Initial local-only startup (`create-folders.sh` smoke-tested; full `docker compose up` requires Docker, not available in this environment — see manual steps in README)
- [x] Basic validation
- [x] Commit and push

## Phase 2: External Deployment Integration Readiness

This repo does not depend on any specific deployment tool — it runs standalone via
`docker compose up -d`, or behind any reverse-proxy/tunnel/deployer of your choice.
`../synology-site-deployer` is documented as one optional worked example, not a requirement.

- [x] Document how external deployment tooling (standalone, or any reverse proxy/deployer — with `../synology-site-deployer` as one worked example) should consume this repo
- [x] Add deployer metadata if useful — investigated `synology-site-deployer`'s `deploy` command source as the example case; it reads no manifest/metadata file from a target project (CLI flags only), so a metadata file would be inert for that tool or any similar one. Documented the actual `synology-site deploy` invocation (flags, and an authentik-specific `--health-path` caveat) in `docs/deployer-integration.md` as an example, alongside the standalone path.
- [x] Confirm the persistent-path contract works whether path is chosen manually or by external tooling (`SSO_BASE_PATH`, never hardcoded)
- [x] Confirm Cloudflare/domain exposure is always external to this repo, regardless of which tool (or none) is used
- [x] Confirm only the authentik web endpoint is ever exposed, regardless of which external tooling fronts it
- [x] Avoid direct Cloudflare implementation in this repo (confirmed — no Cloudflare code/deps anywhere in this repo)
- [x] Genericize every doc/script/example so nothing hardcodes a personal domain or requires a
      specific external tool by name (generic `SSO_DOMAIN` / "external tooling" language
      throughout; `../synology-site-deployer` kept only as one optional worked example)

## Phase 3: First SSO Configuration Guide

Hands-on walkthrough written in `docs/first-sso-configuration.md`, covering every item below with
a worked example. These are live-system actions, so each stays unchecked until actually performed
against a running instance — Docker was not available in the environment this session ran in, so
the guide is ready but unexecuted. Run it via `scripts/bootstrap-sso.sh`, then work the doc top to
bottom.

- [x] First admin account setup — implied done (verified 2026-07-14: a real OIDC provider/app
      exists live in authentik for `publisher.veloso.dev`, which requires having logged in as
      admin at least once; see Phase 4)
- [ ] First normal user setup (guide ready: §2) — unconfirmed whether a separate day-to-day
      account exists yet, or whether the admin account is still being used for everything
- [ ] MFA recommendation applied (guide ready: §3, scope narrowed — see below) — unconfirmed
- [x] First OIDC provider/client example — superseded by the real one for `publisher` (Phase 4);
      no separate placeholder example needed
- [ ] First proxy provider example (guide ready: §6) — not needed for the current app (no
      forward-auth in use), low priority
- [ ] App portal example (guide ready: §7) — unconfirmed
- [ ] Group and role examples (guide ready: §4) — unconfirmed whether `publisher` is
      group-restricted (see Phase 4 note)

MFA scope decision (2026-07-14): only passkey (WebAuthn) and username/password are in scope for
login. TOTP-authenticator-app and SMS-based MFA are explicitly deferred until asked for again or
until there's nothing else to do. `docs/first-sso-configuration.md` §3,
`docs/security.md`, and `docs/security-hardening.md` updated to reflect this. See ADR-012 in
`docs/decision-log.md`.

Tooling note (2026-07-15): the "unconfirmed" items above (group restriction, MFA enrollment
status) couldn't be checked without an API token or a browser session. Added
`scripts/check-app-access.sh` (reports per-application group/user/policy bindings) and documented
how to create an API token in `docs/authentik-manual.md` ("Creating an API Token for Automation").
Once `AUTHENTIK_BOOTSTRAP_TOKEN` is set in `.env`, run that script to resolve the group-restriction
question directly. It hasn't been run against a live instance yet — verify it works as expected
the first time, don't fully trust it blind.

**Incident (2026-07-14/15, discovered and resolved on its own during this session):** the live
instance was unreachable (502 via the tunnel) when checked. Diagnosed via
`../synology-site-deployer`'s read-only `logs`/`ps` commands (no Docker access from this sandbox
otherwise): the NAS's Docker daemon went unreachable around `14:13:52Z` on 2026-07-14 (Watchtower's
own log shows "Cannot connect to the Docker daemon" followed by a fatal panic in its own cron job),
taking down `sso-authentik-server`, `sso-postgresql`, `sso-redis`, the Supabase stack, and
Watchtower itself — `cloudflared` stayed up the whole time and correctly 502'd since it couldn't
reach any of those origins. Everything came back on its own via container restart policies around
`20:42-20:46Z` (~6.5 hours later) — authentik's own worker log shows a 318-second startup
("`took_s`": 318.5) before it was internally healthy again. No action was taken here beyond
read-only diagnosis; verified recovered afterward (`sso.systemsnotsilos.com` → 302,
`publisher.veloso.dev` → 307, OIDC discovery → 200). Root cause of the *original* Docker daemon
outage is not determined — that's DSM/Synology-level, outside what container logs show. Worth
checking DSM's own system log / Docker package status / any update-triggered restart when next at
the NAS, and worth considering whether existing NAS monitoring (there's an `uptime-kuma` bootstrap
command in `../synology-site-deployer` — unclear if it's actually deployed/watching this) should
have alerted on a 6.5-hour outage and didn't.

## Phase 4: Protect First NAS Web App

App chosen: `../wordpress-ai-publisher`, a custom Next.js content-publishing tool (not actually
WordPress — it generates AI content packages and publishes them to a separate WordPress site via
a companion plugin). It currently has zero built-in authentication on any route. See ADR-011 in
[`docs/decision-log.md`](docs/decision-log.md) for the full reasoning below.

- [x] Select one simple internal app — `wordpress-ai-publisher`
- [x] Protect it through OIDC — native OIDC (optional, env-gated) is being added directly in the
      app itself, tracked in `../wordpress-ai-publisher/TODO.md` ("Authentication (Local
      Credentials + Optional SSO)"), not implemented in this repo (by design; see README "What
      This Project Does Not Do"). Forward-auth is **not** needed for this app — no reverse proxy
      is being introduced, since Cloudflare Tunnel already routes straight to the app's existing
      port and native OIDC needs no proxy in front.
- [x] This repo's own remaining piece: create the OIDC Provider and Application against the live
      authentik instance. **Done** (verified 2026-07-14: `publisher.veloso.dev`'s
      `infra/web/.env` has `ENABLE_OIDC_SSO=true` with real issuer/client id/secret, and
      `https://sso.systemsnotsilos.com/application/o/publisher/.well-known/openid-configuration`
      resolves live). Actual application slug is `publisher`, not the originally planned
      `provider-wordpress-ai-publisher` / `app-wordpress-ai-publisher-users` naming from
      [`docs/multi-app-rollout.md`](docs/multi-app-rollout.md) — left as-is since it's live and
      working; renaming would mean recreating the provider/app and updating the redirect URI for
      no functional benefit. Whether the `publisher` application is group-restricted or open to
      any authenticated user is unconfirmed — check **Applications → Applications → publisher →
      Access** in the authentik UI next time you're in there.
- [x] Document rollback and emergency bypass — **Done**, already written into that app's own repo
      per the per-app-docs convention: `../wordpress-ai-publisher/docs/AUTHENTICATION.md` (§"Optional
      OIDC SSO", closing paragraph) states local login is a genuinely separate path, not a fallback
      that depends on OIDC working, and that disabling `ENABLE_OIDC_SSO` + redeploying is the full
      rollback — matching ADR-011's Consequences section here. No separate break-glass path is
      needed beyond that.

## Phase 5: Multi-App SSO Rollout

- [x] Standard app onboarding checklist (`docs/multi-app-rollout.md`)
- [x] Per-app client/provider naming convention (`docs/multi-app-rollout.md`)
- [x] Per-app group access policy (`docs/multi-app-rollout.md`)
- [x] Per-app redirect URL documentation (`docs/multi-app-rollout.md`)
- [x] Per-app logout behavior (`docs/multi-app-rollout.md`)
- [x] App portal organization (`docs/multi-app-rollout.md`)

## Phase 6: Security Hardening

Procedures documented in `docs/security-hardening.md`. Each stays unchecked until actually carried
out against a running instance (requires Docker, not available in this environment this session).

- [ ] MFA enforcement (procedure ready)
- [ ] Admin account separation (procedure ready)
- [ ] Backup and restore test (procedure ready — needs a real run against a disposable environment)
- [ ] Emergency access plan (procedure ready — needs your own off-repo notes filled in)
- [ ] Audit logging (procedure ready — needs an ongoing review cadence you set)
- [ ] Session lifetime review (procedure ready)
- [ ] Password policy review (procedure ready)
- [ ] Recovery codes (procedure ready)
- [x] Pin exact image versions (authentik/PostgreSQL/Redis) instead of floating tags, and document
      the upgrade procedure (`docker-compose.yml`, `.env.example`; procedure in
      `docs/security-hardening.md` — "Image Upgrade Procedure")

## Phase 7: Future Advanced Identity

Intentionally documentation-only for now (per project rules: document future capabilities instead
of implementing them ahead of need). Tracked as flags in `docs/future-flags.md`
(`ENABLE_EXTERNAL_IDENTITY_PROVIDERS`, `ENABLE_PASSWORDLESS_LOGIN`, `ENABLE_LDAP_SUPPORT`,
`ENABLE_SAML_SUPPORT`, `ENABLE_API_AUTH_GATEWAY`, `ENABLE_SERVICE_ACCOUNTS`,
`ENABLE_GROUP_BASED_ACCESS`, `ENABLE_BACKUP_AUTOMATION`, `ENABLE_PORTABLE_LOCAL_SSO_LAB`). No
further action planned until a real need arises. (Passkey/WebAuthn as a second factor is Phase 3/6
scope, not here — see ADR-012.)

- [ ] External identity providers
- [ ] Fully passwordless (passkey-only) login
- [ ] LDAP if needed
- [ ] SAML if needed
- [ ] SCIM/user provisioning if needed
- [ ] API auth and service accounts
- [ ] Fine-grained roles/groups
- [ ] App-specific policies
- [ ] Automated backup scheduling (beyond manual `scripts/backup-sso.sh`)
- [ ] Fully portable local-only SSO lab mode, decoupled from any NAS-specific assumptions
