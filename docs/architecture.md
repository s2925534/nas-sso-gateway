# Architecture

## 1. MVP Architecture (Local / LAN-only)

```
┌─────────────────────────────────────────────────────────┐
│  Docker host (local machine, Linux server, or NAS)        │
│                                                             │
│   ┌───────────────┐   ┌───────────────┐   ┌─────────────┐ │
│   │ authentik-     │   │ authentik-     │   │ authentik-  │ │
│   │ server         │──▶│ worker         │──▶│ postgresql  │ │
│   │ (web UI, API,  │   │ (background    │   │ (private)   │ │
│   │  OIDC/OAuth2)  │   │  tasks, sync)  │   └─────────────┘ │
│   └───────┬────────┘   └───────┬────────┘   ┌─────────────┐ │
│           │                    │             │ redis       │ │
│           └────────────────────┴────────────▶│ (private)   │ │
│                                               └─────────────┘ │
│   bound to: SSO_BIND_HOST:SSO_HTTP_PORT                    │
└───────────────────────┬─────────────────────────────────────┘
                         │ LAN or localhost only
                         ▼
                  Browser on your network
```

- Only the authentik web port is bound to a host port (`SSO_BIND_HOST:SSO_HTTP_PORT`).
- PostgreSQL and Redis have no published host ports — reachable only on the internal Docker
  network.
- All persistent state lives under `${SSO_BASE_PATH}/...` (see `.env.example`), not a hardcoded
  volume path.
- `DEPLOY_MODE=local_only` and `PUBLIC_EXPOSURE=false` are the safe MVP defaults.

## 2. External Public Exposure Architecture

```
Internet
   │
   ▼
Cloudflare (DNS + Tunnel)  ──┐
   or Traefik + Let's Encrypt│  owned by whatever external tooling you choose
   (ports 80/443)            │  (a reverse proxy, a tunnel, or a deployer script —
   ▼                         │   this repo does not require any particular one)
Reverse proxy / tunnel  ─────┘
   │  forwards only:
   │  https://<your SSO_DOMAIN> → SSO_BIND_HOST:SSO_HTTP_PORT
   ▼
authentik-server (this repo)
```

- This repo never talks to Cloudflare, DNS, or certificate APIs, regardless of how it's deployed.
- Whatever you use for exposure — Cloudflare Tunnel, Traefik, Nginx Proxy Manager, Caddy, or a
  deployer script such as the maintainer's own `../synology-site-deployer` — decides the routing
  method, and should point only the authentik web endpoint at the public hostname.
- PostgreSQL, Redis, DSM, and SSH are never included in that routing.

## 3. Native OIDC App Integration Architecture

```
User ──▶ App (e.g. photos.example.com) ──redirect──▶ authentik (auth.example.com)
                                                     │ authenticate + consent
User ◀──────────── redirect w/ auth code ───────────┘
App ──exchange code for tokens──▶ authentik
App ◀── ID token + access token (claims: sub, email, groups, …) ──
```

- Best for apps you build yourself, or any app with native OIDC/OAuth2 support.
- The app never sees the user's password; it only receives signed tokens/claims from authentik.
- See [`docs/oidc-integration.md`](oidc-integration.md).

## 4. Reverse Proxy Forward-Auth Architecture

```
User ──▶ Reverse proxy ──"is this request authenticated?"──▶ authentik outpost
              │                                                    │
              │◀───────────── yes / no + identity headers ─────────┘
              │
   yes ──▶ forward request to backend app (no native SSO support needed)
   no  ──▶ redirect user to authentik login, then retry
```

- Best for simple NAS web apps/admin tools that only support a static login form.
- The reverse proxy is the trust boundary — the backend app must not be reachable by any path
  that bypasses the proxy.
- See [`docs/proxy-auth-integration.md`](proxy-auth-integration.md).

## 5. Future Multi-App SSO Architecture

```
                         ┌───────────────────────────┐
                         │   authentik (app portal)    │
                         │  auth.example.com             │
                         └──────────────┬────────────────┘
        ┌───────────────┬───────────────┼───────────────┬───────────────┐
        ▼               ▼               ▼               ▼               ▼
 photos.example.com  admin-tools...   wiki.example.com  dashboard...  apps.example.com
   (OIDC)          (forward-auth)    (OIDC)          (forward-auth) (OIDC or proxy)
```

- Each app gets its own OIDC client or proxy provider in authentik, its own group-based access
  policy, and its own documented redirect URIs.
- The app portal gives a single launcher view once logged in.
- See [`docs/app-integration-patterns.md`](app-integration-patterns.md) for onboarding patterns.

## 6. Emergency Bypass Concept

Because every protected app depends on authentik being reachable and the admin account being
usable, plan an escape hatch before going to production:

- Keep a documented, non-SSO admin path for at least one critical app (e.g. a local-network-only
  admin URL, or a break-glass local account) until you have tested SSO recovery.
- Keep the authentik admin account credentials and any recovery codes in a password manager
  outside of this repo — never in Git.
- Document per-app rollback steps (removing the forward-auth rule, or disabling the OIDC
  requirement) before enabling enforcement, so a locked-out admin doesn't lock out every app at
  once.
- See [`docs/security.md`](security.md) for the full break-glass discussion, tracked under the
  `ENABLE_ADMIN_BREAK_GLASS` flag in [`docs/future-flags.md`](future-flags.md).
