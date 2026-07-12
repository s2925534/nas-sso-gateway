# Authentik Manual (This Project's Usage)

This is not a full authentik manual — it covers exactly what this project needs. For anything
deeper, use the [official authentik docs](https://docs.goauthentik.io/).

## What authentik Is Used For Here

- Central login for every protected NAS app.
- OIDC/OAuth2 provider for apps you build yourself.
- Proxy provider / forward-auth outpost for apps without native SSO.
- App portal — a single page listing every app you can launch once logged in.

## First-Run Setup

1. Copy `.env.example` to `.env` and fill in real secrets (see
   [`docs/security.md`](security.md) for generation commands).
2. Run `scripts/bootstrap-sso.sh` (Phase 1) or `docker compose up -d` directly.
3. Wait for the `authentik-server` and `authentik-worker` containers to report healthy —
   authentik's first boot runs database migrations and can take a minute or two.
4. Visit `http://<SSO_BIND_HOST or localhost>:<SSO_HTTP_PORT>/if/flow/initial-setup/` to set the
   initial admin password (authentik's own first-run flow), or log in with
   `AUTHENTIK_BOOTSTRAP_EMAIL` / `AUTHENTIK_BOOTSTRAP_PASSWORD` if bootstrap env vars were set.

## Admin Account Setup

- Treat the bootstrap admin account as break-glass/administration only.
- Immediately change the bootstrap password if it was set via `.env`, then remove or rotate
  `AUTHENTIK_BOOTSTRAP_PASSWORD` from your local `.env` once a proper admin login is confirmed.
- Enable MFA on the admin account before doing anything beyond local testing.

## Creating Normal Users

- **Directory → Users → Create.** Give the user a normal (non-admin) role.
- Use normal users for day-to-day login to protected apps — never the admin account.

## Creating Groups

- **Directory → Groups → Create.** Groups are the unit of access control per app (Phase 3/5).
- Example convention: one group per app or app-tier, e.g. `app-tools-users`, `app-portainer-admins`.

## Creating Applications

- **Applications → Applications → Create.** An "Application" in authentik is the user-facing tile
  in the app portal; it wraps a Provider (OIDC or Proxy) that does the actual auth work.

## Creating OIDC Providers

- **Applications → Providers → Create → OAuth2/OpenID Provider.**
- Set the redirect URI(s) to match the app's callback path (see
  [`docs/oidc-integration.md`](oidc-integration.md)).
- Note the generated Client ID/Secret and issuer URL for the app's own configuration.

## Creating Proxy Providers

- **Applications → Providers → Create → Proxy Provider.**
- Choose **Forward auth (single application)** for one app behind its own reverse-proxy rule, or
  **Forward auth (domain level)** for multiple subdomains sharing one outpost.
- Bind the provider to an **Outpost** (Applications → Outposts) so the reverse proxy has something
  to call. See [`docs/proxy-auth-integration.md`](proxy-auth-integration.md).

## App Portal Notes

- Once a user has access (via group membership) to an application, it appears automatically on
  their authentik landing page after login — no extra portal configuration needed.

## MFA Notes

- **Directory → Users → (user) → MFA Authenticators**, or let users self-enroll from their own
  account page.
- authentik supports TOTP and WebAuthn/passkeys; policies can require MFA per-flow or per-group
  (Phase 6).

## Backup Notes

- authentik state lives in PostgreSQL (users, apps, providers, policies) and in
  `${SSO_BASE_PATH}/authentik/media` (uploaded assets) plus
  `${SSO_BASE_PATH}/authentik/custom-templates` (if used).
- `scripts/backup-sso.sh` captures these; see [`scripts/restore-notes.md`](../scripts/restore-notes.md)
  for the restore procedure and its caveats.

## Upgrade Notes

- The authentik image tag is pinned to an exact version (`AUTHENTIK_TAG` in `.env`/`docker-compose.yml`)
  rather than tracking a `latest` floating tag — see ADR-010 in
  [`docs/decision-log.md`](decision-log.md) and the upgrade procedure in
  [`docs/security-hardening.md`](security-hardening.md) ("Image Upgrade Procedure").
- Read authentik's release notes before upgrading across minor versions — some releases include
  required migration steps.
- Always back up before upgrading.
