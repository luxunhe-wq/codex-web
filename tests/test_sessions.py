import time
import unittest
from pathlib import Path

import test_server
from server import SESSION_SECONDS, Store


class RememberedSessionTests(unittest.TestCase):
    setUp = test_server.WebTests.setUp
    tearDown = test_server.WebTests.tearDown
    request = test_server.WebTests.request
    setup_account = test_server.WebTests.setup_account

    def test_idle_login_survives_days_and_refresh_renews_cookie(self):
        self.setup_account()
        token = self.cookie.split('=')[1]
        session = self.app.store.session(token)
        now = time.time()
        self.app.store.write('UPDATE sessions SET last_seen=?,expires=? WHERE token=?',
                             (now - 2 * 86400, now + 10 * 86400, session['token']))
        status, data, header = self.request('/api/bootstrap')
        self.assertEqual(status, 200)
        self.assertTrue(data['authenticated'])
        self.assertIn('Max-Age=' + str(SESSION_SECONDS), header)
        self.assertIn('HttpOnly', header)
        renewed = self.app.store.session(token)
        self.assertGreater(renewed['expires'], now + SESSION_SECONDS - 2)
        self.assertGreater(renewed['last_seen'], now - 2)
        # Reads immediately afterward do not commit another renewal to disk.
        self.assertIsNone(self.request('/api/me')[2])
        reopened = Store(Path(self.temp.name))
        self.assertIsNotNone(reopened.session(token))
        reopened.db.close()

    def test_legacy_live_login_upgrades_without_reentering_password(self):
        self.setup_account()
        session = self.app.store.session(self.cookie.split('=')[1])
        now = time.time()
        self.app.store.write('UPDATE sessions SET last_seen=?,expires=? WHERE token=?',
                             (now - 3600, now + 3600, session['token']))
        self.assertTrue(self.request('/api/bootstrap')[1]['authenticated'])
        self.assertGreater(self.app.store.session(self.cookie.split('=')[1])['expires'], now + 29 * 86400)

    def test_expired_and_revoked_sessions_are_not_restored(self):
        self.setup_account()
        session = self.app.store.session(self.cookie.split('=')[1])
        self.app.store.write('UPDATE sessions SET expires=? WHERE token=?', (time.time() - 1, session['token']))
        self.assertFalse(self.request('/api/bootstrap')[1]['authenticated'])
        self.assertEqual(self.request('/api/me')[0], 401)
        self.request('/api/login', {'username': '测试管理员', 'password': 'Secure-example-123'})
        self.app.store.write('DELETE FROM sessions')
        self.assertFalse(self.request('/api/bootstrap')[1]['authenticated'])

    def test_bootstrap_recovers_latest_conversation_without_browser_storage(self):
        self.setup_account()
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('remembered-thread', 'Remembered', self.temp.name, 1, 1))
        self.app.store.item('remembered-thread', {'id': 'answer', 'type': 'agentMessage', 'text': 'Previous conversation'})
        data = self.request('/api/bootstrap')[1]
        self.assertEqual(data['conversation']['thread']['id'], 'remembered-thread')
        self.assertEqual(data['conversation']['items'][0]['text'], 'Previous conversation')
