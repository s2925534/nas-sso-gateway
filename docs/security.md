# Security

This document is the security contract for the project. Read it before any deployment beyond your
own laptop.

## Secrets Handling

- Never commit real secrets. `.env.example` contains placeholders only — real values live in a
  local, gitignored `.env`.
- Generate strong values for `AUTHENTIK_SECRET_KEY`, `AUTHENTIK_POSTGRES_PASSWORD`,
  `POSTGRES_PASSWORD`, and `AUTHENTIK_BOOTSTRAP_PASSWORD`. A safe generator:

  ```bash
  openssl rand -base64 48
  ```

- If a secret is ever committed by mistake, treat it as compromised: rotate it in authentik/
  PostgreSQL and force-push history rewrite only after coordinating — do not assume `git rm` alone
  is sufficient.

## `.env` Handling

- `.env` must stay out of Git (`.gitignore` enforces this from Phase 1 onward).
- `.env.example` is the only environment file tracked in Git, and must only ever contain safe
  placeholder values.
- Treat `.env` like a credential: file permissions restricted to your user, never pasted into
  chat/issue trackers, never synced to a public cloud drive unencrypted.

## Admin Account Safety

- The authentik admin (`akadmin` / bootstrap admin) account should be used for administration
  only — not as your daily login for protected apps.
- Create a separate normal user account (Phase 3) for day-to-day use, and grant it only the group
  memberships it needs.
- Store admin credentials and recovery codes in a password manager outside of this repository.

## MFA Recommendation

- Login scope is intentionally narrow: username/password and passkey (WebAuthn) only.
  TOTP-authenticator-app and SMS-based MFA are deferred until asked for again — don't build those
  out.
- Enable passkey MFA for the admin account before any public exposure, and for all users before
  relying on the system in production (Phase 3/6 — active scope, see ADR-012 in
  [`docs/decision-log.md`](decision-log.md)); blanket enforcement via `ENABLE_MFA_ENFORCEMENT` (see
  [`docs/future-flags.md`](future-flags.md)) is a separate, later step.
- MFA is not required to complete the local MVP, but treat it as a hard requirement before
  `PUBLIC_EXPOSURE=true`.

## Public Exposure Rules

- This repo does not implement public exposure. Public exposure of your `SSO_DOMAIN` happens only
  through whatever external tooling you choose (Cloudflare Tunnel, Traefik, a deployer script such
  as `../synology-site-deployer`, or similar), and only after you deliberately flip
  `DEPLOY_MODE`/`PUBLIC_EXPOSURE` and configure that tooling.
- Only the authentik web endpoint is ever exposed publicly. PostgreSQL, Redis, Synology DSM, and
  SSH must never be reachable through whatever tooling handles your public routing.

## Trusted Header Warning

- Pattern 3 (trusted-header SSO, see
  [`docs/app-integration-patterns.md`](app-integration-patterns.md)) is only safe when the backend
  app is *unreachable* except through the trusted reverse proxy. If the app's container/port is
  reachable directly (same Docker network without isolation, an exposed host port, etc.), a header
  can be spoofed and the app will trust a forged identity.
- Prefer native OIDC or forward-auth session validation over trusted headers unless you have
  verified the network path is fully closed off.

## Database / Redis Exposure Warning

- Never publish PostgreSQL or Redis ports to the host (`ports:` in Compose) or through the
  reverse proxy. They should only be reachable on the internal Docker network used by authentik's
  own containers.

## Emergency Bypass

- Before enabling SSO enforcement on any app, document how to disable it again (remove the
  forward-auth rule, or turn off the OIDC requirement) without needing authentik to be reachable.
- Keep at least one break-glass path (e.g. a local-network-only admin URL, or a non-SSO fallback
  account) for critical apps until backup/restore has been tested. Tracked as
  `ENABLE_ADMIN_BREAK_GLASS` in [`docs/future-flags.md`](future-flags.md).

## Backup and Restore

- Back up PostgreSQL data and authentik's media/config exports regularly — see
  `scripts/backup-sso.sh` and [`scripts/restore-notes.md`](../scripts/restore-notes.md).
- Test the restore path before relying on this system in production. An untested backup is not a
  backup.

## Account Recovery

- Losing access to the admin account (and having no recovery codes) can lock you out of managing
  every app behind SSO. Store recovery codes and the admin credential outside of Git, in a
  password manager, before going beyond local testing.

## Session Risks

- Review authentik's session lifetime settings (Phase 6) — long-lived sessions reduce login
  friction but increase the exposure window if a device is lost or compromised.
- Log out of shared or non-personal devices explicitly; don't rely on session expiry alone.

## Reverse Proxy Trust Boundary

- The reverse proxy (whatever external tooling manages it) is the trust boundary for forward-auth
  and trusted-header patterns. Everything on the other side of that boundary must assume requests
  are already authenticated — which means nothing on that side may be reachable by any other path.
- Confirm required headers (e.g. `X-Forwarded-*`, `Remote-User`) are preserved end-to-end by the
  reverse proxy; see [`docs/reverse-proxy-domain.md`](reverse-proxy-domain.md) and
  [`docs/proxy-auth-integration.md`](proxy-auth-integration.md).
