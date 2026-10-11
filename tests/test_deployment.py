import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_server
import server
from configuration import load_environment
from scripts.install import render_service
from scripts.check_release import check_entry


class DeploymentTests(unittest.TestCase):
    def test_configuration_is_literal_and_environment_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.env'
            path.write_text('CODEX_WEB_PORT=9000\nCODEX_WEB_DATA="/tmp/folder with spaces"\nCODEX_WEB_CWD=$(touch unexpected)\n')
            with patch.dict(os.environ, {'CODEX_WEB_PORT': '8081'}, clear=True):
                load_environment(path)
                self.assertEqual(os.environ['CODEX_WEB_PORT'], '8081')
                self.assertEqual(os.environ['CODEX_WEB_DATA'], '/tmp/folder with spaces')
                self.assertEqual(os.environ['CODEX_WEB_CWD'], '$(touch unexpected)')
            path.write_text('PATH=unsafe\n')
            with self.assertRaises(ValueError):
                load_environment(path)

    def test_fresh_defaults_and_existing_permissions_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            store = server.Store(path)
            self.assertEqual(store.settings()['sandbox'], 'workspace-write')
            self.assertEqual(store.settings()['approvalPolicy'], 'on-request')
            settings = store.settings()
            settings.update(sandbox='danger-full-access', approvalPolicy='never')
            store.write('UPDATE settings SET value=?', (server.encode(settings),))
            store.db.close()
            with patch.dict(os.environ, {'CODEX_WEB_CWD': '/nonexistent-initial-project'}):
                reopened = server.Store(path)
            self.assertEqual(reopened.settings()['sandbox'], 'danger-full-access')
            self.assertEqual(reopened.settings()['approvalPolicy'], 'never')
            reopened.db.close()

    def test_service_quotes_paths_and_uses_user_manager(self):
        root = Path('/home/user/project with spaces%name')
        unit = render_service(root, root / '.venv/bin/python', root / '.env', '/usr/bin:/home/user/bin')
        self.assertIn('WorkingDirectory=/home/user/project with spaces%%name', unit)
        self.assertIn('WantedBy=default.target', unit)
        self.assertNotIn('User=root', unit)
        self.assertIn('--env-file "', unit)

    def test_release_scanner_rejects_data_and_credentials_without_echoing_them(self):
        self.assertTrue(check_entry('data/web.sqlite3', b'private'))
        self.assertTrue(check_entry('.env', b'private'))
        self.assertTrue(check_entry('config.txt', b'sk-' + b'x'*30))
        self.assertTrue(check_entry('link', b'/etc/passwd', '120000'))
        self.assertEqual(check_entry('.env.example', b'CODEX_WEB_PORT=8080'), [])
        self.assertEqual(check_entry('tests/fixtures/sample.png', b'fixture'), [])

    def test_cli_admin_initialization_and_refusal_do_not_interrupt_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ['server.py', '--init-admin']
            env = {'CODEX_WEB_DATA': directory}
            with patch.dict(os.environ, env), patch.object(sys, 'argv', argv), \
                    patch('builtins.input', return_value='localadmin'), \
                    patch.object(server.getpass, 'getpass', return_value='local-admin-password'), \
                    patch('sys.stdout', new=io.StringIO()):
                server.main()
            with server.sqlite3.connect(str(Path(directory) / 'web.sqlite3')) as db:
                db.execute("INSERT INTO threads(id,title,cwd,created,updated,status) VALUES ('busy','Busy',?,1,1,'running')", (directory,))
            with patch.dict(os.environ, env), patch.object(sys, 'argv', argv), patch('sys.stderr', new=io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    server.main()
                self.assertEqual(raised.exception.code, 1)
            with server.sqlite3.connect(str(Path(directory) / 'web.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT status FROM threads').fetchone()[0], 'running')


class SetupBoundaryTests(unittest.TestCase):
    setUp = test_server.WebTests.setUp
    tearDown = test_server.WebTests.tearDown
    request = test_server.WebTests.request

    def test_proxy_deployment_cannot_claim_account_from_web(self):
        with patch.dict(os.environ, {'CODEX_WEB_ALLOWED_HOSTS': 'codex.example.com'}):
            status, _, _ = self.request('/api/setup', {'username':'remoteadmin','password':'remote-password-123'})
        self.assertEqual(status, 403)
        self.assertIsNone(self.app.store.one('SELECT id FROM account'))

    def test_nonloopback_setup_is_rejected(self):
        with patch.object(server.ipaddress, 'ip_address') as address:
            address.return_value.is_loopback = False
            status, _, _ = self.request('/api/setup', {'username':'remoteadmin','password':'remote-password-123'})
        self.assertEqual(status, 403)
