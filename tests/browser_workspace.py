"""Isolated UI checks with deterministic Codex events; no model calls or real account changes."""
import json
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
    with tempfile.TemporaryDirectory(prefix='codex-workspace-ui-') as directory:
        app = App(Path(directory) / 'data')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        workers = []
        count = 0

        def stream(tid, text, turn_id):
            def event(method, **params):
                app.bridge.notification({'method': method, 'params': {'threadId': tid, 'turnId': turn_id, **params}})
            event('turn/started', turn={'id': turn_id})
            user = {'id': turn_id + '-user', 'type': 'userMessage', 'content': [{'type': 'text', 'text': text}]}
            event('item/started', item=user)
            event('item/completed', item=user.copy())
            reasoning = {'id': turn_id + '-reasoning', 'type': 'reasoning', 'summary': []}
            event('item/started', item=reasoning)
            time.sleep(.35)
            event('item/reasoning/summaryTextDelta', itemId=reasoning['id'], summaryIndex=0, delta='检查项目结构和任务要求。')
            time.sleep(1.3)
            event('item/reasoning/summaryTextDelta', itemId=reasoning['id'], summaryIndex=1, delta='选择适合现有代码的修改方式。')
            event('item/completed', item={'id': reasoning['id'], 'type': 'reasoning', 'summary': []})
            command = {'id': turn_id + '-command', 'type': 'commandExecution', 'command': 'python3 -m unittest',
                       'cwd': directory, 'status': 'inProgress', 'aggregatedOutput': ''}
            event('item/started', item=command)
            for _ in range(12):
                event('item/commandExecution/outputDelta', itemId=command['id'], delta='test passed\n')
                time.sleep(.025)
            command.update(status='completed', exitCode=0, aggregatedOutput='12 tests passed')
            event('item/completed', item=command)
            agent = {'id': turn_id + '-agent', 'type': 'agentMessage', 'phase': 'finalAnswer', 'text': ''}
            event('item/started', item=agent)
            for delta in ['已完成界面更新。\n\n', '**验证通过**：思考计时、流式消息和历史恢复。\n\n', '```python\nprint("ready")\n```']:
                event('item/agentMessage/delta', itemId=agent['id'], delta=delta)
                agent['text'] += delta
                time.sleep(.15)
            event('item/completed', item=agent)
            event('turn/completed', turn={'id': turn_id, 'status': 'completed'})

        def call(method, params, **kwargs):
            nonlocal count
            if method == 'model/list':
                return {'data': [{'model': 'test-model', 'displayName': 'Codex'}]}
            if method == 'thread/start':
                return {'thread': {'id': 'ui-thread', 'cwd': directory}, 'model': 'test-model'}
            if method == 'turn/start':
                count += 1
                turn_id = 'ui-turn-' + str(count)
                # The response deliberately takes time: the message must appear before it returns.
                worker = threading.Thread(target=stream, args=(params['threadId'], params['input'][0]['text'], turn_id))
                workers.append(worker)
                worker.start()
                time.sleep(.65)
                return {'turn': {'id': turn_id}}
            return {}

        app.bridge.call = call
        app.bridge.ensure_loaded = lambda tid: None
        artifacts = Path(__file__).resolve().parents[1] / 'artifacts'
        errors = []
        requests = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                                            headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page(viewport={'width': 1440, 'height': 950})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda request: requests.append((request.method, request.url)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                page.fill('#auth-username', 'uitest')
                page.fill('#auth-password', 'isolated-ui-test-password')
                page.fill('#auth-confirm', 'isolated-ui-test-password')
                page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                expect(page.locator('#connection-label')).to_have_text('已连接本机 Codex')
                page.screenshot(path=str(artifacts / 'workspace-v2-desktop.png'), animations='disabled')
                page.fill('#prompt', '请更新界面并验证。')
                start = time.perf_counter()
                page.click('#send-button')
                expect(page.locator('.user-bubble')).to_have_text('请更新界面并验证。', timeout=500)
                optimistic_ms = round((time.perf_counter() - start) * 1000)
                expect(page.locator('.reasoning strong')).to_contain_text('正在思考')
                expect(page.locator('.reasoning strong')).to_contain_text('1 秒')
                page.click('.reasoning summary')
                page.reload()
                expect(page.locator('.reasoning strong')).to_contain_text('思考')
                expect(page.locator('#run-status')).to_have_text('就绪', timeout=15000)
                expect(page.locator('.reasoning strong')).to_have_text('已思考 1 秒')
                page.click('.reasoning summary')
                expect(page.locator('.reasoning-content')).to_contain_text('选择适合现有代码')
                expect(page.locator('.turn-timing')).to_contain_text('已完成 · 耗时')
                expect(page.locator('.turn-timing')).to_contain_text('思考 1 秒')
                expect(page.locator('.user-bubble')).to_have_count(1)
                page.screenshot(path=str(artifacts / 'workspace-v2-timing.png'), animations='disabled')
                page.reload()
                expect(page.locator('.turn-timing')).to_contain_text('思考 1 秒')

                # A long conversation must preserve historical DOM nodes and the reader's position.
                app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                                ('long-thread', '长对话性能检查', directory, time.time(), time.time()))
                with app.store.transaction():
                    for index in range(240):
                        app.store.item('long-thread', {'id': 'history-' + str(index), 'type': 'agentMessage',
                                                      'text': '历史消息 ' + str(index) + '\n\n' + '保留历史节点，避免重复解析和渲染。' * 12})
                page.evaluate('refreshThreads()')
                page.get_by_role('button', name='长对话性能检查', exact=False).click()
                expect(page.locator('.message.assistant')).to_have_count(80)
                page.click('#load-history')
                expect(page.locator('.message.assistant')).to_have_count(160)
                page.click('#load-history')
                expect(page.locator('.message.assistant')).to_have_count(240)
                assert page.locator('.message.assistant').first.get_attribute('data-item-id') == 'history-0'
                page.evaluate('window.historyNode = document.querySelector("[data-item-id=history-0]"); window.changesMutations = 0; new MutationObserver(records => window.changesMutations += records.length).observe(document.getElementById("changes-body"), {childList:true, subtree:true})')
                requests.clear()
                page.fill('#prompt', '验证长对话性能。')
                page.click('#send-button')
                expect(page.locator('.reasoning strong')).to_contain_text('正在思考')
                page.locator('#scroll-area').evaluate('(el) => { el.scrollTop = 0; }')
                expect(page.locator('#run-status')).to_have_text('就绪', timeout=15000)
                assert page.evaluate('window.historyNode === document.querySelector("[data-item-id=history-0]") && window.historyNode.isConnected')
                assert page.evaluate('window.changesMutations') == 0
                assert page.locator('#scroll-area').evaluate('(el) => el.scrollTop') < 100
                assert not any(method == 'GET' and url.endswith('/api/threads/long-thread') for method, url in requests)
                expect(page.locator('.user-bubble')).to_have_count(1)
                print(json.dumps({'optimistic_message_ms': optimistic_ms, 'history_nodes_preserved': 240,
                                  'unchanged_diff_mutations': 0, 'history_refetches_after_send': 0}, ensure_ascii=False), flush=True)

                page.click('#open-settings')
                page.select_option('#setting-theme', 'dark')
                page.click('#general-form button[type=submit]')
                page.get_by_role('button', name='请更新界面并验证。', exact=False).click()
                page.screenshot(path=str(artifacts / 'workspace-v2-dark.png'), animations='disabled')
                page.set_viewport_size({'width': 390, 'height': 844})
                page.click('#sidebar-open')
                page.click('#new-chat')
                expect(page.locator('#welcome')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.locator('#toast').evaluate('(el) => { el.hidden = true; }')
                page.screenshot(path=str(artifacts / 'workspace-v2-mobile.png'), animations='disabled')
                page.click('#sidebar-open')
                page.click('#open-settings')
                expect(page.locator('#settings-dialog')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                assert not errors, errors
                print('Timing, reload, optimistic send, incremental rendering, reader scroll, dark theme and mobile: PASS', flush=True)
                browser.close()
        finally:
            for worker in workers:
                worker.join(timeout=10)
            app.bridge.stop()
            server.shutdown()
            server.server_close()
            app.store.db.close()


if __name__ == '__main__':
    main()
