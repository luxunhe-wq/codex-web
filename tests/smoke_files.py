"""One actual model call: text PDF, scanned PDF and CSV in an isolated account."""
import http.client
import json
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import time
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from document_fixtures import pdf_file


def main():
    with tempfile.TemporaryDirectory(prefix='codex-file-smoke-') as directory:
        project = Path(directory) / 'project'
        project.mkdir()
        app = App(Path(directory) / 'data')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        cookie = csrf = ''
        tid = None

        def call(path, body=None, binary=None):
            nonlocal cookie, csrf
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=60)
            conn.request('POST' if body is not None or binary is not None else 'GET', '/api' + path,
                         body=binary if binary is not None else json.dumps(body) if body is not None else None,
                         headers={'Cookie': cookie, 'X-CSRF-Token': csrf, 'Content-Type': 'application/octet-stream' if binary is not None else 'application/json'})
            response = conn.getresponse()
            result = json.loads(response.read())
            if response.getheader('Set-Cookie'):
                cookie = response.getheader('Set-Cookie').split(';')[0]
            csrf = result.get('csrf', csrf)
            conn.close()
            if response.status >= 400:
                raise RuntimeError((response.status, result))
            return result

        try:
            call('/setup', {'username': 'filesmoke', 'password': 'isolated-files-smoke-password'})
            call('/settings', {'cwd': str(project), 'effort': 'low', 'sandbox': 'read-only'})
            code, scan = [str(100000 + secrets.randbelow(900000)) for _ in range(2)]
            first, second = [secrets.randbelow(900) + 100 for _ in range(2)]
            fixtures = {'text.pdf': pdf_file('PDF code: ' + code), 'scan.pdf': pdf_file('SCAN ' + scan, scanned=True),
                        'amounts.csv': ('name,amount\na,%d\nb,%d\n' % (first, second)).encode()}
            files = [call('/attachments?kind=file&name=' + quote(name), binary=data)['attachment'] for name, data in fixtures.items()]
            thread = call('/threads', {})['thread']
            tid = thread['id']
            print('Testing file understanding with:', thread['model'], flush=True)
            call('/threads/' + tid + '/send', {'text': 'Read the code in text.pdf, the code shown in scan.pdf, and sum the amount column in amounts.csv. Reply only PDF:<code>;SCAN:<code>;TOTAL:<sum>. Use the provided file content and document page image. Do not use tools or read files.',
                                              'attachments': [file['id'] for file in files]})
            deadline = time.monotonic() + 150
            while time.monotonic() < deadline:
                data = call('/threads/' + tid)
                if data['thread']['status'] not in ('running', 'waiting'):
                    assert data['thread']['status'] == 'completed', data['thread']['status']
                    answer = '\n'.join(item.get('text', '') for item in data['items'] if item['type'] == 'agentMessage')
                    assert all(value in answer for value in (code, scan, str(first + second))), answer
                    assert not any(item['type'] in ('commandExecution', 'mcpToolCall', 'imageView') for item in data['items'])
                    user = next(item for item in data['items'] if item['type'] == 'userMessage')
                    assert sum(part['type'] == 'file' for part in user['content']) == 3
                    print('Text PDF, scanned PDF and CSV analysis: PASS —', answer, flush=True)
                    return
                time.sleep(1)
            raise TimeoutError('File understanding did not finish within 150 seconds')
        finally:
            if tid:
                try:
                    app.bridge.call('thread/archive', {'threadId': tid})
                except Exception:
                    pass
            app.bridge.stop()
            if app.bridge.proc:
                app.bridge.proc.wait(timeout=15)
            server.shutdown(); server.server_close(); app.store.db.close()


if __name__ == '__main__':
    main()
