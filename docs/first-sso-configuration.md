# First SSO Configuration Guide (Phase 3)

A concrete, ordered walkthrough for the first real configuration pass, once the Phase 1 stack is
running (`scripts/bootstrap-sso.sh` or `docker compose up -d`). This is a hands-on companion to
[`docs/authentik-manual.md`](authentik-manual.md) — that document explains *what* each screen
does; this one gives you a specific first path through them with one worked example throughout.

This guide must be run against a live authentik instance — it cannot be completed or verified
from this repo's source alone. Work through it locally/LAN-only before any public exposure.

## 0. Prerequisites

- `docker compose ps` shows `sso-authentik-server`, `sso-authentik-worker`, `sso-postgresql`,
  `sso-redis` all running.
- `scripts/health-check.sh` reports all checks passing.
- You can reach the web UI at `http://<SSO_BIND_HOST or localhost>:<SSO_HTTP_PORT>`.

If any of the above isn't true yet, see [`docs/troubleshooting.md`](troubleshooting.md) —
"Cannot Reach Authentik", "Database Not Starting", "Redis Not Starting".

## 1. First Admin Account Setup

1. Visit `/if/flow/initial-setup/` on your instance (authentik's own first-run flow) if this is a
   brand-new database, and set the initial admin password there.
2. If you instead pre-seeded `AUTHENTIK_BOOTSTRAP_EMAIL` / `AUTHENTIK_BOOTSTRAP_PASSWORD` in
   `.env`, log in with those values directly.
3. Immediately: enable MFA on this account (Step 3 below) and treat it as an **administration-only**
   account from this point on — never your daily login for protected apps.
4. Remove or rotate `AUTHENTIK_BOOTSTRAP_PASSWORD` from your local `.env` once you've confirmed a
   working admin login through the UI.

If you get locked out before rotating it, see [`docs/troubleshooting.md`](troubleshooting.md) —
"Lost Admin Password".

## 2. First Normal User Setup

1. **Directory → Users → Create.**
   - Username: your everyday handle (not `admin`/`akadmin`).
   - Email: your real address.
   - Do **not** grant this user the `akadmin` superuser role.
2. Set an initial password, or trigger authentik's "send recovery link" flow so the user sets
   their own.
3. This is the account you use for day-to-day app logins going forward (see
   [`docs/security.md`](security.md) — admin/day-to-day separation).

## 3. Enable MFA

1. Log in as the account you want to protect (admin first, then your normal user).
2. **User icon (top right) → your account → MFA Authenticators → Enroll.**
3. Choose TOTP (any authenticator app) or WebAuthn/passkey if your device supports it.
4. Save the recovery codes authentik generates, outside of this repo, in a password manager.
5. Do this for the admin account before any public exposure — see `ENABLE_MFA_ENFORCEMENT` in
   [`docs/future-flags.md`](future-flags.md) for later blanket enforcement.

Locked out after enrolling? See [`docs/troubleshooting.md`](troubleshooting.md) — "MFA Lockout".

## 4. Groups and Roles Example

1. **Directory → Groups → Create.** Example convention (see also
   [`docs/multi-app-rollout.md`](multi-app-rollout.md)):
   - `admins` — superuser-equivalent, admin account(s) only.
   - `app-example-users` — everyday access to one example app.
2. Add your normal user (from Step 2) to `app-example-users`.
3. Leave the admin account out of `app-example-users` — admin access to authentik itself does not
   need to imply access to every downstream app.

## 5. First OIDC Provider/Client Example

Worked example using a placeholder app `example-oidc-app` (substitute a real app when you have
one — see Phase 4).

1. **Applications → Providers → Create → OAuth2/OpenID Provider.**
   - Name: `provider-example-oidc-app`
   - Redirect URI: `https://example-oidc-app.example.com/oauth/callback` (or
     `http://localhost:<port>/oauth/callback` for local testing)
   - Scopes: `openid profile email`
2. **Applications → Applications → Create.**
   - Name: `example-oidc-app`
   - Provider: `provider-example-oidc-app`
   - Access restricted to group: `app-example-users`
3. Copy the Client ID/Secret and issuer URL into the app's own config — see
   [`docs/oidc-integration.md`](oidc-integration.md) and
   [`examples/app-integrations/generic-oidc-client.md`](../examples/app-integrations/generic-oidc-client.md).
4. Confirm your normal user can see and launch `example-oidc-app` from the authentik landing page
   (Step 7); confirm the admin account (not in `app-example-users`) cannot.

Redirect loop or client mismatch on first login? See [`docs/troubleshooting.md`](troubleshooting.md)
— "Wrong Redirect URI", "OIDC Client Mismatch".

## 6. First Proxy Provider Example

Worked example using a placeholder app `example-forward-auth-app`.

1. **Applications → Outposts → Create** (if none exists yet) — an embedded outpost is created by
   default on first authentik boot; you can reuse it for a single-host MVP.
2. **Applications → Providers → Create → Proxy Provider.**
   - Mode: **Forward auth (single application)**
   - Name: `provider-example-forward-auth-app`
   - External host: `https://example-forward-auth-app.example.com`
3. **Applications → Applications → Create.**
   - Name: `example-forward-auth-app`
   - Provider: `provider-example-forward-auth-app`
   - Access restricted to group: `app-example-users`
4. Wire the reverse proxy (deployer-managed) per
   [`docs/proxy-auth-integration.md`](proxy-auth-integration.md) and
   [`examples/app-integrations/generic-forward-auth.md`](../examples/app-integrations/generic-forward-auth.md).

Headers not passing through, or the app not seeing the authenticated user? See
[`docs/troubleshooting.md`](troubleshooting.md) — "Reverse Proxy Headers Wrong", "App Not
Respecting Headers".

## 7. App Portal Example

1. Log in as your normal user (not admin) at the authentik root URL.
2. Confirm the landing page lists exactly the applications `app-example-users` has access to —
   this *is* the app portal (Pattern 4); no separate configuration is needed beyond group grants.
3. Confirm apps outside that group's access do **not** appear.

Stuck in a login loop, or the wrong external URL shows up? See
[`docs/troubleshooting.md`](troubleshooting.md) — "Login Loop", "Incorrect External URL".

## What This Guide Does Not Do

- It does not protect a real production app — that's Phase 4, and requires you to pick a specific
  app first (see [`TODO.md`](../TODO.md), Phase 4).
- It does not enable MFA enforcement or session-lifetime hardening — that's Phase 6
  ([`docs/security-hardening.md`](security-hardening.md)).
