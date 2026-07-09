# Deployer Integration

## This Project Is Standalone

`nas-sso-gateway` is a self-contained repository. It does not import, require, or modify
`../synology-site-deployer`, and it can be deployed without that project at all (e.g. for local
testing). Integration is one-directional: the deployer consumes this repo's Compose file and
documented ports/paths; this repo has no dependency back on the deployer.

## Existing Deployer

Local path: `../synology-site-deployer` — a Python CLI that deploys containerized apps to a
Synology NAS over SSH, and manages Cloudflare Tunnel/DNS routing for them (see its own `README.md`
for full capabilities).

## Division of Responsibility

| Concern | Owned by |
|---|---|
| DNS records | `../synology-site-deployer` |
| Cloudflare Tunnel / Traefik + Let's Encrypt | `../synology-site-deployer` |
| TLS certificates | `../synology-site-deployer` |
| Public hostname routing | `../synology-site-deployer` |
| Final NAS persistent-folder paths | `../synology-site-deployer` (sets `SSO_BASE_PATH`) |
| Docker Compose for authentik/Postgres/Redis | this repo |
| Environment variables / `.env.example` | this repo |
| Expected ports and routes | this repo |
| Security assumptions and docs | this repo |

## What This Repo Provides to the Deployer

- `docker-compose.yml` — deployable as-is via `synology-site deploy` (an existing project's own
  Compose file), or copied into the deployer's own project layout.
- `.env.example` — the full set of variables the deployer needs to populate (or generate) before
  starting the stack.
- A single expected internal service: the **authentik web endpoint**, bound to
  `SSO_BIND_HOST:SSO_HTTP_PORT` inside the container network / on the host.
- Documented persistent folders, all relative to `SSO_BASE_PATH` (see `.env.example` and
  [`docs/architecture.md`](architecture.md)) — the deployer decides the real path (e.g. under
  `/volume1/docker/...`) and passes it in via `SSO_BASE_PATH`.

## Expected Public Hostname

`auth.veloso.dev` (preferred) or `sso.veloso.dev` (alternative) — see
[`docs/reverse-proxy-domain.md`](reverse-proxy-domain.md). The deployer is responsible for
pointing that hostname at the authentik web endpoint only.

## Expected Internal Service

Only the authentik web container/port should ever be reachable through the deployer's reverse
proxy or tunnel. Specifically:

- **Expose:** authentik web (`SSO_HTTP_PORT`, default `9000`).
- **Do not expose:** PostgreSQL (`5432`), Redis (`6379`), Synology DSM, SSH.

## How the Deployer Should Consume This Repo

1. Clone or reference this repo on the NAS (or wherever it deploys from).
2. Provide a real `.env` (never commit it) with `SSO_BASE_PATH` set to the deployer-managed
   persistent directory, and `SSO_DOMAIN` / `SSO_EXTERNAL_URL` set to `auth.veloso.dev`.
3. Run `docker compose up -d` (directly, or via the deployer's own `deploy`/`update` workflow for
   an existing project's Compose file).
4. Wire the deployer's reverse-proxy/tunnel routing at the authentik web port only, following
   whichever pattern the deployer already uses for other Compose-based apps (Cloudflare Tunnel or
   Traefik labels — see the deployer's own `docs/traefik-letsencrypt.md` for the labels pattern).
5. Leave `PUBLIC_EXPOSURE=false` until DNS/tunnel/certs are confirmed working end-to-end, then
   flip it and re-deploy.

## Future Apps

Apps protected by this SSO gateway continue to be deployed the same way they are today (via the
deployer or otherwise); only their *authentication* changes, through OIDC or proxy/forward-auth
integration documented in [`docs/app-integration-patterns.md`](app-integration-patterns.md). This
repo does not deploy those apps.
