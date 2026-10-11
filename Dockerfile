ARG NODE_IMAGE=node:22-bookworm-slim
FROM ${NODE_IMAGE}

ARG CODEX_VERSION=0.159.2
ARG CODEX_WEB_UID=1000
ARG CODEX_WEB_GID=1000
ARG DEBIAN_MIRROR=http://deb.debian.org/debian
ARG DEBIAN_SECURITY_MIRROR=http://deb.debian.org/debian-security

LABEL org.opencontainers.image.title="Codex Web Community" \
      org.opencontainers.image.source="https://github.com/luxunhe-wq/codex-" \
      org.opencontainers.image.licenses="AGPL-3.0-only"

RUN sed -i "s|http://deb.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g; s|http://deb.debian.org/debian$|${DEBIAN_MIRROR}|g" /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 update \
    && apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 install -y --no-install-recommends python3 python3-venv git ca-certificates tini bubblewrap \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g "@openai/codex@${CODEX_VERSION}" \
    && npm cache clean --force \
    && codex --version \
    && python3 -m venv /opt/venv

COPY requirements.txt /app/requirements.txt
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

RUN test "$CODEX_WEB_UID" -gt 0 && test "$CODEX_WEB_GID" -gt 0 \
    && if [ "$(id -g node)" != "$CODEX_WEB_GID" ]; then groupmod -g "$CODEX_WEB_GID" node; fi \
    && if [ "$(id -u node)" != "$CODEX_WEB_UID" ]; then usermod -u "$CODEX_WEB_UID" node; fi \
    && mkdir -p /data /workspace /home/node/.codex \
    && chown node:node /data /workspace /home/node/.codex

COPY server.py configuration.py documents.py LICENSE THIRD_PARTY_NOTICES.md README.md /app/
COPY static/ /app/static/
COPY docs/ /app/docs/
COPY deploy/seccomp-codex.json deploy/LICENSE.moby-profiles /app/deploy/
RUN chmod -R a+rX /app

ENV PATH="/opt/venv/bin:${PATH}" \
    HOME=/home/node \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CODEX_HOME=/home/node/.codex \
    CODEX_WEB_HOST=0.0.0.0 \
    CODEX_WEB_PORT=8080 \
    CODEX_WEB_DATA=/data \
    CODEX_WEB_CWD=/workspace

USER node
WORKDIR /workspace
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import json, urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8080/api/status', timeout=3); assert 'setupRequired' in json.load(r)"]
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "/app/server.py"]
