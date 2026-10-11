"""Opt-in Playwright browser smoke test, using an isolated database and project."""
import os
import sys
import tempfile
import threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect


def main():
    with tempfile.TemporaryDirectory(prefix='codex-web-browser-') as directory:
        root=Path(directory)
        project=root/'project';project.mkdir()
        app=App(root/'data')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.daemon_threads=True;server.app=app
        threading.Thread(target=server.serve_forever,daemon=True).start()
        artifacts=Path(__file__).resolve().parents[1]/'artifacts'
        artifacts.mkdir(exist_ok=True)
        errors=[];tid=None
        try:
            with sync_playwright() as p:
                executable=chromium_path()
                browser=p.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
                context=browser.new_context(viewport={'width':1440,'height':950})
                page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                expect(page.locator('#auth-title')).to_have_text('创建你的工作台账号')
                page.screenshot(path=str(artifacts/'login-desktop.png'),full_page=True,animations='disabled')
                page.fill('#auth-username','browseradmin');page.fill('#auth-password','browser-test-password');page.fill('#auth-confirm','browser-test-password')
                page.click('#auth-submit');expect(page.locator('#workspace')).to_be_visible()
                expect(page.locator('#connection-label')).to_have_text('已连接本机 Codex',timeout=15000)
                page.screenshot(path=str(artifacts/'workspace-desktop.png'),full_page=True,animations='disabled')
                page.click('#open-settings');page.fill('#setting-cwd',str(project));page.select_option('#setting-effort','low');page.click('#general-form button[type=submit]')
                expect(page.locator('#settings-dialog')).not_to_be_visible()
                page.fill('#prompt','Reply with exactly BROWSER_CODEX_OK. Do not call tools.');page.click('#send-button')
                expect(page.locator('#messages')).to_contain_text('BROWSER_CODEX_OK',timeout=90000)
                expect(page.locator('#run-status')).to_have_text('就绪',timeout=90000)
                tid=app.store.all('SELECT id FROM threads')[0]['id']
                print('Browser create account, model connection, send real task, streaming output: PASS',flush=True)
                page.reload();expect(page.locator('#messages')).to_contain_text('BROWSER_CODEX_OK',timeout=15000)
                page.click('#thread-menu');page.get_by_text('重命名对话',exact=True).wait_for();page.on('dialog',lambda dialog:dialog.accept('浏览器测试会话'));page.get_by_text('重命名对话',exact=True).click()
                expect(page.locator('#chat-title')).to_have_text('浏览器测试会话')
                page.fill('#search','不存在的对话');expect(page.locator('#thread-list')).to_contain_text('没有找到匹配');page.fill('#search','')
                print('Browser history reload, rename, search: PASS',flush=True)
                page.click('#open-settings');page.select_option('#setting-theme','dark');page.click('#general-form button[type=submit]');expect(page.locator('html')).to_have_attribute('data-theme','dark')
                page.screenshot(path=str(artifacts/'workspace-dark.png'),full_page=True,animations='disabled')
                page.click('#open-settings');page.click('[data-tab=account]');page.fill('#current-password','browser-test-password');page.fill('#setting-username','updatedadmin');page.fill('#new-password','updated-password-123');page.fill('#confirm-password','updated-password-123');page.click('#credentials-form button[type=submit]');expect(page.locator('#account-name')).to_have_text('updatedadmin')
                page.click('#open-settings');page.click('[data-tab=account]');page.click('#logout');expect(page.locator('#auth-title')).to_have_text('登录你的工作台')
                page.fill('#auth-username','updatedadmin');page.fill('#auth-password','updated-password-123');page.click('#auth-submit');expect(page.locator('#workspace')).to_be_visible()
                print('Browser dark theme, change credentials, logout, login with new password: PASS',flush=True)
                page.set_viewport_size({'width':390,'height':844});page.click('#sidebar-open');expect(page.locator('#sidebar')).to_have_class('sidebar open');page.click('#new-chat');expect(page.locator('#welcome')).to_be_visible()
                expect(page.locator('#sidebar')).to_have_class('sidebar')
                page.locator('#toast').evaluate('(el) => el.hidden = true')
                page.screenshot(path=str(artifacts/'workspace-mobile.png'),full_page=True,animations='disabled')
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile layout overflows'
                page.click('#sidebar-open');page.click('#open-settings');expect(page.locator('#settings-dialog')).to_be_visible();page.screenshot(path=str(artifacts/'settings-mobile.png'),full_page=True,animations='disabled')
                print('Mobile sidebar, composer, settings and no horizontal overflow: PASS',flush=True)
                assert not errors, errors
                context.close();browser.close()
        finally:
            if tid:
                try:app.bridge.call('thread/archive',{'threadId':tid})
                except Exception:pass
            app.bridge.stop();server.shutdown();server.server_close()

if __name__=='__main__':main()
