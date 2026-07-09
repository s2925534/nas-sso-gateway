# Reverse Proxy and Domain

## Recommended Hostname

`auth.veloso.dev`

## Alternative Hostname

`sso.veloso.dev`

## Why `auth.veloso.dev` Is Broader and More Future-Proof

`auth.` doesn't box the service into "just SSO." Over time this gateway is expected to represent
authentication, SSO, OIDC, OAuth2, MFA, an app portal, reverse-proxy protection, and future
identity services (LDAP, SAML, service accounts). `sso.` reads narrower and would feel like a
misnomer once those other capabilities land. `sso.veloso.dev` remains documented as an acceptable
alternative if `auth.` is ever needed for something else.

Note: `sso.systemsnotsilos.com` is intentionally **not** used. `systemsnotsilos.com` is reserved
for public-facing/business identity; `veloso.dev` is the private developer infrastructure domain
this project belongs to.

## Intended Public Routing

```
https://auth.veloso.dev  ──▶  authentik web endpoint only
                               (SSO_BIND_HOST:SSO_HTTP_PORT)
```

No other internal service is ever routed under this hostname.

## Domain Handling Belongs to the Deployer

DNS records, Cloudflare Tunnel or Traefik configuration, and TLS certificates for
`auth.veloso.dev` are entirely owned by `../synology-site-deployer`. This repo does not implement
Cloudflare automation, does not call the Cloudflare API, and does not manage certificates.

## Database and Redis Must Remain Private

Regardless of how `auth.veloso.dev` is routed, PostgreSQL and Redis must never be reachable
through that hostname or any other public path. They have no published host ports in
`docker-compose.yml` and must not be added to the deployer's reverse-proxy configuration.

## Reverse Proxy Must Preserve Required Headers

Whichever reverse-proxy technology the deployer uses (Cloudflare Tunnel, Traefik, etc.), it must
preserve:

- `Host` — so authentik generates correct URLs/redirects.
- `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host` — so authentik and downstream apps see
  the real client IP/scheme, and forward-auth headers resolve correctly.
- Any authentik-specific headers required by proxy providers (e.g. `X-Authentik-*`) when using the
  forward-auth pattern — see [`docs/proxy-auth-integration.md`](proxy-auth-integration.md).

Misconfigured or stripped headers are the most common cause of login loops — see
[`docs/troubleshooting.md`](troubleshooting.md).
