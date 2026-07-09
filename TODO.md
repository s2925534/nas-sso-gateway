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

## Phase 2: Deployer Integration Readiness

- [ ] Document how `../synology-site-deployer` should consume this repo
- [ ] Add deployer metadata if useful
- [ ] Confirm deployer-managed persistent path expectation
- [ ] Confirm deployer-managed Cloudflare/domain expectation
- [ ] Confirm deployer exposes only authentik web endpoint
- [ ] Avoid direct Cloudflare implementation in this repo

## Phase 3: First SSO Configuration Guide

- [ ] First admin account setup
- [ ] First normal user setup
- [ ] MFA recommendation applied
- [ ] First OIDC provider/client example
- [ ] First proxy provider example
- [ ] App portal example
- [ ] Group and role examples

## Phase 4: Protect First NAS Web App

- [ ] Select one simple internal app
- [ ] Protect it through OIDC if native support exists
- [ ] Otherwise protect it through reverse-proxy forward-auth
- [ ] Document rollback and emergency bypass

## Phase 5: Multi-App SSO Rollout

- [ ] Standard app onboarding checklist
- [ ] Per-app client/provider naming convention
- [ ] Per-app group access policy
- [ ] Per-app redirect URL documentation
- [ ] Per-app logout behavior
- [ ] App portal organization

## Phase 6: Security Hardening

- [ ] MFA enforcement
- [ ] Admin account separation
- [ ] Backup and restore test
- [ ] Emergency access plan
- [ ] Audit logging
- [ ] Session lifetime review
- [ ] Password policy review
- [ ] Recovery codes

## Phase 7: Future Advanced Identity

- [ ] External identity providers
- [ ] Passkeys/WebAuthn
- [ ] LDAP if needed
- [ ] SAML if needed
- [ ] SCIM/user provisioning if needed
- [ ] API auth and service accounts
- [ ] Fine-grained roles/groups
- [ ] App-specific policies
