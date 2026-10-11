"""Small dotenv reader: literal values only, no shell execution or expansion."""
import os
from pathlib import Path

ENV_KEYS = {
    'CODEX_WEB_DATA', 'CODEX_WEB_HOST', 'CODEX_WEB_PORT', 'CODEX_WEB_SECURE_COOKIE',
    'CODEX_WEB_ALLOWED_HOSTS', 'CODEX_WEB_CWD', 'CODEX_WEB_CODEX_BIN', 'CODEX_HOME',
}


def load_environment(path, required=False):
    path = Path(path)
    if not path.exists() and not required:
        return
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not separator or key not in ENV_KEYS:
            raise ValueError('%s:%d: unsupported configuration key' % (path.name, number))
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError('%s:%d: unmatched quote' % (path.name, number))
            value = value[1:-1]
        if '\0' in value:
            raise ValueError('%s:%d: invalid value' % (path.name, number))
        # systemd/container environment takes precedence over an optional dotenv file.
        os.environ.setdefault(key, value)
