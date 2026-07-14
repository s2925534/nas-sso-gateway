# Decision Log

Architecture Decision Record (ADR) style log. Each entry: context, decision, consequences.

---

## ADR-001: Use authentik for the SSO MVP

**Context:** Need a self-hosted identity provider that covers both apps with native OIDC support
and NAS tools that only understand a login form.

**Decision:** Use authentik as the identity platform for the MVP.

**Consequences:** Get OIDC/OAuth2, SAML, an app portal, and proxy-authentication/forward-auth
outposts in one project. Heavier than Authelia alone, but avoids running two separate systems for
the two integration patterns. Authelia and Keycloak are documented as alternatives, not
implemented (see ADR-002 discussion in [`README.md`](../README.md)).

---

## ADR-002: Prefer an `auth.` subdomain over `sso.`

**Context:** This repo doesn't own or assume any particular domain — the operator sets their own
hostname via `SSO_DOMAIN`/`SSO_EXTERNAL_URL`. Still needed a recommended subdomain *label*
pattern to put in the docs and examples (illustrated here as `auth.example.com`).

**Decision:** Recommend an `auth.<yourdomain>` label as the default pattern; document
`sso.<yourdomain>` as an acceptable alternative label.

**Consequences:** `auth.` is broader and more future-proof than `sso.` — it reads naturally for
authentication, SSO, OIDC, OAuth2, MFA, an app portal, reverse-proxy protection, and future
identity services, without implying the system is *only* an SSO layer. This is a naming
recommendation only; the actual domain is entirely the operator's choice and is never hardcoded
in this repo (see [`docs/reverse-proxy-domain.md`](reverse-proxy-domain.md)).

---

## ADR-003: Keep Cloudflare/domain exposure entirely outside this repo

**Context:** DNS, Cloudflare Tunnel/Traefik, certificates, and reverse-proxy routing are a
separate concern from running authentik, and different operators already use different tools for
this (Cloudflare Tunnel, Traefik, Nginx Proxy Manager, Caddy, a deployer script, or nothing at all
for local-only use). The maintainer happens to have a companion project,
`../synology-site-deployer`, that automates this for NAS-hosted apps — but this repo must not
depend on it.

**Decision:** This repo never talks to Cloudflare or DNS APIs, and never assumes a specific
external tool. It only documents the expected public hostname and internal port/route; whatever
external tooling the operator chooses owns making that hostname reachable.
`../synology-site-deployer` is documented as one worked example in
[`docs/deployer-integration.md`](deployer-integration.md), not a requirement.

