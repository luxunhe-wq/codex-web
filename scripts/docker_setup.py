#!/usr/bin/env python3
"""Private configuration helper for the Docker deployment wizard (Python 3.11+)."""
import argparse
import getpass
import json
import os
from pathlib import Path
import sqlite3
import sys
import tarfile
import tempfile
from urllib.parse import quote, urlsplit


def private_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def api_configuration(base_url, api_key, model):
    url = urlsplit(base_url)
    if url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password:
        raise ValueError('Use an HTTP(S) API URL without embedded credentials.')
    if not model.strip() or not api_key.strip() or any(ord(c) < 32 or ord(c) == 127 for c in base_url + model + api_key):
        raise ValueError('API URL, key and model must be non-empty single-line values.')
    def text(value):
        return json.dumps(value, ensure_ascii=False)
    return ('model_provider = "custom"\nmodel = ' + text(model) + '\n\n'
            '[model_providers.custom]\nname = "Custom API"\nwire_api = "responses"\n'
            'base_url = ' + text(base_url) + '\nexperimental_bearer_token = ' + text(api_key) + '\n'
            'requires_openai_auth = false\n').encode()


def import_configuration(home, stream):
    import tomllib
    records = {}
    with tarfile.open(fileobj=stream, mode='r|*') as archive:
        for member in archive:
            if member.name not in {'config.toml', 'auth.json'} or not member.isfile() or member.size > 1024 * 1024:
                raise ValueError('Import accepts only regular config.toml/auth.json files up to 1 MiB each.')
            if member.name in records:
                raise ValueError('Duplicate configuration file.')
            content = archive.extractfile(member).read()
            if member.name == 'config.toml':
                try:
                    tomllib.loads(content.decode())
                except (UnicodeError, ValueError):
                    raise ValueError('Invalid config.toml; nothing imported.') from None
            else:
                try:
                    if not isinstance(json.loads(content), dict):
                        raise ValueError()
                except (UnicodeError, ValueError):
                    raise ValueError('Invalid auth.json; nothing imported.') from None
            records[member.name] = content
    if not records:
        raise ValueError('No configuration files found.')
    for name, content in records.items():
        private_write(home / name, content)


def database_state(data, query):
    path = data / 'web.sqlite3'
    if not path.exists():
        return False
    with sqlite3.connect('file:' + quote(str(path), safe='/') + '?mode=ro', uri=True) as db:
        return db.execute(query).fetchone() is not None


def use_codex_login(home):
    path = home / 'config.toml'
    if path.exists():
        private_write(home / 'config.before-login.toml', path.read_bytes())
    private_write(path, b'# Use the default Codex provider with the account in auth.json.\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for mode in ('has-config', 'has-admin', 'idle', 'api', 'import', 'use-login'):
        modes.add_argument('--' + mode, action='store_true')
    parser.add_argument('--language', choices=['zh-CN', 'en'], default='zh-CN')
    args = parser.parse_args()
    home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    data = Path(os.environ.get('CODEX_WEB_DATA', '/data'))
    if args.has_config:
        return 0 if any((home / name).is_file() and (home / name).stat().st_size for name in ('config.toml', 'auth.json')) else 1
    if args.has_admin:
        return 0 if database_state(data, 'SELECT id FROM account LIMIT 1') else 1
    if args.idle:
        return 1 if database_state(data, "SELECT id FROM threads WHERE status IN ('running','waiting') LIMIT 1") else 0
    if args.use_login:
        use_codex_login(home)
        return 0
    if getattr(args, 'import'):
        import_configuration(home, sys.stdin.buffer)
    else:
        en = args.language == 'en'
        base_url = input('API base URL (Responses-compatible): ' if en else '模型 API 地址（需支持 Responses，按厂商要求包含 /v1）：').strip()
        model = input('Model name: ' if en else '模型名称：').strip()
        api_key = getpass.getpass('API key (hidden): ' if en else 'API 密钥（输入时隐藏）：').strip()
        private_write(home / 'config.toml', api_configuration(base_url, api_key, model))
    print('Codex configuration saved privately in the persistent volume.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, sqlite3.Error, tarfile.TarError):
        # Parser/filesystem errors can contain credentials: keep diagnostics generic.
        print('Configuration failed. Check the URL/model or config.toml/auth.json format and permissions.', file=sys.stderr)
        sys.exit(2)
