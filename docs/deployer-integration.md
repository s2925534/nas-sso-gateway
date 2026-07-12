# External Deployment Integration

This repo does not require any specific deployment tool. It can be run standalone, or fronted by
whatever reverse-proxy/tunnel/deployer tooling you already use. This document covers both: how to
run it standalone, the generic contract any external tool needs to follow, and one worked example
(the maintainer's own companion project, `../synology-site-deployer`) that is entirely optional.

## This Project Is Standalone

`nas-sso-gateway` is a self-contained repository. It does not import, require, or modify any
external deployment tool, and it runs the same way with or without one — `docker compose up -d`
plus a real `.env` is the entire dependency. Integration with an external tool (if you use one) is
one-directional: that tool consumes this repo's Compose file and documented ports/paths; this repo
has no dependency back on it.

## Running Standalone (No External Tooling Required)

The simplest path, and the one this repo is built and tested against by default:

1. `cp .env.example .env` and fill in real secrets (see [`docs/security.md`](security.md)).
2. `./scripts/bootstrap-sso.sh` (or `docker compose up -d` directly).
3. For local/LAN-only use, stop here — nothing else is needed.
4. For public exposure, put **any** reverse proxy or tunnel you like in front of the authentik web
   port (`SSO_BIND_HOST:SSO_HTTP_PORT`) — Cloudflare Tunnel, Traefik, Caddy, Nginx Proxy Manager,
   or a deployer script. See [`docs/reverse-proxy-domain.md`](reverse-proxy-domain.md) for the
   generic hostname/header contract any of these must satisfy.

## Division of Responsibility

| Concern | Owned by |
|---|---|
| DNS records | External tooling (your choice) |
| Cloudflare Tunnel / Traefik + Let's Encrypt / any reverse proxy | External tooling (your choice) |
| TLS certificates | External tooling (your choice) |
| Public hostname routing | External tooling (your choice) |
| Final persistent-folder paths on the host | External tooling (your choice), or you manually (sets `SSO_BASE_PATH`) |
| Docker Compose for authentik/Postgres/Redis | this repo |
| Environment variables / `.env.example` | this repo |
| Expected ports and routes | this repo |
| Security assumptions and docs | this repo |

## What This Repo Provides to External Tooling

- `docker-compose.yml` — runnable as-is with `docker compose up -d`, or consumed by an external
  deploy tool that uploads/starts an existing project's own Compose file.
- `.env.example` — the full set of variables any external tooling needs to populate (or generate)
  before starting the stack.
- A single expected internal service: the **authentik web endpoint**, bound to
  `SSO_BIND_HOST:SSO_HTTP_PORT` inside the container network / on the host.
- Documented persistent folders, all relative to `SSO_BASE_PATH` (see `.env.example` and
  [`docs/architecture.md`](architecture.md)) — external tooling (or you, manually) decides the
  real path and passes it in via `SSO_BASE_PATH`. This repo never assumes a specific path.

## Expected Public Hostname

An `auth.<yourdomain>` label is recommended (e.g. `auth.example.com`), with `sso.<yourdomain>` as
an acceptable alternative — see [`docs/reverse-proxy-domain.md`](reverse-proxy-domain.md). The
actual value comes from `SSO_DOMAIN`/`SSO_EXTERNAL_URL` in `.env`; this repo never hardcodes a
domain. Whatever tooling you use for exposure is responsible for pointing that hostname at the
authentik web endpoint only.

## Expected Internal Service

Only the authentik web container/port should ever be reachable through any reverse proxy or
tunnel you put in front of this stack. Specifically:

- **Expose:** authentik web (`SSO_HTTP_PORT`, default `9000`).
- **Do not expose:** PostgreSQL (`5432`), Redis (`6379`), Synology DSM, SSH.

## How External Tooling Should Consume This Repo (If You Use Any)

1. Clone or reference this repo wherever it deploys from.
2. Provide a real `.env` (never commit it) with `SSO_BASE_PATH` set to a real persistent
   directory, and `SSO_DOMAIN` / `SSO_EXTERNAL_URL` set to your chosen hostname (e.g.
   `auth.example.com`).
3. Run `docker compose up -d` (directly, or via whatever workflow your tooling uses for an
   existing project's own Compose file).
4. Wire your reverse-proxy/tunnel routing at the authentik web port only.
5. Leave `PUBLIC_EXPOSURE=false` until DNS/tunnel/certs are confirmed working end-to-end, then
   flip it and re-deploy.

## Optional Example: Using `../synology-site-deployer`

The maintainer's own NAS deployments use a companion CLI project at `../synology-site-deployer`
(a Python tool that deploys containerized apps to a Synology NAS over SSH and can wire up
Cloudflare Tunnel/DNS routing). **This is one option, not a requirement** — everything above works
identically with Traefik, Caddy, Nginx Proxy Manager, a manually-configured Cloudflare Tunnel, or
nothing at all. If you happen to use this same tool, here is the concrete invocation:

```bash
synology-site deploy auth.example.com \
  --compose-file ./docker-compose.yml \
  --env-file ./.env \
  --container-name sso-authentik-server \
  --port 9000
```

- **Create the persistent bind-mount folders on the NAS before the first `deploy`.** Unlike
  `scripts/bootstrap-sso.sh` (which runs `scripts/create-folders.sh` first), `synology-site deploy`
  only uploads the compose/env files and runs `docker compose up -d` — it does not create
  `${SSO_BASE_PATH}/{postgres,redis,authentik/media,authentik/custom-templates,authentik/certs,backups,logs,exports,docs}`
  first. Without them, PostgreSQL/Redis fail to start with `Bind mount failed: ... does not exist`.
  Create them once over SSH (`mkdir -p` each path under the NAS project folder,
  e.g. `/volume1/docker/<slug>/data/sso/...`) before the first deploy; subsequent `deploy`/`update`
  runs are unaffected since the folders persist.
- Omit `--port` instead if the NAS already runs Traefik and routing is done via Docker labels
  rather than per-app port allocation (see that project's own `docs/traefik-letsencrypt.md`).
- **Do not pass `--health-path /-/health/ready/` or `/-/health/live/`.** This tool's health check
  requires an exact HTTP `200` response; authentik's own liveness/readiness endpoints return
  `204 No Content`, which would be treated as a failed health check. If you want an automated
  post-deploy health check, use `--health-path /` instead (the login/flow page resolves to `200`),
  or skip `--health-path` entirely and run `scripts/health-check.sh` manually after deploy.
- This tool does not read any manifest/metadata file from a target project — it only reads the
  exact `--compose-file`/`--env-file` paths passed on the command line, plus that project's
  `.dockerignore` if `--source-dir` is used for upload. Service identity (port, health path,
  container name) is passed as CLI flags at deploy time, not discovered from a file in this repo
  — so this repo intentionally has no `deploy.json`/`.deployer/` file, since nothing would read
  it. After `deploy` finishes, it writes its own marker file on the **remote NAS project folder**
  (not in this repo) for later `update` runs — this repo does not need to know about or maintain
  that file.

If you use a different deployment tool, its own docs cover the equivalent invocation — the
contract this repo needs from any of them is the same: expose one port, leave the rest private.

## Future Apps

Apps protected by this SSO gateway continue to be deployed the same way they are today (via
whatever tooling you already use, or manually); only their *authentication* changes, through OIDC
or proxy/forward-auth integration documented in
[`docs/app-integration-patterns.md`](app-integration-patterns.md). This repo does not deploy those
apps.