**Consequences:** Clean separation of concerns — this repo stays portable and testable without
Cloudflare credentials, and works identically whether the operator uses a deployer script, a
reverse proxy configured by hand, or nothing (local-only). Whatever tool is used only needs to
know one thing: which endpoint to expose (authentik's web port).

---

## ADR-004: No hardcoded Synology volume paths

**Context:** The deployer already knows how to place persistent folders in the correct NAS
directory (typically under `/volume1/docker/...`), and future infrastructure may not use Synology
at all.

**Decision:** All persistent storage locations are derived from a single `SSO_BASE_PATH`
environment variable, defaulting to a portable local path (`./data/sso`). No file in this repo
assumes `/volume1` or any other fixed volume.

**Consequences:** The repo runs unmodified on a laptop, a Linux server, or a NAS. The deployer (or
a human) sets `SSO_BASE_PATH` to whatever is correct for that environment.

---

## ADR-005: Use OIDC for apps that support it

**Context:** Some current and future apps (mostly ones built in-house) can speak OIDC/OAuth2
natively.

**Decision:** Prefer native OIDC integration whenever the app supports it, over proxy-based
methods.

**Consequences:** Cleaner trust model — the app itself validates tokens/claims rather than trusting
a proxy header. Documented in [`docs/oidc-integration.md`](oidc-integration.md).

---

## ADR-006: Use proxy/forward-auth for apps without native SSO

**Context:** Many NAS admin tools and simple web apps have no OIDC support and only a built-in
login form.

**Decision:** Protect these with authentik's proxy provider / forward-auth outpost sitting in
front of the reverse proxy.

**Consequences:** Every app gets SSO even without code changes, at the cost of a stronger trust
requirement on the reverse-proxy path (see ADR-007 and
[`docs/proxy-auth-integration.md`](proxy-auth-integration.md)).

---

## ADR-007: Keep database and Redis private

**Context:** PostgreSQL and Redis hold authentik's full state, including credentials and session
data.

**Decision:** Never publish PostgreSQL or Redis ports to the host or the public internet. Only the
authentik web service is exposed, and only to `SSO_BIND_HOST:SSO_HTTP_PORT`.

**Consequences:** Reduces attack surface dramatically. Any tooling that needs DB access uses
`docker exec` / internal Docker networking, not a published port.

---

## ADR-008: Start local-only before any public exposure

**Context:** Public exposure of an identity provider carries outsized risk if misconfigured.

**Decision:** MVP defaults to `DEPLOY_MODE=local_only` and `PUBLIC_EXPOSURE=false`. Public exposure
via the operator's chosen `SSO_DOMAIN` (e.g. `auth.example.com`) is a deliberate, later,
deployer-driven step (Phase 2+).

**Consequences:** Gives time to validate authentik configuration, backups, and MFA before the
service is internet-reachable.

---

## ADR-009: Use MFA as a security-hardening step, not an MVP blocker

**Context:** Requiring MFA on day one adds friction while still validating the base deployment.

**Decision:** Document MFA/TOTP/WebAuthn as a strongly recommended post-MVP step (Phase 3/6),
enabled before any public exposure or production reliance, but not required to complete Phase 1.

**Consequences:** Keeps the MVP simple while making clear that MFA is expected before the system
is trusted for anything beyond local testing.

---

## ADR-010: Pin exact image versions instead of floating tags

**Context:** The MVP Compose file initially used floating tags (`latest`, `16-alpine`, `7-alpine`)
for convenience. A floating tag means `docker compose pull` can silently move the identity
provider, database, or cache to a new version with no review step — risky for a service that
gates access to everything else.

**Decision:** Pin `authentik`/PostgreSQL/Redis to exact versions in `docker-compose.yml` and
`.env.example` (e.g. `2026.5.4`, `16.14-alpine`, `7.4.9-alpine`), and require deliberately bumping
the pin — backing up first and reviewing release notes — per the procedure in
[`docs/security-hardening.md`](security-hardening.md) ("Image Upgrade Procedure").

**Consequences:** Upgrades become an explicit, reviewed action instead of a silent side effect of
a routine pull. Trade-off: the pin needs manual maintenance over time and won't pick up security
patches automatically — acceptable for a self-hosted, operator-controlled deployment where an
unreviewed identity-provider upgrade is the bigger risk.

---

## ADR-011: Protect wordpress-ai-publisher via native OIDC + local credentials, not forward-auth or Cloudflare Access

**Context:** Phase 4 requires picking one real NAS app to protect first. The chosen app,
`../wordpress-ai-publisher`, is a custom Next.js content-publishing tool (not WordPress itself —
it generates AI content packages and publishes them to a separate WordPress site via a companion
plugin) with **zero built-in authentication on any route**, including `/api/settings`, which
exposes/controls its OpenAI key and WordPress credentials. It's deployed via
`../synology-site-deployer`'s `deploy` command straight to a published host port, with Cloudflare
Tunnel routing directly to that port — no reverse proxy sits in front of it today, and none is
currently shared across other NAS sites.

Three options were considered:
1. **Reverse-proxy forward-auth (Pattern 2)** — this repo's usual recommendation for apps with no
   native SSO support. Rejected here because it would require standing up a new Traefik (or
   similar) reverse-proxy layer purely for this, where none exists yet, adding real new
   infrastructure for a single app.
2. **Cloudflare Access (Zero Trust)** — `../synology-site-deployer` already lists this as a
   possible future feature. Rejected because it would gate this one app behind Cloudflare's own
   identity/policy system instead of authentik, fragmenting identity across two separate systems —
   defeating the purpose of a single SSO gateway (see ADR-001).
3. **Native OIDC (Pattern 1), chosen.** `wordpress-ai-publisher` is the maintainer's own codebase,
   so adding real OIDC support is a normal, tractable code change — unlike a closed-source NAS
   tool. Native OIDC needs no reverse proxy at all: the app's own server-side code talks to
   authentik's issuer/token/userinfo endpoints directly, and Cloudflare Tunnel keeps routing
   straight to the app's existing port, unchanged.

**Decision:** `wordpress-ai-publisher` gets its own authentication, tracked in that repo's own
`TODO.md` ("Authentication (Local Credentials + Optional SSO)"), not implemented in this repo (by
design; see README "What This Project Does Not Do"): a local username/email/password login as the
always-available default (so the app works standalone for anyone who self-hosts it with no SSO
dependency), plus optional, env-gated OIDC against authentik. This repo's only remaining job is the
already-generic, already-documented authentik-side step — creating an OIDC Provider/Application for
the app once a live instance exists (see Phase 4 in `TODO.md`) — which requires no new
functionality in this repo's own Phase 1-3 stack; creating an OIDC client for a new app is
already-existing, generic authentik capability.

**Consequences:** No new infrastructure component sits between Cloudflare, authentik, and the app.
Identity stays centralized in authentik as intended for every future Phase 5 app, while
`wordpress-ai-publisher` remains independently usable without this SSO gateway at all — its own
local login is the fallback if authentik is ever unreachable, doubling as its rollback/emergency
path (disable `ENABLE_OIDC_SSO`, log in locally). Trade-off: the auth code itself (session
handling, password hashing, OIDC token exchange) now lives in an app this repo doesn't control or
test — its correctness is that repo's own responsibility, tracked in its own TODO.md.

---

## ADR-012: Narrow MFA scope to passkey (WebAuthn) only, defer TOTP/SMS

**Context:** ADR-009 established MFA as a recommended post-MVP hardening step without picking a
specific method, leaving `docs/first-sso-configuration.md`, `docs/security.md`, and
`docs/security-hardening.md` to describe TOTP, WebAuthn/passkeys, and (implicitly) SMS as
interchangeable options. The operator gave explicit direction (2026-07-14) that login should only
ever offer two things: username/password and passkey.

**Decision:** Passkey (WebAuthn) is the sole MFA/second-factor method actively documented and
pursued. TOTP-authenticator-app and SMS-based MFA are explicitly deferred — not implemented, not
documented as active steps — until the operator asks for them again, or until passkey + password
work is exhausted and nothing else is queued.

**Consequences:** Simpler, narrower guidance across the Phase 3/6 docs — passkey enrollment is
active work now, not a future flag (`ENABLE_MFA_ENFORCEMENT` — blanket requirement, method-agnostic
— remains a separate, later, future-flagged step; see `docs/future-flags.md`). Trade-off: passkey
enrollment ties a user to a physical device/platform authenticator with no TOTP fallback in scope;
recovery codes (already documented in `docs/security-hardening.md`) are the mitigation for a lost
device, not a second MFA method.
