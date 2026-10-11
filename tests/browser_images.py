"""Attachment selection, paste, drop, retry, history and mobile without model calls."""
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect


def main():
    with tempfile.TemporaryDirectory(prefix='codex-browser-images-') as directory:
        root = Path(directory)
        app = App(root / 'data')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        fixtures = Path(__file__).parent / 'fixtures'
        png = (fixtures / 'sample.png').read_bytes()
        seen = []
        count = 0

        def call(method, params, **kwargs):
            nonlocal count
            if method == 'model/list':
                return {'data': []}
            if method == 'thread/start':
                return {'thread': {'id': 'image-browser-thread', 'cwd': directory}, 'model': 'test-model'}
            if method == 'turn/start':
                count += 1
                turn = 'image-browser-turn-' + str(count)
                seen.append(json.loads(json.dumps(params['input'])))
                def event(method, **extra):
                    app.bridge.notification({'method': method, 'params': {'threadId': params['threadId'], 'turnId': turn, **extra}})
                event('turn/started', turn={'id': turn})
                event('item/started', item={'id': turn + '-user', 'type': 'userMessage', 'content': params['input']})
                event('item/completed', item={'id': turn + '-user', 'type': 'userMessage', 'content': params['input']})
                event('item/completed', item={'id': turn + '-answer', 'type': 'agentMessage', 'text': '已收到图片，可进行识别。'})
                event('turn/completed', turn={'id': turn, 'status': 'completed'})
                return {'turn': {'id': turn}}
            return {}

        app.bridge.call = call
        app.bridge.ensure_loaded = lambda tid: None
        errors = []
        artifacts = Path(__file__).resolve().parents[1] / 'artifacts'
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                                            headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width': 1440, 'height': 950})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                page.fill('#auth-username', 'imageadmin')
                page.fill('#auth-password', 'isolated-image-test-password')
                page.fill('#auth-confirm', 'isolated-image-test-password')
                page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                # Decodable camera files may have data after the JPEG end marker.
                photo = (fixtures / 'sample.jpg').read_bytes() + b'\0\0Camera metadata\0'
                page.set_input_files('#image-input', [
                    {'name': 'sample.png', 'mimeType': 'image/png', 'buffer': png},
                    {'name': 'sample.jpg', 'mimeType': 'image/jpeg', 'buffer': photo},
                ])
                expect(page.locator('.attachment-tile.ready')).to_have_count(2)
                expect(page.locator('#send-button')).to_be_enabled()
                assert page.locator('.attachment-tile img').evaluate_all('(images) => images.every(image => image.complete && image.naturalWidth > 0)')
                page.screenshot(path=str(artifacts / 'composer-images.png'), animations='disabled')
                page.get_by_role('button', name='移除图片 sample.jpg', exact=True).click()
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)

                # Clipboard paste and file drop use the same attachment path.
                encoded = base64.b64encode(png).decode()
                page.locator('#prompt').evaluate("""(el, encoded) => {
                    const transfer = new DataTransfer();
                    transfer.items.add(new File([Uint8Array.from(atob(encoded), c => c.charCodeAt(0))], 'pasted.png', {type:'image/png'}));
                    el.dispatchEvent(new ClipboardEvent('paste', {clipboardData: transfer, bubbles: true, cancelable: true}));
                }""", encoded)
                expect(page.locator('.attachment-tile.ready')).to_have_count(2)
                page.locator('#workspace').evaluate("""(el, encoded) => {
                    const transfer = new DataTransfer();
                    transfer.items.add(new File([Uint8Array.from(atob(encoded), c => c.charCodeAt(0))], 'dropped.png', {type:'image/png'}));
                    el.dispatchEvent(new DragEvent('drop', {dataTransfer:transfer, bubbles:true, cancelable:true}));
                }""", encoded)
                expect(page.locator('.attachment-tile.ready')).to_have_count(3)
                page.fill('#prompt', '请识别这三张图片。')
                page.click('#send-button')
                expect(page.locator('#messages .message-image')).to_have_count(3)
                expect(page.locator('#messages')).to_contain_text('已收到图片，可进行识别。')
                assert sum(part['type'] == 'localImage' for part in seen[0]) == 3
                page.reload()
                expect(page.locator('#messages .message-image')).to_have_count(3)
                page.locator('.message-image').first.click()
                expect(page.locator('#image-dialog')).to_be_visible()
                assert page.locator('#image-viewer-image').evaluate('(image) => image.complete && image.naturalWidth === 32')
                page.click('#close-image')
                page.screenshot(path=str(artifacts / 'image-message-history.png'), animations='disabled')

                # Failed uploads remain visible and can be retried without reselecting the file.
                def fail(route):
                    route.fulfill(status=503, content_type='application/json', body='{"error":"模拟上传失败"}')
                page.route('**/api/attachments?*', fail)
                page.set_input_files('#image-input', str(fixtures / 'sample.png'))
                expect(page.locator('.attachment-tile.error')).to_have_count(1)
                expect(page.locator('#send-button')).to_be_disabled()
                page.unroute('**/api/attachments?*', fail)
                page.get_by_role('button', name='重试', exact=True).click()
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                expect(page.locator('#send-button')).to_be_enabled()
                page.click('#send-button')
                expect(page.locator('#messages .message-image')).to_have_count(4)
                expect(page.locator('#messages .message.assistant')).to_have_count(2)
                assert len(seen[1]) == 1 and seen[1][0]['type'] == 'localImage'

                # SVG is a file attachment, with an escaped text preview and forced download.
                page.set_input_files('#image-input', {'name': 'evil.svg', 'mimeType': 'image/svg+xml', 'buffer': b'<svg></svg>'})
                expect(page.locator('.file-tile.ready')).to_have_count(1)
                page.get_by_role('button', name='移除文件 evil.svg', exact=True).click()
                page.locator('#workspace').evaluate("""el => {
                    const transfer = new DataTransfer();
                    transfer.items.add(new File([new Uint8Array(10*1024*1024+1)], 'large.png', {type:'image/png'}));
                    el.dispatchEvent(new DragEvent('drop', {dataTransfer:transfer,bubbles:true,cancelable:true}));
                }""")
                expect(page.locator('#toast')).to_contain_text('最大 10 MB')
                expect(page.locator('.attachment-tile')).to_have_count(0)

                page.set_viewport_size({'width': 390, 'height': 844})
                page.set_input_files('#image-input', str(fixtures / 'sample.png'))
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.locator('#toast').evaluate('(el) => {el.hidden = true;}')
                page.screenshot(path=str(artifacts / 'image-composer-mobile.png'), animations='disabled')
                assert not errors, errors
                browser.close()
                print('Selection, paste, drop, native image payloads, image-only sends, history, preview, retry and mobile: PASS', flush=True)
        finally:
            server.shutdown()
            server.server_close()
            app.store.db.close()


if __name__ == '__main__':
    main()
