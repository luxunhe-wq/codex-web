"""Batched reasoning, short streams, legacy history and live waiting; no model calls."""
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect


def main():
    with tempfile.TemporaryDirectory(prefix='codex-reasoning-ui-') as directory:
        app = App(Path(directory) / 'data')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        app.bridge.call = lambda *args, **kwargs: {'data': []}
        app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                        ('reasoning-ui', '思考计时回归', directory, time.time(), time.time()))
        errors = []

        def event(method, at=None, **params):
            packet = {'method': method, 'params': {'threadId': 'reasoning-ui', 'turnId': 'reasoning-turn', **params}}
            if at is None:
                app.bridge.notification(packet)
            else:
                with patch('server.time.time', return_value=at):
                    app.bridge.notification(packet)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                                            headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width': 390, 'height': 844})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                page.fill('#auth-username', 'timingadmin')
                page.fill('#auth-password', 'isolated-timing-test-password')
                page.fill('#auth-confirm', 'isolated-timing-test-password')
                page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()

                # Replay the real failure: opaque start/end events arrive almost together.
                now = time.time() - 3
                event('turn/started', now, turn={'id': 'reasoning-turn'})
                event('item/started', now + 1, item={'id': 'batched', 'type': 'reasoning', 'summary': []})
                event('item/completed', now + 1.007, item={'id': 'batched', 'type': 'reasoning', 'summary': []})
                # History created before measurement provenance was recorded.
                app.store.item('reasoning-ui', {'id': 'legacy', 'type': 'reasoning', 'summary': [],
                                               'webTurnId': 'reasoning-turn', 'webTiming': {
                                                   'startedAt': now + 1.1, 'completedAt': now + 1.107, 'durationMs': 7}})
                event('item/started', now + 2, item={'id': 'short', 'type': 'reasoning', 'summary': []})
                event('item/reasoning/textDelta', now + 2.1, itemId='short', delta='private streamed text')
                event('item/completed', now + 2.2, item={'id': 'short', 'type': 'reasoning', 'summary': []})
                page.evaluate("selectThread('reasoning-ui')")
                expect(page.locator('[data-reasoning-id=batched]')).to_have_text('思考完成')
                expect(page.locator('[data-reasoning-id=legacy]')).to_have_text('思考完成')
                expect(page.locator('[data-reasoning-id=short]')).to_have_text('已思考 不足 1 秒')
                expect(page.locator('#working-label')).to_have_text('正在思考 / 等待回复')
                expect(page.locator('#working-time')).to_contain_text(re.compile(r'已等待 [1-9]\d* 秒'))
                before = page.locator('#working-time').inner_text()
                expect(page.locator('#working-time')).not_to_have_text(before, timeout=3000)
                assert '思考 0 秒' not in page.locator('#messages').inner_text()
                page.reload()
                expect(page.locator('[data-reasoning-id=batched]')).to_have_text('思考完成')
                expect(page.locator('[data-reasoning-id=legacy]')).to_have_text('思考完成')
                expect(page.locator('[data-reasoning-id=short]')).to_have_text('已思考 不足 1 秒')

                # A reasoning result may arrive while a parallel command is still running.
                command = {'id': 'parallel-command', 'type': 'commandExecution', 'command': 'test command',
                           'cwd': directory, 'status': 'inProgress', 'aggregatedOutput': ''}
                event('item/started', item=command.copy())
                event('item/started', item={'id': 'parallel-reasoning', 'type': 'reasoning', 'summary': []})
                event('item/completed', item={'id': 'parallel-reasoning', 'type': 'reasoning', 'summary': []})
                expect(page.locator('#working-label')).to_have_text('正在执行命令')
                expect(page.locator('#working-time')).not_to_contain_text('已等待')
                command.update(status='completed', exitCode=0)
                event('item/completed', item=command)
                expect(page.locator('#working-label')).to_have_text('正在思考 / 等待回复')
                event('turn/completed', turn={'id': 'reasoning-turn', 'status': 'completed'})
                expect(page.locator('#run-status')).to_have_text('就绪')
                expect(page.locator('.turn-timing')).to_contain_text('已记录思考 不足 1 秒')
                expect(page.locator('.turn-timing')).to_contain_text('部分思考耗时未提供')
                page.reload()
                expect(page.locator('.turn-timing')).to_contain_text('部分思考耗时未提供')
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                artifacts = Path(__file__).resolve().parents[1] / 'artifacts'
                page.screenshot(path=str(artifacts / 'reasoning-timing-fixed-mobile.png'), animations='disabled')
                assert not errors, errors
                browser.close()
                print('Batched events, subsecond streams, legacy history, waiting timer, parallel tools and mobile: PASS')
        finally:
            server.shutdown()
            server.server_close()
            app.store.db.close()


if __name__ == '__main__':
    main()
