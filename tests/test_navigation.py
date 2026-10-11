import gzip
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_server
from server import Handler


class NavigationTests(unittest.TestCase):
    setUp = test_server.WebTests.setUp
    tearDown = test_server.WebTests.tearDown
    request = test_server.WebTests.request
    setup_account = test_server.WebTests.setup_account

    def seed_history(self):
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('navigation', 'Navigation', self.temp.name, 1, 1))
        with self.app.store.transaction():
            for index in range(205):
                self.app.store.item('navigation', {'id': 'item-' + str(index), 'type': 'agentMessage',
                                                  'text': ('history %d ' % index) * 100})

    def test_bootstrap_combines_authenticated_workspace_and_recent_history(self):
        data = self.request('/api/bootstrap')[1]
        self.assertFalse(data['authenticated'])
        self.assertTrue(data['setupRequired'])
        self.assertNotIn('csrf', data)
        self.setup_account()
        self.seed_history()
        self.app.bridge.call = lambda *args: (_ for _ in ()).throw(AssertionError('Navigation must not wait for Codex'))
        data = self.request('/api/bootstrap?thread=navigation')[1]
        self.assertTrue(data['authenticated'])
        self.assertEqual(len(data['threads']), 1)
        self.assertEqual(len(data['conversation']['items']), 80)
        self.assertEqual(data['conversation']['items'][0]['id'], 'item-125')
        self.assertTrue(data['conversation']['hasMore'])
        self.assertGreaterEqual(data['conversation']['seq'], data['seq'])
        self.assertNotIn('conversation', self.request('/api/bootstrap?thread=missing')[1])
        logged_out = self.request('/api/bootstrap?thread=navigation', cookie='')[1]
        self.assertFalse(logged_out['authenticated'])
        self.assertNotIn('threads', logged_out)
        self.assertNotIn('conversation', logged_out)

    def test_history_pages_keep_order_and_preserve_all_messages(self):
        self.setup_account()
        self.seed_history()
        data = self.request('/api/threads/navigation?limit=80')[1]
        items = data['items']
        while data['hasMore']:
            data = self.request('/api/threads/navigation?limit=80&before=' + str(data['before']))[1]
            items = data['items'] + items
        self.assertEqual([item['id'] for item in items], ['item-' + str(i) for i in range(205)])
        self.assertEqual(len(self.request('/api/threads/navigation')[1]['items']), 205)
        for query in ('limit=0', 'limit=201', 'limit=oops', 'before=10', 'limit=80&before=0'):
            self.assertEqual(self.request('/api/threads/navigation?' + query)[0], 400)

    def test_json_compression_is_negotiated_and_preserves_history(self):
        self.setup_account()
        self.seed_history()
        for encoding, expected in [('gzip', 'gzip'), ('gzip;q=0, br', None)]:
            conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
            conn.request('GET', '/api/threads/navigation?limit=80',
                         headers={'Cookie': self.cookie, 'Accept-Encoding': encoding})
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader('Content-Encoding'), expected)
            self.assertEqual(response.getheader('Cache-Control'), 'no-store')
            self.assertEqual(response.getheader('Vary'), 'Accept-Encoding')
            body = response.read()
            decoded = gzip.decompress(body) if expected else body
            self.assertEqual(len(json.loads(decoded)['items']), 80)
            if expected:
                self.assertLess(len(body), len(decoded) / 5)
            conn.close()

    def test_slow_history_delivery_does_not_lock_other_requests(self):
        self.setup_account()
        self.seed_history()
        started, release = threading.Event(), threading.Event()
        original = Handler.json
        def blocked_network(handler, *args, **kwargs):
            if handler.path == '/api/threads/navigation':
                started.set()
                release.wait(timeout=5)
            return original(handler, *args, **kwargs)
        with patch.object(Handler, 'json', blocked_network), ThreadPoolExecutor(max_workers=2) as pool:
            history = pool.submit(self.request, '/api/threads/navigation')
            try:
                self.assertTrue(started.wait(timeout=2))
                threads = pool.submit(self.request, '/api/threads')
                self.assertEqual(threads.result(timeout=2)[0], 200)
            finally:
                release.set()
            self.assertEqual(history.result(timeout=2)[0], 200)


if __name__ == '__main__':
    unittest.main()
