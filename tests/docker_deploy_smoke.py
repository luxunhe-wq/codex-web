"""Test the actual deployment wizard in a terminal with isolated volumes and fake credentials."""
import argparse
import errno
import os
from pathlib import Path
import pty
import secrets
import select
import shutil
import subprocess
import tempfile
import time
import uuid


def terminal_wizard(directory, env, arguments, prompts, hidden_values):
    master, slave = pty.openpty()
    process = None
    try:
        process = subprocess.Popen(['bash', 'deploy.sh', *arguments], cwd=directory, env=env,
                                   stdin=slave, stdout=slave, stderr=slave)
        os.close(slave)
        pending = bytearray()
        transcript = bytearray()
        deadline = time.monotonic() + 180
        while process.poll() is None or select.select([master], [], [], 0)[0]:
            if time.monotonic() > deadline:
                raise AssertionError('Deployment wizard timed out')
            if not select.select([master], [], [], .2)[0]:
                continue
            try:
                chunk = os.read(master, 65536)
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise
            if not chunk:
                break
            pending.extend(chunk)
            transcript.extend(chunk)
            if prompts and prompts[0][0].encode() in pending:
                prompt, answer = prompts.pop(0)
                pending.clear()
                os.write(master, (answer + '\n').encode())
        process.wait(timeout=10)
        output = transcript.decode(errors='replace')
        assert all(value not in output for value in hidden_values), 'Terminal exposed credentials'
        assert process.returncode == 0 and not prompts, output
        return output
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        os.close(master)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='codex-web-community:local')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    project = 'codex-web-wizard-' + uuid.uuid4().hex[:12]
    env = dict(os.environ, COMPOSE_PROJECT_NAME=project, CODEX_WEB_IMAGE=args.image,
               CODEX_WEB_PUBLISH_PORT='0', CODEX_HOME='/nonexistent-wizard-test-home')
    api_key, password = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
    with tempfile.TemporaryDirectory(prefix='codex web wizard ') as temporary:
        directory = Path(temporary)
        for name in ['deploy.sh', 'compose.yaml', '.env.docker.example']:
            shutil.copyfile(root / name, directory / name)
        (directory / 'deploy').mkdir()
        shutil.copyfile(root / 'deploy/seccomp-codex.json', directory / 'deploy/seccomp-codex.json')
        compose = ['docker', 'compose', '--env-file', '.env.docker']
        def run(*argv):
            result = subprocess.run(argv, cwd=directory, env=env, capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            return result.stdout.strip()
        try:
            output = terminal_wizard(directory, env, [], [
                ('请选择 [1/2/3，默认 1]：', '1'),
                ('模型 API 地址（需支持 Responses，按厂商要求包含 /v1）：', 'https://example.invalid/v1'),
                ('模型名称：', 'test-model'), ('API 密钥（输入时隐藏）：', api_key),
                ('Administrator username:', 'wizardadmin'),
                ('Password (at least 10 characters):', password), ('Confirm password:', password)
            ], [api_key, password])
            assert '网页已启动' in output
            assert (directory / '.env.docker').stat().st_mode & 0o777 == 0o600
            for file in directory.rglob('*'):
                if file.is_file():
                    assert api_key.encode() not in file.read_bytes(), 'Credential saved in host checkout'
            before = run(*compose, 'ps', '-q', 'codex-web')
            run(*compose, 'exec', '-T', 'codex-web', 'python', '-c',
                'import os,tomllib; from pathlib import Path; p=Path(os.environ["CODEX_HOME"])/"config.toml"; '
                'config=tomllib.loads(p.read_text()); assert config["model"]=="test-model"; '
                'assert p.stat().st_mode & 0o777 == 0o600; '
                'Path("/workspace/retained.txt").write_text("retained")')
            result = run('bash', 'deploy.sh', '--en')
            assert 'Existing Codex configuration retained.' in result
            assert run(*compose, 'ps', '-q', 'codex-web') == before, 'Repeated setup recreated the running container'
            run(*compose, 'exec', '-T', 'codex-web', 'python', '-c',
                'import sys; sys.path.insert(0,"/app"); from server import App; '
                'app=App(); app.bridge.start(); '
                'assert app.bridge.call("config/read", {"includeLayers":False})["config"]["model"]=="test-model"; '
                'app.bridge.stop(); app.store.db.close(); '
                'from pathlib import Path; assert Path("/workspace/retained.txt").read_text()=="retained"')
            output = terminal_wizard(directory, env, ['configure'], [
                ('请选择 [1/2/3，默认 1]：', '1'),
                ('模型 API 地址（需支持 Responses，按厂商要求包含 /v1）：', 'https://example.invalid/v1'),
                ('模型名称：', 'changed-model'), ('API 密钥（输入时隐藏）：', api_key)
            ], [api_key, password])
            assert '已保留网页账号和数据' in output
            changed = run(*compose, 'ps', '-q', 'codex-web')
            assert changed != before, 'Configure did not restart the CLI process'
            before = changed
            run(*compose, 'exec', '-T', 'codex-web', 'python', '-c',
                'import sys; sys.path.insert(0,"/app"); from server import App; '
                'app=App(); app.bridge.start(); '
                'assert app.bridge.call("config/read", {"includeLayers":False})["config"]["model"]=="changed-model"; '
                'app.bridge.stop(); app.store.db.close(); '
                'from pathlib import Path; assert Path("/workspace/retained.txt").read_text()=="retained"')
            run(*compose, 'exec', '-T', 'codex-web', 'python', '-c',
                'import sqlite3; db=sqlite3.connect("/data/web.sqlite3"); '
                'db.execute("INSERT INTO threads(id,status) VALUES (?,?)", ("active-test","running")); db.commit()')
            blocked = subprocess.run(['bash', 'deploy.sh', '--en'], cwd=directory, env=env,
                                     capture_output=True, text=True, timeout=60)
            assert blocked.returncode != 0 and 'tasks are active' in blocked.stderr
            assert run(*compose, 'ps', '-q', 'codex-web') == before
            run(*compose, 'exec', '-T', 'codex-web', 'python', '-c',
                'import sqlite3; db=sqlite3.connect("/data/web.sqlite3"); '
                'assert db.execute("SELECT status FROM threads WHERE id=?", ("active-test",)).fetchone()[0]=="running"')
            print('Guided Docker setup, hidden API/password input, private config, real CLI config and repeat deployment: PASS')
        finally:
            subprocess.run(compose + ['down', '--volumes', '--remove-orphans', '--timeout', '5'],
                           cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)


if __name__ == '__main__':
    main()
