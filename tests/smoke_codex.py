"""Opt-in integration test: uses the installed Codex service and real model calls."""
import http.client
import json
import sys
import tempfile
import threading
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer


def main():
    with tempfile.TemporaryDirectory(prefix='codex-web-smoke-') as directory:
        root = Path(directory)
        project = root / 'project'
        project.mkdir()
        app = App(root / 'data')
        server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.daemon_threads = True
        server.app = app
        threading.Thread(target=server.serve_forever,daemon=True).start()
        cookie, csrf = '', ''
        def call(path,body=None):
            nonlocal cookie,csrf
            conn = http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=60)
            headers = {'Cookie':cookie,'Content-Type':'application/json','X-CSRF-Token':csrf}
            conn.request('GET' if body is None else 'POST','/api'+path,body=json.dumps(body) if body is not None else None,headers=headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.getheader('Set-Cookie'):cookie=response.getheader('Set-Cookie').split(';')[0]
            if 'csrf' in data:csrf=data['csrf']
            conn.close()
            if response.status>=400:raise RuntimeError((response.status,data))
            return data
        tid = None
        try:
            call('/setup',{'username':'smokeadmin','password':'temporary-test-password'})
            call('/settings',{'cwd':str(project),'effort':'low'})
            assert call('/models')['data']
            thread = call('/threads',{})['thread'];tid=thread['id']
            print('Created real Codex thread; model:',thread['model'],flush=True)
            def wait():
                deadline=time.time()+180
                while time.time()<deadline:
                    data=call('/threads/'+tid)
                    for request in data['requests']:
                        print('Approving smoke-test action:',request['method'],flush=True)
                        call('/respond',{'id':request['id'],'decision':'accept'})
                    if data['thread']['status'] not in ('running','waiting'):
                        assert data['thread']['status']=='completed',data
                        return data
                    time.sleep(1)
                raise RuntimeError('Real Codex test timed out')
            call('/threads/'+tid+'/send',{'text':'Remember this test code: 7319. Reply with only CODEX_WEB_OK. Do not call any tools.'})
            first=wait();messages=[i.get('text','') for i in first['items'] if i['type']=='agentMessage'];assert any('CODEX_WEB_OK' in t for t in messages),messages
            print('Real model reply and persisted streaming items: PASS',flush=True)
            call('/threads/'+tid+'/send',{'text':'What test code did I give you earlier? Reply with only that number. Do not call tools.'})
            second=wait();messages=[i.get('text','') for i in second['items'] if i['type']=='agentMessage'];assert '7319' in messages[-1],messages
            print('Continuous conversation context: PASS',flush=True)
            call('/threads/'+tid+'/send',{'text':'Create smoke.txt in the current working directory containing exactly browser-codex-tested, then run cat smoke.txt to verify it. Only operate on this file.'})
            third=wait();assert (project/'smoke.txt').read_text().strip()=='browser-codex-tested',third
            print('Actual project file modification and command execution: PASS',flush=True)
            assert any(i['type']=='commandExecution' for i in third['items'])
            app.bridge.stop()
            if app.bridge.proc:app.bridge.proc.wait(timeout=15)
            time.sleep(.2)
            call('/threads/'+tid+'/send',{'text':'After reconnecting, what was my original test code? Reply only with the number. Do not call tools.'})
            resumed=wait();messages=[i.get('text','') for i in resumed['items'] if i['type']=='agentMessage'];assert '7319' in messages[-1],messages
            print('Codex reconnection and resume: PASS',flush=True)
            call('/threads/'+tid+'/send',{'text':'For a cancellation test, run the shell command sleep 30 in the current project now. Do not modify files.'})
            deadline=time.time()+90
            while time.time()<deadline:
                data=call('/threads/'+tid)
                for request in data['requests']:
                    call('/respond',{'id':request['id'],'decision':'accept'})
                if any(i['type']=='commandExecution' and i.get('status')=='inProgress' for i in data['items']):
                    break
                time.sleep(.5)
            else:raise RuntimeError('Timed out waiting for long-running command')
            call('/threads/'+tid+'/interrupt',{})
            deadline=time.time()+15
            while time.time()<deadline:
                data=call('/threads/'+tid)
                if data['thread']['status']=='interrupted':break
                time.sleep(.25)
            else:raise RuntimeError('Interrupt did not complete')
            print('Stop a real running command from browser API: PASS',flush=True)

        finally:
            if tid:
                try:app.bridge.call('thread/archive',{'threadId':tid})
                except Exception:pass
            app.bridge.stop()
            server.shutdown();server.server_close()

if __name__=='__main__':main()
