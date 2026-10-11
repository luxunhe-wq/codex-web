import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import restart_when_idle


class IdleUpdateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / 'web.sqlite3'
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE TABLE threads(id TEXT, status TEXT)')
            db.execute('CREATE TABLE turns(id TEXT)')

    def tearDown(self):
        self.directory.cleanup()

    def test_active_task_prevents_restart(self):
        with sqlite3.connect(self.database) as db:
            db.execute("INSERT INTO threads VALUES ('active', 'running')")
        argv = ['restart_when_idle.py', '--database', str(self.database), '--timeout', '2']
        with patch.object(sys, 'argv', argv), patch.object(restart_when_idle.time, 'monotonic', side_effect=[0, 1, 2]), \
                patch.object(restart_when_idle.time, 'sleep'), patch.object(restart_when_idle.subprocess, 'run') as restart:
            with self.assertRaises(TimeoutError):
                restart_when_idle.main()
            restart.assert_not_called()
        self.assertFalse((self.database.parent / 'backups').exists())

    def test_idle_restart_backs_up_database_and_checks_health(self):
        with sqlite3.connect(self.database) as db:
            db.execute("INSERT INTO threads VALUES ('done', 'completed')")
        connection = MagicMock()
        connection.getresponse.return_value.status = 200
        argv = ['restart_when_idle.py', '--database', str(self.database)]
        with patch.object(sys, 'argv', argv), patch.object(restart_when_idle.time, 'monotonic', side_effect=[0, 1, 2, 3, 9]), \
                patch.object(restart_when_idle.time, 'sleep'), patch.object(restart_when_idle.subprocess, 'run') as restart, \
                patch.object(restart_when_idle.http.client, 'HTTPConnection', return_value=connection) as connect:
            restart_when_idle.main()
            restart.assert_called_once_with(['systemctl', 'restart', 'codex-web'], check=True)
            connect.assert_called_once_with('127.0.0.1', 8080, timeout=2)
            connection.request.assert_called_once_with('GET', '/api/status')
        backups = list((self.database.parent / 'backups').glob('*.sqlite3'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(os.stat(backups[0]).st_mode & 0o777, 0o600)
        with sqlite3.connect(backups[0]) as db:
            self.assertEqual(db.execute('SELECT status FROM threads').fetchone()[0], 'completed')


if __name__ == '__main__':
    unittest.main()
