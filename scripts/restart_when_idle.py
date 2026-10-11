"""Apply a tested backend update once all web conversations have finished."""
import argparse
import http.client
import os
from pathlib import Path
import sqlite3
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--service', default='codex-web')
    parser.add_argument('--user', action='store_true', help='Restart a systemd user service')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--timeout', type=float, default=86400)
    parser.add_argument('--require-table', action='append', choices=('turns', 'projects', 'attachments'), default=['turns'])
    args = parser.parse_args()
    deadline = time.monotonic() + args.timeout
    idle_since = None
    print('Waiting for all Codex Web tasks to finish before restarting.', flush=True)
    while time.monotonic() < deadline:
        with sqlite3.connect(f'file:{args.database}?mode=ro', uri=True) as db:
            busy = db.execute("SELECT COUNT(*) FROM threads WHERE status IN ('running','waiting')").fetchone()[0]
        if busy:
            idle_since = None
        elif idle_since is None:
            idle_since = time.monotonic()
        elif time.monotonic() - idle_since >= 5:
            backup_directory = args.database.parent / 'backups'
            backup_directory.mkdir(mode=0o700, exist_ok=True)
            backup = backup_directory / ('before-update-' + time.strftime('%Y%m%d-%H%M%S') + '.sqlite3')
            descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(descriptor)
            with sqlite3.connect(f'file:{args.database}?mode=ro', uri=True) as source:
                with sqlite3.connect(str(backup)) as target:
                    source.backup(target)
            # Recheck after the backup in case someone sent a new task meanwhile.
            with sqlite3.connect(f'file:{args.database}?mode=ro', uri=True) as db:
                if db.execute("SELECT COUNT(*) FROM threads WHERE status IN ('running','waiting')").fetchone()[0]:
                    idle_since = None
                    continue
            subprocess.run(['systemctl'] + (['--user'] if args.user else []) + ['restart', args.service], check=True)
            for _ in range(20):
                connection = http.client.HTTPConnection('127.0.0.1', args.port, timeout=2)
                try:
                    connection.request('GET', '/api/status')
                    response = connection.getresponse()
                    response.read()
                    if response.status == 200:
                        with sqlite3.connect(f'file:{args.database}?mode=ro', uri=True) as db:
                            for table in args.require_table:
                                db.execute('SELECT COUNT(*) FROM ' + table).fetchone()
                        print('Backend update is live; HTTP health check and required schema passed.', flush=True)
                        return
                except (OSError, sqlite3.Error):
                    pass
                finally:
                    connection.close()
                time.sleep(1)
            raise RuntimeError('Service restarted but the health check did not pass; inspect codex-web logs.')
        time.sleep(2)
    raise TimeoutError('Tasks remained active; the server was not restarted.')


if __name__ == '__main__':
    main()
