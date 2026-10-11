"""Browser security regressions; isolated database, no model calls, no real-account lockout."""
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect


def main():
    with tempfile.TemporaryDirectory(prefix='codex-web-security-') as directory:
        app = App(Path(directory))
        app.bridge.call = lambda *args, **kwargs: {'data': []}
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}'
        errors = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                    headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width': 1280, 'height': 900})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(url)
                page.fill('#auth-username', 'securityadmin')
                page.fill('#auth-password', 'browser-security-password')
                page.fill('#auth-confirm', 'browser-security-password')
                page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                page.click('#open-settings'); page.click('[data-tab=account]'); page.click('#logout')
                expect(page.locator('#auth-title')).to_have_text('登录你的工作台')
                page.fill('#auth-username', 'securityadmin')
                for attempt in range(1, 7):
                    page.fill('#auth-password', 'wrong')
                    page.click('#auth-submit')
                    if attempt < 6:
                        expect(page.locator('#auth-error')).to_contain_text(f'还可尝试 {6-attempt} 次')
                    else:
                        expect(page.locator('#auth-submit')).to_be_disabled()
                        expect(page.locator('#auth-submit')).to_contain_text('登录已锁定')
                print('Six wrong passwords lock the browser and show a countdown: PASS', flush=True)
                page.reload()
                expect(page.locator('#auth-submit')).to_be_disabled()
                expect(page.locator('#auth-error')).to_contain_text('刷新页面不会解除锁定')
                artifacts = Path(__file__).resolve().parents[1] / 'artifacts'
                artifacts.mkdir(exist_ok=True)
                page.screenshot(path=str(artifacts / 'login-locked.png'), animations='disabled')
                # A second browser and direct API requests cannot bypass the lock.
                other = browser.new_context()
                response = other.request.post(url + '/api/login', data={
                    'username': 'securityadmin', 'password': 'browser-security-password'})
                assert response.status == 423
                assert 350 <= int(response.headers['retry-after']) <= 360
                other.close()
                print('Reload and direct API bypass attempts remain locked: PASS', flush=True)
                # Fast-forward the persisted deadline instead of blocking for six real minutes.
                app.store.write('UPDATE auth_limits SET locked_until=? WHERE locked_until>0', (time.time()-1,))
                page.reload()
                expect(page.locator('#auth-submit')).to_be_enabled()
                expect(page.locator('#auth-password')).to_be_enabled()
                page.fill('#auth-username', 'securityadmin')
                page.fill('#auth-password', 'browser-security-password')
                page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible(timeout=15000)
                print('Expired lock automatically clears and the correct password works: PASS', flush=True)
                # Treat all model/tool text as untrusted browser input.
                app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                    ('xss-test', '<img src=x onerror="window.pwned=true">', directory, time.time(), time.time()))
                payload = '<img src=x onerror="window.pwned=true">\n<script>window.pwned=true</script>\n[click](javascript:window.pwned=true)\n**bold**\n```html\n<img src=x onerror="window.pwned=true">\n```'
                app.store.item('xss-test', {'id':'xss-user', 'type':'userMessage','content':[{'type':'text','text':payload}]})
                app.store.item('xss-test', {'id':'xss-agent','type':'agentMessage','text':payload})
                page.reload()
                page.locator('.thread-item').click()
                expect(page.locator('#messages')).to_contain_text('<img src=x')
                assert page.locator('#messages img, #messages script').count() == 0
                assert page.locator('#messages a[href^="javascript:"]').count() == 0
                assert not page.evaluate('Boolean(window.pwned)')
                assert not errors, errors
                print('Model text, code, titles and unsafe links cannot inject scripts: PASS', flush=True)
                browser.close()
        finally:
            server.shutdown(); server.server_close(); app.store.db.close()


if __name__ == '__main__':
    main()
