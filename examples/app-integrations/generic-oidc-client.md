# Generic OIDC Client Example

A technology-agnostic sketch of wiring an app to authentik via OIDC (Pattern 1). Substitute your
framework's own OIDC/OAuth2 library — this is not runnable code, just the shape of the
configuration.

## 1. Create the Provider in authentik

Applications → Providers → Create → OAuth2/OpenID Provider:

- **Redirect URI:** `https://app.example.com/oauth/callback`
- **Scopes:** `openid profile email` (add `groups` if the app needs role/group data)

Note the generated **Client ID**, **Client Secret**, and issuer URL, e.g.:

```
https://auth.veloso.dev/application/o/app-example/
```

## 2. Configure the App

Most OIDC libraries want roughly this shape (illustrative, not a specific SDK):

```env
OIDC_ISSUER_URL=https://auth.veloso.dev/application/o/app-example/
OIDC_CLIENT_ID=<from authentik>
OIDC_CLIENT_SECRET=<from authentik>
OIDC_REDIRECT_URI=https://app.example.com/oauth/callback
OIDC_SCOPES=openid profile email
```

## 3. Verify Discovery

```bash
curl https://auth.veloso.dev/application/o/app-example/.well-known/openid-configuration
```

Confirms the issuer, authorization/token/userinfo endpoints, and supported scopes/claims.

## 4. Test the Flow

1. Visit the app; it should redirect to `auth.veloso.dev` for login.
2. Log in (and complete MFA if enabled).
3. Confirm redirect back to `OIDC_REDIRECT_URI` with a valid session in the app.
4. Confirm the app can read expected claims (`email`, `groups`, etc.) from the ID token/userinfo.

See [`docs/oidc-integration.md`](../../docs/oidc-integration.md) for the full onboarding checklist
and security notes.
