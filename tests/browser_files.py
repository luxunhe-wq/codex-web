import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from document_fixtures import office_files, pdf_file
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect


def main():
    with tempfile.TemporaryDirectory(prefix='codex-files-ui-') as directory:
        app = App(Path(directory) / 'data')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        seen, errors = [], []

        def call(method, params, **kwargs):
            if method == 'model/list':
                return {'data': []}
            if method == 'thread/start':
                return {'thread': {'id': 'file-ui', 'cwd': directory}, 'model': 'test-model'}
            if method == 'turn/start':
                seen.extend(params['input'])
                for event, value in [('turn/started', {'turn': {'id': 'file-turn'}}),
                                     ('item/completed', {'item': {'id': 'file-user', 'type': 'userMessage', 'content': params['input']}}),
                                     ('item/completed', {'item': {'id': 'file-answer', 'type': 'agentMessage', 'text': '附件已分析：销售总额为 40。'}}),
                                     ('turn/completed', {'turn': {'id': 'file-turn', 'status': 'completed'}})]:
                    app.bridge.notification({'method': event, 'params': {'threadId': 'file-ui', 'turnId': 'file-turn', **value}})
                return {'turn': {'id': 'file-turn'}}
            return {}
        app.bridge.call = call
        app.bridge.ensure_loaded = lambda tid: None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                                            args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width': 1440, 'height': 950})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                page.fill('#auth-username', 'filesadmin'); page.fill('#auth-password', 'isolated-files-ui-password')
                page.fill('#auth-confirm', 'isolated-files-ui-password'); page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                page.set_input_files('#image-input', [{'name': 'sales.xlsx', 'mimeType': 'application/octet-stream', 'buffer': office_files()['sales.xlsx']},
                                                      {'name': 'scan.pdf', 'mimeType': 'application/pdf', 'buffer': pdf_file(scanned=True)},
                                                      {'name': 'photo.png', 'mimeType': 'image/png', 'buffer': (Path(__file__).parent / 'fixtures/sample.png').read_bytes()}])
                expect(page.locator('.attachment-tile.ready')).to_have_count(3)
                page.get_by_role('button', name='预览文件 sales.xlsx', exact=True).click()
                expect(page.locator('#file-preview-text')).to_contain_text('B3=40')
                page.click('#close-file')
                page.get_by_role('button', name='预览文件 scan.pdf', exact=True).click()
                expect(page.locator('#file-preview-pages img')).to_have_count(1)
                page.click('#close-file')
                page.fill('#prompt', '分析附件中的内容。'); page.click('#send-button')
                expect(page.locator('.message-file')).to_have_count(2)
                expect(page.locator('.message-image')).to_have_count(1)
                expect(page.locator('#messages')).to_contain_text('销售总额为 40')
                assert 'B3=40' in json.dumps(seen, ensure_ascii=False)
                assert sum(part['type'] == 'localImage' for part in seen) == 2
                page.reload()
                expect(page.locator('.message-file')).to_have_count(2)
                page.locator('.message-file').filter(has_text='sales.xlsx').click()
                expect(page.locator('#file-preview-text')).to_contain_text('咖啡')
                with page.expect_download() as event:
                    page.click('#file-download')
                assert event.value.suggested_filename == 'sales.xlsx'
                page.click('#close-file')
                page.set_viewport_size({'width': 390, 'height': 844})
                # Generic files also use the clipboard and drop handlers.
                page.locator('#prompt').evaluate('''el => {
                    const data = new DataTransfer();
                    data.items.add(new File(['name,amount\\ntea,17'], 'pasted.csv', {type:'text/csv'}));
                    el.dispatchEvent(new ClipboardEvent('paste', {clipboardData:data,bubbles:true,cancelable:true}));
                }''')
                expect(page.locator('.file-tile.ready')).to_have_count(1)
                page.get_by_role('button', name='移除文件 pasted.csv', exact=True).click()
                page.set_input_files('#image-input', {'name': 'unsafe.html', 'mimeType': 'text/html', 'buffer': b'<script>window.uploadExecuted=true</script>'})
                expect(page.locator('.file-tile.ready')).to_have_count(1)
                page.get_by_role('button', name='预览文件 unsafe.html', exact=True).click()
                expect(page.locator('#file-preview-text')).to_contain_text('<script>')
                assert page.evaluate('() => !window.uploadExecuted')
                page.click('#close-file')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(Path(__file__).resolve().parents[1] / 'artifacts/file-attachments-mobile.png'), animations='disabled')
                assert not errors, errors
                browser.close()
                print('Mixed files/images, Office preview, scanned PDF, download, history, clipboard, escaping and mobile: PASS')
        finally:
            server.shutdown(); server.server_close(); app.store.db.close()


if __name__ == '__main__':
    main()
