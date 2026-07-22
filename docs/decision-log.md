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

---

## ADR-013: Add the veloso.dev binary-dot signature to the login footer, as an explicit exception to the domain-generic policy

**Context:** This repo has a longstanding, deliberate policy of staying domain-generic — no
`veloso.dev` references anywhere except the README's "Developer / Contact" line — so the repo
stays reusable by other operators and doesn't hardcode a brand that isn't this deployment's own
(`Systems Not Silos`, at `sso.systemsnotsilos.com`). Separately, the operator's standard convention
(see global frontend conventions) requires a veloso.dev binary-dot signature on every frontend page
and app, including client/contract work. These two policies conflict for this project's login page.

**Decision:** The operator explicitly overrode the domain-generic policy for this one element: the
login page's footer carries a veloso.dev binary-dot signature (80-bit ASCII-to-binary encoding of
"veloso.dev", rendered as CSS `box-shadow` dots), added as a minimal `"·"` entry in the Tenant's
`footer_links` alongside the "Powered by Systems Not Silos" and contact-form entries (see
`docs/authentik-manual.md`, "Footer Links"). The rest of the repo's domain-generic policy is
unchanged — this is a narrow, deployment-side branding exception, not a reversal of the policy.

**Consequences:** The signature lives in live Tenant/Brand configuration (set via `ak shell` or the
admin UI), not in this repo's git-tracked source — so the domain-generic policy for the repo itself
still holds; only the live deployment's rendered login page carries the mark. Known limitation:
authentik's `footer_links` schema has no `aria-hidden` equivalent, so a screen reader still
announces the entry's `name` text even though it's visually minimized to a single character — full
accessibility-tree invisibility isn't achievable through this integration point.

---

## ADR-014: Login-page-only theme toggle via a scoped template override, not authentik's native theme mechanism

**Context:** The operator wants a single light→dark→system cycling theme button on the login page
(matching the convention used in the `zqx` project), plus removal of the "Powered by authentik"
footer text and a corrected footer/veloso.dev-signature CSS selector (the previously-documented
`ak-flow-executor::part(footer) li:...` rules turned out to be spec-invalid — `::part()` can't take
a descendant combinator per the CSS Shadow Parts spec, so those rules were likely inert; see
`docs/authentik-manual.md` for the corrected selectors). The operator was explicit and emphatic that
this toggle must affect **only** the login/flow-executor pages — not authentik's own post-login
interface (User/Admin), which already has its own native light/dark/auto picker exposed via Brand
defaults and per-user account settings. authentik's native mechanism reads/writes a single
site-wide `localStorage["theme"]` key and `data-theme`/`data-theme-choice` attributes on `<html>`
(`authentik/core/templates/base/theme.html`, `web/src/common/theme.ts`), so naively hooking a login
button into that same mechanism would leak the login-page preference into the authenticated
interface after signing in — explicitly not wanted.

