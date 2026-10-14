"""Installed plugin/skill management and native skill input, without a model request."""
from pathlib import Path
import sys
import tempfile
import threading

from browser_support import chromium_path
from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer


def main():
    with tempfile.TemporaryDirectory(prefix='codex-extensions-') as directory:
        app = App(Path(directory) / 'data')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        calls, inputs, errors = [], [], []
        skill_path = str(Path(directory) / 'demo' / 'SKILL.md')
        enabled, plugin_enabled, unsupported = True, True, False

        def call(method, params, **kwargs):
            nonlocal enabled, plugin_enabled
            calls.append(method)
            if method == 'model/list': return {'data': []}
            if method == 'plugin/installed':
                if unsupported:
                    from server import ApiError
                    raise ApiError('Method not found', 502)
                return {'marketplaces': [{'name': 'demo-market', 'plugins': [
                    {'id': 'demo@demo-market', 'name': 'demo-plugin', 'installed': True,
                     'enabled': plugin_enabled, 'interface': {'displayName': '演示插件',
                                                              'shortDescription': '<img src=x onerror=alert(1)>'}}]}]}
            if method == 'skills/list':
                return {'data': [{'cwd': params['cwds'][0], 'errors': [], 'skills': [
                    {'name': 'demo-skill', 'description': '演示技能', 'path': skill_path,
                     'scope': 'user', 'enabled': enabled}]}]}
            if method == 'skills/config/write': enabled = params['enabled']
            if method == 'config/value/write': plugin_enabled = params['value']
            if method == 'thread/start':
                return {'thread': {'id': 'extension-browser', 'cwd': directory}, 'model': 'demo-model'}
            if method == 'turn/start':
                inputs.extend(params['input'])
                for event, value in [('turn/started', {'turn': {'id': 'extension-turn'}}),
                                     ('item/completed', {'item': {'id': 'demo-user', 'type': 'userMessage', 'content': params['input']}}),
                                     ('item/completed', {'item': {'id': 'demo-answer', 'type': 'agentMessage', 'text': '演示技能已收到。'}}),
                                     ('turn/completed', {'turn': {'id': 'extension-turn', 'status': 'completed'}})]:
                    app.bridge.notification({'method': event, 'params': {'threadId': 'extension-browser', 'turnId': 'extension-turn', **value}})
                return {'turn': {'id': 'extension-turn'}}
            return {}
        app.bridge.call = call
        app.bridge.ensure_loaded = lambda tid: None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(), args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width': 1440, 'height': 960})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                page.fill('#auth-username', 'extensionadmin'); page.fill('#auth-password', 'isolated-extension-password')
                page.fill('#auth-confirm', 'isolated-extension-password'); page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                assert 'skills/list' not in calls and 'plugin/installed' not in calls
                page.fill('#prompt', '检查测试页面')
                page.set_input_files('#image-input', str(Path(__file__).parent / 'fixtures/sample.png'))
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                page.click('#open-extensions')
                expect(page.locator('.extension-card')).to_have_count(2)
                expect(page.locator('#extensions-list img')).to_have_count(0)
                expect(page.locator('#extensions-list')).to_contain_text('<img src=x onerror=alert(1)>')
                page.get_by_role('button', name='禁用 demo-plugin', exact=True).click()
                expect(page.get_by_role('button', name='启用 demo-plugin', exact=True)).to_be_enabled()
                assert plugin_enabled is False
                page.get_by_role('button', name='禁用 demo-skill', exact=True).click()
                expect(page.get_by_role('button', name='在对话中使用', exact=True)).to_be_disabled()
                page.get_by_role('button', name='启用 demo-skill', exact=True).click()
                expect(page.get_by_role('button', name='在对话中使用', exact=True)).to_be_enabled()
                page.get_by_role('button', name='在对话中使用', exact=True).click()
                expect(page.locator('#prompt')).to_have_value('$demo-skill 检查测试页面')
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                page.click('#send-button')
                expect(page.locator('.message.assistant')).to_contain_text('演示技能已收到。')
                assert {'type': 'skill', 'name': 'demo-skill', 'path': skill_path} in inputs
                expect(page.locator('.user-text')).to_contain_text('$demo-skill')
                page.reload()
                expect(page.locator('.user-text')).to_contain_text('$demo-skill')
                page.click('#open-extensions')
                expect(page.get_by_role('button', name='启用 demo-plugin', exact=True)).to_be_enabled()
                page.locator('[data-tab=general]').click()
                page.locator('#settings-dialog [data-language-picker]').select_option('en')
                page.locator('[data-tab=extensions]').click()
                expect(page.locator('.extension-card')).to_have_count(2)
                expect(page.get_by_role('button', name='Use in conversation', exact=True)).to_be_enabled()
                page.set_viewport_size({'width': 390, 'height': 844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(Path('artifacts') / 'extensions-mobile-en.png'))
                unsupported = True
                page.click('#refresh-extensions')
                expect(page.locator('#extensions-list')).to_contain_text('Upgrade Codex')
                expect(page.get_by_role('button', name='Use in conversation', exact=True)).to_be_enabled()
                assert not errors, errors
                browser.close()
                print('Plugin/skill persistence, escaping, draft/attachment preservation, native input, bilingual mobile and version fallback: PASS')
        finally:
            server.shutdown(); server.server_close(); app.store.db.close()


if __name__ == '__main__':
    main()
