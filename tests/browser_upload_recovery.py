"""Slow confirmations, invalid responses and missing browser timeout events recover safely."""
from pathlib import Path
import sys
import tempfile
import threading

from browser_support import chromium_path
from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer


def main():
    with tempfile.TemporaryDirectory(prefix='codex-upload-recovery-') as directory:
        app = App(Path(directory) / 'data')
        app.bridge.call = lambda *args, **kwargs: {'data': []}
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        release = threading.Event()
        entered = threading.Event()
        add = app.store.add_attachment

        def held(*args, **kwargs):
            entered.set()
            assert release.wait(15), 'Test did not release server validation'
            return add(*args, **kwargs)

        app.store.add_attachment = held
        errors = []
        sample = Path(__file__).parent / 'fixtures' / 'sample.png'
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                                            args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                page.fill('#auth-username', 'recoveryadmin')
                page.fill('#auth-password', 'isolated-upload-recovery')
                page.fill('#auth-confirm', 'isolated-upload-recovery')
                page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                page.set_input_files('#image-input', str(sample))
                assert entered.wait(5)
                expect(page.locator('.attachment-caption')).to_have_text('等待确认 1 秒')
                expect(page.locator('#send-button')).to_be_disabled()
                page.evaluate("setUILanguage('en')")
                expect(page.locator('.attachment-caption')).to_contain_text('Awaiting confirmation')
                release.set()
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                page.evaluate("setUILanguage('zh-CN'); clearAttachments()")
                page.wait_for_function('activeUploads === 0')

                # A successful HTTP response with null used to throw in onload and leave the promise pending.
                for body in ['null', '{}', '{"attachment":{"id":"bad","url":"https://example.com"}}']:
                    page.route('**/api/attachments?*', lambda route, request, body=body:
                               route.fulfill(status=201, content_type='application/json', body=body))
                    page.set_input_files('#image-input', str(sample))
                    expect(page.locator('.attachment-tile.error')).to_have_count(1)
                    assert page.evaluate('state.attachments[0].error') == '服务器返回了无效响应'
                    page.unroute('**/api/attachments?*')
                    page.click('.attachment-retry')
                    expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                    page.evaluate('clearAttachments()')
                    page.wait_for_function('activeUploads === 0')

                # Simulate a browser that reports 100% but never dispatches load/error/timeout.
                # Accelerate only the two-minute deadline, leaving the application timers alone.
                page.evaluate('''() => {
                    window.realXHR = window.XMLHttpRequest;
                    window.realSetTimeout = window.setTimeout;
                    window.setTimeout = (fn, delay, ...args) => realSetTimeout(fn, delay === 120000 ? 200 : delay, ...args);
                    window.XMLHttpRequest = class {
                        constructor() { this.upload = {}; }
                        open() {} setRequestHeader() {}
                        send() { this.upload.onprogress({lengthComputable:true, loaded:10, total:10}); }
                        abort() { this.onabort?.(); }
                    };
                }''')
                page.set_input_files('#image-input', str(sample))
                expect(page.locator('.attachment-tile.error')).to_have_count(1)
                assert page.evaluate('state.attachments[0].error') == '上传超时，请检查网络后重试'
                page.wait_for_function('activeUploads === 0')
                page.evaluate('window.XMLHttpRequest = realXHR; window.setTimeout = realSetTimeout')
                page.click('.attachment-retry')
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                assert not errors, errors
                browser.close()
                print('Upload confirmation, bilingual elapsed status, invalid response recovery, deadline and retry passed.')
        finally:
            release.set()
            server.shutdown()
            server.server_close()
            app.store.db.close()


if __name__ == '__main__':
    main()
