"""Saved project folder workflows in an isolated account, without model calls."""
import os
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer, encode
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect


def main():
    with tempfile.TemporaryDirectory(prefix='codex-project-folders-') as directory:
        root = Path(directory)
        parent = root / 'projects'
        alpha = parent / '中文项目 alpha'
        beta = parent / 'beta'
        alpha.mkdir(parents=True)
        beta.mkdir()
        (alpha / 'src').mkdir()
        (beta / 'keep.txt').write_text('keep')
        (parent / '<img onerror=alert(1)>').mkdir()
        app = App(root / 'data')
        settings = app.store.settings()
        settings['cwd'] = str(parent)
        app.store.write('UPDATE settings SET value=? WHERE id=1', (encode(settings),))
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        counter = 0
        seen_directories = []

        def call(method, params, **kwargs):
            nonlocal counter
            if method == 'model/list':
                return {'data': []}
            if method == 'thread/start':
                counter += 1
                seen_directories.append(params['cwd'])
                return {'thread': {'id': 'project-thread-' + str(counter), 'cwd': params['cwd']}, 'model': 'test-model'}
            if method == 'turn/start':
                tid = params['threadId']
                turn = 'project-turn-' + str(counter)
                def event(method, **extra):
                    app.bridge.notification({'method': method, 'params': {'threadId': tid, 'turnId': turn, **extra}})
                event('turn/started', turn={'id': turn})
                event('item/completed', item={'id': turn + '-user', 'type': 'userMessage', 'content': params['input']})
                event('item/completed', item={'id': turn + '-answer', 'type': 'agentMessage', 'text': '项目目录验证完成。'})
                event('turn/completed', turn={'id': turn, 'status': 'completed'})
                return {'turn': {'id': turn}}
            return {}

        app.bridge.call = call
        app.bridge.ensure_loaded = lambda tid: None
        errors = []
        artifacts = Path(__file__).resolve().parents[1] / 'artifacts'
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                                            headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
                context = browser.new_context(viewport={'width': 1440, 'height': 950})
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(url)
                page.fill('#auth-username', 'projectadmin')
                page.fill('#auth-password', 'isolated-project-password')
                page.fill('#auth-confirm', 'isolated-project-password')
                page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                page.fill('#prompt', '保留正在编辑的草稿。')
                page.click('#add-project')
                expect(page.locator('#project-dialog')).to_be_visible()
                expect(page.locator('#folder-list')).to_contain_text('中文项目 alpha')
                assert page.locator('#folder-list img').count() == 0
                page.locator('.folder-entry').filter(has_text='中文项目 alpha').click()
                expect(page.locator('#folder-current-path')).to_have_text(str(alpha))
                page.click('#folder-up')
                expect(page.locator('#folder-current-path')).to_have_text(str(parent))
                page.locator('.folder-entry').filter(has_text='中文项目 alpha').click()
                page.click('#save-project')
                expect(page.locator('#project-dialog')).not_to_be_visible()
                expect(page.get_by_role('button', name='选择项目 中文项目 alpha', exact=True)).to_be_visible()
                expect(page.locator('#composer-project')).to_have_text('中文项目 alpha')
                expect(page.locator('#prompt')).to_have_value('保留正在编辑的草稿。')
                page.click('#send-button')
                expect(page.locator('#messages')).to_contain_text('项目目录验证完成。')
                expect(page.locator('#run-status')).to_have_text('就绪')
                assert seen_directories == [str(alpha)]

                # Add another folder by path and keep the old conversation in its original group.
                page.click('#add-project')
                page.fill('#project-path', str(beta))
                page.click('#save-project')
                expect(page.locator('#composer-project')).to_have_text('beta')
                alpha_group = page.locator('.project-group').filter(has=page.get_by_role('button', name='选择项目 中文项目 alpha', exact=True))
                expect(alpha_group.locator('.thread-item')).to_have_count(1)
                page.fill('#prompt', 'beta 项目任务')
                page.click('#send-button')
                expect(page.locator('#messages')).to_contain_text('项目目录验证完成。')
                expect(page.locator('#run-status')).to_have_text('就绪')
                assert seen_directories == [str(alpha), str(beta)]
                page.get_by_role('button', name='选择项目 中文项目 alpha', exact=True).click()
                expect(page.locator('#welcome')).to_be_visible()
                expect(page.locator('#composer-project')).to_have_text('中文项目 alpha')
                page.reload()
                expect(page.get_by_role('button', name='选择项目 beta', exact=True)).to_be_visible()
                expect(page.locator('#composer-project')).to_have_text('中文项目 alpha')

                # Duplicate adds reuse the folder; errors keep the picker open.
                project_count = page.locator('.project-group').count()
                page.click('#add-project')
                page.fill('#project-path', str(alpha))
                page.click('#save-project')
                expect(page.locator('#project-dialog')).not_to_be_visible()
                expect(page.locator('.project-group')).to_have_count(project_count)
                page.click('#add-project')
                page.fill('#project-path', str(parent / 'missing'))
                page.click('#save-project')
                expect(page.locator('#project-error')).to_contain_text('文件夹不存在')
                expect(page.locator('#project-dialog')).to_be_visible()
                page.click('#cancel-project')

                # Remove only the saved entry, preserving both the files and conversation.
                beta_group = page.locator('.project-group').filter(has=page.get_by_role('button', name='选择项目 beta', exact=True))
                beta_group.get_by_role('button', name='beta 项目操作', exact=True).click()
                page.get_by_role('button', name='从列表移除', exact=True).click()
                expect(page.get_by_role('button', name='选择项目 beta', exact=True)).to_have_count(0)
                expect(page.locator('#thread-list')).to_contain_text('beta 项目任务')
                assert (beta / 'keep.txt').read_text() == 'keep'
                assert app.store.thread('project-thread-2')['cwd'] == str(beta)
                page.locator('#toast').evaluate('(el) => { el.hidden = true; }')
                page.screenshot(path=str(artifacts / 'workspace-projects.png'), animations='disabled')

                # A new browser context has no saved local/session storage and must recover from the server.
                page.click('#open-settings')
                page.click('[data-tab=account]')
                page.click('#logout')
                context.close()
                fresh = browser.new_context(viewport={'width': 390, 'height': 844})
                page = fresh.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(url)
                page.fill('#auth-username', 'projectadmin')
                page.fill('#auth-password', 'isolated-project-password')
                page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                expect(page.locator('#composer-project')).to_have_text('中文项目 alpha')
                page.click('#sidebar-open')
                expect(page.get_by_role('button', name='选择项目 中文项目 alpha', exact=True)).to_be_visible()
                expect(page.get_by_role('button', name='选择项目 beta', exact=True)).to_have_count(0)
                page.click('#add-project')
                expect(page.locator('#project-dialog')).to_be_visible()
                expect(page.locator('#folder-current-path')).to_have_text(str(alpha))
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.screenshot(path=str(artifacts / 'project-picker-mobile.png'), animations='disabled')
                assert not errors, errors
                browser.close()
                print('Folder browsing, persistence in a fresh browser, selected directory, grouped history, deduplication, safe removal and mobile: PASS', flush=True)
        finally:
            server.shutdown()
            server.server_close()
            app.store.db.close()


if __name__ == '__main__':
    main()
