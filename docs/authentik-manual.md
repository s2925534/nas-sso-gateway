# Authentik Manual (This Project's Usage)

This is not a full authentik manual — it covers exactly what this project needs. For anything
deeper, use the [official authentik docs](https://docs.goauthentik.io/).

## What authentik Is Used For Here

- Central login for every protected NAS app.
- OIDC/OAuth2 provider for apps you build yourself.
- Proxy provider / forward-auth outpost for apps without native SSO.
- App portal — a single page listing every app you can launch once logged in.

## First-Run Setup

1. Copy `.env.example` to `.env` and fill in real secrets (see
   [`docs/security.md`](security.md) for generation commands).
2. Run `scripts/bootstrap-sso.sh` (Phase 1) or `docker compose up -d` directly.
3. Wait for the `authentik-server` and `authentik-worker` containers to report healthy —
   authentik's first boot runs database migrations and can take a minute or two.
4. Visit `http://<SSO_BIND_HOST or localhost>:<SSO_HTTP_PORT>/if/flow/initial-setup/` to set the
   initial admin password (authentik's own first-run flow), or log in with
   `AUTHENTIK_BOOTSTRAP_EMAIL` / `AUTHENTIK_BOOTSTRAP_PASSWORD` if bootstrap env vars were set.

## Admin Account Setup

- Treat the bootstrap admin account as break-glass/administration only.
- Immediately change the bootstrap password if it was set via `.env`, then remove or rotate
  `AUTHENTIK_BOOTSTRAP_PASSWORD` from your local `.env` once a proper admin login is confirmed.
- Enable MFA on the admin account before doing anything beyond local testing.

## Creating Normal Users

- **Directory → Users → Create.** Give the user a normal (non-admin) role.
- Use normal users for day-to-day login to protected apps — never the admin account.

## Creating Groups

- **Directory → Groups → Create.** Groups are the unit of access control per app (Phase 3/5).
- Example convention: one group per app or app-tier, e.g. `app-tools-users`, `app-portainer-admins`.

## Creating Applications

- **Applications → Applications → Create.** An "Application" in authentik is the user-facing tile
  in the app portal; it wraps a Provider (OIDC or Proxy) that does the actual auth work.

## Creating OIDC Providers

- **Applications → Providers → Create → OAuth2/OpenID Provider.**
- Set the redirect URI(s) to match the app's callback path (see
  [`docs/oidc-integration.md`](oidc-integration.md)).
- Note the generated Client ID/Secret and issuer URL for the app's own configuration.

## Creating Proxy Providers

- **Applications → Providers → Create → Proxy Provider.**
- Choose **Forward auth (single application)** for one app behind its own reverse-proxy rule, or
  **Forward auth (domain level)** for multiple subdomains sharing one outpost.
- Bind the provider to an **Outpost** (Applications → Outposts) so the reverse proxy has something
  to call. See [`docs/proxy-auth-integration.md`](proxy-auth-integration.md).

## App Portal Notes

- Once a user has access (via group membership) to an application, it appears automatically on
  their authentik landing page after login — no extra portal configuration needed.

## MFA Notes

- **Directory → Users → (user) → MFA Authenticators**, or let users self-enroll from their own
  account page.
- authentik supports TOTP and WebAuthn/passkeys, but this project's scope is passkey (WebAuthn)
  only for now — see ADR-012 in [`docs/decision-log.md`](decision-log.md). Don't enroll or
  document TOTP/SMS as an active path.
- Policies can require MFA per-flow or per-group (Phase 6).

## Password Reset (Recovery Flow)

authentik ships a built-in `default-recovery-flow` (Identification → email/verification →
Prompt-for-new-password → User Write) that isn't wired up to the login page out of the box. To
surface a working "Forgot password?" option:

1. **System → Brands → (edit the active brand).** Set **Recovery flow** to `default-recovery-flow`
   (or a custom recovery flow if you've built one). This is what puts the link on the login page.
2. Also check **Flows & Stages → Flows → `default-authentication-flow` → Stage Bindings →
   (Identification stage) → Edit Stage.** Some authentik versions read the "Forgot password?" link
   from the Identification stage's own **Recovery flow** field rather than (or in addition to) the
   Brand-level one — set it there too if present, so the link shows regardless of version. Verify
   against your actual running version; this repo can't confirm the exact behavior without a live
   instance.
3. **Email delivery is required for self-service reset to actually work.** Set the
   `AUTHENTIK_EMAIL__*` variables in `.env` (see `.env.example`) to a real SMTP relay, then restart
   the stack. Without SMTP configured, the Recovery flow exists but has nothing to deliver the reset
   link with.
4. **No SMTP yet, or need to reset one user right now?** Use the existing admin-triggered path:
   **Directory → Users → (user) → "Send recovery link"** (already used for first-time account setup
   in `docs/first-sso-configuration.md` §2) — copies a one-time recovery URL you hand to the user
   directly. This works with or without SMTP configured.
5. Test end-to-end once SMTP is set: log out, click "Forgot password?" on the login page, confirm
   the email arrives, and confirm the link actually resets the password.

See ADR-013 in [`docs/decision-log.md`](decision-log.md) for why this is done via authentik's
built-in flow rather than custom code — there's no bespoke login frontend in this repo to add a
"reset password" button to.

## Branding (Login Page / "Systems Not Silos")

authentik's login/flow-executor UI is themed per-**Brand** (`System → Brands → edit the active
brand`), not by editing frontend source in this repo — there is none. Live and verified as of this
writing (`<title>Systems Not Silos</title>`, logo serving `200 image/jpeg`):

1. **Branding title** — `Systems Not Silos`. Shown in the browser tab and flow-executor UI.
2. **Default flow background** — cleared, removing authentik's stock background image.
3. **Logo** — uploaded (the real "Systems Not Silos" circular badge asset). See "Media Storage
   Prerequisite" below — this silently fails without it.
4. **Custom CSS** — brand color palette (navy `#0B1C33` / blue `#5B84B4`), plus the shadow-DOM
   fixes below. See ADR-013 in [`docs/decision-log.md`](decision-log.md) for the veloso.dev
   binary-dot signature decision (added, not skipped — the domain-generic policy was explicitly
   overridden by the operator for this specific element).

### Media Storage Prerequisite (Logo/Favicon/Background Uploads)

authentik's file-management backend (what actually powers logo/favicon/background uploads, via the
web UI *and* the API) treats a storage path as usable only if it resolves to an actual mount
point — its default (`./data`) isn't one, so uploads fail with `ImproperlyConfigured: No file
management backend configured` until `AUTHENTIK_STORAGE__MEDIA__FILE__PATH=/media` is set (already
in `docker-compose.yml`, pointing at the volume already mounted there). This is a **prerequisite
config fix**, not brand-specific — without it, brand logo uploads are broken in the *admin UI too*,
not just automation.

Separately, the host directory backing `/media` needs to be **writable by the container's runtime
user** (`uid=1000:gid=1000` for the official authentik image). If it was created some other way
(e.g. before `scripts/create-folders.sh` existed, or by hand), check its ownership/mode — it needs
to be at least `755` and owned by `1000:1000`, not the NAS's own default file-creation UID. Symptom
if wrong: uploads fail with a `PermissionError` on `os.mkdir` deep in authentik's own traceback.

### Custom CSS and Shadow DOM (Read This Before Fighting a Selector)

authentik's flow-executor UI is built from Lit web components using **Shadow DOM**. Plain CSS
selectors (e.g. `.pf-c-brand`) that look right from browser inspection often silently do nothing,
because they target markup that's actually inside a shadow root and unreachable from `branding_custom_css`
(which is injected into the light DOM). Two things actually work, plus one thing that looked like it
worked but doesn't (see the footer correction below):

- **`::part()` selectors** — authentik deliberately exposes a small set of shadow-piercing parts on
  `<ak-flow-executor>` (verified against `2026.5.4` source, `web/src/flow/FlowExecutor.ts`):
  `part="main"` (auth form container), `part="branding"` (logo container), `part="footer"`,
  `part="locale-select"` / `part="locale-select-label"` / `part="locale-select-select"` (the
  language switcher), `part="content"`, `part="content-iframe"`, `part="loading-overlay"`,
  `part="challenge-additional-actions"`, `part="challenge-footer-band"`. (An earlier version of
  this doc also listed `part="login"` — not present in `2026.5.4`'s source; likely stale from an
  older authentik version, corrected here.) Example, used live here:
  `ak-flow-executor::part(branding) { max-height: 64px; max-width: 200px; object-fit: contain; }`
  — fixes an oversized logo hiding form fields, which a `.pf-c-brand` rule could not.
- **CSS custom properties** (`--ak-*`/`--pf-*`) inherit through shadow boundaries normally, so
  `:root { --something: ...; }` works if the component reads that variable internally — but there's
  no comprehensive documented list of which properties exist; `::part()` is the more reliable path.
- **`::part()` cannot be followed by a descendant combinator or structural pseudo-class** (e.g.
  `::part(footer) li:last-child`) — per the CSS Shadow Parts spec, `::part()` must be the rightmost
  compound selector; chaining a combinator after it makes the whole rule invalid, and browsers drop
  it silently rather than erroring. An earlier version of this doc recommended exactly that pattern
  for the footer, believed at the time to be "used live" — it was not; see the correction below.

There is **no way to remove "Powered by authentik"** from the footer — confirmed by reading
authentik's actual frontend source at the pinned `2026.5.4` tag. The component is
`web/src/flow/components/ak-brand-footer.ts`, but it defines a custom element named
**`ak-brand-links`** (not `ak-brand-footer` — the filename is stale relative to the export), and,
critically, it **opts out of Shadow DOM** (`createRenderRoot() { return this; }`), rendering its
`<ul>`/`<li>` footer entries as ordinary **light DOM** — slotted directly into
`<ak-flow-executor>` from `authentik/flows/templates/if/flow.html` as
`<ak-brand-links name="flow-links" slot="footer">`. `render()` unconditionally appends
`{ name: msg("Powered by authentik"), href: null }` after the tenant's own configured links, with
no prop/attribute/config flag to suppress it — same conclusion as before, but now source-confirmed
at the pinned tag along with the corrected component name and DOM placement.

**Because `ak-brand-links` has no shadow root, its footer `<li>` entries are reachable with plain
CSS — no `::part()` needed at all.** Since "Powered by authentik" is appended last (after the
tenant's own `footer_links`), `ak-brand-links li:last-child` is the correct, spec-valid selector to
hide it — see the corrected CSS block under Footer Links below.

The **locale/language switcher** (native to authentik, easily mistaken for a "Google Translate"
widget — no such third-party widget is used anywhere in this deployment) can be restyled via the
`locale-select*` parts above for contrast/visibility, but **cannot be changed to show flag icons
instead of language names, and there's no config to disable it** — this is a confirmed upstream
authentik limitation (its internal rendering isn't exposed via any part or prop), not a gap in this
repo's config. See [goauthentik/authentik#19506](https://github.com/goauthentik/authentik/issues/19506).

### Footer Links (Including the veloso.dev Signature)

Counter-intuitively, footer links are **not** a Brand field — despite appearing in the frontend
config as `ui_footer_links`, they're sourced from the current **Tenant**'s `footer_links` JSONField
(`authentik.tenants.models.Tenant`, via `get_current_tenant()`), a separate model from Brand —
confirmed at the pinned tag via `authentik/tenants/models.py` and
`authentik/brands/api.py:get_default_ui_footer_links()`. Set via `ak shell` (no dedicated admin-UI
form found for this field as of this writing):

```python
from authentik.tenants.utils import get_current_tenant
tenant = get_current_tenant()
tenant.footer_links = [
    {"name": "·", "href": None},  # veloso.dev binary-dot signature -- see below
    {"name": "Powered by Systems Not Silos", "href": None},
    {"name": "Contact Support (coming soon)", "href": None},  # update once a real page exists
]
tenant.save()
```

Each entry renders as an `<li>` (or `<a>` if `href` is set) as a **light-DOM child of
`ak-brand-links`** (not inside any shadow root, and not reachable via `::part(footer)` — see above).
Rendered DOM order is: the tenant's own `footer_links`, in the order set above, followed by the
client-side-appended "Powered by authentik" entry — making `ak-brand-links li:last-child` the
correct target for that entry, and `ak-brand-links li:first-child` the correct target for the
veloso.dev dot signature (the first tenant-configured entry). **Never use a `mailto:` href for
anything in this ecosystem** (operator policy) — link to a real contact-form page instead once one
exists; a bare `{"name": "...", "href": None}` entry with no href is the correct interim
placeholder.

**Corrected custom CSS for the footer** (replaces the spec-invalid `::part(footer) li:...` rules
from an earlier version of this doc — those had no effect since `::part()` can't take a descendant
combinator):

```css
/* "Powered by authentik" cannot be removed from the underlying data (see above), but since
   ak-brand-links renders in the light DOM, plain CSS can hide the rendered <li> -- unlike the
   footer_links JSONField, this leaves no trace in the accessibility tree either, since
   display:none (unlike opacity/visibility tricks) removes a node from the a11y tree. */
ak-brand-links li:last-child { display: none !important; }

/* veloso.dev binary-dot signature: 80-bit ASCII-to-binary encoding of "veloso.dev", rendered as
   80 small box-shadow dots (filled = 1, low-opacity = 0). Hides the literal "·" text and
   renders the dots instead via a pseudo-element. */
ak-brand-links li:first-child {
  position: relative;
  color: transparent;
  user-select: none;
  pointer-events: none;
}
ak-brand-links li:first-child::after {
  content: "";
  display: inline-block;
  width: 1px;
  height: 1px;
  box-shadow: 0px 0 0 rgba(120,120,120,.12), 5px 0 0 rgba(120,120,120,.55) /* ...80 dots total, unchanged from the original encoding... */;
}
```

**Known accessibility limitation** (applies only to the veloso.dev entry, since "Powered by
authentik" above is fully removed from the a11y tree via `display: none`): authentik's
`footer_links` schema has no `aria-hidden` equivalent, so a screen reader will still announce
whatever text is in `name` for the dot-signature entry — the `color: transparent` trick hides it
visually only. Using a single minimal-width character (rather than a long decorative label) was the
deliberate mitigation chosen here; a fully invisible-to-AT implementation isn't possible through
this integration point.

**Not yet re-verified live against this correction** — the previous (spec-invalid) CSS was
confirmed still present in the live `branding_custom_css` as of this session, meaning "Powered by
authentik" was likely still visible and the dot signature likely wasn't rendering. Apply the
corrected block above via **System → Brands → edit the active brand → Custom CSS** next time you're
in the admin UI, then reload the login page to confirm both fixes visually.

### Flow Title, Logo Position, and the "Hover to Reveal" Report

The "Welcome to authentik!" (here: "Welcome to Systems, Not Silos!") heading is not Brand-level —
it's the `title` field on the Flow object itself (`Flow.objects.get(slug="default-authentication-flow")`),
set independently per flow, and rendered by a completely different component
(`web/src/flow/components/ak-flow-card.ts`) than the logo. Structurally, per `FlowExecutor.ts`'s
`render()`, the logo (`part="branding"` div) and the challenge content (which starts with the title
`<h1>`, inside `ak-flow-card`) are **siblings inside `<main part="main">`, in that order** — meaning
the title already renders *after* (visually: below) the logo by default DOM order, with no
overlap in the source.

An operator report during this session described the title only becoming visible when hovering
over the logo. Source review (both authentik's bundled `flow-*.css` and this deployment's live
`branding_custom_css`) found **no `opacity`, `position: absolute`/`z-index`, `:hover`, or native
`title`-attribute tooltip rule anywhere** that would explain that behavior — the logo `<img>` (via
`ThemedImage()`) doesn't even set an HTML `title` attribute. This doesn't rule out the report (a
live visual bug can exist without a static source/CSS explanation — e.g. a transient rendering
glitch, a devtools artifact, or something version/browser-specific), but there's no fix to make
here without seeing it happen live. **Needs a live re-check** (hard refresh, devtools closed) before
writing any CSS for it — the two changes above (footer correction, theme toggle below) are safe to
ship regardless of this open item, since neither touches the branding/title layout.

### Login-Page-Only Theme Toggle (Light / Dark / System)

Scope, deliberately narrow: this affects **only the login/flow-executor pages** (anything rendered
via `if/flow.html`, e.g. the authentication and recovery flows). It does **not** touch authentik's
own theme mechanism, which is a separate, native, already-working light/dark/auto picker (Brand
default + per-user account settings) that also governs the **post-login** interface (User/Admin
apps) — that native mechanism is intentionally left alone; this login-only toggle **must not**
share its storage key or DOM attribute, or a preference set on the login page would leak into the
authenticated interface after signing in, which is explicitly out of scope. See ADR-014 in
[`docs/decision-log.md`](decision-log.md).

authentik's native mechanism (`authentik/core/templates/base/theme.html`, `web/src/common/theme.ts`,
confirmed at the pinned tag) reads/writes `localStorage["theme"]` and sets
`data-theme-choice`/`data-theme` on `<html>`, which authentik's own `colors-dark.css` keys off of
site-wide. This toggle intentionally uses **its own, independent** key (`sns-login-theme`) and
attribute (`data-sns-login-theme`), and its CSS is scoped to `.pf-c-login`/`.pf-c-title`/etc. —
classes that exist only on flow/login pages — so there is no shared state with, and no possibility
of bleeding into, the post-login UI even though the attribute technically lives on the shared
`<html>` element.

Implementation requires actual JS (a click handler + persistence), which `branding_custom_css`
cannot provide (CSS only) — it's delivered via a **Django template override**, mounted through the
`/templates` volume already wired in `docker-compose.yml`
(`${SSO_BASE_PATH}/authentik/custom-templates:/templates`). Although authentik's own docs only
describe `/templates` for the Email stage, `authentik/root/settings.py`'s Django `TEMPLATES`
config sets a global `DIRS`+`APP_DIRS` filesystem loader that checks `/templates` **before**
authentik's own bundled templates for every Django-rendered page, including `if/flow.html` — so an
override placed at `custom-templates/if/flow.html` takes precedence, without touching
`base/skeleton.html` (which is shared by the post-login interfaces too, and must **not** be
overridden for this).

The override file is version-controlled in this repo at
[`authentik-custom-templates/if/flow.html`](../authentik-custom-templates/if/flow.html) — a
minimal diff from authentik's own `authentik/flows/templates/if/flow.html` at the pinned
`2026.5.4` tag, adding only: an anti-flash-of-wrong-theme init script in `{% block head %}`, and a
toggle button + its click-handler script at the end of `{% block body %}`. To deploy it:

```bash
mkdir -p "${SSO_BASE_PATH}/authentik/custom-templates/if"
cp authentik-custom-templates/if/flow.html "${SSO_BASE_PATH}/authentik/custom-templates/if/flow.html"
```

then restart the `authentik-server`/`authentik-worker` containers. **Upgrade caveat**: because this
is a full-file override, it will not automatically pick up authentik's own changes to
`if/flow.html` across version bumps — diff it against the new tag's version as part of the upgrade
procedure in `docs/security-hardening.md` ("Image Upgrade Procedure") whenever `AUTHENTIK_TAG`
changes.

Add the toggle button's own styling to the Brand's Custom CSS field alongside the corrected footer
CSS above:

```css
:root[data-sns-login-theme="dark"] .pf-c-login {
  background: linear-gradient(135deg, #0B1220 0%, #10192b 100%);
}
:root[data-sns-login-theme="dark"] .pf-c-login__main,
:root[data-sns-login-theme="dark"] .pf-c-login__main-body {
  background-color: rgba(11, 18, 32, 0.94);
}
:root[data-sns-login-theme="dark"] .pf-c-title,
:root[data-sns-login-theme="dark"] h1,
:root[data-sns-login-theme="dark"] h2 {
  color: #eaf0f8;
}
:root[data-sns-login-theme="dark"] a,
:root[data-sns-login-theme="dark"] a:visited {
  color: #9db9dd;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-sns-login-theme="light"]):not([data-sns-login-theme="dark"]) .pf-c-login {
    background: linear-gradient(135deg, #0B1220 0%, #10192b 100%);
  }
  :root:not([data-sns-login-theme="light"]):not([data-sns-login-theme="dark"]) .pf-c-login__main,
  :root:not([data-sns-login-theme="light"]):not([data-sns-login-theme="dark"]) .pf-c-login__main-body {
    background-color: rgba(11, 18, 32, 0.94);
  }
  :root:not([data-sns-login-theme="light"]):not([data-sns-login-theme="dark"]) .pf-c-title,
  :root:not([data-sns-login-theme="light"]):not([data-sns-login-theme="dark"]) h1,
  :root:not([data-sns-login-theme="light"]):not([data-sns-login-theme="dark"]) h2 {
    color: #eaf0f8;
  }
}

.sns-theme-toggle {
  position: fixed;
  top: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  color: var(--sns-navy);
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 0.375rem;
  opacity: 0.7;
  cursor: pointer;
  z-index: 1000;
}
:root[data-sns-login-theme="dark"] .sns-theme-toggle { color: #eaf0f8; }
.sns-theme-toggle:hover { opacity: 1; }
```

Cycle order matches the convention used elsewhere (e.g. `zqx`): `system → light → dark → system`,
persisted in `localStorage["sns-login-theme"]` (absent = system), sun/moon/monitor SVG icons,
`aria-label`/`title` announcing current and next state. **Not yet deployed or verified live** — no
Docker access from this sandbox; copy the template file, paste the CSS, restart the containers, and
click through all three states next time you're at the NAS.

## Creating an API Token for Automation

For scripted/read-only checks against a live instance (e.g. `scripts/check-app-access.sh`)
instead of clicking through the UI each time:

- **Quick (token on your existing admin account):** top-right user menu → your account →
  **Tokens** (or **Directory → Tokens → Create** in the admin interface). Create a token with
  intent **API**. Store the key in `.env` as `AUTHENTIK_BOOTSTRAP_TOKEN` (already gitignored).
- **Scoped (recommended once you have more than one automated check):** create a dedicated
  non-superuser user (**Directory → Users → Create**, e.g. `automation`), create a **Role**
  (**Directory → Roles** or **System → Roles**, depending on version) granting only the view
  permissions the checks need (e.g. `authentik_core.view_application`,
  `authentik_core.view_provider`, `authentik_core.view_group`,
  `authentik_policies.view_policybinding`), assign that role to the user, then create its token
  the same way. A leaked scoped token can only read, not modify or impersonate.
- Either way, the token only needs to live in this repo's own gitignored `.env` — never commit it,
  never paste it anywhere public.

## Backup Notes

- authentik state lives in PostgreSQL (users, apps, providers, policies) and in
  `${SSO_BASE_PATH}/authentik/media` (uploaded assets) plus
  `${SSO_BASE_PATH}/authentik/custom-templates` (if used).
- `scripts/backup-sso.sh` captures these; see [`scripts/restore-notes.md`](../scripts/restore-notes.md)
  for the restore procedure and its caveats.

## Upgrade Notes

- The authentik image tag is pinned to an exact version (`AUTHENTIK_TAG` in `.env`/`docker-compose.yml`)
  rather than tracking a `latest` floating tag — see ADR-010 in
  [`docs/decision-log.md`](decision-log.md) and the upgrade procedure in
  [`docs/security-hardening.md`](security-hardening.md) ("Image Upgrade Procedure").
- Read authentik's release notes before upgrading across minor versions — some releases include
  required migration steps.
- Always back up before upgrading.
