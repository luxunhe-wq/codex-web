import importlib.util
import io
import os
from pathlib import Path
import sqlite3
import tarfile
import tempfile
import unittest

from scripts.docker_setup import api_configuration, database_state, import_configuration, private_write, use_codex_login


class DockerSetupTests(unittest.TestCase):
    def test_switching_to_codex_login_retains_private_backup_and_removes_api_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            before = api_configuration('https://example.invalid/v1', 'test-key', 'test-model')
            private_write(home / 'config.toml', before)
            use_codex_login(home)
            self.assertEqual((home / 'config.before-login.toml').read_bytes(), before)
            self.assertEqual((home / 'config.before-login.toml').stat().st_mode & 0o777, 0o600)
            self.assertNotIn(b'model_provider', (home / 'config.toml').read_bytes())

    def test_private_files_replace_without_exposing_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'codex' / 'config.toml'
            private_write(path, b'first')
            os.chmod(path, 0o644)
            private_write(path, b'second')
            self.assertEqual(path.read_bytes(), b'second')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_api_configuration_rejects_invalid_inputs(self):
        for url, key, model in [('file:///tmp/x', 'key', 'model'), ('https://user:pass@example.invalid', 'key', 'model'),
                                ('https://example.invalid/v1', '', 'model'), ('https://example.invalid/v1', 'key', 'model\nother')]:
            with self.assertRaises(ValueError):
                api_configuration(url, key, model)

    @unittest.skipUnless(importlib.util.find_spec('tomllib'), 'Container helper uses Python 3.11+')
    def test_api_config_quotes_model_and_credentials_as_toml_values(self):
        import tomllib
        model = 'quoted"model\\name'
        key = 'test"key\\value'
        config = tomllib.loads(api_configuration('https://example.invalid/v1', key, model).decode())
        self.assertEqual(config['model'], model)
        provider = config['model_providers']['custom']
        self.assertEqual(provider['experimental_bearer_token'], key)
        self.assertEqual(provider['wire_api'], 'responses')
        self.assertFalse(provider['requires_openai_auth'])

    @unittest.skipUnless(importlib.util.find_spec('tomllib'), 'Container helper uses Python 3.11+')
    def test_import_validates_every_file_before_writing_and_blocks_unsafe_members(self):
        def archive(entries):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w') as tar:
                for name, data, kind in entries:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    member.size = len(data)
                    tar.addfile(member, io.BytesIO(data))
            stream.seek(0)
            return stream
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            for entries in [[('../auth.json', b'{}', tarfile.REGTYPE)], [('auth.json', b'{}', tarfile.SYMTYPE)],
                            [('config.toml', b'model="test"', tarfile.REGTYPE), ('auth.json', b'invalid', tarfile.REGTYPE)]]:
                with self.assertRaises(ValueError):
                    import_configuration(home, archive(entries))
                self.assertEqual(list(home.iterdir()), [])
            import_configuration(home, archive([('config.toml', b'model="test"', tarfile.REGTYPE), ('auth.json', b'{}', tarfile.REGTYPE)]))
            self.assertEqual((home / 'config.toml').read_bytes(), b'model="test"')
            self.assertEqual((home / 'auth.json').stat().st_mode & 0o777, 0o600)

    def test_status_checks_preserve_active_tasks_and_do_not_create_missing_databases(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            query = "SELECT id FROM threads WHERE status IN ('running','waiting') LIMIT 1"
            self.assertFalse(database_state(home, query))
            self.assertEqual(list(home.iterdir()), [])
            with sqlite3.connect(home / 'web.sqlite3') as db:
                db.execute('CREATE TABLE threads (id TEXT, status TEXT)')
                db.execute("INSERT INTO threads VALUES ('test', 'running')")
            self.assertTrue(database_state(home, query))
            with sqlite3.connect(home / 'web.sqlite3') as db:
                self.assertEqual(db.execute('SELECT status FROM threads').fetchone()[0], 'running')


if __name__ == '__main__':
    unittest.main()
