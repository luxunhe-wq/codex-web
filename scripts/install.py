#!/usr/bin/env python3
"""Install dependencies in a venv and optionally configure a systemd user service."""
import argparse
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from configuration import load_environment


def unit_quote(value):
    if any(c in value for c in '\n\r\0'):
        raise ValueError('Paths and environment values must not contain control characters')
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'


def render_service(root, python, env_path, executable_path):
    return '''[Unit]
Description=Codex Web Community browser workspace
After=network.target

[Service]
Type=simple
WorkingDirectory={root}
Environment=PYTHONUNBUFFERED=1
Environment={path}
UMask=0077
ExecStart={python} {server} --env-file {env}
Restart=on-failure
RestartSec=3
TimeoutStopSec=15
KillMode=control-group

[Install]
WantedBy=default.target
'''.format(root=unit_quote(str(root))[1:-1], path=unit_quote('PATH=' + executable_path),
           python=unit_quote(str(python)), server=unit_quote(str(root / 'server.py')),
           env=unit_quote(str(env_path)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-service', action='store_true', help='Prepare venv/configuration without starting a service')
    parser.add_argument('--allow-root', action='store_true', help='Explicitly allow installation as root (not recommended)')
    args = parser.parse_args()
    if sys.platform != 'linux':
        parser.error('This installer supports Linux')
    if sys.version_info < (3, 9):
        parser.error('Python 3.9 or newer is required; 3.11/3.12 is recommended')
    if os.geteuid() == 0 and not args.allow_root:
        parser.error('Run as your normal Linux user, or explicitly specify --allow-root')
    try:
        load_environment(ROOT / '.env')
    except (OSError, ValueError) as error:
        parser.error(str(error))
    codex = shutil.which(os.environ.get('CODEX_WEB_CODEX_BIN', 'codex'))
    if not codex:
        parser.error('Install and configure Codex CLI first; codex must be on PATH or set CODEX_WEB_CODEX_BIN')
    subprocess.run([codex, '--version'], check=True)
    venv = ROOT / '.venv'
    if not (venv / 'bin/python').exists():
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
    python = venv / 'bin/python'
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], check=True)
    env_path = ROOT / '.env'
    if not env_path.exists():
        values = {'CODEX_WEB_HOST': '127.0.0.1', 'CODEX_WEB_PORT': '8080',
                  'CODEX_WEB_DATA': str(ROOT / 'data'), 'CODEX_WEB_CWD': str(ROOT),
                  'CODEX_WEB_CODEX_BIN': codex}
        for key in values:
            values[key] = os.environ.get(key, values[key])
        for key in ('CODEX_HOME', 'CODEX_WEB_ALLOWED_HOSTS', 'CODEX_WEB_SECURE_COOKIE'):
            if key in os.environ:
                values[key] = os.environ[key]
        if any(any(c in value for c in '\n\r\0') for value in values.values()):
            parser.error('Installation paths cannot contain control characters')
        with os.fdopen(os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as file:
            file.write(''.join(key + '=' + value + '\n' for key, value in values.items()))
    subprocess.run([str(python), str(ROOT / 'server.py'), '--env-file', str(env_path), '--check'], check=True)
    print('Create the administrator before exposing this service:')
    print(shlex.join([str(python), str(ROOT / 'server.py'), '--init-admin']))
    if args.no_service:
        print('Start with: ' + shlex.join([str(python), str(ROOT / 'server.py')]))
        return
    service_dir = Path.home() / '.config/systemd/user'
    service_dir.mkdir(parents=True, exist_ok=True)
    service = service_dir / 'codex-web.service'
    service.write_text(render_service(ROOT, python, env_path, os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin')))
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    active = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', 'codex-web'], check=False).returncode == 0
    subprocess.run(['systemctl', '--user', 'enable'] + ([] if active else ['--now']) + ['codex-web'], check=True)
    print('Service configured. URL: http://127.0.0.1:8080 (unless changed in .env)')
    if active:
        print('Existing service kept running; restart only after active tasks finish.')


if __name__ == '__main__':
    main()
