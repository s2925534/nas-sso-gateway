# Generic Forward-Auth Example

A technology-agnostic sketch of protecting an app with authentik's forward-auth outpost (Pattern
2), for apps with no native SSO support. The actual reverse-proxy configuration is applied by
`../synology-site-deployer` (or wherever the app's own reverse proxy lives) — this is a reference
shape, not something this repo deploys.

## 1. Create the Provider in authentik

Applications → Providers → Create → Proxy Provider:

- Mode: **Forward auth (single application)** for one app, or **Forward auth (domain level)** for
  several subdomains behind one outpost.
- Bind it to an Outpost (Applications → Outposts).

## 2. Reverse Proxy Configuration (Traefik example, illustrative)

```yaml
labels:
  - traefik.http.middlewares.authentik.forwardauth.address=http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
  - traefik.http.middlewares.authentik.forwardauth.trustForwardHeader=true
  - traefik.http.middlewares.authentik.forwardauth.authResponseHeaders=X-authentik-username,X-authentik-groups,X-authentik-email,X-authentik-name,X-authentik-uid
  - traefik.http.routers.your-app.middlewares=authentik@docker
  - traefik.http.routers.your-app.rule=Host(`tools.example.com`)
```

Equivalent concepts apply for other reverse proxies (nginx `auth_request`, Caddy
`forward_auth`, etc.) — see authentik's own docs for provider-specific snippets.

## 3. Confirm the Trust Boundary

Before enabling this in front of a real app:

- Confirm the app's container/port is **not** reachable by any path other than through this
  reverse proxy (see [`docs/security.md`](../../docs/security.md)).
- Confirm the reverse proxy is actually configured to deny by default when the auth check fails,
  not fail open.

## 4. Test

1. Visit the app's hostname while logged out — expect a redirect to authentik login.
2. Log in, get redirected back, and confirm the app loads.
3. If the app reads identity headers (`X-authentik-*`), confirm they arrive correctly — see the
   trusted-header warning in [`docs/proxy-auth-integration.md`](../../docs/proxy-auth-integration.md).
4. Document the rollback step (disable the middleware/rule) before relying on this in production.
