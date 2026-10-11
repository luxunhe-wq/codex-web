import http.client
import json
import sys
import tempfile
import threading
import unittest
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, ApiError, Handler, ThreadingHTTPServer, Store, SESSION_IDLE_SECONDS, ROOT


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = App(Path(self.temp.name))
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.server.app = self.app
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.cookie = ''
        self.csrf = ''

    def tearDown(self):
        self.app.bridge.stop()
        self.server.shutdown()
        self.server.server_close()
        self.app.store.db.close()
        self.temp.cleanup()

    def request(self, path, body=None, csrf=True, cookie=None, origin=None, extra_headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        headers = {'Cookie': self.cookie if cookie is None else cookie}
        if body is not None:
            headers['Content-Type'] = 'application/json'
            if csrf:
                headers['X-CSRF-Token'] = self.csrf
        if origin:
            headers['Origin'] = origin
        headers.update(extra_headers or {})
        conn.request('GET' if body is None else 'POST', path, body=None if body is None else json.dumps(body), headers=headers)
        response = conn.getresponse()
        data = response.read()
        content_type = response.getheader('Content-Type', '')
        result = json.loads(data) if 'application/json' in content_type else data
        cookie_header = response.getheader('Set-Cookie')
        if cookie_header:
            self.cookie = cookie_header.split(';')[0]
        if isinstance(result, dict) and 'csrf' in result:
            self.csrf = result['csrf']
        status = response.status
        conn.close()
        return status, result, cookie_header

    def setup_account(self):
        status, data, header = self.request('/api/setup', {'username':'测试管理员','password':'Secure-example-123'})
        self.assertEqual(status, 200, data)
        self.assertIn('HttpOnly', header)
        self.assertIn('SameSite=Strict', header)

    def test_auth_and_csrf_and_single_setup(self):
        self.assertTrue(self.request('/api/status')[1]['setupRequired'])
        for path in ['/api/me','/api/threads','/api/models','/api/events','/api/files','/api/projects','/api/directories']:
            self.assertEqual(self.request(path)[0], 401)
        self.assertEqual(self.request('/api/setup', {'username':'aa','password':'short'})[0], 400)
        self.setup_account()
        self.assertFalse(self.request('/api/status')[1]['setupRequired'])
        self.assertEqual(self.request('/api/setup', {'username':'second','password':'another-password'})[0], 409)
        self.assertEqual(self.request('/api/settings', {'theme':'dark'}, csrf=False)[0], 403)
        self.assertEqual(self.request('/api/settings', {'theme':'dark'}, origin='http://evil.test')[0], 403)
        self.assertEqual(self.request('/api/settings', {'theme':'dark'})[0], 200)
        self.assertEqual(self.request('/api/me')[1]['settings']['theme'], 'dark')
        self.assertNotIn('Secure-example-123', self.app.store.one('SELECT * FROM account').values())
        self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'incorrect-password'})[0], 401)

    def test_password_change_revokes_sessions_and_logout(self):
        self.setup_account()
        old_cookie = self.cookie
        self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'})
        self.assertEqual(self.request('/api/credentials', {'currentPassword':'wrong','username':'admin','password':'new-password-123'})[0], 403)
        status, data, _ = self.request('/api/credentials', {'currentPassword':'Secure-example-123','username':'newadmin','password':'new-password-123'})
        self.assertEqual(status, 200, data)
        self.assertEqual(self.request('/api/me', cookie=old_cookie)[0], 401)
        self.assertEqual(self.request('/api/me')[1]['username'], 'newadmin')
        self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'})[0], 401)
        self.assertEqual(self.request('/api/login', {'username':'newadmin','password':'new-password-123'})[0], 200)
        cookie = self.cookie
        status, _, header = self.request('/api/logout', {})
        self.assertEqual(status, 200)
        self.assertIn('Max-Age=0', header)
        self.assertEqual(self.request('/api/me', cookie=cookie)[0], 401)

    def test_six_failures_lock_for_six_minutes(self):
        self.setup_account()
        for body in [{'cwd':'relative'}, {'cwd':'/does-not-exist'}, {'sandbox':'bad'}, {'effort':'bad'}, {'model':[]}, {'theme':'bad'}]:
            self.assertEqual(self.request('/api/settings', body)[0], 400)
        with patch('server.time.time', return_value=2000000000):
            for attempt in range(1, 6):
                status, data, _ = self.request('/api/login', {'username':'wrong','password':'x'})
                self.assertEqual(status, 401, data)
                self.assertEqual(data['remainingAttempts'], 6 - attempt)
            status, data, _ = self.request('/api/login', {'username':'测试管理员','password':'wrong'})
            self.assertEqual(status, 423, data)
            self.assertEqual(data['retryAfter'], 360)
            until = data['lockedUntil']
        with patch('server.time.time', return_value=2000000100):
            self.assertEqual(self.request('/api/status')[1]['retryAfter'], 260)
            self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'})[0], 423)
            self.assertEqual(self.request('/api/status')[1]['lockedUntil'], until)
            reopened = Store(Path(self.temp.name))
            self.assertEqual(reopened.lock_status('different-ip')['retryAfter'], 260)
            reopened.db.close()
        with patch('server.time.time', return_value=2000000360):
            self.assertEqual(self.request('/api/status')[1]['retryAfter'], 0)
            self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'})[0], 200)
            self.assertEqual(self.request('/api/status')[1]['remainingAttempts'], 6)

    def test_success_resets_counter_and_successes_are_not_limited(self):
        self.setup_account()
        for _ in range(5):
            self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'wrong'})[0], 401)
        for _ in range(11):
            self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'})[0], 200)
        self.assertEqual(self.request('/api/status')[1]['remainingAttempts'], 6)
        self.assertEqual(self.request('/api/login', {'username':'wrong','password':'wrong'})[1]['remainingAttempts'], 5)

    def test_success_resets_other_source_counters(self):
        self.setup_account()
        store = self.app.store
        with store.lock:
            for _ in range(5):
                with self.assertRaises(ApiError):
                    store.auth_failure('other-source')
        self.assertEqual(store.lock_status('other-source')['remainingAttempts'], 1)
        self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'})[0], 200)
        self.assertEqual(store.lock_status('other-source')['remainingAttempts'], 6)

    def test_concurrent_failures_cannot_bypass_lock(self):
        self.setup_account()
        def fail(index):
            conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=15)
            conn.request('POST', '/api/login', json.dumps({'username':'wrong'+str(index),'password':'wrong'}),
                         headers={'Content-Type':'application/json', 'X-Forwarded-For':str(index)})
            response = conn.getresponse()
            status = response.status
            response.read(); conn.close()
            return status
        with ThreadPoolExecutor(max_workers=12) as executor:
            statuses = list(executor.map(fail, range(12)))
        self.assertEqual(statuses.count(401), 5, statuses)
        self.assertEqual(statuses.count(423), 7, statuses)
        self.assertEqual(self.request('/api/status')[1]['remainingAttempts'], 0)
        # Existing authenticated sessions keep working while login is locked.
        self.assertEqual(self.request('/api/me')[0], 200)

    def test_credential_change_has_separate_failure_lock(self):
        self.setup_account()
        bad = {'currentPassword':'wrong','username':'admin','password':'new-password-123'}
        for _ in range(5):
            self.assertEqual(self.request('/api/credentials', bad)[0], 403)
        self.assertEqual(self.request('/api/credentials', bad)[0], 423)
        self.assertEqual(self.request('/api/credentials', {**bad,'currentPassword':'Secure-example-123'})[0], 423)
        self.assertEqual(self.request('/api/status')[1]['retryAfter'], 0)
        self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'})[0], 200)

    def test_request_source_and_security_headers(self):
        self.setup_account()
        for headers in [{'Host':'evil.example:'+str(self.server.server_port)}, {'Sec-Fetch-Site':'cross-site'}]:
            self.assertEqual(self.request('/api/me', extra_headers=headers)[0], 403)
        wrong_scheme = 'https://127.0.0.1:'+str(self.server.server_port)
        self.assertEqual(self.request('/api/me', origin=wrong_scheme)[0], 403)
        self.assertEqual(self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'},
                                      origin='http://evil.example')[0], 403)
        self.assertEqual(self.request('/api/status')[1]['remainingAttempts'], 6)
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        conn.request('GET','/')
        response = conn.getresponse()
        self.assertEqual(response.getheader('X-Frame-Options'),'DENY')
        self.assertIn("frame-ancestors 'none'", response.getheader('Content-Security-Policy'))
        self.assertEqual(response.getheader('Cache-Control'),'no-store')
        self.assertNotIn('Python',response.getheader('Server'))
        response.read();conn.close()

    def test_static_compression_and_cache_validation(self):
        import gzip
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        conn.request('GET', '/app.js', headers={'Accept-Encoding': 'gzip'})
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader('Content-Encoding'), 'gzip')
        self.assertEqual(response.getheader('Cache-Control'), 'no-cache')
        etag = response.getheader('ETag')
        body = response.read()
        self.assertIn(b'function renderMessages()', gzip.decompress(body))
        self.assertLess(len(body), len(gzip.decompress(body)) / 2)
        conn.request('GET', '/app.js', headers={'If-None-Match': etag})
        response = conn.getresponse()
        self.assertEqual(response.status, 304)
        self.assertEqual(response.read(), b'')
        conn.request('GET', '/app.js', headers={'Accept-Encoding': 'gzip;q=0, br'})
        response = conn.getresponse()
        self.assertIsNone(response.getheader('Content-Encoding'))
        self.assertIn(b'function renderMessages()', response.read())
        conn.close()

    def test_reasoning_timing_summary_indices_and_history(self):
        self.setup_account()
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('timed', 'Timed', self.temp.name, 1, 1))
        bridge = self.app.bridge
        def event(at, method, **params):
            with patch('server.time.time', return_value=at):
                bridge.notification({'method': method, 'params': {'threadId': 'timed', 'turnId': 'turn-1', **params}})
        event(100, 'turn/started', turn={'id': 'turn-1'})
        event(101, 'item/started', item={'id': 'reason-1', 'type': 'reasoning', 'summary': []})
        event(102, 'item/reasoning/summaryTextDelta', itemId='reason-1', summaryIndex=0, delta='first')
        event(103, 'item/reasoning/summaryTextDelta', itemId='reason-1', summaryIndex=1, delta='second')
        event(104, 'item/reasoning/textDelta', itemId='reason-1', delta='not a summary')
        event(106, 'item/completed', item={'id': 'reason-1', 'type': 'reasoning', 'summary': []})
        event(107, 'item/completed', item={'id': 'reason-1', 'type': 'reasoning', 'summary': []})
        event(120, 'turn/completed', turn={'id': 'turn-1', 'status': 'completed'})
        data = self.request('/api/threads/timed')[1]
        self.assertEqual(data['turns'][0]['reasoningMs'], 5000)
        self.assertEqual(data['turns'][0]['completedAt'] - data['turns'][0]['startedAt'], 20)
        self.assertEqual(data['items'][0]['webTiming']['durationMs'], 5000)
        self.assertEqual(data['items'][0]['summary'], ['first', 'second'])
        reopened = Store(Path(self.temp.name))
        self.assertEqual(reopened.turns('timed'), data['turns'])
        reopened.db.close()

    def test_batched_reasoning_does_not_measure_delivery_as_thinking(self):
        self.setup_account()
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('timed', 'Timed', self.temp.name, 1, 1))
        def event(at, method, **params):
            with patch('server.time.time', return_value=at):
                self.app.bridge.notification({'method': method, 'params': {'threadId': 'timed', 'turnId': 'turn-1', **params}})
        event(100, 'turn/started', turn={'id': 'turn-1'})
        event(120, 'item/started', item={'id': 'batched', 'type': 'reasoning', 'summary': []})
        event(120.01, 'item/completed', item={'id': 'batched', 'type': 'reasoning', 'summary': []})
        event(121, 'item/started', item={'id': 'short', 'type': 'reasoning', 'summary': []})
        event(121.1, 'item/reasoning/textDelta', itemId='short', delta='streamed reasoning')
        event(121.3, 'item/completed', item={'id': 'short', 'type': 'reasoning', 'summary': []})
        # A completion without a start cannot give a duration, even with a summary.
        event(123, 'item/completed', item={'id': 'missing-start', 'type': 'reasoning', 'summary': ['already completed']})
        event(123.1, 'item/completed', item={'id': 'missing-start', 'type': 'reasoning', 'summary': []})
        event(125, 'turn/completed', turn={'id': 'turn-1', 'status': 'completed'})
        data = self.request('/api/threads/timed')[1]
        items = {item['id']: item for item in data['items']}
        self.assertEqual(items['batched']['webTiming']['measurement'], 'unavailable')
        self.assertEqual(items['batched']['webTiming']['durationMs'], 10)
        self.assertEqual(items['short']['webTiming']['measurement'], 'observed')
        self.assertEqual(items['short']['webTiming']['durationMs'], 300)
        self.assertEqual(items['missing-start']['webTiming']['measurement'], 'unavailable')
        self.assertEqual(data['turns'][0]['reasoningMs'], 300)
        reopened = Store(Path(self.temp.name))
        self.assertEqual(reopened.turns('timed'), data['turns'])
        reopened.db.close()

    def test_projects_remember_deduplicate_select_and_remove(self):
        self.setup_account()
        folder = Path(self.temp.name) / '中文 project'
        folder.mkdir()
        (folder / 'keep.txt').write_text('keep')
        alias = Path(self.temp.name) / 'alias'
        alias.symlink_to(folder, target_is_directory=True)
        count = len(self.request('/api/projects')[1]['projects'])
        self.assertEqual(self.request('/api/projects', {'path': str(folder)}, csrf=False)[0], 403)
        status, added, _ = self.request('/api/projects', {'path': str(folder)})
        self.assertEqual(status, 201)
        project_id = added['project']['id']
        self.assertEqual(added['settings']['cwd'], str(folder))
        self.assertEqual(added['project']['name'], '中文 project')
        duplicate = self.request('/api/projects', {'path': str(alias)})
        self.assertEqual(duplicate[0], 200)
        self.assertEqual(duplicate[1]['project']['id'], project_id)
        self.assertEqual(len(duplicate[1]['projects']), count + 1)
        self.assertEqual(self.request('/api/me')[1]['projects'], self.request('/api/projects')[1]['projects'])
        self.request('/api/settings', {'cwd': str(ROOT)})
        selected = self.request('/api/projects/' + project_id + '/select', {})
        self.assertEqual(selected[1]['settings']['cwd'], str(folder))
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('keep-history', 'Keep', str(folder), 1, 1))
        self.assertEqual(self.request('/api/projects/' + project_id + '/remove', {}, csrf=False)[0], 403)
        removed = self.request('/api/projects/' + project_id + '/remove', {})
        self.assertEqual(removed[0], 200)
        self.assertFalse(any(project['id'] == project_id for project in removed[1]['projects']))
        self.assertEqual((folder / 'keep.txt').read_text(), 'keep')
        self.assertEqual(self.app.store.thread('keep-history')['cwd'], str(folder))
        reopened = Store(Path(self.temp.name))
        self.assertFalse(any(project['path'] == str(folder) for project in reopened.projects()))
        reopened.db.close()

    def test_projects_survive_restart_and_validate_directories(self):
        self.setup_account()
        folder = Path(self.temp.name) / 'remembered'
        folder.mkdir()
        (folder / 'child').mkdir()
        (folder / '.hidden').mkdir()
        file = folder / 'file.txt'
        file.write_text('file')
        added = self.request('/api/projects', {'path': str(folder)})[1]
        for value, expected in [(None, 400), (123, 400), ('relative', 400), ('/bad\0path', 400),
                                (str(folder / 'missing'), 404), (str(file), 400)]:
            self.assertEqual(self.request('/api/projects', {'path': value})[0], expected)
        import urllib.parse
        listing = self.request('/api/directories?path=' + urllib.parse.quote(str(folder)))[1]
        self.assertEqual(listing['path'], str(folder))
        self.assertEqual(listing['parent'], str(folder.parent))
        self.assertEqual([entry['name'] for entry in listing['directories']], ['child'])
        self.assertIsNone(self.request('/api/directories?path=/')[1]['parent'])
        self.assertEqual(self.request('/api/directories?path=relative')[0], 400)
        reopened = Store(Path(self.temp.name))
        self.assertEqual(reopened.settings()['cwd'], str(folder))
        self.assertTrue(any(project['id'] == added['project']['id'] for project in reopened.projects()))
        reopened.db.close()
        (folder / 'child').rmdir()
        (folder / '.hidden').rmdir()
        file.unlink()
        folder.rmdir()
        stored = self.request('/api/projects')[1]['projects']
        self.assertFalse(next(project for project in stored if project['id'] == added['project']['id'])['available'])
        self.assertEqual(self.request('/api/projects/' + added['project']['id'] + '/select', {})[0], 404)

    def test_new_thread_uses_selected_folder_without_changing_existing_threads(self):
        self.setup_account()
        folder = Path(self.temp.name) / 'project-a'
        folder.mkdir()
        other = Path(self.temp.name) / 'project-b'
        other.mkdir()
        self.request('/api/projects', {'path': str(folder)})
        self.request('/api/projects', {'path': str(other)})
        seen = []
        def call(method, params):
            seen.append((method, params))
            return {'thread': {'id': 'new-project-thread', 'cwd': params['cwd']}, 'model': 'test-model'}
        self.app.bridge.call = call
        created = self.request('/api/threads', {'cwd': str(folder)})
        self.assertEqual(created[0], 201)
        self.assertEqual(seen[0][1]['cwd'], str(folder))
        self.assertEqual(created[1]['thread']['cwd'], str(folder))
        self.assertEqual(self.app.store.settings()['cwd'], str(other))
        self.request('/api/settings', {'cwd': str(other)})
        self.assertEqual(self.app.store.thread('new-project-thread')['cwd'], str(folder))

    def test_interruption_closes_reasoning_and_recovers_after_restart(self):
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('timed', 'Timed', self.temp.name, 1, 1))
        with patch('server.time.time', return_value=100):
            self.app.bridge.notification({'method': 'turn/started', 'params': {'threadId': 'timed', 'turn': {'id': 'turn-1'}}})
        with patch('server.time.time', return_value=102):
            self.app.bridge.notification({'method': 'item/started', 'params': {'threadId': 'timed', 'turnId': 'turn-1',
                                         'item': {'id': 'reason-1', 'type': 'reasoning', 'summary': []}}})
        with patch('server.time.time', return_value=110):
            recovered = Store(Path(self.temp.name))
        turn = recovered.turns('timed')[0]
        self.assertEqual(turn['status'], 'interrupted')
        self.assertEqual(turn['completedAt'], 110)
        self.assertEqual(turn['reasoningMs'], 8000)
        recovered.db.close()

    def test_notification_item_and_event_share_one_commit(self):
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('timed', 'Timed', self.temp.name, 1, 1))
        statements = []
        self.app.store.db.set_trace_callback(statements.append)
        self.app.bridge.notification({'method': 'item/started', 'params': {'threadId': 'timed',
                                     'item': {'id': 'agent-1', 'type': 'agentMessage', 'text': ''}}})
        self.app.store.db.set_trace_callback(None)
        self.assertEqual(sum(s == 'COMMIT' for s in statements), 1)
        seq = self.app.store.seq()
        packet = json.loads(self.app.store.one('SELECT value FROM events WHERE seq=?', (seq,))['value'])
        self.assertEqual(packet['params']['item']['webTiming'],
                         json.loads(self.app.store.one('SELECT value FROM items WHERE item_id=?', ('agent-1',))['value'])['webTiming'])

    def test_ambiguous_request_framing_is_rejected_and_closed(self):
        for framing in [b'Content-Length: 2\r\nContent-Length: 2\r\n',
                        b'Transfer-Encoding: chunked\r\nContent-Length: 2\r\n']:
            with socket.create_connection(('127.0.0.1', self.server.server_port), timeout=5) as connection:
                packet = (f'POST /api/login HTTP/1.1\r\nHost: 127.0.0.1:{self.server.server_port}\r\n'
                          'Content-Type: application/json\r\n').encode() + framing + b'\r\n{}'
                connection.sendall(packet)
                result = b''
                while True:
                    data = connection.recv(8192)
                    if not data:
                        break
                    result += data
                self.assertIn(b'400 Bad Request', result)
                self.assertIn(b'Connection: close', result)

    def test_session_idle_expiry_rotation_and_database_migration(self):
        self.setup_account()
        old = self.cookie
        self.request('/api/login', {'username':'测试管理员','password':'Secure-example-123'})
        self.assertEqual(self.request('/api/me',cookie=old)[0],401)
        session = self.app.store.session(self.cookie.split('=')[1])
        self.app.store.write('UPDATE sessions SET last_seen=? WHERE token=?',
                             (session['last_seen']-SESSION_IDLE_SECONDS-1,session['token']))
        self.assertEqual(self.request('/api/me')[0],401)
        import sqlite3
        legacy = Path(self.temp.name)/'legacy';legacy.mkdir()
        with sqlite3.connect(str(legacy/'web.sqlite3')) as db:
            db.execute('CREATE TABLE sessions(token TEXT PRIMARY KEY,csrf TEXT,expires REAL)')
            db.execute('INSERT INTO sessions VALUES (?,?,?)',('old','csrf',9999999999))
        migrated = Store(legacy)
        row = migrated.one('SELECT * FROM sessions')
        self.assertGreater(row['last_seen'],0)
        self.assertLess(row['expires'],9999999999)
        migrated.db.close()

    def test_file_scope_and_history_persistence(self):
        self.setup_account()
        project = Path(self.temp.name) / 'project'
        project.mkdir()
        (project / 'hello.txt').write_text('hello')
        (project / '.env').write_text('SECRET=test')
        (project / 'outside').symlink_to('/etc/passwd')
        (project / 'secret-link').symlink_to(project / '.env')
        (project / 'secret.pem').write_text('PRIVATE KEY')
        (project / '.ssh').mkdir()
        (project / '.ssh' / 'key').write_text('SSH KEY')
        (project / 'internal-link').symlink_to(project/'hello.txt')
        import os
        os.link(project/'.env',project/'hardlinked-secret')
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)', ('example','Example',str(project),1,1))
        self.app.store.item('example', {'id':'item1','type':'agentMessage','text':'durable history'})
        self.assertEqual(self.request('/api/files?thread=example&path=hello.txt')[1]['text'], 'hello')
        for path in ['../../etc/passwd', 'outside', '.env', 'secret-link', 'secret.pem', '.ssh/key',
                     'internal-link', 'hardlinked-secret']:
            self.assertEqual(self.request('/api/files?thread=example&path='+path)[0], 403)
        self.assertEqual(self.request('/api/threads/example/rename', {'title':'Renamed'})[0], 200)
        self.assertEqual(self.request('/api/threads/example')[1]['items'][0]['text'], 'durable history')
        store2 = Store(Path(self.temp.name))
        self.assertEqual(store2.thread('example')['title'], 'Renamed')
        self.assertEqual(store2.settings()['cwd'], self.app.store.settings()['cwd'])
        store2.db.close()
        self.app.store.write("UPDATE threads SET status='running' WHERE id='example'")
        self.assertEqual(self.request('/api/threads/example/archive', {})[0], 409)
        self.assertEqual(self.request('/api/threads/example/send', {'text':'hello'})[0], 409)
        self.app.store.write("UPDATE threads SET status='completed' WHERE id='example'")
        self.assertEqual(self.request('/api/threads/example/archive', {})[0], 200)
        self.assertEqual(self.request('/api/threads')[1]['threads'], [])

    def test_approval_response_requires_login_and_live_request(self):
        self.setup_account()
        store = self.app.store
        store.write('INSERT INTO threads(id,title,cwd,created,updated,status) VALUES (?,?,?,?,?,?)',
                    ('approval', 'Approval', self.temp.name, 1, 1, 'waiting'))
        bridge = self.app.bridge
        request = {'id': 77, 'method': 'item/commandExecution/requestApproval',
                   'params': {'threadId': 'approval', 'command': 'echo approved'}}
        bridge.requests['77'] = request
        sent = []
        bridge.send = sent.append
        self.assertEqual(self.request('/api/respond', {'id':77,'decision':'accept'}, cookie='')[0], 401)
        self.assertEqual(self.request('/api/respond', {'id':77,'decision':'accept'}, csrf=False)[0], 403)
        self.assertEqual(self.request('/api/respond', {'id':77,'decision':'invalid'})[0], 400)
        self.assertEqual(sent, [])
        self.assertEqual(self.request('/api/respond', {'id':77,'decision':'accept'})[0], 200)
        self.assertEqual(sent, [{'id':77,'result':{'decision':'accept'}}])
        self.assertEqual(store.thread('approval')['status'], 'running')
        self.assertEqual(self.request('/api/respond', {'id':77,'decision':'accept'})[0], 409)

    def test_stream_auth_revocation(self):
        self.setup_account()
        conn = http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=15)
        conn.request('GET','/api/events',headers={'Cookie':self.cookie})
        response = conn.getresponse()
        self.assertEqual(response.status,200)
        self.assertIn('text/event-stream',response.getheader('Content-Type'))
        self.assertEqual(response.readline(),b': connected\n')
        response.readline()
        self.app.store.publish({'method':'test/event','params':{'value':'hello'}})
        line = response.readline()
        while not line.startswith(b'id: '):
            line = response.readline()
        self.assertTrue(line.startswith(b'id: '))
        self.assertIn(b'hello',response.readline())
        response.readline()
        self.app.store.write('DELETE FROM sessions')
        with self.app.store.changed:
            self.app.store.changed.notify_all()
        lines = response.read()
        self.assertIn(b'event: expired',lines)
        conn.close()


if __name__ == '__main__':
    unittest.main()
