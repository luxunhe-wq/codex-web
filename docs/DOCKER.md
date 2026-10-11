# Docker deployment

[中文](DOCKER.zh-CN.md) | [English home](README.en.md)

Use Docker Engine and Docker Compose v2 on Linux. The image includes Python, Node.js, Git and
Codex CLI 0.159.2 and runs as a non-root user. Host Python/Codex installation is unnecessary.
Building requires access to the image registry, Debian, npm and Python package sources.
Running requires access to your own model provider.
Start with 2 CPU cores, 4 GB RAM and 20 GB free disk; project builds may need more resources.

The Codex Linux sandbox requires unprivileged user namespaces. Compose uses the included seccomp
profile, extending Docker's default rules to let bubblewrap create its inner sandbox. The container
remains non-root, drops all container capabilities and prevents privilege escalation. Keep
`deploy/seccomp-codex.json` in the checkout. If the host kernel or AppArmor blocks user namespaces,
the server administrator must configure support first.

**Configure and verify Codex inside the container before using the website.** Your host Codex
sign-in is not imported automatically. You supply your own account/provider credentials and quota.

## One-command guided deployment

With Git, Docker and Compose v2 (supporting `up --wait`) installed, paste this line:

```sh
git clone https://github.com/luxunhe-wq/codex-.git codex-web && cd codex-web && bash deploy.sh --en
```

From an existing checkout, run `bash deploy.sh --en`. The wizard prepares `.env.docker` and the runtime,
guides you through entering your own model API, signing in to Codex or importing `config.toml` / `auth.json`,
then creates the web account and starts the service.

For a custom provider, supply its URL, model name and API key; it must support the Responses API used by Codex.
Keys are entered without echo and saved only in the private persistent volume, never in source files,
command arguments or the image. Imports include only configuration/authentication files, not history,
plugins or host environment variables. Choose API entry if your old configuration requires a key from an environment variable.
Switching from a custom API to Codex sign-in backs up the old configuration as `config.before-login.toml`
inside the volume and resets the provider override. Send a test message in the website to verify model connectivity.

Rerunning keeps configuration, accounts and data:

```sh
bash deploy.sh status --en
bash deploy.sh stop --en
bash deploy.sh --en
bash deploy.sh configure --en
bash deploy.sh logs --en
```

For slow/unreachable download sources, use `bash deploy.sh --en --mirror` to select ECR Public,
Berkeley Debian mirrors and the Huawei Cloud Python mirror. To force a rebuild, use
`bash deploy.sh build --en --mirror`. Host Docker and package-source settings are not changed.
Initial configuration needs an interactive terminal; do not pipe the script into Bash.

The default address is `http://127.0.0.1:8080`. For a remote server use the SSH tunnel below;
see the HTTPS section for phone/public access. The wizard checks container health and Codex sandbox
execution; an actual conversation verifies model credentials, quota and connectivity.

## Manual installation (optional)

These are the Docker commands wrapped by the wizard, available when you want to control each step:

```sh
git clone https://github.com/luxunhe-wq/codex-.git codex-web
cd codex-web
cp .env.docker.example .env.docker
docker compose --env-file .env.docker build
docker compose --env-file .env.docker run --rm -it codex-web codex login --device-auth

# Verify that Codex can answer a message, then exit the CLI.
docker compose --env-file .env.docker run --rm -it codex-web codex

# Create the separate web administrator using the terminal prompts.
docker compose --env-file .env.docker run --rm -it codex-web python /app/server.py --init-admin
docker compose --env-file .env.docker up -d
```

Device authentication availability depends on your account; alternatively import your supported provider
configuration below. Open `http://127.0.0.1:8080`. For a remote server use an SSH tunnel:

```sh
ssh -N -L 8080:127.0.0.1:8080 your-user@your-server
```

The first build downloads dependencies; later builds reuse cached layers. This deployment builds locally
from source. No prebuilt image registry login is needed.

If Docker Hub is unreachable, use the Docker Official Images base image on Amazon ECR Public:

