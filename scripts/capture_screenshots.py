"""Capture the real UI using fictional data only; never starts Codex or reads its config.

Optional development dependencies: pip install playwright Pillow
Install Chromium with: playwright install chromium
Run: python3 scripts/capture_screenshots.py
Use CHROMIUM_PATH to select an existing Chromium installation.
Chinese screenshots require an installed CJK font (e.g. fonts-noto-cjk).
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs' / 'images'
ASSETS = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/style.css': ('style.css', 'text/css; charset=utf-8'),
          '/favicon.svg': ('favicon.svg', 'image/svg+xml')}


def demo_data(language, theme, mobile=False):
    english = language == 'en'
    cwd = '/workspace/demo-shop'
    title = 'Improve the product page' if english else '优化商品展示页面'
    thread = {'id': 'demo-thread', 'title': title, 'cwd': cwd,
              'created': 1700000000, 'updated': 1700000042, 'status': 'idle'}
    changes = [{'path': cwd + '/src/product.css', 'kind': {'type': 'update'},
                'diff': '@@ Product grid @@\n-.products { display: block; }\n+.products {\n+  display: grid;\n+  gap: 24px;\n+  grid-template-columns: repeat(3, 1fr);\n+}\n+@media (max-width: 640px) {\n+  .products { grid-template-columns: 1fr; }\n+}'}]
    prompt = ('Make the product page responsive, and check the tests.' if english else
              '请优化商品展示页面，让桌面和手机上都能清晰浏览，并检查测试。')
    summary = 'Check the layout and mobile breakpoints' if english else '检查页面布局与移动端适配'
    reply = ('### The product page is ready\n\n'
             '- Added a responsive grid: three columns on desktop, one on mobile.\n'
             '- Improved spacing and keyboard focus states.\n'
             '- All 12 demo tests passed.\n\n'
             'Changes are in `src/product.css`. You can review the diff in the side panel.' if english else
             '### 商品页面已优化\n\n'
             '- 响应式网格：桌面三列，手机单列。\n'
             '- 统一卡片间距，完善键盘焦点样式。\n'
             '- 演示测试全部通过，共 12 项。\n\n'
             '修改位于 `src/product.css`，可在右侧查看文件变更。')
    if mobile:
        reply = '已完成手机适配：商品卡片自动切换为单列，按钮更方便点击。\n\n演示测试 12 项全部通过。'
    items = [
        {'id': 'demo-user', 'type': 'userMessage', 'content': [{'type': 'text', 'text': prompt}]},
        {'id': 'demo-reasoning', 'type': 'reasoning', 'summary': [summary],
         'webTiming': {'startedAt': 1700000000, 'completedAt': 1700000008,
                       'measurement': 'observed', 'streamed': True}},
        {'id': 'demo-command', 'type': 'commandExecution', 'command': 'npm test',
         'cwd': cwd, 'status': 'completed', 'exitCode': 0,
         'aggregatedOutput': 'Test Files  3 passed (3)\n     Tests  12 passed (12)\n  Duration  1.24s'},
        {'id': 'demo-change', 'type': 'fileChange', 'changes': changes},
        {'id': 'demo-assistant', 'type': 'agentMessage', 'text': reply},
    ]
    for item in items:
        item['webTurnId'] = 'demo-turn'
    conversation = {'thread': thread, 'items': items, 'requests': [], 'seq': 0,
                    'hasMore': False, 'allChanges': changes,
                    'changePaths': [change['path'] for change in changes],
                    'turns': [{'id': 'demo-turn', 'startedAt': 1700000000,
                               'completedAt': 1700000042, 'status': 'completed'}]}
    return {'authenticated': True, 'username': 'demo', 'csrf': 'demo-only', 'seq': 0,
            'settings': {'cwd': cwd, 'theme': theme, 'model': '', 'effort': 'high',
                         'sandbox': 'workspace-write', 'approvalPolicy': 'on-request'},
            'projects': [{'id': 'demo-shop', 'path': cwd, 'name': 'demo-shop', 'available': True},
                         {'id': 'demo-notes', 'path': '/workspace/demo-notes',
                          'name': 'demo-notes', 'available': True}],
            'threads': [thread, {'id': 'demo-previous', 'title': 'Add a search filter' if english else '添加商品搜索',
                                'cwd': cwd, 'updated': 1699999900, 'status': 'idle'},
                        {'id': 'demo-notes-thread', 'title': 'Organize the README' if english else '整理使用说明',
                         'cwd': '/workspace/demo-notes', 'updated': 1699999800, 'status': 'idle'}],
            'conversation': conversation}


class DemoHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            try:
                while not self.server.stopping.is_set():
                    self.wfile.write(b': demo only\n\n')
                    self.wfile.flush()
                    self.server.stopping.wait(1)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if path == '/api/bootstrap':
            body, mime = json.dumps(self.server.fixture).encode(), 'application/json'
        elif path == '/api/models':
            body, mime = b'{"data": []}', 'application/json'
        elif path in ASSETS:
            name, mime = ASSETS[path]
            body = (ROOT / 'static' / name).read_bytes()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), DemoHandler)
    server.stopping = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_port}'
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None,
                                                  args=['--no-sandbox', '--disable-dev-shm-usage'])
            for name, language, theme, width, height in [
                ('desktop-light', 'zh-CN', 'light', 1440, 960),
                ('desktop-dark', 'zh-CN', 'dark', 1440, 960),
                ('mobile', 'zh-CN', 'light', 390, 844),
                ('desktop-en', 'en', 'light', 1440, 960),
            ]:
                server.fixture = demo_data(language, theme, mobile=width < 600)
                context = browser.new_context(viewport={'width': width, 'height': height},
                                              device_scale_factor=1, reduced_motion='reduce')
                # Prevent external requests, including accidental future analytics/assets.
                context.route('**/*', lambda route: route.continue_() if
                              route.request.url.startswith(origin + '/') else route.abort())
                context.add_init_script("localStorage.setItem('codex-web-language', " + json.dumps(language) + ');')
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(origin)
                expect(page.locator('#workspace')).to_be_visible()
                expect(page.locator('.message.assistant')).to_be_visible()
                expect(page.locator('#connection-label')).to_have_text(
                    'Connected to local Codex' if language == 'en' else '已连接本机 Codex')
                if name == 'desktop-dark':
                    page.click('#show-changes')
                    expect(page.locator('.file-card')).to_be_visible()
                if name == 'desktop-light':
                    page.locator('details[data-item-id="demo-command"] summary').click()
                page.evaluate("async () => { await document.fonts.ready; document.getElementById('scroll-area').scrollTop = 0; }")
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                # Only fixture data can appear in the page; no real backend/config is used.
                assert page.locator('#account-name').text_content() == 'demo'
                assert page.evaluate('state.settings.cwd') == '/workspace/demo-shop'
                path = OUTPUT / (name + '.png')
                page.screenshot(path=str(path), animations='disabled')
                # Re-encode pixels without source/browser metadata.
                with Image.open(path) as screenshot:
                    clean = Image.new('RGB', screenshot.size)
                    clean.paste(screenshot)
                clean.save(path, optimize=True)
                assert path.stat().st_size < 3 * 1024 * 1024
                print(f'{path.relative_to(ROOT)}: {width}x{height}, {path.stat().st_size // 1024} KiB')
                context.close()
            browser.close()
        if errors:
            raise RuntimeError('Browser errors: ' + '; '.join(errors))
    finally:
        server.stopping.set()
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