**Decision:** Implement the toggle with its own, independent storage key
(`localStorage["sns-login-theme"]`) and DOM attribute (`data-sns-login-theme`), never touching
authentik's own `theme`/`data-theme`/`data-theme-choice`. Because `branding_custom_css` is CSS-only
and can't carry the required `<script>`/`<button>` markup, the toggle is delivered via a Django
template override of `if/flow.html` (the flow-executor page template only — not
`base/skeleton.html`, which is shared with the post-login interfaces and must not be touched),
mounted through the `/templates` volume already wired in `docker-compose.yml`. The override,
version-controlled at [`authentik-custom-templates/if/flow.html`](../authentik-custom-templates/if/flow.html),
is a strict superset of authentik's own `if/flow.html` at the pinned `2026.5.4` tag — confirmed via
a line-level diff showing only additive lines, no changes or deletions to any of authentik's
original template content. The footer fix (`ak-brand-links li:last-child` to hide "Powered by
authentik", `ak-brand-links li:first-child` for the veloso.dev signature) is a `branding_custom_css`
correction only, requiring no template change.

**Consequences:** The login page gets independent theming without risk of altering the
authenticated interface's appearance, and without patching authentik's own compiled JS/CSS. Trade-off:
a full-file template override means authentik's own future changes to `if/flow.html` won't
propagate automatically — each `AUTHENTIK_TAG` bump needs a manual re-diff (documented in
`docs/security-hardening.md`, "Image Upgrade Procedure") to catch upstream changes this override
would otherwise silently miss. Not yet deployed or visually verified against the live instance as
of this decision — no Docker access from the sandbox this was written in.

---

## ADR-015: Fix logo/title overlap via `transform: scale()`, not `max-height`, on the branding part

**Context:** A browser screenshot taken 2026-07-22 (this repo's first actual visual check of the
live login page, as opposed to `curl`/source review) confirmed a real bug: the flow title ("Welcome
to Systems, Not Silos!") overlapped the logo. The existing custom CSS set
`max-height: 56px !important` on `ak-flow-executor::part(branding)` — the logo's wrapper `<div>` —
believing this would shrink the logo. It didn't: the wrapper div's own box respected the cap
reasonably well, but the `<img>` inside it kept rendering at its full intrinsic size (~122px),
overflowing the div and overlapping the title below. This is a general CSS fact, not an
authentik-specific bug: a parent's `max-height`/`height` does not constrain a child's own rendered
size unless the child is explicitly sized relative to the parent (e.g. `height: 100%`) — and here,
the child (`<img>`) cannot be targeted directly, since `::part(branding)` is the div, and a
descendant combinator after `::part()` is invalid per the CSS Shadow Parts spec (same limitation
already documented for the footer in ADR-013-era work).

**Decision:** Use `transform: scale()` on `ak-flow-executor::part(branding)` instead of
`max-height`/`overflow: hidden`. A CSS transform repaints the *entire* subtree of the transformed
element, regardless of shadow-DOM boundaries or descendant-selector restrictions — so it can
visually shrink the logo without needing to reach the `<img>` itself, and without cropping any of
the image's content. First attempt used `scale(0.46)` with `overflow: hidden` and a fixed
`height: 56px`, sized to match the original (wrong) 56px target; the operator reported it visually
too small and appearing "cut" at the bottom. Corrected to `scale(0.68)` with `transform-origin: top
center` and no `overflow`/fixed `height` (transform alone is sufcient; clipping isn't needed since
nothing needs to be cropped), plus a negative `margin-bottom` to close the layout gap left by the
wrapper div's own box not shrinking (transforms don't affect layout size, only paint). Verified live
via browser screenshot after each iteration.

**Consequences:** Logo renders at a reasonable size, fully visible (including its "SYSTEMS NOT
SILOS" text), with no overlap with the title. Trade-off: the exact scale/margin values (`0.68`,
`-30px`) are tuned to this specific logo asset's aspect ratio and the current flow-card layout —
they are not a generic formula, and would need re-tuning if the logo asset or authentik's own flow
layout changes materially (e.g. a future `AUTHENTIK_TAG` bump). This is the same
full-file/full-value re-tuning risk already noted for the template override in ADR-014, extended to
this CSS value pair.

## ADR-016: Favicon reuses the existing logo asset, downscaled for lightweight delivery

**Context:** The Brand's `branding_favicon` field was still pointing at authentik's own stock icon
(`/static/dist/assets/icons/icon.png`) — no "Systems Not Silos" favicon had been set. The operator
asked for one sourced from the existing logo, explicitly downscaled rather than reusing the
full-size asset directly (the source logo is a 1254×1254 JPEG, ~89KB — too heavy for a favicon,
which browsers fetch on every page load and often cache poorly).

**Decision:** Generate a dedicated favicon asset from the existing logo rather than pointing
`branding_favicon` at the same file used for `branding_logo`: downscaled to a multi-resolution
`.ico` (16×16, 32×32, 48×48) for broad browser/OS compatibility, ~7.9KB. Uploaded to the same
`media/public/` storage location as the logo (`systemsnotsilos-favicon.ico`), matching the existing
asset-naming convention, and set via the same `ak shell`/Django-ORM path used for the other live
Brand/CSS changes this session (no admin-UI session available). Ownership set to match the
container's runtime user (`1000:1000`), same as the existing media directory — the login user's own
SFTP session doesn't have write access there, unlike `custom-templates`, so this went through a
root-privileged (`sudo`) write instead.

**Consequences:** Favicon now shows the actual brand mark instead of authentik's stock icon, at a
size appropriate for how favicons are actually used (small, frequently-fetched, rarely
zoomed-in-on) rather than the full marketing-quality source asset. Neither the source logo nor the
generated favicon are committed to this repo (consistent with the existing "don't commit brand
image assets" policy — see the Branding section of `docs/authentik-manual.md`) — both live only in
the NAS's own media storage, per-deployment.

---

## ADR-017: Add `contact-relay`, this repo's first bespoke backend service

**Context:** The operator asked for a "Contact Support" link on the login page that opens a form
(sender email + message) and emails it to an admin inbox. Sending email requires server-side logic
— something has to receive the submission and talk to an SMTP relay. This repo has had zero
bespoke code until now: every service in `docker-compose.yml` wraps a third-party image
(authentik, PostgreSQL, Redis), and every prior customization (theme toggle, footer/branding CSS)
was achievable through authentik's own template-override/custom-CSS mechanisms, requiring no new
server-side component. A contact form's email-sending step has no equivalent hook — authentik has
no generic, safe-to-expose-unauthenticated "send arbitrary email" endpoint, and building one by
patching authentik itself would be a far more invasive, upgrade-fragile change than adding one
small, independent service.

**Decision:** Add `contact-relay/`, a minimal Flask service with a single `POST /send` endpoint,
built and published by this repo's own CI (`.github/workflows/contact-relay-publish.yml`) to GHCR,
and run as a new `contact-relay` service in `docker-compose.yml`. Deliberately *not* pinned to an
exact version like authentik (ADR-010) — since this is code this repo owns and controls, it tracks
`:latest` with a Watchtower label, matching the convention used for this project's own code
elsewhere in the operator's ecosystem (e.g. `wordpress-ai-publisher`), rather than the
pin-third-party-images posture used for authentik/PostgreSQL/Redis. Security posture, given this is
a new **unauthenticated, public-facing** endpoint: strips CR/LF from user input (prevents SMTP
header injection), never uses visitor-supplied input as the SMTP `From` (uses a fixed configured
address, with the visitor's address only in `Reply-To` — avoids the receiving mail server rejecting
or spam-filtering a spoofed `From`), fixed non-user-controllable subject and destination
(`CONTACT_ADMIN_EMAIL`, an operator-set env var — never taken from the request), and a simple
in-memory per-IP rate limit as a casual anti-spam measure (explicitly not a hard security control —
documented as such, resets on container restart).

**Consequences:** This is a real, if small, expansion of what this repo is — it now has application
code to review, patch, and maintain, not just configuration and docs. It also introduces a new
public attack surface (an unauthenticated form endpoint) that didn't exist before, which is why the
input-sanitization and rate-limiting above aren't optional extras. Deliberately staged so the live
login page never shows a non-functional "Send" button: the footer link's text/href and the
contact-form CSS are pushed live only *after* the service is actually deployed and reachable — see
"Deployment sequence" in `docs/authentik-manual.md`, "Contact Support Form". As with `contact-relay`
itself, its own SMTP credentials (`CONTACT_EMAIL__*`) are kept separate from authentik's
(`AUTHENTIK_EMAIL__*`) so rotating one relay's credentials can never silently break the other.

**Update, 2026-07-22:** the container is deployed and running (`sso-contact-relay`, healthy,
`/health` returns `200` on the NAS's own loopback). `CONTACT_EMAIL__*` (SMTP) was left unset,
identical to `AUTHENTIK_EMAIL__*`'s current state — no real relay credentials exist yet, so
`/send` will 502 on every call until they're added. The footer link/CSS are still deliberately not
live. See TODO.md for the remaining steps.
