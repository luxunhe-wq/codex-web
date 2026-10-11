# Security policy and deployment boundaries

This is a single-administrator browser interface for Codex running on your Linux account.
Authenticated users can change execution permissions and operate files accessible to that
account. Web authentication is not an OS sandbox or isolation between tenants.

## Defaults and protections

- New databases use project-scoped write access and on-request approvals; saved settings are preserved.
- The server defaults to localhost:8080. Use a normal Linux account and HTTPS for public access.
- Remote/proxy deployments create the administrator locally with `--init-admin`; remote web registration is rejected.
- Passwords use salted PBKDF2-SHA256; SQLite stores hashes of session tokens.
- HttpOnly/SameSite cookies, CSRF checks, Host/Origin validation and CSP protect browser requests.
- Login failures persist in SQLite; six failures lock new login for six minutes.
- Sessions persist for 30 days and renew on ordinary authenticated requests. Logout/password changes revoke tokens.
- File previews reject credential paths, symlinks, hardlinks, nonregular files and excessive sizes.
- Uploaded files are private; ordinary files download as attachments, not executable HTML.
- Document parsing runs with CPU/memory/output/time and archive-expansion limits.
- Connection count, socket timeouts and request framing checks bound resource consumption.
- New data directories are mode 700, data files mode 600; generated services use UMask 0077.

These controls are covered by API and simulated browser regressions. They do not constitute
an external penetration test, guarantee against every denial-of-service attack or replace
provider-side protections. A background event stream alone does not renew the login.

## Deployment responsibility

Do not expose an uninitialized application through an unconfigured proxy. Create the
administrator first, then configure the allowed domain and HTTPS cookies. Keep the backend
port private. The first loopback user can register through the local UI before initialization.
People with access to your Linux account already have access to its Codex configuration.

Build/test commands and model tools operate with the service user's permissions. Avoid
running as root. Only grant full-server access deliberately. The model/provider and uploaded
content are external inputs; review execution approvals. Login locking is shared by the
single account, so an attacker may temporarily prevent new logins.

Backups contain private account data, project names, history and attachments; keep them
outside Git. Do not publish Codex auth/configuration files, environment secrets or screenshots
of real conversations. The release scanner detects known patterns, not every possible secret.

## Reporting a vulnerability

Use GitHub private vulnerability reporting once enabled on the published repository. Until
then, contact the repository maintainer privately through their GitHub profile; do not post
credentials or exploit details in public issues. No private reporting address is bundled yet.
