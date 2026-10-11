"""Switch UI language without altering content, drafts, attachments or an active stream."""
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect


def main():
    with tempfile.TemporaryDirectory(prefix='codex-language-') as directory:
        app = App(Path(directory) / 'data')
        app.bridge.call = lambda *args, **kwargs: {'data': []}
        app.bridge.ensure_loaded = lambda tid: None
        app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                        ('language-thread', '项目', directory, 1, 2))
        app.store.item('language-thread', {'id': 'original-message', 'type': 'agentMessage',
                                         'text': '设置\n\n```text\n文件变更\n```'})
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler); server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        errors = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(), args=['--no-sandbox', '--disable-dev-shm-usage'])
                context = browser.new_context(viewport={'width': 390, 'height': 844})
                page = context.new_page(); page.on('pageerror', lambda error: errors.append(str(error)))
                url = f'http://127.0.0.1:{server.server_port}'
                page.goto(url)
                expect(page.locator('#auth-title')).to_have_text('创建你的工作台账号')
                page.fill('#auth-username', 'languageadmin')
                page.fill('#auth-password', 'isolated-language-password')
                page.fill('#auth-confirm', 'isolated-language-password')
                page.locator('#auth-form [data-language-picker]').select_option('en')
                expect(page.locator('html')).to_have_attribute('lang', 'en')
                expect(page.locator('#auth-title')).to_have_text('Create your workspace account')
                expect(page.locator('#auth-password')).to_have_value('isolated-language-password')
                page.click('#auth-submit'); expect(page.locator('#workspace')).to_be_visible()
                page.evaluate("selectThread('language-thread')")
                expect(page.locator('#chat-title')).to_have_text('项目')
                expect(page.locator('.message.assistant p')).to_have_text('设置')
                expect(page.locator('.copy-button')).to_have_text('Copy')
                expect(page.locator('#prompt')).to_have_attribute('placeholder', 'Give Codex a task or ask a question')
                page.fill('#prompt', '未发送的草稿 Settings')
                page.locator('#image-input').set_input_files(str(Path(__file__).parent / 'fixtures/sample.png'))
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                page.evaluate('''() => {
                    window.languageStream = state.stream;
                    state.thread.status = 'running'; state.thread.turn_id = 'language-turn';
                    state.turns = [{id:'language-turn', status:'running', startedAt:Date.now()/1000-3}];
                    state.items.push({id:'language-reasoning', type:'reasoning', summary:['正在分析任务'],
                        webTurnId:'language-turn', webTiming:{startedAt:Date.now()/1000-2, streamed:true}});
                    state.requests = [{id:'language-question', method:'item/tool/requestUserInput',
                        params:{questions:[{id:'choice', header:'Question', question:'保留问题原文',
                            options:[{label:'原始选项', description:'保持不变'}]}]}}];
                    renderMessages(); renderRequests();
                }''')
                page.locator('.reasoning summary').click()
                page.locator('[data-question-id=choice]').select_option('__custom__')
                page.locator('[data-custom-for=choice]').fill('未提交的回答')
                page.click('#sidebar-open'); page.click('#open-settings')
                page.locator('#settings-dialog [data-language-picker]').select_option('zh-CN')
                expect(page.locator('#run-status')).to_have_text('运行中')
                expect(page.locator('#settings-dialog h2')).to_have_text('设置')
                page.locator('#settings-dialog [data-language-picker]').select_option('en')
                expect(page.locator('#run-status')).to_have_text('Running')
                expect(page.locator('#settings-dialog h2')).to_have_text('Settings')
                expect(page.locator('#prompt')).to_have_value('未发送的草稿 Settings')
                expect(page.locator('.attachment-tile.ready')).to_have_count(1)
                assert page.locator('.reasoning').get_attribute('open') is not None
                expect(page.locator('.reasoning-content')).to_have_text('正在分析任务')
                expect(page.locator('[data-custom-for=choice]')).to_have_value('未提交的回答')
                assert page.evaluate('state.stream === window.languageStream')
                expect(page.locator('#chat-title')).to_have_text('项目')
                expect(page.locator('.message.assistant p')).to_have_text('设置')
                expect(page.locator('.message.assistant code')).to_have_text('文件变更')
                page.click('#close-settings')
                expect(page.locator('#attach-image')).to_have_attribute('aria-label', 'Attach files or images')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.click('#sidebar-open'); page.click('#open-settings')
                page.screenshot(path=str(Path(__file__).resolve().parents[1] / 'artifacts/language-mobile-en.png'))
                page.click('#close-settings')
                # Persisted English is applied before bootstrap returns; loading remains themed.
                held = []
                page.route('**/api/bootstrap*', lambda route: held.append(route))
                page.reload(wait_until='domcontentloaded')
                expect(page.locator('#startup-message')).to_have_text('Restoring your conversation…')
                expect(page.locator('html')).to_have_attribute('lang', 'en')
                assert held; held.pop().continue_(); page.unroute('**/api/bootstrap*')
                expect(page.locator('#chat-title')).to_have_text('项目')
                expect(page.locator('#run-status')).to_have_text('Ready')
                expect(page.locator('.copy-button')).to_have_text('Copy')
                # Actual server-side validation messages are translated at the API boundary.
                page.click('#sidebar-open'); page.click('#open-settings'); page.locator('[data-tab=account]').click()
                page.click('#logout'); expect(page.locator('#auth-title')).to_have_text('Sign in to your workspace')
                expect(page.locator('#auth-form [data-language-picker]')).to_have_value('en')
                page.fill('#auth-username', 'languageadmin'); page.fill('#auth-password', 'incorrect-password')
                page.click('#auth-submit')
                expect(page.locator('#auth-error')).to_have_text('Incorrect username or password. 5 attempts remaining.')
                page.locator('#auth-form [data-language-picker]').select_option('zh-CN')
                expect(page.locator('#auth-title')).to_have_text('登录你的工作台')
                expect(page.locator('#auth-error')).to_have_text('账号或密码错误，还可尝试 5 次')
                page.reload(); expect(page.locator('#auth-title')).to_have_text('登录你的工作台')
                # Browser storage being disabled must still allow changing language for this page.
                page.add_init_script("Storage.prototype.getItem = Storage.prototype.setItem = () => { throw new DOMException('blocked','SecurityError'); };")
                page.reload(); expect(page.locator('#auth-screen')).to_be_visible()
                page.locator('#auth-form [data-language-picker]').select_option('en')
                expect(page.locator('#auth-title')).to_have_text('Sign in to your workspace')
                # User-owned names must stay unchanged even when they match a UI label exactly.
                app.store.write('UPDATE threads SET title=? WHERE id=?', ('新对话', 'language-thread'))
                other = browser.new_page(viewport={'width': 390, 'height': 844})
                other.on('pageerror', lambda error: errors.append(str(error)))
                other.goto(url)
                other.fill('#auth-username', 'languageadmin'); other.fill('#auth-password', 'isolated-language-password')
                other.click('#auth-submit'); expect(other.locator('#workspace')).to_be_visible()
                other.evaluate("selectThread('language-thread')")
                expect(other.locator('#chat-title')).to_have_text('新对话')
                other.click('#sidebar-open'); other.click('#open-settings')
                other.locator('#settings-dialog [data-language-picker]').select_option('en')
                expect(other.locator('#chat-title')).to_have_text('新对话')
                expect(other.locator('.message.assistant p')).to_have_text('设置')
                other.close()
                assert not errors, errors
                browser.close()
                print('Chinese/English UI, refresh, login errors, live task, draft, attachment, question, original content, mobile and storage fallback: PASS')
        finally:
            server.shutdown(); server.server_close(); app.store.db.close()


if __name__ == '__main__':
    main()
