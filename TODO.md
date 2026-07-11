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

- [ ] First admin account setup (guide ready: `docs/first-sso-configuration.md` §1)
- [ ] First normal user setup (guide ready: §2)
- [ ] MFA recommendation applied (guide ready: §3)
- [ ] First OIDC provider/client example (guide ready: §5)
- [ ] First proxy provider example (guide ready: §6)
- [ ] App portal example (guide ready: §7)
- [ ] Group and role examples (guide ready: §4)

## Phase 4: Protect First NAS Web App

Blocked on a decision only you can make — which real NAS app to protect first. Nothing here is
implemented against a real app (by design; see README "What This Project Does Not Do"). When
you've picked one, `docs/first-sso-configuration.md` §5/§6 and
`examples/app-integrations/` give you the concrete steps to follow.

- [ ] Select one simple internal app
- [ ] Protect it through OIDC if native support exists
- [ ] Otherwise protect it through reverse-proxy forward-auth
- [ ] Document rollback and emergency bypass

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
(`ENABLE_EXTERNAL_IDENTITY_PROVIDERS`, `ENABLE_WEBAUTHN_PASSKEYS`, `ENABLE_LDAP_SUPPORT`,
`ENABLE_SAML_SUPPORT`, `ENABLE_API_AUTH_GATEWAY`, `ENABLE_SERVICE_ACCOUNTS`,
`ENABLE_GROUP_BASED_ACCESS`, `ENABLE_BACKUP_AUTOMATION`, `ENABLE_PORTABLE_LOCAL_SSO_LAB`). No
further action planned until a real need arises.

- [ ] External identity providers
- [ ] Passkeys/WebAuthn
- [ ] LDAP if needed
- [ ] SAML if needed
- [ ] SCIM/user provisioning if needed
- [ ] API auth and service accounts
- [ ] Fine-grained roles/groups
- [ ] App-specific policies
- [ ] Automated backup scheduling (beyond manual `scripts/backup-sso.sh`)
- [ ] Fully portable local-only SSO lab mode, decoupled from any NAS-specific assumptions
