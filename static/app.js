'use strict';
const $ = id => document.getElementById(id);
const state = { csrf: '', username: '', settings: {}, projects: [], threads: [], thread: null, items: [], turns: [], attachments: [], requests: [], seq: 0, threadSeq: 0, stream: null, setup: false, sending: false, models: [], selection: 0, serverOffset: 0 };
let toastTimer, renderFrame, threadRefreshTimer;
const messageNodes = new Map();
const messageVersions = new Map();
const dirtyItems = new Set();
let renderedThread, changesVersion = '', changesDirty = true, pinToBottom = true, threadListRequest = 0;
function setText(node, text) { if (node.textContent !== text) node.textContent = text; }
let authLockedUntil = 0, authPending = false, lockWasActive = false;
let folderBrowseRequest = 0, folderParent = null, projectSwitchRequest = 0;
const MAX_IMAGES = 8, MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const MAX_FILE_BYTES = 25 * 1024 * 1024;
let imageSequence = 0, imageDragDepth = 0;
const uploadQueue = [];
let activeUploads = 0;
const HISTORY_PAGE_SIZE = 80, threadCache = new Map();
let navigationController, projectSaveChain = Promise.resolve(), changesRequest = 0, pendingProjectPath = null;
let collapsedProjects = new Set();
try { collapsedProjects = new Set(JSON.parse(localStorage.getItem('codex-web-collapsed-projects') || '[]')); } catch { /* Start expanded if browser storage is unavailable. */ }
const escapeHTML = text => String(text ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 3800); }
function savedThread() {
  for (const name of ['sessionStorage', 'localStorage']) {
    try { const id = window[name].getItem('codex-web-thread'); if (id) return id; } catch { /* Storage may be unavailable. */ }
  }
  return null;
}
function rememberThread(id) {
  for (const name of ['sessionStorage', 'localStorage']) {
    try { if (id) window[name].setItem('codex-web-thread', id); else window[name].removeItem('codex-web-thread'); } catch { /* Authentication lives in the HttpOnly cookie. */ }
  }
}
async function api(path, body, options = {}) {
  const response = await fetch('/api' + path, {method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', headers: body === undefined ? {} : {'Content-Type':'application/json', 'X-CSRF-Token': state.csrf}, body: body === undefined ? undefined : JSON.stringify(body), ...options});
  let data;
  try { data = await response.json(); } catch { throw new Error('服务器返回了无效响应'); }
  if (!response.ok) { if (response.status === 401 && !['/login','/setup'].includes(path)) showAuth(false); const error = new Error(data.error || '请求失败'); error.status = response.status; error.details = data; throw error; }
  return data;
}
function showAuth(setup) {
  $('startup-screen').hidden = true;
  navigationController?.abort(); threadCache.clear();
  clearAttachments();
  state.setup = setup;
  if (state.stream) state.stream.close();
  state.stream = null; state.csrf = '';
  state.thread = null; state.items = []; state.turns = []; state.requests = []; state.threads = []; state.projects = []; state.selection++; state.loadingThread = null;
  state.hasMore = false; state.before = null; state.allChanges = null; state.changePaths = [];
  if ($('history-control')) $('history-control').hidden = true;
  for (const dialog of document.querySelectorAll('dialog[open]')) dialog.close();
  $('workspace').hidden = true; $('auth-screen').hidden = false;
  $('auth-title').textContent = setup ? '创建你的工作台账号' : '登录你的工作台';
  $('auth-eyebrow').textContent = setup ? 'A FRESH START' : 'WELCOME BACK';
  $('auth-desc').textContent = setup ? '首次使用，设置一个只有你知道的账号和密码。' : '继续你的对话，接着完成下一件事。';
  $('auth-submit').innerHTML = setup ? '创建账号并开始 <span>→</span>' : '登录 <span>→</span>';
  $('confirm-label').hidden = !setup; $('auth-confirm').required = setup;
  $('auth-password').autocomplete = setup ? 'new-password' : 'current-password';
  $('auth-password').minLength = setup ? 10 : 1;
  $('auth-note').textContent = setup ? '密码至少 10 位，可在设置中随时修改。' : '连续输错 6 次锁定 6 分钟，成功登录后清零。';
  $('auth-form').reset(); $('auth-error').textContent = '';
  $('auth-submit').disabled = !setup;
  $('auth-username').focus();
  if (!setup) refreshLoginLock();
}
function setLoginLock(details) {
  authLockedUntil = details.retryAfter > 0 ? Date.now() + details.retryAfter * 1000 : 0;
  updateLoginLock();
}
function updateLoginLock() {
  if ($('auth-screen').hidden || state.setup) return;
  const seconds = Math.max(0, Math.ceil((authLockedUntil - Date.now()) / 1000));
  const locked = seconds > 0;
  $('auth-submit').disabled = locked || authPending;
  $('auth-username').disabled = locked; $('auth-password').disabled = locked;
  $('auth-submit').innerHTML = locked ? `登录已锁定 · ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2,'0')}` : '登录 <span>→</span>';
  if (locked) $('auth-error').textContent = '密码错误已达 6 次，请等待锁定结束。刷新页面不会解除锁定。';
  else if (lockWasActive) { $('auth-error').textContent = ''; $('auth-password').value = ''; refreshLoginLock(); }
  lockWasActive = locked;
}
async function refreshLoginLock() {
  if (authPending || state.setup || $('auth-screen').hidden) return;
  try { const status = await api('/status'); if (!$('auth-screen').hidden && !state.setup) setLoginLock(status); } catch { /* Keep the last server-confirmed lock if temporarily disconnected. */ }
}
setInterval(updateLoginLock, 1000);
setInterval(refreshLoginLock, 15000);
async function enterWorkspace(data) {
  $('startup-screen').hidden = true;
  state.csrf = data.csrf; state.username = data.username; state.settings = data.settings; state.projects = data.projects || []; state.seq = data.seq || 0;
  $('auth-screen').hidden = true; $('workspace').hidden = false;
  $('account-name').textContent = state.username; $('avatar').textContent = state.username.slice(0,1).toUpperCase();
  state.threads = data.threads || [];
  applySettings(); renderMessages(); renderThreadList();
  connectEvents();
  loadModels();
  if (!data.threads) await refreshThreads();
  const saved = savedThread();
  if (data.conversation) { state.selection++; displayThread(data.conversation); }
  else if (saved && state.threads.some(t => t.id === saved)) await selectThread(saved);
}
function applyTheme() {
  const theme = state.settings.theme;
  document.documentElement.dataset.theme = theme === 'system' ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : (theme || 'light');
}
function applySettings() {
  applyTheme();
  const s = state.settings;
  const cwd = state.thread?.cwd || s.cwd || '';
  const name = cwd.split('/').filter(Boolean).at(-1) || '/';
  $('project-name').textContent = name; $('composer-project').textContent = name; $('project-button').title = cwd;
  $('effort-picker').value = s.effort || 'high';
  const model = s.model || '';
  if (model && ![...$('model-picker').options].some(o => o.value === model)) $('model-picker').add(new Option(model,model));
  $('model-picker').value = model;
  $('permission-label').textContent = ({'read-only':'只读','workspace-write':'项目内读写','danger-full-access':'完全访问服务器'}[s.sandbox] || '项目内读写') + ' · ' + ({'on-request':'按需审批','untrusted':'谨慎审批','never':'无需审批'}[s.approvalPolicy] || '按需审批');
}
async function loadModels() {
  try {
    const {data} = await api('/models'); state.models = data;
    const picker = $('model-picker'); picker.replaceChildren(new Option('服务器默认模型',''));
    $('model-options').replaceChildren();
    for (const m of data) { picker.add(new Option(m.displayName || m.model, m.model)); const option = document.createElement('option'); option.value = m.model; $('model-options').append(option); }
    applySettings(); setConnection(true);
  } catch (e) { setConnection(false); toast('模型列表暂不可用：' + e.message); }
}
function setConnection(connected) { $('connection-dot').classList.toggle('offline',!connected); $('connection-label').textContent = connected ? '已连接本机 Codex' : '连接中，自动重试'; }
function connectEvents() {
  if (state.stream) state.stream.close();
  const source = new EventSource('/api/events?after=' + state.seq); state.stream = source;
  source.onopen = () => { if (state.stream === source) setConnection(true); };
  source.onerror = () => { if (state.stream === source) setConnection(false); };
  source.addEventListener('expired', () => { source.close(); if (state.stream !== source) return; showAuth(false); toast('登录已失效，请重新登录'); });
  source.onmessage = event => {
    state.seq = Math.max(state.seq, Number(event.lastEventId) || 0);
    const obj = JSON.parse(event.data), method = obj.method, p = obj.params || {};
    if (p.webTimestamp) state.serverOffset = p.webTimestamp * 1000 - Date.now();
    if (method === 'web/projectsChanged') {
      state.projects = p.projects || []; state.settings.cwd = pendingProjectPath || p.cwd;
      applySettings(); renderThreadList(); return;
    }
    if (method === 'web/resync' || method === 'web/disconnected') {
      for (const cached of threadCache.values()) { cached.stale = true; cached.pendingEvents = []; }
      if (method === 'web/disconnected') { setConnection(false); toast('Codex 连接中断，重新发送可恢复连接'); }
      refreshThreads().catch(e => toast(e.message));
      refreshProjects().catch(e => toast(e.message));
      if (state.thread) selectThread(state.thread.id, {force: true}).catch(e => toast(e.message));
      return;
    }
    const tid = method === 'web/request' ? p.params?.threadId : p.threadId;
    if (!tid) return;
    const eventId = Number(event.lastEventId);
    const cached = threadCache.get(tid);
    if (cached && state.thread?.id !== tid && !cached.stale) {
      cached.pendingEvents ||= [];
      if (cached.pendingEvents.length < 500) cached.pendingEvents.push({method, p, eventId, tid});
      else { cached.pendingEvents = []; cached.stale = true; }
    }
    if (['turn/started','turn/completed','web/request','web/responded'].includes(method)) scheduleThreadRefresh();
    if (state.loadingThread?.id === tid) {
      state.loadingThread.events.push({method, p, eventId, tid, serverOffset: state.serverOffset});
      return;
    }
    applyThreadEvent(method, p, eventId, tid);
  };
}
function applyThreadEvent(method, p, eventId, tid) {
  if (!state.thread || tid !== state.thread.id || eventId <= state.threadSeq) return;
  state.threadSeq = eventId;
  if (p.webTurn) {
    const index = state.turns.findIndex(t => t.id === p.webTurn.id);
    if (index >= 0) state.turns[index] = p.webTurn; else state.turns.push(p.webTurn);
  }
  if (method === 'turn/started') { state.thread.status = 'running'; state.thread.turn_id = p.turn.id; }
  if (method === 'turn/completed') { state.thread.status = p.turn.status || 'completed'; state.thread.turn_id = null; state.requests = []; if (p.turn.error) appendError(p.turn.error.message || '任务失败'); }
  if (method === 'item/started' || method === 'item/completed') {
    if (p.item.type === 'userMessage') state.items = state.items.filter(item => !item.webPending);
    const index = state.items.findIndex(item => item.id === p.item.id);
    if (index >= 0) state.items[index] = p.item; else state.items.push(p.item);
    dirtyItems.add(p.item.id);
    if (p.item.type === 'fileChange') changesDirty = true;
    if (p.item.type === 'fileChange') state.allChanges = null;
  }
  if (method.endsWith('/delta') || method.endsWith('Delta')) {
    const item = state.items.find(item => item.id === p.itemId);
    if (item) {
      if (method.includes('reasoning')) {
        if (p.delta && item.webTiming) item.webTiming.streamed = true;
        if (method.includes('summaryTextDelta')) {
          const index = Math.max(0, Number(p.summaryIndex) || 0); item.summary ||= [];
          while (item.summary.length <= index) item.summary.push('');
          item.summary[index] += p.delta || '';
        }
      } else {
        const field = method.includes('commandExecution') ? 'aggregatedOutput' : 'text';
        item[field] = (item[field] || '') + (p.delta || '');
      }
      dirtyItems.add(item.id);
      if (item.type === 'fileChange') changesDirty = true;
    }
  }
  if (method === 'web/request') { state.requests.push(p); state.thread.status = 'waiting'; renderRequests(); }
  if (method === 'web/responded') { state.requests = state.requests.filter(r => r.id !== p.id); state.thread.status = 'running'; renderRequests(); }
  if (method === 'error') appendError(p.error?.message || 'Codex 发生错误');
  scheduleRender();
}

function scheduleThreadRefresh() { clearTimeout(threadRefreshTimer); threadRefreshTimer = setTimeout(() => refreshThreads().catch(e => toast(e.message)), 200); }
async function refreshThreads() {
  const request = ++threadListRequest;
  const result = await api('/threads'); if (request !== threadListRequest) return; state.threads = result.threads;
  if (state.thread) { const t = state.threads.find(t => t.id === state.thread.id); if (t) { state.thread = {...state.thread,...t}; $('chat-title').textContent = t.title; updateRunState(); } }
  renderThreadList();
}
function relativeTime(timestamp) { const age = Date.now()/1000 - timestamp; if (age < 60) return '刚刚'; if (age < 3600) return Math.floor(age/60)+'分钟'; if (age < 86400) return Math.floor(age/3600)+'小时'; return new Date(timestamp*1000).toLocaleDateString('zh-CN',{month:'numeric',day:'numeric'}); }
function renderThreadList() {
  const query = $('search').value.toLowerCase().trim();
  $('thread-count').textContent = state.threads.length;
  const list = $('thread-list'); list.replaceChildren();
  const activePath = state.thread?.cwd || state.settings.cwd;
  const savedPaths = new Set(state.projects.map(project => project.path));
  for (const project of state.projects) {
    const projectMatches = !query || (project.name + ' ' + project.path).toLowerCase().includes(query);
    const threads = state.threads.filter(thread => thread.cwd === project.path && (projectMatches || thread.title.toLowerCase().includes(query)));
    if (!projectMatches && !threads.length) continue;
    const group = document.createElement('section'); group.className = 'project-group'; group.dataset.projectId = project.id;
    const row = document.createElement('div'); row.className = 'project-row' + (activePath === project.path ? ' selected' : '') + (project.available === false ? ' unavailable' : '');
    const toggle = document.createElement('button'); toggle.className = 'project-expand'; toggle.type = 'button';
    const collapsed = !query && collapsedProjects.has(project.id);
    toggle.setAttribute('aria-label', (collapsed ? '展开 ' : '收起 ') + project.name); toggle.setAttribute('aria-expanded', String(!collapsed));
    toggle.innerHTML = '<span aria-hidden="true">›</span>';
    toggle.onclick = () => { if (collapsedProjects.has(project.id)) collapsedProjects.delete(project.id); else collapsedProjects.add(project.id); try { localStorage.setItem('codex-web-collapsed-projects', JSON.stringify([...collapsedProjects])); } catch {} renderThreadList(); };
    const button = document.createElement('button'); button.className = 'project-select'; button.type = 'button'; button.title = project.path;
    button.setAttribute('aria-label', '选择项目 ' + project.name); button.disabled = project.available === false;
    button.innerHTML = `<svg class="icon" aria-hidden="true"><use href="#icon-folder"/></svg><span>${escapeHTML(project.name)}</span>`;
    button.onclick = () => selectProject(project.id).catch(error => toast(error.message));
    const create = document.createElement('button'); create.className = 'project-new icon-button'; create.type = 'button'; create.textContent = '+';
    create.setAttribute('aria-label', '在 ' + project.name + ' 中新建对话'); create.disabled = project.available === false;
    create.onclick = button.onclick;
    const menu = document.createElement('button'); menu.className = 'project-more icon-button'; menu.type = 'button'; menu.textContent = '•••';
    menu.setAttribute('aria-label', project.name + ' 项目操作'); menu.onclick = () => openProjectMenu(project, menu);
    row.append(toggle, button, create, menu); group.append(row);
    const children = document.createElement('div'); children.className = 'project-threads'; children.hidden = collapsed;
    for (const thread of threads) children.append(threadButton(thread));
    group.append(children); list.append(group);
  }
  const otherThreads = state.threads.filter(thread => !savedPaths.has(thread.cwd) && (!query || thread.title.toLowerCase().includes(query)));
  if (otherThreads.length) {
    if (state.projects.length) { const label = document.createElement('div'); label.className = 'other-threads-label'; label.textContent = '其他对话'; list.append(label); }
    for (const thread of otherThreads) list.append(threadButton(thread));
  }
  if (!list.children.length) { const p = document.createElement('p'); p.className = 'sidebar-empty'; p.textContent = query ? '没有找到匹配的对话。' : '添加一个项目文件夹，\n从这里开始工作。'; list.append(p); }
}
function threadButton(t) {
    const button = document.createElement('button'); button.className = 'thread-item' + (state.thread?.id === t.id ? ' active' : ''); button.title = t.title;
    button.innerHTML = `<span class="thread-icon">${['running','waiting'].includes(t.status) ? '<span class="spinner"></span>' : '○'}</span><span class="thread-text">${escapeHTML(t.title)}</span><span class="thread-time">${relativeTime(t.updated)}</span>`;
    button.onclick = () => selectThread(t.id).catch(e => toast(e.message)); return button;
}
async function refreshProjects() {
  const result = await api('/projects'); state.projects = result.projects; state.settings.cwd = result.cwd;
  applySettings(); renderThreadList();
}
async function selectProject(id) {
  const request = ++projectSwitchRequest;
  const project = state.projects.find(project => project.id === id);
  if (!project || project.available === false) return;
  const previousCwd = state.settings.cwd;
  pendingProjectPath = project.path; state.settings.cwd = project.path; collapsedProjects.delete(id);
  newChat({preserveDraft: true}); closeSidebar();
  const selection = state.selection;
  // Save rapid project changes in click order while the local view responds immediately.
  const saving = projectSaveChain.catch(() => {}).then(() => api('/projects/' + encodeURIComponent(id) + '/select', {}));
  projectSaveChain = saving;
  let result;
  try { result = await saving; }
  catch (error) { if (request === projectSwitchRequest) { pendingProjectPath = null; state.settings.cwd = previousCwd; applySettings(); renderThreadList(); } throw error; }
  if (request !== projectSwitchRequest) return;
  pendingProjectPath = null;
  state.projects = result.projects; state.settings = result.settings;
  applySettings(); renderThreadList(); if (selection === state.selection) updateRunState();
}
function openProjectMenu(project, button) {
  document.querySelector('.project-menu-popover')?.remove();
  const menu = document.createElement('div'); menu.className = 'project-menu-popover';
  const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = '从列表移除';
  remove.title = '保留服务器文件和已有对话';
  remove.onclick = async () => {
    remove.disabled = true;
    try { const result = await api('/projects/' + encodeURIComponent(project.id) + '/remove', {}); state.projects = result.projects; state.settings = result.settings; applySettings(); renderThreadList(); menu.remove(); toast('已从列表移除，文件和对话已保留'); }
    catch (error) { remove.disabled = false; toast(error.message); }
  };
  menu.append(remove); document.body.append(menu);
  const rect = button.getBoundingClientRect(); menu.style.left = Math.max(8, Math.min(innerWidth - 180, rect.right - 170)) + 'px'; menu.style.top = Math.min(innerHeight - 60, rect.bottom + 4) + 'px';
}
function openProjectDialog() {
  closeSidebar(); $('project-error').textContent = ''; $('project-path').value = state.settings.cwd || '/root';
  $('project-dialog').showModal(); browseDirectories($('project-path').value);
}
async function browseDirectories(path) {
  const request = ++folderBrowseRequest;
  const inputAtStart = $('project-path').value;
  $('project-error').textContent = ''; $('folder-list').textContent = '正在读取文件夹…'; $('folder-list').setAttribute('aria-busy', 'true');
  try {
    const result = await api('/directories?path=' + encodeURIComponent(path)); if (request !== folderBrowseRequest) return;
    if ($('project-path').value === inputAtStart) $('project-path').value = result.path;
    $('folder-current-path').textContent = result.path; folderParent = result.parent;
    $('folder-up').disabled = !folderParent; $('folder-list').replaceChildren();
    for (const directory of result.directories) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'folder-entry'; button.title = directory.path;
      button.innerHTML = `<svg class="icon" aria-hidden="true"><use href="#icon-folder"/></svg><span>${escapeHTML(directory.name)}</span><span class="folder-arrow" aria-hidden="true">›</span>`;
      button.onclick = () => browseDirectories(directory.path); $('folder-list').append(button);
    }
    if (!result.directories.length) { const p = document.createElement('p'); p.className = 'folder-empty'; p.textContent = '此文件夹中没有子文件夹，可以直接添加。'; $('folder-list').append(p); }
    if (result.truncated) { const p = document.createElement('p'); p.className = 'folder-empty'; p.textContent = '文件夹较多，也可以直接输入目标路径。'; $('folder-list').append(p); }
  } catch (error) {
    if (request === folderBrowseRequest) { $('folder-list').replaceChildren(); $('project-error').textContent = error.message; }
  } finally { if (request === folderBrowseRequest) $('folder-list').setAttribute('aria-busy', 'false'); }
}
function rememberCurrentThread() {
  if (!state.thread || state.loadingThread) return;
  const id = state.thread.id;
  threadCache.delete(id);
  threadCache.set(id, {thread: {...state.thread}, items: [...state.items], turns: [...state.turns],
    requests: [...state.requests], seq: state.threadSeq, hasMore: state.hasMore, before: state.before,
    changePaths: state.changePaths, allChanges: state.allChanges, scrollTop: $('scroll-area').scrollTop,
    stale: false});
  while (threadCache.size > 6) threadCache.delete(threadCache.keys().next().value);
}
function historyControl() {
  let node = $('history-control');
  if (!node) {
    node = document.createElement('div'); node.id = 'history-control'; node.className = 'history-control';
    node.innerHTML = '<button type="button" id="load-history">加载更早消息</button><span id="history-status" class="muted"></span>';
    $('messages').before(node); $('load-history').onclick = () => loadEarlierMessages().catch(error => toast(error.message));
  }
  node.hidden = !state.hasMore && !state.loadingThread?.blocking && !state.historyLoading;
  $('load-history').hidden = !state.hasMore || !!state.loadingThread?.blocking;
  $('load-history').disabled = !!state.historyLoading || !!state.loadingThread;
  setText($('history-status'), state.loadingThread?.blocking ? '正在加载对话…' : state.historyLoading ? '正在加载更早消息…' : '');
}
function displayThread(data, {merge = false, scrollTop = null} = {}) {
  const oldItems = merge ? state.items : [];
  const oldBefore = state.before, oldMore = state.hasMore;
  const ids = new Set(data.items.map(item => item.id));
  state.thread = data.thread; state.items = [...oldItems.filter(item => !ids.has(item.id) && !item.webPending), ...data.items];
  state.turns = data.turns || []; state.requests = data.requests || []; state.threadSeq = data.seq;
  state.hasMore = merge ? oldMore : !!data.hasMore; state.before = merge ? oldBefore : data.before;
  state.changePaths = data.changePaths || []; state.allChanges = data.allChanges || null;
  if (data.serverTime) state.serverOffset = data.serverTime * 1000 - Date.now();
  if (!merge) resetMessageCache(); pinToBottom = scrollTop === null;
  rememberThread(data.thread.id);
  $('chat-title').textContent = data.thread.title; applySettings(); renderThreadList(); renderMessages(); renderRequests(); closeSidebar();
  if (scrollTop !== null) $('scroll-area').scrollTop = scrollTop;
  historyControl();
}
async function selectThread(id, {force = false} = {}) {
  rememberCurrentThread(); navigationController?.abort();
  const selection = ++state.selection;
  const cached = threadCache.get(id);
  if (cached && force) cached.stale = true;
  const loading = {id, events: [], blocking: !cached || cached.stale}; state.loadingThread = loading;
  navigationController = new AbortController(); state.historyLoading = false;
  if (cached) {
    displayThread(cached, {scrollTop: cached.scrollTop});
    for (const event of cached.pendingEvents || []) applyThreadEvent(event.method, event.p, event.eventId, event.tid);
    cached.pendingEvents = []; renderMessages();
  }
  else {
    const thread = state.threads.find(thread => thread.id === id);
    state.thread = thread || {id, status: 'idle', title: '对话'}; state.items = []; state.turns = []; state.requests = [];
    state.hasMore = false; state.before = null; state.changePaths = []; state.allChanges = null;
    resetMessageCache(); $('chat-title').textContent = state.thread.title;
    applySettings(); renderThreadList(); renderMessages(); renderRequests(); closeSidebar(); historyControl();
  }
  const refresh = async () => {
    let data;
    try { data = await api('/threads/' + id + '?limit=' + HISTORY_PAGE_SIZE, undefined, {signal: navigationController.signal}); }
    catch (error) {
      if (error.name === 'AbortError' || selection !== state.selection) return;
      if (state.loadingThread === loading) { state.loadingThread = null; updateRunState(); historyControl(); }
      throw error;
    }
    if (selection !== state.selection) return;
    state.loadingThread = null;
    const scrollTop = cached ? $('scroll-area').scrollTop : null;
    displayThread(data, {merge: !!cached && !cached.stale, scrollTop});
    for (const event of loading.events) applyThreadEvent(event.method, event.p, event.eventId, event.tid);
    if (loading.events.length) { state.serverOffset = loading.events.at(-1).serverOffset; renderMessages(); }
    rememberCurrentThread();
  };
  if (cached) { refresh().catch(error => toast(error.message)); return; }
  await refresh();
}
async function loadEarlierMessages() {
  if (!state.thread || !state.hasMore || state.historyLoading || state.loadingThread) return;
  const selection = state.selection, id = state.thread.id, before = state.before;
  state.historyLoading = true; historyControl();
  try {
    const data = await api('/threads/' + id + '?limit=' + HISTORY_PAGE_SIZE + '&before=' + before);
    if (selection !== state.selection) return;
    const scroll = $('scroll-area'), height = scroll.scrollHeight, top = scroll.scrollTop;
    const ids = new Set(state.items.map(item => item.id));
    state.items = [...data.items.filter(item => !ids.has(item.id)), ...state.items];
    state.hasMore = !!data.hasMore; state.before = data.before; pinToBottom = false;
    renderMessages(); scroll.scrollTop = top + scroll.scrollHeight - height;
    rememberCurrentThread();
  } finally { if (selection === state.selection) { state.historyLoading = false; historyControl(); } }
}
function newChat({preserveDraft = false} = {}) {
  rememberCurrentThread(); navigationController?.abort();
  if (!preserveDraft) clearAttachments(); state.selection++; state.loadingThread = null;
  state.thread = null; state.items = []; state.turns = []; state.requests = []; state.threadSeq = state.seq;
  state.hasMore = false; state.before = null; state.historyLoading = false; state.changePaths = []; state.allChanges = null;
  // Preserve a deliberately selected new conversation instead of reopening an older project on reload.
  rememberThread('__new_chat__'); $('chat-title').textContent = '新对话';
  if (!preserveDraft) $('prompt').value = ''; resetMessageCache(); pinToBottom = true;
  applySettings(); renderMessages(); renderRequests(); renderThreadList(); historyControl(); closeSidebar(); $('prompt').focus();
}

function inlineMarkdown(text) {
  let s = escapeHTML(text);
  s = s.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*\n]+)\*/g,'<em>$1</em>');
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  return s;
}
function markdown(text) {
  const parts = String(text || '').split(/```/); let html = '';
  parts.forEach((part,index) => {
    if (index % 2) { const newline = part.indexOf('\n'); const lang = newline >= 0 ? part.slice(0,newline).trim() : ''; const code = newline >= 0 ? part.slice(newline+1) : part; html += `<pre><button class="copy-button" type="button">复制</button><div class="code-label">${escapeHTML(lang || 'CODE')}</div><code>${escapeHTML(code.trimEnd())}</code></pre>`; return; }
    let list = null;
    for (const line of part.split('\n')) {
      const li = line.match(/^\s*([-*]|\d+\.)\s+(.+)/);
      if (li) { const kind = /\d/.test(li[1]) ? 'ol' : 'ul'; if (list !== kind) { if (list) html += `</${list}>`; list = kind; html += `<${kind}>`; } html += `<li>${inlineMarkdown(li[2])}</li>`; continue; }
      if (list) { html += `</${list}>`; list = null; }
      const h = line.match(/^(#{1,3})\s+(.+)/);
      if (h) html += `<h${h[1].length}>${inlineMarkdown(h[2])}</h${h[1].length}>`;
      else if (line.startsWith('> ')) html += `<blockquote>${inlineMarkdown(line.slice(2))}</blockquote>`;
      else if (line.trim()) html += `<p>${inlineMarkdown(line)}</p>`;
    }
    if (list) html += `</${list}>`;
  });
  return html;
}
function itemHTML(item) {
  const id = escapeHTML(item.id);
  if (item.type === 'userMessage') {
    const content = item.content || [];
    const images = content.filter(part => part.type === 'image' || part.type === 'localImage');
    const files = content.filter(part => part.type === 'file');
    const text = content.filter(part => part.type === 'text').map(part => part.text || '').join('\n');
    const thumbnails = images.map(image => {
      const url = safeImageURL(image.url);
      return url ? `<button class="message-image" type="button" data-image-url="${escapeHTML(url)}" data-image-name="${escapeHTML(image.name || '图片')}" aria-label="查看图片 ${escapeHTML(image.name || '')}"><img src="${escapeHTML(url)}" alt="${escapeHTML(image.name || '图片附件')}" loading="lazy"></button>` : '<span class="missing-image">图片附件</span>';
    }).join('');
    const documents = files.map(file => safeImageURL(file.url) ? `<button type="button" class="message-file" data-file-id="${escapeHTML(file.id || file.attachmentId)}"><span class="file-symbol">▤</span><span><strong>${escapeHTML(file.name || '文件')}</strong><small>${escapeHTML(fileSize(file.size))}</small></span></button>` : '<span class="missing-image">文件附件</span>').join('');
    return `<article class="message user" data-item-id="${id}"><div class="user-bubble${images.length || files.length ? ' has-images' : ''}">${images.length ? '<div class="message-images">' + thumbnails + '</div>' : ''}${files.length ? '<div class="message-files">' + documents + '</div>' : ''}${text ? '<div class="user-text">' + escapeHTML(text) + '</div>' : ''}</div></article>`;
  }
  if (item.type === 'agentMessage') return `<article class="message assistant ${item.phase === 'commentary' ? 'commentary' : ''}" data-item-id="${id}"><div class="markdown">${markdown(item.text)}</div></article>`;
  if (item.type === 'commandExecution') return `<details class="tool" data-item-id="${id}"><summary><span>${item.status === 'inProgress' ? '◌' : item.exitCode && item.exitCode !== 0 ? '!' : '✓'}</span><strong>执行命令</strong><span>${escapeHTML((item.command || '').slice(0,95))}</span></summary><div class="tool-cwd">${escapeHTML(item.cwd || '')} ${item.exitCode != null ? ' · 退出码 '+escapeHTML(item.exitCode) : ''}</div><pre></pre></details>`;
  if (item.type === 'fileChange') return `<details class="tool" data-item-id="${id}"><summary><span>✓</span><strong>文件变更</strong><span>${escapeHTML((item.changes || []).map(c => c.path.split('/').at(-1)).join(', '))}</span></summary><pre class="diff"></pre></details>`;
  if (item.type === 'reasoning') {
    const text = item.summaryText || (item.summary || []).join('\n');
    return `<details class="tool reasoning" data-item-id="${id}"><summary><span class="reasoning-symbol">✧</span><strong data-reasoning-id="${id}">思考</strong><span class="reasoning-preview">${escapeHTML(text.split('\n').find(Boolean) || '正在分析任务')}</span></summary><div class="reasoning-content"><p class="muted">展开查看思考摘要。</p></div></details>`;
  }
  if (item.type === 'plan') return `<article class="message"><div class="assistant-label"><span>☷</span> 工作计划</div><div class="markdown">${markdown(item.text || '')}</div></article>`;
  if (item.type === 'mcpToolCall') return `<details class="tool" data-item-id="${id}"><summary><span>◇</span><strong>调用工具</strong><span>${escapeHTML(item.server || '')} / ${escapeHTML(item.tool || '')}</span></summary><pre></pre></details>`;
  if (item.type === 'webSearch') return `<details class="tool" data-item-id="${id}"><summary><span>⌕</span><strong>搜索</strong><span>${escapeHTML(item.query || '')}</span></summary></details>`;
  return '';
}
function scheduleRender() { if (renderFrame) return; renderFrame = setTimeout(() => { renderFrame = null; requestAnimationFrame(renderMessages); }, 40); }
function renderToolBody(node, item) {
  if (!node.open) return;
  if (item.type === 'reasoning') {
    const text = item.summaryText || (item.summary || []).join('\n');
    node.querySelector('.reasoning-content').innerHTML = text ? markdown(text) : '<p class="muted">当前模型未提供思考摘要。</p>';
  } else if (item.type === 'commandExecution') node.querySelector('pre').textContent = item.aggregatedOutput || '等待输出…';
  else if (item.type === 'fileChange') node.querySelector('pre').textContent = (item.changes || []).map(change => change.path + '\n' + (change.diff || '')).join('\n\n');
  else if (item.type === 'mcpToolCall') node.querySelector('pre').textContent = JSON.stringify(item.result || item.arguments || {}, null, 2);
}
function resetMessageCache() { messageNodes.clear(); messageVersions.clear(); dirtyItems.clear(); $('messages').replaceChildren(); changesVersion = ''; changesDirty = true; }
function renderMessages() {
  const scroll = $('scroll-area');
  const threadKey = state.thread?.id || 'new';
  if (renderedThread !== threadKey) { resetMessageCache(); renderedThread = threadKey; }
  $('welcome').hidden = state.items.length > 0 || !!state.loadingThread?.blocking;
  const liveIds = new Set([...state.items.map(item => item.id), ...state.turns.map(turn => 'turn:' + turn.id)]);
  for (const [id, node] of messageNodes) if (!liveIds.has(id)) { node.remove(); messageNodes.delete(id); messageVersions.delete(id); }
  let previousNode = null;
  for (const item of state.items) {
    if (messageVersions.get(item.id) === item && !dirtyItems.has(item.id)) { previousNode = messageNodes.get(item.id) || previousNode; continue; }
    const html = itemHTML(item);
    let node = messageNodes.get(item.id);
    if (!html) continue;
    if (!node) {
      const template = document.createElement('template'); template.innerHTML = html; node = template.content.firstElementChild;
      messageNodes.set(item.id, node); if (previousNode) previousNode.after(node); else $('messages').prepend(node);
    } else if (item.type === 'agentMessage') {
      node.classList.toggle('commentary', item.phase === 'commentary');
      node.querySelector('.markdown').innerHTML = markdown(item.text);
    } else if (item.type === 'reasoning') {
      const text = item.summaryText || (item.summary || []).join('\n');
      node.querySelector('.reasoning-preview').textContent = text.split('\n').find(Boolean) || '正在分析任务';
    } else if (item.type === 'commandExecution') {
      node.querySelector('summary > span').textContent = item.status === 'inProgress' ? '◌' : item.exitCode && item.exitCode !== 0 ? '!' : '✓';
      node.querySelector('.tool-cwd').textContent = (item.cwd || '') + (item.exitCode != null ? ' · 退出码 ' + item.exitCode : '');
    } else {
      const template = document.createElement('template'); template.innerHTML = html;
      const replacement = template.content.firstElementChild; if (node.open) replacement.open = true;
      node.replaceWith(replacement); messageNodes.set(item.id, replacement);
      node = replacement;
    }
    renderToolBody(node, item); previousNode = node;
    messageVersions.set(item.id, item);
  }
  dirtyItems.clear();
  renderTurnTimings();
  updateRunState(); renderChanges();
  if (pinToBottom) scroll.scrollTop = scroll.scrollHeight;
}
function durationLabel(milliseconds) {
  const seconds = Math.floor(Math.max(0, milliseconds) / 1000);
  if (seconds < 1) return '不足 1 秒';
  return seconds < 60 ? `${seconds} 秒` : `${Math.floor(seconds / 60)} 分 ${String(seconds % 60).padStart(2, '0')} 秒`;
}
function serverNow() { return Date.now() + state.serverOffset; }
function reasoningDuration(item, turnsById) {
  const timing = item.webTiming; if (!timing) return null;
  if (timing.measurement === 'unavailable') return null;
  const turn = turnsById ? turnsById.get(item.webTurnId) : state.turns.find(t => t.id === item.webTurnId);
  const end = timing.completedAt || turn?.completedAt;
  // Apply the same rule to existing history, which has no measurement marker.
  if (end && !timing.measurement && !timing.streamed && !item.summaryText && !(item.summary || []).some(Boolean) && end - timing.startedAt < 1) return null;
  return end ? Math.max(0, (end - timing.startedAt) * 1000) : Math.max(0, serverNow() - timing.startedAt * 1000);
}
function renderTurnTimings() {
  const turnsById = new Map(state.turns.map(turn => [turn.id, turn]));
  const grouped = new Map();
  for (const item of state.items) { if (!grouped.has(item.webTurnId)) grouped.set(item.webTurnId, []); grouped.get(item.webTurnId).push(item); }
  for (const turn of state.turns) {
    let node = messageNodes.get('turn:' + turn.id);
    const items = grouped.get(turn.id) || [];
    const anchor = (turn.completedAt && [...items].reverse().find(item => item.type === 'agentMessage' && item.phase !== 'commentary')) || items.find(item => item.type !== 'userMessage');
    if (!anchor || !messageNodes.has(anchor.id)) continue;
    if (!node) { node = document.createElement('div'); node.className = 'turn-timing'; node.dataset.turnId = turn.id; messageNodes.set('turn:' + turn.id, node); }
    if (node.nextElementSibling !== messageNodes.get(anchor.id)) messageNodes.get(anchor.id).before(node);
    if (turn.completedAt) {
      const reasoningItems = items.filter(item => item.type === 'reasoning');
      const intervals = reasoningItems.filter(item => reasoningDuration(item, turnsById) !== null).map(item => [item.webTiming.startedAt, item.webTiming.completedAt || turn.completedAt]).sort((a, b) => a[0] - b[0]);
      let reasoning = 0, end = 0;
      for (const [start, stop] of intervals) { reasoning += Math.max(0, stop - Math.max(start, end)) * 1000; end = Math.max(end, stop); }
      const unavailable = reasoningItems.some(item => reasoningDuration(item, turnsById) === null);
      const status = turn.status === 'interrupted' ? '已停止' : turn.status === 'failed' ? '任务失败' : '已完成';
      setText(node, `${status} · 耗时 ${durationLabel((turn.completedAt - turn.startedAt) * 1000)}${reasoning ? ' · ' + (unavailable ? '已记录思考 ' : '思考 ') + durationLabel(reasoning) : ''}${unavailable ? ' · ' + (reasoning ? '部分' : '') + '思考耗时未提供' : ''}`);
    } else setText(node, '任务进行中');
  }
  updateClocks();
}
function updateClocks() {
  const turnsById = new Map(state.turns.map(turn => [turn.id, turn]));
  for (const item of state.items) if (item.type === 'reasoning') {
    const label = messageNodes.get(item.id)?.querySelector('[data-reasoning-id]');
    if (!label) continue;
    const ms = reasoningDuration(item, turnsById);
    const turn = turnsById.get(item.webTurnId);
    const completed = item.webTiming?.completedAt || turn?.completedAt;
    setText(label, ms === null ? (completed ? '思考完成' : '思考摘要') : (completed ? '已思考 ' : '正在思考 ') + durationLabel(ms));
    const text = item.summaryText || (item.summary || []).join('\n');
    if (!text) {
      const node = messageNodes.get(item.id);
      setText(node.querySelector('.reasoning-preview'), completed ? (ms === null ? '耗时未提供' : '未提供思考摘要') : '正在分析任务');
      setText(node.querySelector('.reasoning-content p'), completed && ms === null ? '模型未提供可单独计量的思考耗时。任务总用时和等待回复时间会继续显示。' : '当前模型未提供思考摘要。');
    }
  }
  const turn = state.turns.find(t => t.id === state.thread?.turn_id) || state.turns.at(-1);
  const items = state.items.filter(item => item.webTurnId === turn?.id);
  const active = [...items].reverse().find(item => item.type !== 'userMessage' && item.webTiming && !item.webTiming.completedAt);
  const waiting = turn && !turn.completedAt && !active && state.thread?.status !== 'waiting';
  const lastOutputAt = Math.max(turn?.startedAt || 0, ...items.map(item => item.webTiming?.completedAt || item.webTiming?.startedAt || 0));
  setText($('working-label'), state.sending && !turn ? '正在发送任务' : active?.type === 'reasoning' ? '正在思考' : active?.type === 'commandExecution' ? '正在执行命令' : waiting ? '正在思考 / 等待回复' : 'Codex 正在工作');
  setText($('working-time'), turn && !turn.completedAt ? (waiting ? '已等待 ' + durationLabel(serverNow() - lastOutputAt * 1000) + ' · ' : '') + '已用时 ' + durationLabel(serverNow() - turn.startedAt * 1000) : '');
}
setInterval(() => { if (!$('workspace').hidden && ['running','waiting'].includes(state.thread?.status)) updateClocks(); }, 250);
function appendError(message) { const node = document.createElement('p'); node.className = 'error-message'; node.textContent = message; $('messages').append(node); }
function updateRunState() {
  const status = state.thread?.status || 'idle'; const running = ['running','waiting'].includes(status);
  $('run-status').textContent = status === 'running' ? '运行中' : status === 'waiting' ? '等待你的确认' : status === 'failed' ? '任务失败' : status === 'interrupted' ? '已停止' : '就绪';
  $('run-status').className = 'status-pill' + (running ? ' '+status : '');
  $('working-indicator').hidden = (!running && !state.sending) || status === 'waiting';
  $('stop-button').hidden = !running; $('stop-button').disabled = !state.thread?.turn_id;
  const imagesReady = state.attachments.length > 0 && state.attachments.every(image => image.status === 'ready');
  const imagesPending = state.attachments.some(image => image.status !== 'ready');
  $('send-button').hidden = running; $('send-button').disabled = !state.csrf || !!state.loadingThread?.blocking || (!$('prompt').value.trim() && !imagesReady) || imagesPending || state.sending;
  $('attach-image').disabled = !state.csrf || state.sending || state.attachments.length >= MAX_IMAGES;
  updateClocks();
}
function renderChanges() {
  if (!changesDirty) return; changesDirty = false;
  const loadedChanges = state.items.filter(item => item.type === 'fileChange').flatMap(item => item.changes || []);
  const paths = new Set([...(state.changePaths || []), ...(state.allChanges || loadedChanges).map(change => change.path)]);
  $('change-count').textContent = paths.size;
  if ($('changes-panel').hidden) return;
  if (!Array.isArray(state.allChanges) && state.thread) {
    const selection = state.selection, id = state.thread.id, request = ++changesRequest;
    $('changes-body').textContent = '正在加载文件变更…';
    api('/threads/' + id + '/changes').catch(async error => {
      if (error.status !== 404) throw error;
      const data = await api('/threads/' + id); return {changes: data.items.filter(item => item.type === 'fileChange').flatMap(item => item.changes || [])};
    }).then(data => {
      if (selection !== state.selection || request !== changesRequest) return;
      state.allChanges = data.changes; changesDirty = true; renderChanges();
    }).catch(error => { if (selection === state.selection) $('changes-body').textContent = error.message; });
    return;
  }
  const changes = state.allChanges || loadedChanges;
  const version = JSON.stringify(changes); if (version === changesVersion) return; changesVersion = version;
  $('changes-body').innerHTML = changes.length ? changes.map(c => `<article class="file-card"><div class="file-card-header"><span>▤</span><strong>${escapeHTML(c.path)}</strong><button class="secondary preview-file" data-path="${escapeHTML(c.path)}">预览</button></div><pre>${(c.diff || '').split('\n').map(line => `<div class="diff-line ${line.startsWith('+') ? 'add' : line.startsWith('-') ? 'remove' : ''}">${escapeHTML(line)}</div>`).join('')}</pre></article>`).join('') : '<p class="muted">当前对话还没有文件变更。</p>';
}

function renderRequests() {
  $('requests').replaceChildren();
  for (const request of state.requests) {
    const p = request.params || {}, card = document.createElement('section'); card.className = 'request-card';
    if (request.method === 'item/tool/requestUserInput') {
      card.innerHTML = '<h3>Codex 需要你的回答</h3>';
      for (const q of p.questions || []) {
        const label = document.createElement('label'); label.textContent = q.question;
        const input = q.options?.length ? document.createElement('select') : document.createElement('input'); input.dataset.questionId = q.id;
        if (q.options?.length) { input.add(new Option('选择一个回答','')); for (const opt of q.options) input.add(new Option(opt.label+(opt.description ? ' · '+opt.description : ''),opt.label)); input.add(new Option('自定义回答','__custom__')); }
        label.append(input);
        const custom = document.createElement('input'); custom.placeholder = '输入你的回答'; custom.hidden = !!q.options?.length; custom.dataset.customFor = q.id;
        if (q.options?.length) { label.append(custom); input.onchange = () => custom.hidden = input.value !== '__custom__'; }
        card.append(label);
      }
      const button = document.createElement('button'); button.className = 'primary request-actions'; button.textContent = '提交回答';
      button.onclick = async () => { const answers = {}; for (const input of card.querySelectorAll('[data-question-id]')) { const value = input.value === '__custom__' ? [...card.querySelectorAll('[data-custom-for]')].find(c => c.dataset.customFor === input.dataset.questionId).value : input.value; if (!value.trim()) { toast('请回答所有问题'); return; } answers[input.dataset.questionId] = {answers:[value]}; } await respond(request, {answers}, button); };
      card.append(button);
    } else {
      const supported = ['item/commandExecution/requestApproval','item/fileChange/requestApproval','item/permissions/requestApproval'].includes(request.method);
      card.innerHTML = `<h3>${supported ? '需要你的批准' : '此工具请求暂不支持'}</h3><p>${escapeHTML(p.reason || (supported ? '查看操作内容，决定是否继续。' : request.method))}</p><pre>${escapeHTML(p.command || JSON.stringify(p.permissions || p.changes || p, null,2))}</pre>`;
      const actions = document.createElement('div'); actions.className = 'request-actions';
      for (const [label,decision] of (supported ? [['批准本次','accept'],['拒绝','decline']] : [['跳过请求','decline']])) { const button = document.createElement('button'); button.className = decision === 'accept' ? 'primary' : 'secondary'; button.textContent = label; button.onclick = () => respond(request, {decision},button); actions.append(button); }
      card.append(actions);
    }
    $('requests').append(card);
  }
}
async function respond(request, result, button) {
  button.disabled = true;
  try { await api('/respond',{id:request.id,...result}); state.requests = state.requests.filter(r => r.id !== request.id); renderRequests(); } catch (e) { toast(e.message); button.disabled = false; }
}
function safeImageURL(url) { return typeof url === 'string' && /^\/api\/attachments\/[a-f0-9]{32}$/.test(url) ? url : ''; }
function fileSize(size) { return size >= 1024 * 1024 ? (size / (1024 * 1024)).toFixed(1) + ' MB' : Math.max(1, Math.ceil((size || 0) / 1024)) + ' KB'; }
let filePreviewRequest = 0;
async function previewFile(id) {
  if (!/^[a-f0-9]{32}$/.test(id)) return;
  const request = ++filePreviewRequest;
  $('file-dialog-title').textContent = '文件预览'; $('file-preview-text').textContent = '正在读取文件…';
  $('file-preview-pages').replaceChildren(); $('file-preview-note').textContent = ''; $('file-download').hidden = true;
  $('file-dialog').showModal();
  try {
    const data = await api('/attachments/' + id + '/preview');
    if (request !== filePreviewRequest || !$('file-dialog').open) return;
    $('file-dialog-title').textContent = data.attachment.name;
    $('file-preview-text').textContent = data.text || (data.pages.length ? '以下为文档页面预览。' : '此文件暂无文本预览，可下载原文件或让 Codex 分析。');
    $('file-preview-note').textContent = data.attachment.note || (data.truncated ? '预览展示部分内容，原文件可完整下载。' : fileSize(data.attachment.size));
    $('file-download').href = safeImageURL(data.attachment.url); $('file-download').download = data.attachment.name; $('file-download').hidden = false;
    for (const page of data.pages) if (new RegExp('^/api/attachments/' + id + '/pages/\\d+$').test(page.url)) {
      const image = document.createElement('img'); image.src = page.url; image.alt = '第 ' + page.number + ' 页'; image.loading = 'lazy'; $('file-preview-pages').append(image);
    }
  } catch (error) { if (request === filePreviewRequest) $('file-preview-text').textContent = error.message; }
}
function renderAttachments() {
  const container = $('composer-attachments'); container.replaceChildren(); container.hidden = !state.attachments.length;
  for (const image of state.attachments) {
    const tile = document.createElement('div'); tile.className = 'attachment-tile ' + image.status + (image.kind === 'file' ? ' file-tile' : ''); tile.title = image.name;
    let preview;
    if (image.kind === 'file') {
      preview = document.createElement('button'); preview.type = 'button'; preview.className = 'file-tile-preview';
      preview.textContent = '▤ ' + (image.name.split('.').at(-1) || 'FILE').toUpperCase().slice(0,8);
      preview.setAttribute('aria-label', '预览文件 ' + image.name); preview.disabled = image.status !== 'ready';
      preview.onclick = () => previewFile(image.id);
    } else {
      preview = document.createElement('img'); preview.src = image.previewURL; preview.alt = image.name;
      preview.onclick = () => { $('image-viewer-image').src = image.previewURL; $('image-dialog-title').textContent = image.name; $('image-dialog').showModal(); };
    }
    tile.append(preview);
    const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'attachment-remove'; remove.textContent = '×'; remove.setAttribute('aria-label', '移除图片 ' + image.name);
    remove.onclick = () => removeAttachment(image.clientId); remove.setAttribute('aria-label', '移除' + (image.kind === 'file' ? '文件 ' : '图片 ') + image.name); tile.append(remove);
    const caption = document.createElement('span'); caption.className = 'attachment-caption'; caption.textContent = attachmentCaption(image); tile.append(caption);
    image.caption = caption;
    if (image.savedBytes) tile.title += '\n已减少 ' + Math.round(image.savedBytes / image.file.size * 100) + '% 上传流量，保留像素尺寸';
    if (image.status === 'error') {
      const retry = document.createElement('button'); retry.type = 'button'; retry.className = 'attachment-retry'; retry.textContent = '重试'; retry.title = image.error || '重新上传图片';
      retry.onclick = () => uploadImage(image); tile.append(retry);
    }
    container.append(tile);
  }
  updateRunState();
}
function attachmentCaption(image) {
  if (image.status === 'error') return '上传失败';
  if (image.status === 'ready') return image.name;
  if (image.phase === 'queued') return '等待上传…';
  if (image.phase === 'preparing') return '优化图片…';
  if (image.phase === 'processing') return image.kind === 'file' ? '解析文件…' : '校验图片…';
  return '上传 ' + (image.progress || 0) + '%';
}
function updateUploadCaption(image) { if (image.caption) image.caption.textContent = attachmentCaption(image); }
function prepareImageUpload(image, signal) {
  if (image.kind !== 'image' || image.original || image.file.size < 256 * 1024 || !window.Worker) return Promise.resolve(image.file);
  return new Promise(resolve => {
    let worker, timer;
    const finish = blob => { clearTimeout(timer); worker?.terminate(); signal.removeEventListener('abort', aborted); resolve(blob); };
    const aborted = () => finish(image.file);
    try {
      worker = new Worker('/image-upload-worker.js');
      worker.onmessage = event => finish(event.data);
      worker.onerror = () => finish(image.file);
      signal.addEventListener('abort', aborted, {once:true});
      timer = setTimeout(() => finish(image.file), 8000);
      worker.postMessage(image.file);
    } catch { finish(image.file); }
  });
}
function transferAttachment(image, blob, signal) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const aborted = () => xhr.abort();
    const finish = (error, value) => { signal.removeEventListener('abort', aborted); error ? reject(error) : resolve(value); };
    xhr.open('POST', '/api/attachments?name=' + encodeURIComponent(image.name) + (image.kind === 'file' ? '&kind=file' : ''));
    xhr.timeout = 120000;
    xhr.setRequestHeader('Content-Type', blob.type || 'application/octet-stream');
    xhr.setRequestHeader('X-CSRF-Token', state.csrf);
    xhr.upload.onprogress = event => { if (event.lengthComputable) { image.progress = Math.round(event.loaded / event.total * 100); if (event.loaded === event.total) image.phase = 'processing'; updateUploadCaption(image); } };
    xhr.onload = () => {
      let result;
      try { result = JSON.parse(xhr.responseText); } catch { finish(new Error('服务器返回了无效响应')); return; }
      if (xhr.status < 200 || xhr.status >= 300) { if (xhr.status === 401) showAuth(false); finish(new Error(result.error || '附件上传失败')); }
      else finish(null, result);
    };
    xhr.onerror = () => finish(new Error('网络连接中断，请重试上传'));
    xhr.ontimeout = () => finish(new Error('上传超时，请检查网络后重试'));
    xhr.onabort = () => finish(new DOMException('上传已取消', 'AbortError'));
    signal.addEventListener('abort', aborted, {once:true});
    if (signal.aborted) { finish(new DOMException('上传已取消', 'AbortError')); return; }
    xhr.send(blob);
  });
}
function uploadImage(image) {
  if (uploadQueue.includes(image) || image.uploadActive) return;
  image.status = 'uploading'; image.phase = 'queued'; image.progress = 0;
  uploadQueue.push(image); renderAttachments(); drainUploads();
}
function drainUploads() {
  while (activeUploads < 2 && uploadQueue.length) {
    const image = uploadQueue.shift();
    if (!state.attachments.includes(image)) continue;
    activeUploads++; image.uploadActive = true;
    performUpload(image).finally(() => { activeUploads--; image.uploadActive = false; drainUploads(); });
  }
}
async function performUpload(image) {
  image.phase = 'preparing'; image.controller = new AbortController(); updateUploadCaption(image);
  try {
    const signal = image.controller.signal;
    const blob = image.uploadBlob || await prepareImageUpload(image, signal);
    if (signal.aborted || !state.attachments.includes(image)) return;
    image.uploadBlob = blob; image.savedBytes = image.file.size - blob.size;
    image.phase = 'transferring'; updateUploadCaption(image);
    const result = await transferAttachment(image, blob, signal);
    if (!state.attachments.includes(image)) { api('/attachments/' + result.attachment.id + '/remove', {}).catch(() => {}); return; }
    Object.assign(image, result.attachment); image.status = 'ready';
  } catch (error) {
    if (error.name === 'AbortError' || !state.attachments.includes(image)) return;
    image.status = 'error'; image.error = error.message; toast(error.message);
  } finally { if (state.attachments.includes(image)) renderAttachments(); }
}
function addImageFiles(files) {
  if (!state.csrf || state.sending) return;
  for (const file of files) {
    if (state.attachments.length >= MAX_IMAGES) { toast('每条消息最多添加 8 个附件'); break; }
    const isImage = ['image/png', 'image/jpeg', 'image/webp', 'image/gif'].includes(file.type) || /\.(png|jpe?g|webp|gif)$/i.test(file.name);
    if (!file.size || file.size > (isImage ? MAX_IMAGE_BYTES : MAX_FILE_BYTES)) { toast(isImage ? '每张图片最大 10 MB' : '每个文件最大 25 MB'); continue; }
    const image = {clientId: 'image-' + ++imageSequence, kind: isImage ? 'image' : 'file', file, name: file.name || '粘贴的图片.png', previewURL: isImage ? URL.createObjectURL(file) : '', status: 'uploading', original: $('original-image').checked};
    state.attachments.push(image); uploadImage(image);
  }
  renderAttachments();
}
function removeAttachment(clientId) {
  const image = state.attachments.find(value => value.clientId === clientId); if (!image) return;
  state.attachments = state.attachments.filter(value => value !== image); const queued = uploadQueue.indexOf(image); if (queued >= 0) uploadQueue.splice(queued, 1); image.controller?.abort(); URL.revokeObjectURL(image.previewURL);
  if (image.id && state.csrf) api('/attachments/' + image.id + '/remove', {}).catch(() => {});
  renderAttachments();
}
function clearAttachments() { for (const image of [...state.attachments]) removeAttachment(image.clientId); }
async function sendMessage(event) {
  event.preventDefault(); const text = $('prompt').value.trim(); const images = [...state.attachments];
  if ((!text && !images.length) || images.some(image => image.status !== 'ready') || state.sending || state.loadingThread?.blocking || ['running','waiting'].includes(state.thread?.status)) return;
  const selection = state.selection;
  const pendingId = 'pending:' + Date.now();
  state.items.push({id: pendingId, type: 'userMessage', content: [...(text ? [{type: 'text', text}] : []), ...images.map(image => ({type: image.kind || 'image', ...image, file: undefined, uploadBlob: undefined, caption: undefined, controller: undefined}))], webPending: true});
  state.attachments = []; renderAttachments();
  $('prompt').value = ''; $('prompt').style.height = '';
  state.sending = true; pinToBottom = true; renderMessages();
  let targetThread = state.thread;
  const targetCwd = targetThread?.cwd || state.settings.cwd;
  try {
    if (!targetThread) {
      const result = await api('/threads',{cwd: targetCwd}); targetThread = result.thread;
      if (selection === state.selection) {
        state.thread = targetThread; state.threadSeq = state.seq;
        // Keep the optimistic message when the server assigns the new thread ID.
        renderedThread = targetThread.id;
        rememberThread(targetThread.id); applySettings();
      }
    }
    const tid = targetThread.id;
    await api('/threads/'+tid+'/send',{text, attachments: images.map(image => image.id)});
    for (const image of images) URL.revokeObjectURL(image.previewURL);
    scheduleThreadRefresh();
    if (selection === state.selection && state.items.some(item => item.id === pendingId)) {
      // A disconnected stream needs a snapshot; ordinary sends use live events.
      if (state.stream?.readyState !== EventSource.OPEN) await selectThread(tid).catch(error => toast('消息已发送，历史暂未加载：' + error.message));
    }
  } catch (e) {
    toast(e.message);
    if (selection === state.selection) {
      state.items = state.items.filter(item => item.id !== pendingId);
      if (!$('prompt').value) $('prompt').value = text;
      state.attachments = [...images, ...state.attachments]; renderAttachments();
      renderMessages();
    } else {
      for (const image of images) URL.revokeObjectURL(image.previewURL);
    }
    if (state.thread) refreshThreads().catch(() => {});
  }
  finally { state.sending = false; updateRunState(); }
}
function closeSidebar() { $('sidebar').classList.remove('open'); $('sidebar-backdrop').hidden = true; }
function openSettings(tab='general') {
  const s = state.settings;
  $('setting-cwd').value = s.cwd; $('setting-model').value = s.model; $('setting-effort').value = s.effort; $('setting-sandbox').value = s.sandbox; $('setting-approval').value = s.approvalPolicy; $('setting-theme').value = s.theme;
  $('credentials-form').reset(); $('setting-username').value = state.username;
  $('general-error').textContent = ''; $('credentials-error').textContent = ''; selectSettingsTab(tab);
  closeSidebar(); $('settings-dialog').showModal();
}
function selectSettingsTab(tab) { for (const el of document.querySelectorAll('[data-panel]')) el.hidden = el.dataset.panel !== tab; for (const el of document.querySelectorAll('[data-tab]')) el.classList.toggle('active',el.dataset.tab === tab); }
async function copyText(text) { try { if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text); else { const field = document.createElement('textarea'); field.value = text; document.body.append(field); field.select(); if (!document.execCommand('copy')) throw new Error(); field.remove(); } toast('已复制'); } catch { toast('复制失败，请选择文字手动复制'); } }
$('auth-form').onsubmit = async event => {
  event.preventDefault(); if (authPending || (!state.setup && authLockedUntil > Date.now())) return; $('auth-error').textContent = '';
  if (state.setup && $('auth-password').value !== $('auth-confirm').value) { $('auth-error').textContent = '两次输入的密码不一致'; return; }
  authPending = true; $('auth-submit').disabled = true;
  try { const data = await api(state.setup ? '/setup' : '/login', {username:$('auth-username').value.trim(),password:$('auth-password').value}); authLockedUntil = 0; lockWasActive = false; $('auth-form').reset(); await enterWorkspace(data); }
  catch (e) { $('auth-error').textContent = e.message; $('auth-password').value = ''; if (e.details?.retryAfter) setLoginLock(e.details); }
  finally { authPending = false; $('auth-submit').disabled = false; updateLoginLock(); }
};
$('password-toggle').onclick = () => { const show = $('auth-password').type === 'password'; $('auth-password').type = show ? 'text' : 'password'; $('password-toggle').setAttribute('aria-label',show ? '隐藏密码' : '显示密码'); };
$('new-chat').onclick = newChat; $('search').oninput = renderThreadList; $('composer-form').onsubmit = sendMessage;
function resizePrompt() {
  const prompt = $('prompt');
  if (!prompt.value) { prompt.style.height = ''; return; }
  prompt.style.height = '0px';
  const maximum = parseFloat(getComputedStyle(prompt).maxHeight) || 180;
  prompt.style.height = Math.min(maximum, prompt.scrollHeight) + 'px';
}
$('prompt').oninput = () => { resizePrompt(); updateRunState(); };
window.addEventListener('resize', resizePrompt);
$('attach-image').onclick = () => $('image-input').click();
$('image-input').onchange = () => { addImageFiles([...$('image-input').files]); $('image-input').value = ''; };
$('prompt').addEventListener('paste', event => { const files = [...(event.clipboardData?.files || [])]; if (files.length) { event.preventDefault(); addImageFiles(files); } });
$('workspace').addEventListener('dragenter', event => { if (event.dataTransfer?.types.includes('Files')) { event.preventDefault(); imageDragDepth++; $('composer-form').classList.add('drag-over'); } });
$('workspace').addEventListener('dragover', event => { if (event.dataTransfer?.types.includes('Files')) { event.preventDefault(); event.dataTransfer.dropEffect = 'copy'; } });
$('workspace').addEventListener('dragleave', event => { if (event.dataTransfer?.types.includes('Files')) { imageDragDepth = Math.max(0, imageDragDepth - 1); if (!imageDragDepth) $('composer-form').classList.remove('drag-over'); } });
$('workspace').addEventListener('drop', event => { if (event.dataTransfer?.files.length) { event.preventDefault(); imageDragDepth = 0; $('composer-form').classList.remove('drag-over'); addImageFiles([...event.dataTransfer.files]); } });
$('close-image').onclick = () => $('image-dialog').close();
$('image-dialog').addEventListener('close', () => { $('image-viewer-image').removeAttribute('src'); });
$('close-file').onclick = () => $('file-dialog').close();
$('file-dialog').addEventListener('close', () => { filePreviewRequest++; });
$('scroll-area').addEventListener('scroll', () => { const scroll = $('scroll-area'); pinToBottom = scroll.scrollHeight - scroll.scrollTop - scroll.clientHeight < 100; }, {passive: true});
$('prompt').onkeydown = event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); $('composer-form').requestSubmit(); } };
$('stop-button').onclick = async () => { if (!state.thread) return; $('stop-button').disabled = true; try { await api('/threads/'+state.thread.id+'/interrupt',{}); toast('已请求停止任务'); } catch (e) { toast(e.message); } finally { updateRunState(); } };
for (const button of document.querySelectorAll('[data-prompt]')) button.onclick = () => { $('prompt').value = button.dataset.prompt; resizePrompt(); $('prompt').focus(); updateRunState(); };
$('sidebar-open').onclick = () => { $('sidebar').classList.add('open'); $('sidebar-backdrop').hidden = false; };
$('sidebar-close').onclick = closeSidebar; $('sidebar-backdrop').onclick = closeSidebar;
$('open-settings').onclick = () => openSettings(); $('project-button').onclick = openProjectDialog; $('close-settings').onclick = () => $('settings-dialog').close();
$('add-project').onclick = openProjectDialog;
$('close-project').onclick = () => $('project-dialog').close();
$('cancel-project').onclick = () => $('project-dialog').close();
$('browse-folder').onclick = () => browseDirectories($('project-path').value.trim());
$('folder-up').onclick = () => { if (folderParent) browseDirectories(folderParent); };
$('project-dialog').addEventListener('close', () => { folderBrowseRequest++; });
$('project-form').onsubmit = async event => {
  event.preventDefault(); const button = $('save-project'); button.disabled = true; $('project-error').textContent = '';
  const selection = state.selection;
  try {
    const result = await api('/projects', {path: $('project-path').value.trim()});
    state.projects = result.projects; state.settings = result.settings; collapsedProjects.delete(result.project.id);
    $('project-dialog').close();
    if (selection === state.selection) { newChat({preserveDraft: true}); updateRunState(); } else { applySettings(); renderThreadList(); }
    toast('项目文件夹已保存，下次登录可直接使用');
  } catch (error) { $('project-error').textContent = error.message; }
  finally { button.disabled = false; }
};
for (const button of document.querySelectorAll('[data-tab]')) button.onclick = () => selectSettingsTab(button.dataset.tab);
$('general-form').onsubmit = async event => {
  event.preventDefault(); const button = $('general-form').querySelector('[type=submit]'); button.disabled = true; $('general-error').textContent = '';
  try { state.settings = await api('/settings',{cwd:$('setting-cwd').value.trim(),model:$('setting-model').value.trim(),effort:$('setting-effort').value,sandbox:$('setting-sandbox').value,approvalPolicy:$('setting-approval').value,theme:$('setting-theme').value}); applySettings(); await refreshProjects(); toast('工作偏好已保存'); $('settings-dialog').close(); }
  catch (e) { $('general-error').textContent = e.message; } finally { button.disabled = false; }
};
$('credentials-form').onsubmit = async event => {
  event.preventDefault(); $('credentials-error').textContent = '';
  if ($('new-password').value !== $('confirm-password').value) { $('credentials-error').textContent = '两次输入的密码不一致'; return; }
  const button = $('credentials-form').querySelector('[type=submit]'); button.disabled = true;
  try { const data = await api('/credentials',{currentPassword:$('current-password').value,username:$('setting-username').value.trim(),password:$('new-password').value}); state.csrf = data.csrf; state.username = data.username; $('account-name').textContent = data.username; $('avatar').textContent = data.username.slice(0,1).toUpperCase(); $('credentials-form').reset(); $('settings-dialog').close(); connectEvents(); toast('账号与密码已更新，其他登录已失效'); }
  catch (e) { $('credentials-error').textContent = e.message; } finally { button.disabled = false; }
};
$('logout').onclick = async () => { try { await api('/logout',{}); rememberThread(null); showAuth(false); } catch (e) { toast(e.message); } };
$('model-picker').onchange = async () => { const model = $('model-picker').value; try { state.settings = await api('/settings',{model}); applySettings(); toast('模型已更新，将在下次发送时使用'); } catch (e) { toast(e.message); applySettings(); } };
$('effort-picker').onchange = async () => { try { state.settings = await api('/settings',{effort:$('effort-picker').value}); applySettings(); } catch (e) { toast(e.message); applySettings(); } };
$('show-changes').onclick = () => { $('changes-panel').hidden = !$('changes-panel').hidden; if (!$('changes-panel').hidden) { changesDirty = true; renderChanges(); } };
$('close-changes').onclick = () => $('changes-panel').hidden = true; $('close-text').onclick = () => $('text-dialog').close();
$('changes-body').onclick = async event => { const button = event.target.closest('.preview-file'); if (!button || !state.thread) return; try { const data = await api('/files?thread='+encodeURIComponent(state.thread.id)+'&path='+encodeURIComponent(button.dataset.path)); $('text-dialog-title').textContent = data.path; $('text-dialog-body').textContent = data.text; $('text-dialog').showModal(); } catch (e) { toast(e.message); } };
$('messages').onclick = event => { const button = event.target.closest('.copy-button'); if (button) copyText(button.closest('pre').querySelector('code').textContent); const image = event.target.closest('.message-image'); if (image && safeImageURL(image.dataset.imageUrl)) { $('image-viewer-image').src = image.dataset.imageUrl; $('image-dialog-title').textContent = image.dataset.imageName || '图片预览'; $('image-dialog').showModal(); } };
$('messages').addEventListener('toggle', event => {
  const node = event.target;
  if (!node.matches('details[data-item-id]') || !node.open) return;
  const item = state.items.find(item => item.id === node.dataset.itemId);
  if (item) { renderToolBody(node, item); updateClocks(); }
}, true);
$('messages').addEventListener('click', event => { const button = event.target.closest('[data-file-id]'); if (button) previewFile(button.dataset.fileId); });
$('thread-menu').onclick = () => {
  const old = document.querySelector('.thread-menu-popover'); if (old) { old.remove(); return; }
  if (!state.thread) { toast('开始一段对话后，可以重命名或归档'); return; }
  const menu = document.createElement('div'); menu.className = 'thread-menu-popover';
  for (const [label,action] of [['重命名对话','rename'],['归档对话','archive']]) { const button = document.createElement('button'); button.textContent = label; button.onclick = async () => { menu.remove(); const tid = state.thread?.id; if (!tid) return; try { if (action === 'rename') { const title = window.prompt('输入对话名称',state.thread.title); if (!title?.trim()) return; await api('/threads/'+tid+'/rename',{title}); } else { await api('/threads/'+tid+'/archive',{}); newChat(); toast('对话已归档'); } await refreshThreads(); } catch (e) { toast(e.message); } }; menu.append(button); }
  document.body.append(menu);
};
document.addEventListener('click', event => { if (!event.target.closest('.thread-menu-popover') && !event.target.closest('#thread-menu')) document.querySelector('.thread-menu-popover')?.remove(); if (!event.target.closest('.project-menu-popover') && !event.target.closest('.project-more')) document.querySelector('.project-menu-popover')?.remove(); });
document.addEventListener('keydown', event => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k' && state.csrf && !$('settings-dialog').open) { event.preventDefault(); newChat(); } });
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',applyTheme);
window.addEventListener('online', () => { if (state.csrf) connectEvents(); });
async function restoreWorkspace() {
  $('startup-screen').hidden = false; $('startup-retry').hidden = true;
  $('startup-message').textContent = '正在恢复你的对话…';
  try {
    const saved = savedThread();
    let data;
    try { data = await api('/bootstrap' + (saved ? '?thread=' + encodeURIComponent(saved) : '')); }
    catch (error) {
      // Keep the updated frontend usable while a running server waits to restart.
      if (error.status !== 404) throw error;
      const status = await api('/status');
      if (status.setupRequired) data = {...status, authenticated: false};
      else { try { data = {...await api('/me'), authenticated: true}; } catch (error) { if (error.status !== 401) throw error; data = {...status, authenticated: false}; } }
    }
    if (data.authenticated) await enterWorkspace(data);
    else { showAuth(data.setupRequired); if (!data.setupRequired) setLoginLock(data); }
  } catch (error) {
    if (state.csrf) { $('startup-screen').hidden = true; toast('对话暂未恢复：' + error.message); }
    else { $('startup-message').textContent = '暂时无法连接服务器：' + error.message; $('startup-retry').hidden = false; }
  }
}
$('startup-retry').onclick = restoreWorkspace;
restoreWorkspace();
