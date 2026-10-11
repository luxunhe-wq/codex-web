# Linux deployment

Use a normal Linux account with access only to the projects it should operate on.
Install and authenticate Codex under that same account; the web password is separate.
The Python server starts Codex on demand and inherits the configured environment.

For Docker Compose, see [Docker deployment](DOCKER.md) / [中文 Docker 说明](DOCKER.zh-CN.md).
The image includes Codex CLI; configure authentication inside its persistent Codex volume first.

## Local and SSH access

The default listener is `127.0.0.1:8080`. Use an SSH tunnel for a remote machine:

```sh
ssh -N -L 8080:127.0.0.1:8080 your-user@your-server
```

Visit localhost:8080 on your computer. Do not change Secure Cookie to 1 for this HTTP tunnel.

## User service

Run `python3 scripts/install.py` from your checkout. It creates a venv, keeps an existing
`.env`, and generates `~/.config/systemd/user/codex-web.service` with absolute paths.
Run `systemctl --user status codex-web` and `journalctl --user -u codex-web` for diagnostics.
An administrator may enable boot/logout persistence using `loginctl enable-linger your-user`.
The root-level `codex-web.service` is an example, not this server's deployment file.

## HTTPS with Caddy

1. Create the administrator locally using `.venv/bin/python server.py --init-admin`.
2. Point your domain to the server and allow TCP 80/443 in the cloud firewall for Caddy.
3. Keep the application listener on localhost. In `.env` set:

   ```dotenv
   CODEX_WEB_HOST=127.0.0.1
   CODEX_WEB_PORT=8080
   CODEX_WEB_ALLOWED_HOSTS=codex.example.com
   CODEX_WEB_SECURE_COOKIE=1
   ```

4. Install Caddy and use `deploy/Caddyfile.example`, replacing the domain.
5. Restart the user service after active tasks finish, and visit `https://codex.example.com`.

Caddy handles TLS and streams responses without buffering. It must forward the original
Host; the application deliberately ignores untrusted forwarded headers. DNS, certificate
issuance and your cloud firewall are managed separately. Do not expose the backend port.
A browser accessing plain HTTP will not send Secure cookies.

## Backup and upgrade

Stop new work, wait for running tasks to finish, then stop the user service. Back up the
whole configured data directory (SQLite database and attachments) outside the repository,
plus Codex's own history/configuration using your existing private backup process. Pull the
new code, install requirements and start the service. Restore matching code, dependencies
and the data backup if rollback is necessary.

For an automated idle restart on systemd, `scripts/restart_when_idle.py` supports
`--user`, `--service`, `--database` and `--port`. Run it in a separate process/service:

```sh
systemd-run --user --unit=codex-web-upgrade --collect \
  .venv/bin/python scripts/restart_when_idle.py \
  --user --database /absolute/path/to/data/web.sqlite3 --port 8080
```

Use absolute paths for the Python executable and script when invoking it from another directory.
The helper waits for all conversations to be idle, backs up SQLite and health-checks the restart.
This database backup does not include attachments; retain full-directory backups separately.

## Troubleshooting

- `codex` not found: use `CODEX_WEB_CODEX_BIN` with its absolute path or rerun the installer.
- Model connection fails: verify Codex works from a terminal under the service user; check network/provider configuration.
- Login fails only behind a proxy: verify the allowed hostname, HTTPS and Secure Cookie match.
- First-time account setup rejected: use `--init-admin` locally; remote registration is intentionally unavailable.
- User systemd bus unavailable: use the foreground command and your preferred supervisor.
- Browser tests need Chromium: run `python -m playwright install chromium`, or set `CHROMIUM_PATH`.
- Upload/PDF limits: split oversized documents; extraction is bounded in a subprocess.

This version is for a single trusted administrator. It does not isolate multiple tenants,
package a model or include credentials. Native and Docker Compose deployments are supported.
