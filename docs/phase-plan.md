# Phase Plan

This project is built in phases so the scope stays small and reviewable at each step. Checkbox
status for each item lives in [`TODO.md`](../TODO.md) — this document explains what each phase
means and why it's scoped the way it is.

## Phase 0 — Planning and Documentation Foundation

Goal: organise every requirement into Markdown before any code exists. Produces the README, this
phase plan, the decision log, security doc, authentik manual, deployer integration notes,
reverse-proxy/domain notes, app integration patterns, OIDC/proxy-auth integration references,
troubleshooting guide, future flags, and `TODO.md` itself. Validated, committed, and pushed before
Phase 1 starts.

## Phase 1 — Authentik MVP Foundation

Goal: the smallest possible working local deployment. `.env.example`, `.gitignore`, a Docker
Compose file for authentik server + worker + PostgreSQL + Redis, and four scripts
(`create-folders.sh`, `bootstrap-sso.sh`, `health-check.sh`, `backup-sso.sh`). Runs local-only or
LAN-only; no public exposure. Validated (shell syntax, compose syntax, no secrets staged) before
commit.

## Phase 2 — External Deployment Integration Readiness

Goal: make this repo consumable by *any* external deployment/reverse-proxy tooling — or none at
all — without this repo reaching into that tooling's responsibilities. Document what such tooling
needs to know (expected port, expected hostname, expected persistent-path contract) and confirm
Cloudflare/DNS is always owned externally, end to end. No Cloudflare code lands in this repo. The
maintainer's own companion project, `../synology-site-deployer`, is documented as one worked
example, not a requirement.

## Phase 3 — First SSO Configuration Guide

Goal: document (and, where scripted, verify) the first real walk-through — creating the admin
account, creating a normal day-to-day user, enabling MFA, creating one example OIDC provider/client,
one example proxy provider, confirming the app portal view, and example groups/roles.

## Phase 4 — Protect First NAS Web App

Goal: pick exactly one simple internal app and put it behind SSO — via native OIDC if the app
supports it, otherwise via reverse-proxy forward-auth. Document rollback and an emergency bypass
for that specific app before enabling enforcement.

## Phase 5 — Multi-App SSO Rollout

Goal: turn the Phase 4 experience into a repeatable checklist — standard onboarding steps, a
naming convention for per-app clients/providers, per-app group access policy, per-app redirect URL
documentation, per-app logout behavior, and app portal organisation.

## Phase 6 — Security Hardening

Goal: move from "works" to "production-safe" — MFA enforcement, admin/day-to-day account
separation, a tested backup and restore cycle, a written emergency access plan, audit log review,
session lifetime review, password policy review, and recovery codes.

## Phase 7 — Future Advanced Identity

Goal: optional, later capabilities — external identity providers, passkeys/WebAuthn, LDAP, SAML,
SCIM/user provisioning, API auth and service accounts, fine-grained roles/groups, and
app-specific policies. Not required for the MVP; tracked as flags in
[`docs/future-flags.md`](future-flags.md).

## Sequencing Rule

Each phase's items are only marked done in `TODO.md` after they are implemented (where
applicable), validated, committed, and pushed. Phases are not started early — in particular, no
Docker Compose or shell scripts are written until Phase 0 is fully committed and pushed.
