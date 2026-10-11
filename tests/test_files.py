import http.client
import json
from pathlib import Path
import sys
import time
import unittest
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_server
from server import ApiError, Store, MAX_FILE_BYTES
from document_fixtures import archive, office_files, pdf_file


class FileTests(unittest.TestCase):
    setUp = test_server.WebTests.setUp
    tearDown = test_server.WebTests.tearDown
    request = test_server.WebTests.request
    setup_account = test_server.WebTests.setup_account

    def upload(self, data=b'hello world', name='notes.txt', **headers):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=30)
        conn.request('POST', '/api/attachments?kind=file&name=' + quote(name), body=data,
                     headers={'Cookie': self.cookie, 'X-CSRF-Token': self.csrf, 'Content-Type': 'application/octet-stream', **headers})
        response = conn.getresponse()
        result = json.loads(response.read())
        status = response.status
        conn.close()
        return status, result

    def test_files_require_auth_csrf_and_size_limit(self):
        self.assertEqual(self.upload()[0], 401)
        self.setup_account()
        self.assertEqual(self.upload(**{'X-CSRF-Token': ''})[0], 403)
        self.assertEqual(self.upload(**{'Content-Length': str(MAX_FILE_BYTES + 1)})[0], 413)
        self.assertEqual(self.upload(b'not a pdf', 'bad.pdf')[0], 400)
        self.assertEqual(self.upload(b'broken archive', 'bad.docx')[0], 400)

    def test_text_office_and_archives_are_readable_and_private(self):
        self.setup_account()
        cases = [('中文.txt', '中文内容'.encode('gb18030'), '中文内容'),
                 ('data.csv', b'item,amount\ntea,17\ncoffee,23', 'coffee,23'),
                 ('data.json', b'{"total":40}', '"total":40'),
                 ('script.py', b'print("a code file")', 'a code file'),
                 ('report.docx', office_files()['report.docx'], '下周上线'),
                 ('sales.xlsx', office_files()['sales.xlsx'], 'B3=40 [公式: SUM(B1:B2)]'),
                 ('slides.pptx', office_files()['slides.pptx'], '验证通过'),
                 ('sources.zip', archive({'../../escape.txt': 'archived content'}), 'archived content')]
        for name, data, expected in cases:
            with self.subTest(name=name):
                status, result = self.upload(data, name)
                self.assertEqual(status, 201, result)
                attachment = result['attachment']
                self.assertEqual(attachment['kind'], 'file')
                self.assertNotIn('analysis', attachment)
                preview = self.request(attachment['url'] + '/preview')[1]
                self.assertIn(expected, preview['text'])
                self.assertEqual(self.request(attachment['url'], cookie='')[0], 401)
                self.assertEqual(self.request(attachment['url'] + '/preview', cookie='')[0], 401)
                self.assertEqual(self.request(attachment['url'])[1], data)
        self.assertFalse((Path(self.temp.name) / 'escape.txt').exists())
        # Even uploaded HTML is downloaded, and its preview is JSON text.
        html = self.upload(b'<script>alert(1)</script>', '../unsafe.html')[1]['attachment']
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        conn.request('GET', html['url'], headers={'Cookie': self.cookie})
        response = conn.getresponse()
        self.assertIn('attachment;', response.getheader('Content-Disposition'))
        self.assertEqual(response.getheader('Content-Type'), 'application/octet-stream')
        response.read(); conn.close()

    def test_pdf_text_and_scanned_pages(self):
        self.setup_account()
        for scanned in (False, True):
            with self.subTest(scanned=scanned):
                status, result = self.upload(pdf_file(scanned=scanned), 'invoice.pdf')
                self.assertEqual(status, 201, result)
                preview = self.request(result['attachment']['url'] + '/preview')[1]
                self.assertEqual(result['attachment']['pages'], 1)
                if scanned:
                    self.assertEqual(len(preview['pages']), 1)
                    url = preview['pages'][0]['url']
                    self.assertTrue(self.request(url)[1].startswith(b'\x89PNG'))
                    self.assertEqual(self.request(url, cookie='')[0], 401)
                    self.assertEqual(self.request(url.rsplit('/', 1)[0] + '/999')[0], 404)
                else:
                    self.assertIn('84731', preview['text'])

    def test_file_context_is_sent_but_history_stays_compact(self):
        self.setup_account()
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('files', '新对话', self.temp.name, 1, 1))
        self.app.bridge.ensure_loaded = lambda tid: None
        file = self.upload(b'nonce=483926\namount=40', 'report.txt')[1]['attachment']
        seen = []
        def call(method, params):
            seen.extend(params['input'])
            for event, value in [('turn/started', {'turn': {'id': 'file-turn'}}),
                                 ('item/started', {'item': {'id': 'file-user', 'type': 'userMessage', 'content': params['input']}}),
                                 ('item/completed', {'item': {'id': 'file-user', 'type': 'userMessage', 'content': params['input']}}),
                                 ('turn/completed', {'turn': {'id': 'file-turn', 'status': 'completed'}})]:
                self.app.bridge.notification({'method': event, 'params': {'threadId': 'files', 'turnId': 'file-turn', **value}})
            return {'turn': {'id': 'file-turn'}}
        self.app.bridge.call = call
        self.assertEqual(self.request('/api/threads/files/send', {'text': '', 'attachments': [file['id']]})[0], 200)
        self.assertIn('483926', json.dumps(seen))
        data = self.request('/api/threads/files')[1]
        self.assertEqual(data['items'][0]['content'][0]['type'], 'file')
        self.assertEqual(data['items'][0]['content'][0]['url'], file['url'])
        self.assertNotIn('483926', json.dumps(data))
        self.assertNotIn(str(self.app.store.attachment_directory), json.dumps(data))
        self.assertEqual(data['thread']['title'], '文件对话')
        self.assertEqual(self.request(file['url'] + '/remove', {})[0], 409)
        reopened = Store(Path(self.temp.name))
        self.assertEqual(reopened.attachment(file['id'])['kind'], 'file')
        reopened.db.close()

    def test_failed_sends_and_unused_documents_are_cleaned(self):
        self.setup_account()
        file = self.upload(pdf_file(scanned=True), 'scan.pdf')[1]['attachment']
        folder = self.app.store.attachment_directory / file['id']
        self.assertTrue(folder.exists())
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('files', '新对话', self.temp.name, 1, 1))
        self.app.bridge.ensure_loaded = lambda tid: None
        self.app.bridge.call = lambda *args: (_ for _ in ()).throw(ApiError('Unavailable', 502))
        self.assertEqual(self.request('/api/threads/files/send', {'text': 'read', 'attachments': [file['id']]})[0], 502)
        self.assertIsNone(self.app.store.attachment(file['id'])['thread_id'])
        self.app.store.write('UPDATE attachments SET created=? WHERE id=?', (time.time() - 90000, file['id']))
        self.app.store.attachments_pruned_at = 0
        self.app.store.prune_unused_attachments()
        self.assertFalse(folder.exists())
        self.assertEqual(self.request(file['url'])[0], 404)

    def test_long_files_are_explicitly_truncated(self):
        self.setup_account()
        file = self.upload(b'x' * 200000, 'long.txt')[1]['attachment']
        preview = self.request(file['url'] + '/preview')[1]
        self.assertTrue(preview['truncated'])
        self.assertEqual(len(preview['text']), 20000)
        self.assertEqual(self.request(file['url'])[1], b'x' * 200000)
