# Troubleshooting

## Cannot Reach Authentik

- Confirm the `authentik-server` container is running: `docker compose ps`.
- Confirm `SSO_BIND_HOST`/`SSO_HTTP_PORT` match what you're browsing to.
- If running locally, try `http://localhost:<SSO_HTTP_PORT>` before troubleshooting DNS/proxy.
- If deployer-managed, confirm the tunnel/reverse-proxy rule for `auth.example.com` is active — see
  [`docs/deployer-integration.md`](deployer-integration.md).

## Login Loop

- Usually caused by `SSO_EXTERNAL_URL` not matching the URL actually used to reach authentik, or
  the reverse proxy stripping `Host`/`X-Forwarded-*` headers so authentik generates redirects to
  the wrong origin. See [`docs/reverse-proxy-domain.md`](reverse-proxy-domain.md).
- Confirm cookies aren't being blocked (third-party cookie settings, mismatched scheme http vs.
  https).

## Incorrect External URL

- `SSO_EXTERNAL_URL` must be the exact public URL (scheme + host, no trailing path) that users and
  apps will use — e.g. `https://auth.example.com`, not `http://localhost:9000` once exposed.
- Changing this after apps are integrated may require updating their OIDC issuer URLs too.

## Wrong Redirect URI

- authentik will reject the callback if the app's redirect URI doesn't exactly match what's
  registered on the provider (scheme, host, path, and trailing slash all matter).
- Fix by updating the Provider's redirect URI list to match the app exactly. See
  [`docs/oidc-integration.md`](oidc-integration.md).

## OIDC Client Mismatch

- "invalid_client" or similar errors usually mean the Client ID/Secret in the app's config don't
  match the provider in authentik, or the app is pointed at the wrong issuer URL.
- Re-copy the Client ID/Secret directly from the provider page after any regeneration.

## Reverse Proxy Headers Wrong

- Forward-auth and trusted-header patterns depend on the proxy preserving/injecting specific
  headers. Missing `X-Forwarded-*` headers, or a proxy that overwrites `X-authentik-*` headers
  from a previous hop, will break identity propagation. See
  [`docs/proxy-auth-integration.md`](proxy-auth-integration.md).

## Database Not Starting

- Check `docker compose logs postgresql` for errors.
- Common cause: `SSO_BASE_PATH`/`${SSO_BASE_PATH}/postgres` not writable by the container's user,
  or a stale/incompatible data directory from a previous PostgreSQL major version.
- Never delete the Postgres data directory to "fix" this without a backup first.

## Redis Not Starting

- Check `docker compose logs redis`.
- Common cause: `${SSO_BASE_PATH}/redis` permission issues, or a port conflict if you've added a
  host port mapping (which you shouldn't — see [`docs/security.md`](security.md)).

## Permission Issues on `SSO_BASE_PATH`

- Ensure the path exists and is writable before starting containers — `scripts/create-folders.sh`
  handles creation, but ownership/permissions depend on your host (Docker Desktop vs. Linux vs.
  Synology container user).
- On Synology, container processes may run as a specific UID/GID; check the deployer's own
  conventions for matching folder ownership.

## Lost Admin Password

- If you still have shell/DB access: authentik supports resetting the admin password via its
  management command inside the `authentik-worker`/`authentik-server` container (see the official
  authentik docs for the current `manage.py` invocation for your deployed version).
- If you have no access at all, this is why backups and a break-glass plan matter — see
  [`docs/security.md`](security.md) and [`scripts/restore-notes.md`](../scripts/restore-notes.md).

## MFA Lockout

- If a user is MFA-locked, an admin can remove their MFA device from **Directory → Users → (user)
  → MFA Authenticators**, forcing re-enrollment on next login.
- If the *admin* account itself is MFA-locked with no recovery codes, this is a break-glass
  scenario — see the emergency bypass notes in [`docs/security.md`](security.md).

## App Not Respecting Headers

- Confirm the app is actually configured for the trusted-header pattern (Pattern 3) and not
  silently expecting OIDC/session auth instead.
- Confirm the reverse proxy is actually injecting the expected header names — these vary by app
  and must be mapped explicitly.

## Public Domain Not Routing

- This is a deployer-side issue by design — check `../synology-site-deployer`'s own DNS/Cloudflare
  Tunnel/Traefik configuration and logs, not this repo. Confirm `auth.example.com` resolves and
  confirm the tunnel/proxy rule points at the correct internal port
  (`SSO_BIND_HOST:SSO_HTTP_PORT`).

## Deployer Integration Issues

- Confirm `.env` (on the deployer side) sets `SSO_BASE_PATH` to a real, writable, persistent path
  — not left at the local default (`./data/sso`) when deployed to the NAS.
- Confirm only the authentik web port is included in the deployer's routing config — see
  [`docs/deployer-integration.md`](deployer-integration.md).
