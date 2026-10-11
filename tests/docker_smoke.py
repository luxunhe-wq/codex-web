"""Exercise a built Docker image with isolated volumes; never call a model or use host credentials."""
import argparse
import http.cookiejar
import json
from pathlib import Path
import secrets
import subprocess
import time
import urllib.error
import urllib.request
import uuid


def docker(*args, **kwargs):
    result = subprocess.run(['docker', *args], capture_output=True, text=True,
                            timeout=kwargs.pop('timeout', 60), **kwargs)
    if result.returncode:
        raise RuntimeError('Docker command failed:\n' + result.stdout + result.stderr)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='codex-web-community:local')
    args = parser.parse_args()
    name = 'codex-web-smoke-' + uuid.uuid4().hex[:12]
    seccomp = str(Path(__file__).resolve().parents[1] / 'deploy/seccomp-codex.json')
    volumes = []
    container_created = False
    mounts = []
    password = secrets.token_urlsafe(24)
    try:
        assert docker('run', '--rm', args.image, 'id', '-u') != '0'
        check = docker('run', '--rm', args.image, 'python', '/app/server.py', '--check')
        assert 'runtime checks passed' in check
        for suffix, target in [('data', '/data'), ('codex', '/home/node/.codex'), ('projects', '/workspace')]:
            volume = name + '-' + suffix
            docker('volume', 'create', volume); volumes.append(volume)
            mounts.extend(['--mount', 'type=volume,source=' + volume + ',target=' + target])
        # No TTY: getpass reads the isolated generated password from stdin without putting it in arguments.
        docker('run', '--rm', '-i', *mounts, args.image, 'python', '/app/server.py', '--init-admin',
               input='dockeradmin\n' + password + '\n' + password + '\n')

        def start():
            nonlocal container_created
            docker('run', '-d', '--name', name, '--cap-drop=ALL', '--security-opt=no-new-privileges',
                   '--security-opt=seccomp=' + seccomp,
                   '--health-interval=2s', '--health-start-period=1s',
                   '-e', 'CODEX_WEB_ALLOWED_HOSTS=localhost,127.0.0.1',
                   '-p', '127.0.0.1::8080', *mounts, args.image)
            container_created = True
            binding = json.loads(docker('inspect', '--format', '{{json .NetworkSettings.Ports}}', name))
            base = 'http://127.0.0.1:' + binding['8080/tcp'][0]['HostPort']
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(base + '/api/status', timeout=2) as response:
                        assert not json.load(response)['setupRequired']
                    if docker('inspect', '--format', '{{.State.Health.Status}}', name) == 'healthy':
                        return base
                except (urllib.error.URLError, TimeoutError, ConnectionError):
                    pass
                time.sleep(.2)
            raise AssertionError('Container web server did not become ready')

        base = start()
        cookies = http.cookiejar.CookieJar()
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
        csrf = ''

        def api(path, body=None, binary=None):
            nonlocal csrf
            request = urllib.request.Request(base + '/api' + path,
                data=binary if binary is not None else json.dumps(body).encode() if body is not None else None,
                headers={'Content-Type': 'text/plain' if binary is not None else 'application/json',
                         'X-CSRF-Token': csrf})
            with client.open(request, timeout=10) as response:
                result = json.load(response)
            csrf = result.get('csrf', csrf)
            return result

        api('/login', {'username': 'dockeradmin', 'password': password})
        assert api('/bootstrap')['authenticated']
        with client.open(base) as response:
            assert 'data-language-picker' in response.read().decode()
        attachment = api('/attachments?kind=file&name=container-check.txt', binary=b'container document content')['attachment']
        preview = api('/attachments/' + attachment['id'] + '/preview')
        assert 'container document content' in preview['text']
        docker('exec', name, 'python', '-c',
               'from pathlib import Path; Path("/workspace/persistence-check.txt").write_text("project survived"); '
               'Path("/home/node/.codex/persistence-check.txt").write_text("config survived")')
        # Initialize the real CLI App Server without authentication or a model request.
        result = docker('exec', name, 'python', '-c',
               'import sys; sys.path.insert(0,"/app"); from server import App; '
               'app=App(); app.bridge.start(); print("App Server initialized"); app.bridge.stop(); app.store.db.close()')
        assert 'App Server initialized' in result
        # Verify that project command execution works with the normal Codex sandbox inside Docker.
        docker('exec', name, 'codex', 'sandbox', '-c', 'sandbox_mode="workspace-write"', '--',
               'python', '-c', 'from pathlib import Path; Path("/workspace/sandbox-check.txt").write_text("sandbox worked")')
        docker('exec', name, 'codex', 'sandbox', '-c', 'sandbox_mode="workspace-write"', '--',
               'python', '-c', 'import errno\nfrom pathlib import Path\n'
               'try: Path("/data/sandbox-escape.txt").write_text("unexpected")\n'
               'except OSError as e: assert e.errno in (errno.EACCES, errno.EPERM, errno.EROFS)\n'
               'else: raise AssertionError("Sandbox allowed a write outside the workspace")')
        docker('exec', name, 'python', '-c',
               'from pathlib import Path; assert Path("/workspace/sandbox-check.txt").read_text()=="sandbox worked"')
        assert docker('inspect', '--format', '{{.State.Health.Status}}', name) == 'healthy'
        docker('stop', '--time', '10', name); docker('rm', name); container_created = False
        base = start()
        cookies.clear()
        api('/login', {'username': 'dockeradmin', 'password': password})
        assert 'container document content' in api('/attachments/' + attachment['id'] + '/preview')['text']
        docker('exec', name, 'python', '-c',
               'from pathlib import Path; assert Path("/workspace/persistence-check.txt").read_text()=="project survived"; '
               'assert Path("/home/node/.codex/persistence-check.txt").read_text()=="config survived"')
        print('Docker non-root runtime, administrator, login, UI, file parsing, Codex App Server/sandbox and volume persistence: PASS')
    finally:
        if container_created:
            subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for volume in volumes:
            subprocess.run(['docker', 'volume', 'rm', volume], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
