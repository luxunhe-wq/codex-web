"""Navigation correctness and performance with 350 messages, throttled network and CPU; no model calls."""
import sys, tempfile, threading, time, json, os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect
from unittest.mock import patch
with tempfile.TemporaryDirectory() as d:
 app=App(Path(d)/'data'); app.bridge.call=lambda *a,**k:{'data':[]}
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.app=app
 threading.Thread(target=server.serve_forever,daemon=True).start()
 with app.store.transaction():
  for tid in ('perf-a','perf-b'):
   app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',(tid,tid,d,1,1))
   for i in range(350):
    if i%3==0:
     item={'id':tid+str(i),'type':'commandExecution','command':'python3 checks.py','cwd':d,'status':'completed','exitCode':0,'aggregatedOutput':'\n'.join('test_%04d passed: %s'%(n,'abcdefghij'*8) for n in range(65))}
    elif i%3==1:
     item={'id':tid+str(i),'type':'fileChange','changes':[{'path':'src/file.py','diff':'\n'.join('+ line_%04d = "%s"'%(n,'abcdefghij'*8) for n in range(65))}]}
    else:
     item={'id':tid+str(i),'type':'agentMessage','text':'This is the response with **formatting**.\n\n'+'We checked the project and validated the change. '*12}
    app.store.item(tid,item)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=chromium_path(),args=['--no-sandbox','--disable-dev-shm-usage'])
  ctx=browser.new_context();page=ctx.new_page();url=f'http://127.0.0.1:{server.server_port}'
  errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  ctx.request.post(url+'/api/setup',data={'username':'perfadmin','password':'perf-test-password-123'})
  session=ctx.new_cdp_session(page);session.send('Network.enable');session.send('Network.emulateNetworkConditions',{'offline':False,'latency':100,'downloadThroughput':200000,'uploadThroughput':200000});session.send('Emulation.setCPUThrottlingRate',{'rate':4})
  page.goto(url);page.wait_for_function('() => state.csrf && state.threads.length === 2')
  start=time.perf_counter();page.evaluate("selectThread('perf-a')");first=round((time.perf_counter()-start)*1000)
  page.evaluate("selectThread('perf-b')")
  start=time.perf_counter();page.evaluate("selectThread('perf-a')");switch=round((time.perf_counter()-start)*1000)
  start=time.perf_counter();page.reload();page.wait_for_function("() => state.thread?.id==='perf-a' && document.querySelector('[data-item-id]')");reload=round((time.perf_counter()-start)*1000)
  metrics={'first_thread_ms':first,'revisit_ms':switch,'reload_ms':reload,'rendered_items':page.locator('[data-item-id]').count(),'DOM_nodes':page.locator('#messages *').count()}
  assert first < 2000 and switch < 1000 and reload < 3000, metrics
  assert metrics['rendered_items'] == 80
  assert metrics['DOM_nodes'] < 1000
  assert page.locator('details[data-item-id] pre').evaluate_all('(nodes) => nodes.every(node => !node.textContent)')
  assert page.locator('#changes-body .diff-line').count() == 0
  command=page.locator('details[data-item-id]').filter(has=page.locator('strong',has_text='执行命令')).first
  command.locator('summary').click()
  expect(command.locator('pre')).to_contain_text('test_0000 passed')
  page.click('#show-changes')
  expect(page.locator('.file-card')).to_have_count(117)
  page.click('#close-changes')
  while page.evaluate('() => state.hasMore'):
   page.evaluate('loadEarlierMessages()')
  expect(page.locator('[data-item-id]')).to_have_count(350)
  assert page.locator('[data-item-id]').first.get_attribute('data-item-id') == 'perf-a0'

  # A delayed snapshot must replay events received while switching.
  gate={'enabled':True}; started=threading.Event();release=threading.Event()
  original=Handler.json
  def slow_snapshot(handler,*args,**kwargs):
   if gate['enabled'] and handler.path.startswith('/api/threads/perf-b?'):
    started.set();release.wait(timeout=8)
   return original(handler,*args,**kwargs)
  with patch.object(Handler,'json',slow_snapshot):
   page.evaluate("void selectThread('perf-b')")
   assert started.wait(timeout=3)
   try:
    for method,params in [('turn/started',{'turn':{'id':'switch-live'}}),
                         ('item/completed',{'item':{'id':'switch-result','type':'agentMessage','text':'Live message during navigation'}}),
                         ('turn/completed',{'turn':{'id':'switch-live','status':'completed'}})]:
     app.bridge.notification({'method':method,'params':{'threadId':'perf-b','turnId':'switch-live',**params}})
    page.wait_for_function('() => state.loadingThread?.events.length >= 3')
   finally:
    release.set()
   page.wait_for_function('() => !state.loadingThread')
   expect(page.locator('[data-item-id=switch-result]')).to_contain_text('Live message during navigation')
   expect(page.locator('#run-status')).to_have_text('就绪')
   started.clear();release.clear()
   page.evaluate("void selectThread('perf-b')")
   assert started.wait(timeout=3)
   try:
    page.evaluate("selectThread('perf-a')")
    expect(page.locator('#chat-title')).to_have_text('perf-a')
   finally:
    release.set();gate['enabled']=False
   page.wait_for_function('() => !state.loadingThread')
   expect(page.locator('#chat-title')).to_have_text('perf-a')
   assert page.locator('[data-item-id=switch-result]').count() == 0

   # Work in another conversation stays current before revalidation returns.
   gate['enabled']=True;started.clear();release.clear()
   for method,params in [('turn/started',{'turn':{'id':'away-live'}}),
                        ('item/completed',{'item':{'id':'away-result','type':'agentMessage','text':'Updated while viewing another conversation'}}),
                        ('turn/completed',{'turn':{'id':'away-live','status':'completed'}})]:
    app.bridge.notification({'method':method,'params':{'threadId':'perf-b','turnId':'away-live',**params}})
   page.wait_for_function("() => threadCache.get('perf-b')?.pendingEvents?.length >= 3")
   page.evaluate("void selectThread('perf-b')")
   assert started.wait(timeout=3)
   try:
    expect(page.locator('[data-item-id=away-result]')).to_contain_text('Updated while viewing another conversation')
   finally:
    release.set();gate['enabled']=False
   page.wait_for_function('() => !state.loadingThread')

  alpha=Path(d)/'alpha';beta=Path(d)/'beta';alpha.mkdir();beta.mkdir()
  pa=app.store.remember_project(alpha);pb=app.store.remember_project(beta)
  page.evaluate('refreshProjects()')
  page.fill('#prompt','Preserve my draft')
  page.evaluate('(id) => { void selectProject(id); }',pa['id'])
  expect(page.locator('#composer-project')).to_have_text('alpha')
  expect(page.locator('#prompt')).to_have_value('Preserve my draft')
  page.evaluate('(ids) => Promise.all(ids.map(id => selectProject(id)))',[pb['id'],pa['id']])
  expect(page.locator('#composer-project')).to_have_text('alpha')
  assert app.store.settings()['cwd']==str(alpha)
  artifacts=Path(__file__).resolve().parents[1]/'artifacts'
  report_path=artifacts/'navigation-performance.json'
  report=json.loads(report_path.read_text()) if report_path.exists() else {}
  report.update({'conditions':{'latency_ms':100,'download_bytes_sec':200000,'CPU_throttle':4,'history_items':350},'after':metrics})
  report_path.write_text(json.dumps(report,indent=2)+'\n')
  assert not errors,errors
  print(json.dumps(metrics))
  print('Pagination, lazy details, full change history, buffered events, canceled navigation and ordered project saves: PASS')
  browser.close()
 server.shutdown();server.server_close();app.store.db.close()
