# Future Flags

These are documented, planned capabilities — not implemented in the MVP. They give a shared
vocabulary for what "later" means, and a place to link phase/security docs to a specific concept.
None of these are read by any script in this repo today; they are planning flags, not env vars,
unless a specific env var already exists for one (e.g. `PUBLIC_EXPOSURE`, `DEPLOY_MODE`).

| Flag | Meaning |
|---|---|
| `ENABLE_DEPLOYER_DOMAIN_MANAGEMENT` | Allow an external deployment tool of your choice (e.g. `../synology-site-deployer`, or any reverse-proxy/tunnel tooling) to manage DNS, Cloudflare, tunnel, reverse proxy, certs, and hostname exposure for this service. |
| `ENABLE_PUBLIC_AUTH_DOMAIN` | Expose authentik at your chosen `SSO_DOMAIN` (e.g. `auth.example.com`) through whatever external tooling you use. |
| `ENABLE_MFA_ENFORCEMENT` | Require MFA for all users, or for selected groups. |
| `ENABLE_WEBAUTHN_PASSKEYS` | Support WebAuthn/passkeys as a stronger authentication method. |
| `ENABLE_OIDC_APP_TEMPLATES` | Create reusable templates for adding OIDC clients to future apps. |
| `ENABLE_PROXY_AUTH_TEMPLATES` | Create reusable forward-auth templates for apps without OIDC support. |
| `ENABLE_APP_PORTAL` | Use authentik as an app launcher/portal for NAS apps. |
| `ENABLE_GROUP_BASED_ACCESS` | Use groups to control per-application access. |
| `ENABLE_ADMIN_BREAK_GLASS` | Create emergency admin recovery and bypass documentation/tooling. |
| `ENABLE_BACKUP_AUTOMATION` | Automate backups of authentik data and the database (beyond the manual `scripts/backup-sso.sh`). |
| `ENABLE_RESTORE_TESTING` | Regularly test the restore process before relying on the SSO service in production. |
| `ENABLE_AUDIT_LOG_REVIEW` | Regularly review login, access, and admin activity logs. |
| `ENABLE_EXTERNAL_IDENTITY_PROVIDERS` | Allow login through external identity providers later if needed. |
| `ENABLE_LDAP_SUPPORT` | Add LDAP support later if needed. |
| `ENABLE_SAML_SUPPORT` | Add SAML support later if needed. |
| `ENABLE_API_AUTH_GATEWAY` | Use authentik/OIDC for custom API authorization. |
| `ENABLE_SERVICE_ACCOUNTS` | Create machine-to-machine auth patterns for apps and automations. |
| `ENABLE_PORTABLE_LOCAL_SSO_LAB` | Allow this SSO lab to run locally on any computer for testing, fully decoupled from the NAS. |

See [`docs/phase-plan.md`](phase-plan.md) for which phase each of these belongs to.

Image version pinning (previously listed here) is done — `docker-compose.yml` and `.env.example`
now pin exact authentik/PostgreSQL/Redis versions, with the upgrade procedure documented in
[`docs/security-hardening.md`](security-hardening.md) ("Image Upgrade Procedure").
