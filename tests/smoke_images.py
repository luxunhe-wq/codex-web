"""One real vision call using a generated image and an isolated account/project."""
import http.client
import json
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from PIL import Image, ImageDraw, ImageFont


def main():
    with tempfile.TemporaryDirectory(prefix='codex-image-smoke-') as directory:
        root = Path(directory)
        project = root / 'project'
        project.mkdir()
        code = str(100000 + secrets.randbelow(900000))
        image = Image.new('RGB', (800, 440), 'white')
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf', 72)
        draw.text((65, 25), code, fill='black', font=font)
        draw.rectangle((65, 160, 355, 365), fill=(220, 35, 45))
        draw.ellipse((450, 160, 655, 365), fill=(35, 90, 225))
        file = root / 'vision.png'
        image.save(file)
        app = App(root / 'data')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        cookie = csrf = ''
        tid = None

        def call(path, body=None, binary=None):
            nonlocal cookie, csrf
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=60)
            headers = {'Cookie': cookie, 'X-CSRF-Token': csrf, 'Content-Type': 'image/png' if binary else 'application/json'}
            connection.request('POST' if binary is not None or body is not None else 'GET', '/api' + path,
                               body=binary if binary is not None else json.dumps(body) if body is not None else None, headers=headers)
            response = connection.getresponse()
            data = json.loads(response.read())
            if response.getheader('Set-Cookie'):
                cookie = response.getheader('Set-Cookie').split(';')[0]
            csrf = data.get('csrf', csrf)
            connection.close()
            if response.status >= 400:
                raise RuntimeError((response.status, data))
            return data

        try:
            call('/setup', {'username': 'visiontest', 'password': 'isolated-vision-test-password'})
            call('/settings', {'cwd': str(project), 'effort': 'low', 'sandbox': 'read-only'})
            upload = call('/attachments?name=vision.png', binary=file.read_bytes())['attachment']
            thread = call('/threads', {})['thread']
            tid = thread['id']
            print('Testing native image input with server default model:', thread['model'], flush=True)
            call('/threads/' + tid + '/send', {'text': 'Read the six-digit number in the attached image, and identify the two shapes and their colors. Reply with only the number and shapes/colors in English. Do not call tools or read files.', 'attachments': [upload['id']]})
            deadline = time.monotonic() + 150
            while time.monotonic() < deadline:
                data = call('/threads/' + tid)
                if data['thread']['status'] not in ('running', 'waiting'):
                    assert data['thread']['status'] == 'completed', data['thread']['status']
                    answer = '\n'.join(item.get('text', '') for item in data['items'] if item['type'] == 'agentMessage')
                    assert code in answer, answer
                    assert all(term in answer.lower() for term in ('red', 'rectangle', 'blue', 'circle')), answer
                    assert not any(item['type'] in ('commandExecution', 'mcpToolCall', 'viewImage') for item in data['items'])
                    user = next(item for item in data['items'] if item['type'] == 'userMessage')
                    assert any(part.get('url') == upload['url'] for part in user['content']), user
                    print('Real native image recognition: PASS —', answer, flush=True)
                    return
                time.sleep(1)
            raise TimeoutError('Native image recognition did not finish within 150 seconds')
        finally:
            if tid:
                try:
                    app.bridge.call('thread/archive', {'threadId': tid})
                except Exception:
                    pass
            app.bridge.stop()
            if app.bridge.proc:
                app.bridge.proc.wait(timeout=15)
            server.shutdown()
            server.server_close()
            app.store.db.close()


if __name__ == '__main__':
    main()