```sh
docker compose --env-file .env.docker build \
  --build-arg NODE_IMAGE=public.ecr.aws/docker/library/node:22-bookworm-slim
```

This changes the base image source only; Debian, npm and Python package repositories must still be reachable.
The `DEBIAN_MIRROR` and `DEBIAN_SECURITY_MIRROR` build arguments can also select Debian mirrors;
they default to the official Debian repositories.
Use `--build-arg PIP_INDEX_URL=https://your-mirror/simple` to select a Python package mirror; the default is PyPI.

## Persistent configuration and projects

| Container path | Contents |
| --- | --- |
| `/home/node/.codex` | Codex configuration, authentication and history |
| `/data` | Web account, conversation database and attachments |
| `/workspace` | Projects and the default working directory |

Recreated containers reuse these named volumes. `docker compose down -v` deletes the volumes;
do not use it to upgrade. Do not run multiple web instances against the same `/data`.

Import your own configuration without putting it into the image:

```sh
docker compose --env-file .env.docker run --rm -T codex-web \
  sh -c 'umask 077; cat > "$CODEX_HOME/config.toml"' < /secure/path/config.toml
```

You can import an existing `auth.json` in the same way by changing both filenames. Import only the
configuration and credentials you need. Never commit real credentials. Paths in your configuration
must exist inside the container. Provider URLs using `localhost` point at the container itself;
use an address reachable from the container for a gateway running on your host.

Clone a project into the persistent workspace and select `/workspace/your-project` in the web folder picker:

```sh
docker compose --env-file .env.docker exec codex-web \
  git clone https://github.com/your-account/your-project.git /workspace/your-project
```

To bind a host project folder, set `CODEX_WEB_UID` / `CODEX_WEB_GID` in `.env.docker` to your normal
user's `id -u` / `id -g` before building (both default to 1000). Create `compose.override.yaml`:

```yaml
services:
  codex-web:
    volumes:
      - type: bind
        source: /home/your-user/projects
        target: /workspace
        bind:
          create_host_path: false
```

Create the host directory first and give the runtime user write access. Use `/workspace` paths in the UI.
Existing named-volume ownership is not changed by rebuilding with different IDs; migrate permissions
when changing the IDs of an existing deployment. Extend the Dockerfile with project-specific tools as needed.

## Status and HTTPS

```sh
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs --tail=100 codex-web
docker compose --env-file .env.docker exec codex-web python /app/server.py --check
```

The health check validates the web server, not model authentication or model network access.
`CODEX_WEB_PUBLISH_PORT` changes the host port; the internal port remains 8080 and is published on host
loopback. For phone/public access, follow [HTTPS deployment](DEPLOYMENT.md) using Caddy on the host
and set these values in `.env.docker`:

```dotenv
CODEX_WEB_ALLOWED_HOSTS=localhost,127.0.0.1,codex.example.com
CODEX_WEB_SECURE_COOKIE=1
```

Wait for active tasks to finish and run `docker compose --env-file .env.docker up -d`. Visit your HTTPS domain;
browsers will not send Secure cookies over plain HTTP. Create the administrator in the terminal beforehand.

## Backup and upgrade

Wait for tasks to finish, stop the service and back up all three volumes. Backups include private credentials:

```sh
docker compose --env-file .env.docker stop
umask 077
mkdir -p backups
docker compose --env-file .env.docker run --rm -T codex-web tar -C /data -czf - . > backups/web-data.tar.gz
docker compose --env-file .env.docker run --rm -T codex-web tar -C /home/node/.codex -czf - . > backups/codex-config.tar.gz
docker compose --env-file .env.docker run --rm -T codex-web tar -C /workspace -czf - . > backups/projects.tar.gz
git pull --ff-only
docker compose --env-file .env.docker build
docker compose --env-file .env.docker up -d
```

Keep the same project directory and Compose project name to reuse the original volumes. Rollback requires
matching code, image and complete data backups.
