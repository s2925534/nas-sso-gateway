# App Integration Patterns

Five patterns for connecting an app to this SSO gateway. Pick per-app based on what the app
supports and how much you trust the network path in front of it. This document only describes the
patterns and points at future example apps — it does not configure them in the MVP.

## Pattern 1: Native OIDC App Integration

**Use when:** the app supports OAuth2/OIDC login natively.

**Flow:** the app redirects the user to authentik → authentik authenticates the user → the app
receives identity claims (ID token / userinfo) directly from authentik.

**Best for:** modern apps you build yourself, where you control the auth stack.

**Reference:** [`docs/oidc-integration.md`](oidc-integration.md),
[`examples/app-integrations/generic-oidc-client.md`](../examples/app-integrations/generic-oidc-client.md).

## Pattern 2: Reverse Proxy Forward-Auth

**Use when:** the app does not support SSO natively.

**Flow:** the reverse proxy asks authentik's outpost "is this request authenticated?" for every
request. If not authenticated, the user is redirected to authentik's login. If authenticated, the
request is allowed through to the app unchanged (or with identity headers attached, see Pattern 3).

**Best for:** simple NAS web apps or admin tools with only a built-in login form.

**Reference:** [`docs/proxy-auth-integration.md`](proxy-auth-integration.md),
[`examples/app-integrations/generic-forward-auth.md`](../examples/app-integrations/generic-forward-auth.md).

## Pattern 3: Trusted Header SSO

**Use carefully:** when the reverse proxy passes authenticated username/email/groups to the
backend app as headers (e.g. `X-Authentik-Username`, `X-Authentik-Email`, `X-Authentik-Groups`),
and the app trusts those headers instead of doing its own session validation.

**Only safe when** the backend app is not reachable except through the trusted reverse proxy — if
the app's container/port can be reached by any other path, headers can be forged and the app will
trust a spoofed identity. See the trusted-header warning in [`docs/security.md`](security.md).

## Pattern 4: App Portal

**Use when:** you want a single page to see and launch every app you have access to after logging
in once.

**Flow:** authentik's own landing page lists every Application the logged-in user's groups grant
access to. No extra configuration beyond creating the Application/Provider and group grants.

## Pattern 5: Future API Auth

**Use when:** a custom API needs to authorize requests from another service or script, not just a
browser session.

**Flow:** validate OIDC-issued JWTs (access tokens) directly in the API using authentik's issuer/
JWKS endpoint — no session or cookie involved. Suited to service-to-service and automation use
cases. Tracked under `ENABLE_API_AUTH_GATEWAY` / `ENABLE_SERVICE_ACCOUNTS` in
[`docs/future-flags.md`](future-flags.md).

## Future App Examples (Documentation Only — Not Configured in MVP)

| App | Likely pattern |
|---|---|
| `ai.veloso.dev` | OIDC (Pattern 1) |
| `tools.veloso.dev` | Forward-auth (Pattern 2) |
| `blog-admin.veloso.dev` | OIDC (Pattern 1) or forward-auth |
| `research.veloso.dev` | OIDC (Pattern 1) |
| `apps.veloso.dev` | App portal umbrella (Pattern 4) over several apps |
| Portainer / other container tools | Forward-auth (Pattern 2) |
| Any future NAS web app | Whichever of Pattern 1/2/3 fits its native support |

These are documented examples for planning purposes only; none are configured as part of this
MVP. Actual onboarding follows the Phase 4/5 checklist in [`docs/phase-plan.md`](phase-plan.md).
