# Multi-App SSO Rollout (Phase 5)

Once one app is protected end-to-end (Phase 4), use this checklist to onboard every app after it
consistently. This document defines the convention; it does not configure any specific app.

## Standard App Onboarding Checklist

For each new app:

1. Decide the pattern: native OIDC (Pattern 1) if the app supports it, otherwise reverse-proxy
   forward-auth (Pattern 2) — see [`docs/app-integration-patterns.md`](app-integration-patterns.md).
2. Create the Provider (OIDC or Proxy) using the naming convention below.
3. Create the Application, and restrict access to the correct group(s) — see per-app group policy
   below.
4. Document the redirect URI(s) (OIDC) or the protected hostname (forward-auth) — see below.
5. Confirm logout behavior end-to-end (see below).
6. Test as a non-admin user before considering the app "onboarded."
7. Record the rollback step (how to disable enforcement for this app) before relying on it.
8. Confirm the app appears correctly in the app portal for the groups that should see it, and does
   not appear for groups that shouldn't.

## Per-App Client/Provider Naming Convention

Use the app's own subdomain label as the stable identifier:

| Object | Convention | Example (`tools.veloso.dev`) |
|---|---|---|
| Provider name | `provider-<app-label>` | `provider-tools` |
| Application name | `<app-label>` | `tools` |
| Application slug | `<app-label>` | `tools` |
| Group | `app-<app-label>-users` (add `-admins` for elevated access if needed) | `app-tools-users` |

This keeps authentik's object list sorted and searchable by app, and keeps a 1:1 mapping between a
provider and the app it protects — don't reuse one OIDC provider across multiple unrelated apps.

## Per-App Group Access Policy

- Default to one `app-<label>-users` group per app; add the day-to-day user account(s) that should
  reach it.
- Only create `app-<label>-admins` if the app itself has an internal admin role that should map to
  a different authentik group (e.g. different claims/headers).
- Do not reuse a single broad "everyone" group for all apps — that removes the ability to revoke
  one app's access without affecting others.
- Review group membership when Phase 6's audit-logging review happens.

## Per-App Redirect URL Documentation

For each OIDC app, record (in that app's own repo/deployment docs, not this one):

- Issuer URL used
- Exact redirect URI(s) registered in authentik
- Scopes requested
- Where the Client ID/Secret are stored (never in this repo)

For each forward-auth app, record:

- The outpost/provider name protecting it
- The exact hostname(s) covered
- Whether it's single-application or domain-level forward-auth

## Per-App Logout Behavior

- OIDC apps: confirm whether the app calls authentik's end-session endpoint on logout, or only
  clears its own local session (leaving the authentik SSO session active — the user would not be
  prompted to log in again on the next app). Decide per-app whether that's acceptable.
- Forward-auth apps: logging out of authentik's own session ends access to all forward-auth-
  protected apps sharing that outpost; the app itself has no separate logout unless it has its own
  local session on top.
- Document the expected behavior per app so it isn't a surprise during Phase 4/5 testing.

## App Portal Organization

- Rely on group-based visibility (Step 8 above) rather than manually reordering tiles for
  visibility control.
- Keep application names in the portal human-readable (e.g. "Tools" not `provider-tools`) even
  though the underlying Provider/Application slugs follow the naming convention above.
