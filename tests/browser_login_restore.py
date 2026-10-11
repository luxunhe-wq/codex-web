"""Remember login across refresh, browser restart, idle time and network errors."""
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect


def main():
    with tempfile.TemporaryDirectory(prefix='codex-login-restore-') as directory:
        app = App(Path(directory) / 'data')
        app.bridge.call = lambda *args, **kwargs: {'data': []}
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler); server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        for tid, updated in [('remember-a', 1), ('remember-b', 2)]:
            app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                            (tid, tid, directory, 1, updated))
            app.store.item(tid, {'id': tid + '-answer', 'type': 'agentMessage', 'text': tid + ' conversation'})
        errors = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                                            args=['--no-sandbox', '--disable-dev-shm-usage'])
                context = browser.new_context(); page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.add_init_script('''window.loginFlashes = 0;
                    new MutationObserver(() => {
                        const auth = document.getElementById('auth-screen');
                        if (auth && !auth.hidden) window.loginFlashes++;
                    }).observe(document, {subtree:true,attributes:true,childList:true});''')
                url = f'http://127.0.0.1:{server.server_port}'
                page.goto(url)
                page.fill('#auth-username', 'restoreadmin'); page.fill('#auth-password', 'isolated-login-restore-password')
                page.fill('#auth-confirm', 'isolated-login-restore-password'); page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                page.evaluate("selectThread('remember-a')")
                for _ in range(3):
                    page.reload()
                    expect(page.locator('#chat-title')).to_have_text('remember-a')
                    expect(page.locator('#auth-screen')).to_be_hidden()
                    assert page.evaluate('window.loginFlashes') == 0
                app.store.write('UPDATE sessions SET last_seen=?,expires=?', (time.time() - 2*86400, time.time() + 86400))
                page.reload(); expect(page.locator('#chat-title')).to_have_text('remember-a')
                cookie = next(c for c in context.cookies() if c['name'] == 'codex_web')
                assert cookie['expires'] > time.time() + 29*86400 and cookie['httpOnly']

                def unavailable(route):
                    route.fulfill(status=503, content_type='application/json', body='{"error":"temporarily unavailable"}')
                page.route('**/api/bootstrap*', unavailable)
                page.reload(); expect(page.locator('#startup-retry')).to_be_visible()
                expect(page.locator('#auth-screen')).to_be_hidden()
                page.unroute('**/api/bootstrap*', unavailable)
                page.click('#startup-retry'); expect(page.locator('#chat-title')).to_have_text('remember-a')

                # Browser storage_state preserves cookies/localStorage, but no sessionStorage.
                stored = context.storage_state(); context.close()
                context = browser.new_context(storage_state=stored); page = context.new_page()
                page.goto(url); expect(page.locator('#chat-title')).to_have_text('remember-a')
                expect(page.locator('#auth-screen')).to_be_hidden()

                # Storage disabled: valid cookie still restores the latest server conversation.
                page.add_init_script("Storage.prototype.getItem = () => { throw new DOMException('blocked','SecurityError'); };")
                page.reload(); expect(page.locator('#chat-title')).to_have_text('remember-b')
                expect(page.locator('#auth-screen')).to_be_hidden()
                page.click('#open-settings'); page.locator('[data-tab="account"]').click(); page.click('#logout')
                expect(page.locator('#auth-screen')).to_be_visible()
                page.reload(); expect(page.locator('#auth-screen')).to_be_visible()
                expect(page.locator('#workspace')).to_be_hidden()
                assert not errors, errors
                browser.close()
                print('Refresh, idle login, cookie renewal, browser restart, storage fallback, network retry and logout: PASS')
        finally:
            server.shutdown(); server.server_close(); app.store.db.close()


if __name__ == '__main__':
    main()
