# Proxy Auth (Forward-Auth) Integration Reference

## What Forward-Auth / Proxy Auth Is

A pattern where the reverse proxy checks with authentik on every request ("is this session
authenticated, and does it have access to this app?") before forwarding the request to the
backend app. authentik's **outpost** does this check; the reverse proxy just needs to call it and
respect the answer (allow, or redirect to login).

## When to Use It

Use forward-auth (Pattern 2 in
[`docs/app-integration-patterns.md`](app-integration-patterns.md)) when the app has no native
OIDC/OAuth2 support — most NAS admin UIs, self-hosted tools, and legacy web apps.

## Why It's Useful for Apps Without Native SSO

It adds SSO in front of an app with zero code changes to that app — the reverse proxy and
authentik outpost do all the work. This is the only realistic option for closed-source or
minimal-config NAS tools.

## Trusted Header Warning

Some setups pass identity as headers (`X-Authentik-Username`, `X-Authentik-Email`,
`X-Authentik-Groups`) to the backend app for it to read directly (Pattern 3). This is only safe if
the backend app is *unreachable except through the trusted reverse proxy* — otherwise a header can
be forged by anyone who can reach the app directly. Prefer relying on the forward-auth
allow/deny decision itself (the proxy simply doesn't forward unauthenticated requests) over
header-based app-level trust, unless you've verified the network path is closed. See
[`docs/security.md`](security.md).

## Reverse Proxy Trust Boundary

The reverse proxy is the security boundary for this entire pattern. That means:

- The backend app's port/container must not be reachable on any path that skips the proxy (no
  published host port, no unrestricted Docker network access, no direct LAN route).
- The proxy must be configured to always consult the authentik outpost before forwarding — a
  misconfigured rule that forwards unconditionally defeats the whole pattern.
- TLS/certs and the public hostname for the app are still deployer-managed, same as for authentik
  itself.

## Deployer-Managed Reverse Proxy Assumption

This repo assumes the actual reverse proxy (Cloudflare Tunnel ingress rules, or Traefik with
forward-auth middleware) is configured by `../synology-site-deployer`, the same way it configures
routing for any other app. This repo's job is to run the authentik outpost/proxy provider that the
reverse proxy calls — not to run the reverse proxy itself.

Traefik forward-auth middleware example (for reference only — actual labels are applied by the
deployer or the protected app's own Compose file):

```yaml
labels:
  - traefik.http.middlewares.authentik.forwardauth.address=http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
  - traefik.http.middlewares.authentik.forwardauth.trustForwardHeader=true
  - traefik.http.middlewares.authentik.forwardauth.authResponseHeaders=X-authentik-username,X-authentik-groups,X-authentik-email,X-authentik-name,X-authentik-uid
  - traefik.http.routers.your-app.middlewares=authentik@docker
```

See also [`examples/app-integrations/generic-forward-auth.md`](../examples/app-integrations/generic-forward-auth.md).

## App-Specific Policy Notes

- Each protected app should get its own authentik Proxy Provider and Application, even if several
  apps share one outpost — this keeps per-app access policies (which groups can reach it)
  independent.
- Document per-app policy decisions (which group(s) grant access) alongside that app's own repo/
  deployment notes, not inside this repo — this repo only documents the pattern.
