# Reverse Proxy and Domain

This repo does not hardcode or assume any specific domain. The hostname is entirely the
operator's choice, set via `SSO_DOMAIN`/`SSO_EXTERNAL_URL` in `.env`. This document describes the
recommended *pattern* for choosing that hostname, illustrated with the placeholder
`auth.example.com` — substitute your own domain everywhere it appears.

## Recommended Hostname Pattern

`auth.<yourdomain>` — for example `auth.example.com`.

## Alternative Hostname Pattern

`sso.<yourdomain>` — for example `sso.example.com`.

## Why `auth.` Is Broader and More Future-Proof Than `sso.`

`auth.` doesn't box the service into "just SSO." Over time this gateway is expected to represent
authentication, SSO, OIDC, OAuth2, MFA, an app portal, reverse-proxy protection, and future
identity services (LDAP, SAML, service accounts). `sso.` reads narrower and would feel like a
misnomer once those other capabilities land. `sso.<yourdomain>` remains a perfectly acceptable
alternative if `auth.` is already used for something else in your own setup — see
[`docs/decision-log.md`](decision-log.md) (ADR-002).

## Intended Public Routing

```
https://auth.example.com  ──▶  authentik web endpoint only
                                (SSO_BIND_HOST:SSO_HTTP_PORT)
```

Replace `auth.example.com` with your own `SSO_DOMAIN`. No other internal service is ever routed
under this hostname.

## Domain Handling Is Entirely External to This Repo

DNS records, Cloudflare Tunnel or Traefik configuration, and TLS certificates for your chosen
hostname are owned by whatever external tooling you choose (a reverse proxy, a tunnel, or a
deployer script such as `../synology-site-deployer` — none required). This repo does not
implement Cloudflare automation, does not call the Cloudflare API, and does not manage
certificates, regardless of which tool (if any) you use.

## Database and Redis Must Remain Private

Regardless of how your `SSO_DOMAIN` is routed, PostgreSQL and Redis must never be reachable
through that hostname or any other public path. They have no published host ports in
`docker-compose.yml` and must not be added to any reverse-proxy configuration.

## Reverse Proxy Must Preserve Required Headers

Whichever reverse-proxy technology you use (Cloudflare Tunnel, Traefik, Nginx Proxy Manager,
Caddy, etc.), it must preserve:

- `Host` — so authentik generates correct URLs/redirects.
- `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host` — so authentik and downstream apps see
  the real client IP/scheme, and forward-auth headers resolve correctly.
- Any authentik-specific headers required by proxy providers (e.g. `X-Authentik-*`) when using the
  forward-auth pattern — see [`docs/proxy-auth-integration.md`](proxy-auth-integration.md).

Misconfigured or stripped headers are the most common cause of login loops — see
[`docs/troubleshooting.md`](troubleshooting.md).
