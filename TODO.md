# TODO

Status legend: `[ ]` not done, `[x]` done. See [`docs/phase-plan.md`](docs/phase-plan.md) for the
full description of each phase.

## Current Priorities (updated 2026-07-22)

Top of the queue right now, ahead of the older unconfirmed Phase 3/6 items below. This
branding/customization work is merged into `main` (PR #2).

- [x] **Deploy the login-page-only theme toggle template** (ADR-014) — `authentik-custom-templates/if/flow.html`
      was copied to the live NAS (`/volume1/docker/sso-systemsnotsilos-com/data/sso/authentik/custom-templates/if/flow.html`)
      via SSH (synology-site-deployer credentials), and `sso-authentik-server`/`sso-authentik-worker`
      were restarted. Verified live: both containers report `(healthy)`, the login page returns
      HTTP 200, and the served HTML contains `sns-theme-toggle` — the template override is
      confirmed active. **Still needs a real browser click-through** of all three states
      (system/light/dark) and confirmation the post-login interface's theme is unaffected — that
      isolation is the whole point of this design and hasn't been eyeballed yet, only source- and
      curl-verified.
- [x] **Deploy the corrected footer CSS** (`docs/authentik-manual.md`, "Footer Links") — done
      2026-07-22 via `ak shell` over SSH (the one Brand record, `Brand.objects.get(default=True)`,
      `branding_custom_css` updated in place; no admin-UI session available, so this went through
      the Django ORM directly instead). Verified live by re-fetching the login page: the old
      spec-invalid `::part(footer) li:...` rule is gone, the corrected `ak-brand-links` selectors
      are present, and the theme-toggle CSS is present too (`grep` confirmed, not a browser
      screenshot). "Powered by authentik" is still in the DOM (expected — the field can't be
      removed at the data layer) but is now `display: none`, which also removes it from the
      accessibility tree, not just visually.
- [x] **Real browser check, footer + logo** — done 2026-07-22 via a real Chrome browser
      (Playwright, screenshots taken). Confirmed live: "Powered by authentik" is visually hidden,
      the veloso.dev dot signature renders as a row of dots in the footer, and — this is how the
      logo/title overlap bug was actually found and confirmed (see below) — a real screenshot
      caught a bug that `curl`/source review had missed entirely.
- [x] **Logo/title overlap — was real, not a hover artifact** — fixed and verified live, see
      ADR-015 in `docs/decision-log.md`. Root cause: `max-height` on the logo's wrapper div doesn't
      constrain the `<img>` inside it; fixed with `transform: scale(0.68)` on the wrapper instead
      (shrinks the whole rendered subtree, not croppable-selector-dependent). Two live iterations
      were needed — the first (`scale(0.46)` + `overflow: hidden`) visually cropped the logo per
      operator feedback; the corrected version shows the full logo, no overlap, no cropping.
- [x] **Favicon** — done 2026-07-22, see ADR-016. A dedicated lightweight `.ico` (7.9KB,
      16/32/48px) generated from the existing logo, not the full-size asset reused directly.
      Verified live: `<link rel="icon">` points at it, serves `200` with the correct
      `image/vnd.microsoft.icon` content-type.
- [ ] **Theme toggle click-through** — the template is deployed and confirmed present in the served
      HTML, but nobody has actually clicked it yet to confirm all three states (system/light/dark)
      render correctly and that the post-login interface's own theme is unaffected — that isolation
      is the whole point of this design and still hasn't been exercised, only inspected.
- [x] **Contact Support form — code written and pushed** (ADR-017) — `contact-relay/` (Flask,
      this repo's first bespoke service), `docker-compose.yml` service definition,
      `.github/workflows/contact-relay-publish.yml` (GHCR CI), `.env.example` vars, and the
      form/JS in `authentik-custom-templates/if/flow.html` are all merged to `main`. CI confirmed
      green — `ghcr.io/s2925534/nas-sso-gateway-contact-relay:latest` built and pushed successfully.
- [x] **`contact-relay` deployed to the NAS** — done 2026-07-22 via SSH (synology-site-deployer
      credentials): live `docker-compose.yml` synced from this repo (diffed empty after upload —
      confirms nothing else had drifted), `.env` updated with `CONTACT_ADMIN_EMAIL` (
      `admin@systemsnotsilos.com`) and `CONTACT_ALLOWED_ORIGIN` (`https://sso.systemsnotsilos.com`),
      container started and confirmed `(healthy)`, `/health` returns `200` on `127.0.0.1:9001` on
      the NAS itself.
- [x] **SMTP fully working end-to-end, correct sender identity** (2026-07-25, ADR-018) —
      `CONTACT_EMAIL__*` set on the live `.env`: auth as `pedro@veloso.dev` (the real Google
      Workspace account — aliases can't authenticate directly), `CONTACT_EMAIL__FROM=
      admin@systemsnotsilos.com`. Initial test looked like it worked (`{"ok":true}`) but the
      operator caught that the delivered message actually showed `pedro@veloso.dev` as sender —
      Gmail silently rewrites an unregistered alias instead of rejecting it. Root cause: the alias
      wasn't yet added under that Gmail account's **Settings → Accounts and Import → "Send mail
      as"**. Operator added and verified it there; re-tested via IMAP (checking the real
      delivered/sent message, not just the HTTP response) against both a direct SMTP test and the
      actual `contact-relay` `POST /send` endpoint — both now show the correct `From:
      admin@systemsnotsilos.com`, correct `Reply-To`, correct body. This account-vs-alias pattern
      and its "verify via IMAP, never trust a successful SMTP transaction alone" testing method are
      now captured as a reusable skill (`~/.claude/skills/ecosystem-mail-relay/`).
  - [ ] Route a reverse-proxy/tunnel path at `CONTACT_RELAY_PORT` (`9001`) so it's reachable from
        outside the NAS — outside this repo's scope, same as every other app in this ecosystem
        (ADR-003); right now the service only answers on `127.0.0.1` on the NAS itself
  - [ ] Update `authentik-custom-templates/if/flow.html`'s `RELAY_ENDPOINT` constant to match
        whatever path/host you actually routed, then redeploy the template
  - [ ] Only then: update the live Tenant's `footer_links` ("Contact Support (coming soon)" →
        "Contact Support", add `href`) and push the contact-form CSS to the Brand's Custom CSS field
  - [ ] Test end-to-end: submit the form, confirm the email arrives, confirm reply-to works,
        confirm rate-limiting kicks in on rapid resubmission
- Everything in Phase 3/6 below that was already queued before this session remains queued — this
  branding work doesn't supersede it, just sits ahead of it.

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
- [ ] Favicon branded with our logo, not authentik's default (guide ready: §9 "Branding" — Logo/Favicon
      currently left unset per ADR-013 until a real asset is supplied; see `docs/authentik-manual.md`
      "Branding (Login Page / 'Systems Not Silos')")

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

**Incident (2026-07-14/15, ongoing/unresolved as of this session — read below before trusting the
"healthy" status elsewhere in this doc):** the live instance was unreachable (502 via the tunnel)
when checked. Diagnosed via `../synology-site-deployer`'s read-only `logs`/`ps` commands (no Docker
access from this sandbox otherwise): the NAS's Docker daemon went unreachable around `14:13:52Z` on
2026-07-14 (Watchtower's own log shows "Cannot connect to the Docker daemon" followed by a fatal
panic in its own cron job), taking down `sso-authentik-server`, `sso-postgresql`, `sso-redis`, the
Supabase stack, and Watchtower itself — `cloudflared` stayed up the whole time and correctly 502'd
since it couldn't reach any of those origins. Everything came back on its own via container restart
policies around `20:42-20:46Z` (~6.5 hours later) — authentik's own worker log shows a 318-second
startup ("`took_s`": 318.5) before it was internally healthy again. Verified recovered at that point
(`sso.systemsnotsilos.com` → 302, `publisher.veloso.dev` → 307, OIDC discovery → 200).

**Then it went down again, worse, ~30 minutes later (2026-07-14T21:12Z):** `synology-site
check-nas` (SSH to the NAS itself still fully reachable, so the NAS/OS is up) showed the running
container count drop from 37 to 1, and it stayed stuck at 1 for 2+ minutes of polling rather than
climbing back like the first cycle did. `synology-site ps` showed this is **host-wide, not
SSO-specific** — every project's containers exited around the same time (`au-address-*`, `zqx-*`,
`uptime-kuma`, `resilinked-*`, plus this stack), with exit codes 137 (SIGKILL — consistent with
OOM-kill or a forced daemon restart), 143 (SIGTERM), and 0. Reads as the NAS's Docker/Container
Manager service itself being unstable (resource exhaustion or a DSM-level restart loop), not
anything wrong with this repo's stack or anything done in this session — only read-only
`check-nas`/`ps`/`logs` were ever run against the NAS; no `deploy`/`restart`/`stop` command was
issued. There is a live `uptime-kuma` container on this NAS — worth checking its dashboard/alert
history once things stabilize, since an outage this long should have triggered something.

This is beyond what's diagnosable or fixable from a sandboxed session with no DSM/host-level access
(no disk/memory visibility, no ability to restart the Container Manager package itself). Left as-is
rather than polling further — needs the operator's own attention at the NAS (DSM system log,
Container Manager status, storage/memory usage) next time they're at it.

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
