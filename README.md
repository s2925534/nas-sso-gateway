# NAS SSO Gateway

Self-hosted Single Sign-On (SSO) gateway for NAS-hosted web apps, built on
[authentik](https://goauthentik.io/), Docker, OIDC, and reverse-proxy/forward-auth patterns.

**Recommended hostname:** `auth.example.com`

## What This Project Does

- Runs a central identity provider (authentik) in Docker Compose, so you log in once and reuse
  that session across every protected app.
- Documents how to integrate future apps via native OIDC/OAuth2, reverse-proxy forward-auth, or
  trusted headers.
- Provides a portable, deployer-friendly deployment: no hardcoded NAS volume paths, no Cloudflare
  automation baked in.
- Keeps the database and cache private, and documents a security-first rollout (local-only /
  LAN-only first, MFA before any public exposure).

## What This Project Does Not Do

- It does not implement Cloudflare, DNS, tunnel, or certificate automation. That belongs to
  [`../synology-site-deployer`](../synology-site-deployer).
- It does not retrofit every existing app with SSO immediately. The MVP stands up the identity
  provider and documents integration patterns; app-by-app integration is a later phase.
- It does not assume or require a specific Synology volume (e.g. `/volume1`). All persistent data
  lives under a configurable `SSO_BASE_PATH`.
- It does not expose Synology DSM, SSH, PostgreSQL, or Redis publicly.

## Why authentik

authentik supports OIDC/OAuth2, SAML, an app-portal UI, and proxy-authentication ("forward-auth")
for apps that can't natively speak SSO — which covers the two realistic cases for a NAS homelab:
apps you build yourself (OIDC) and off-the-shelf NAS tools that only understand a login page
(forward-auth). One identity provider covers both without extra moving parts.

### Alternatives Considered

| Option | Verdict for this MVP |
|---|---|
| **Authelia** | Good lightweight forward-auth + 2FA companion for a reverse proxy, but no bundled OIDC provider UI or app portal — would need pairing with something else for native OIDC apps. Documented as an alternative, not implemented. |
| **Keycloak** | Enterprise-grade, very capable, but heavier (JVM-based, more operational surface) than a first NAS SSO MVP needs. Documented as an alternative, not implemented. |

See [`docs/decision-log.md`](docs/decision-log.md) for the full reasoning.

## Architecture (Text Diagram)

```
                        ┌────────────────────────────┐
                        │   ../synology-site-deployer │
                        │  (DNS, Cloudflare, tunnel,  │
                        │   certs, reverse proxy)     │
                        └─────────────┬────────────────┘
                                      │ routes public hostname
                                      │ auth.veloso.dev
                                      ▼
                        ┌────────────────────────────┐
                        │      authentik server       │◄──┐
                        │   (web UI, OIDC, proxy      │   │ session
                        │    provider, app portal)    │   │
                        └─────────────┬────────────────┘   │
                                      │                     │
                        ┌─────────────┴───────────┐         │
                        ▼                         ▼         │
                ┌───────────────┐         ┌───────────────┐ │
                │  authentik     │         │  authentik     │ │
                │  worker        │         │  outposts      │ │
                └───────┬────────┘         │ (future proxy  │ │
                        │                  │  providers)    │ │
              ┌─────────┴────────┐         └───────────────┘ │
              ▼                  ▼                            │
      ┌───────────────┐  ┌───────────────┐                    │
      │  PostgreSQL    │  │  Redis         │                    │
      │  (private)     │  │  (private)     │                    │
      └───────────────┘  └───────────────┘                    │
                                                                │
        Protected apps (OIDC client or forward-auth) ──────────┘
```

This repo owns the box in the middle (authentik + Postgres + Redis). Everything above the dashed
line — public hostname, TLS, tunnel — is owned by `../synology-site-deployer`.

## Deployer-Managed Domain

Public exposure of `auth.example.com` (DNS, Cloudflare Tunnel or Traefik, certificates) is handled
entirely by `../synology-site-deployer`. This repo only needs to expose authentik's web port on
the configured bind host/port; see [`docs/deployer-integration.md`](docs/deployer-integration.md)
and [`docs/reverse-proxy-domain.md`](docs/reverse-proxy-domain.md).

## No Fixed Synology Volume

Persistent storage is controlled entirely by the `SSO_BASE_PATH` environment variable — never a
hardcoded `/volume1/...` path. Run it anywhere (local Docker, a Linux server, or a Synology NAS)
and let the deployer (or you, manually) decide the real path. See
[`docs/architecture.md`](docs/architecture.md) and `.env.example`.

## Security Warning

This stack, once exposed, becomes the single point of entry for every app behind it. Read
[`docs/security.md`](docs/security.md) before any non-local deployment — in particular: never
commit `.env`, never expose PostgreSQL/Redis, enable MFA before going public, and have an
emergency bypass plan for protected apps in case the SSO admin account is ever locked out.

## Phase Overview

| Phase | Focus |
|---|---|
| 0 | Planning and documentation foundation (this stage) |
| 1 | authentik MVP: Docker Compose, env, scripts |
| 2 | Deployer integration readiness |
| 3 | First SSO configuration (admin, users, MFA, first OIDC/proxy provider) |
| 4 | Protect first NAS web app |
| 5 | Multi-app SSO rollout |
| 6 | Security hardening |
| 7 | Future advanced identity (passkeys, LDAP, SAML, SCIM, service accounts) |

Full breakdown: [`docs/phase-plan.md`](docs/phase-plan.md) and [`TODO.md`](TODO.md).

## Documentation Index

- [`docs/architecture.md`](docs/architecture.md) — system architecture and diagrams
- [`docs/phase-plan.md`](docs/phase-plan.md) — all phases in detail
- [`docs/decision-log.md`](docs/decision-log.md) — ADR-style decisions
- [`docs/security.md`](docs/security.md) — security assumptions and rules
- [`docs/authentik-manual.md`](docs/authentik-manual.md) — operating authentik in this project
- [`docs/deployer-integration.md`](docs/deployer-integration.md) — how the deployer consumes this repo
- [`docs/reverse-proxy-domain.md`](docs/reverse-proxy-domain.md) — hostname and routing plan
- [`docs/app-integration-patterns.md`](docs/app-integration-patterns.md) — five SSO integration patterns
- [`docs/oidc-integration.md`](docs/oidc-integration.md) — OIDC integration reference
- [`docs/proxy-auth-integration.md`](docs/proxy-auth-integration.md) — forward-auth integration reference
- [`docs/troubleshooting.md`](docs/troubleshooting.md) — common problems and fixes
- [`docs/future-flags.md`](docs/future-flags.md) — planned feature flags
- [`docs/first-sso-configuration.md`](docs/first-sso-configuration.md) — Phase 3 hands-on configuration walkthrough
- [`docs/multi-app-rollout.md`](docs/multi-app-rollout.md) — Phase 5 onboarding checklist and naming convention
- [`docs/security-hardening.md`](docs/security-hardening.md) — Phase 6 hardening procedures

## License

See [`LICENSE`](LICENSE).
