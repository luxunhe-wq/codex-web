#!/usr/bin/env python3
"""Authenticated browser client for the locally installed Codex app-server."""
import argparse
from contextlib import contextmanager
import gzip
import hashlib
import hmac
import getpass
import ipaddress
from io import BytesIO
import json
import logging
import math
import os
from pathlib import Path
import queue
import re
import secrets
import shutil
import signal
import socket
import sqlite3
import stat
import subprocess
import sys
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer as BaseThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

from PIL import Image
from configuration import load_environment

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('CODEX_WEB_DATA', str(ROOT / 'data')))
STATIC = ROOT / 'static'
LOG = logging.getLogger('codex-web')
LOGIN_FAILURE_LIMIT = 6
LOGIN_LOCK_SECONDS = 6 * 60
SESSION_SECONDS = 30 * 24 * 60 * 60
SESSION_IDLE_SECONDS = SESSION_SECONDS
SESSION_RENEW_SECONDS = 5 * 60
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGES = 8
MAX_IMAGE_PIXELS = 40_000_000
MAX_FILE_BYTES = 25 * 1024 * 1024


class ApiError(Exception):
    def __init__(self, message, status=400, **details):
        super().__init__(message)
        self.status = status
        self.details = details


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def reasoning_duration_available(item):
    timing = item.get('webTiming')
    if not timing or timing.get('measurement') == 'unavailable':
        return False
    if not timing.get('completedAt') or timing.get('measurement') == 'observed':
        return True
    # Opaque reasoning is often delivered as a start/end pair after computation.
    # A subsecond pair without streamed text is not a model duration measurement.
    return bool(timing.get('streamed') or item.get('summaryText')
                or any(item.get('summary') or [])
                or timing['completedAt'] - timing['startedAt'] >= 1)


def image_info(data):
    """Validate actual raster content, allowing camera metadata after image data."""
    formats = {'PNG': ('image/png', 'png'), 'JPEG': ('image/jpeg', 'jpg'),
               'GIF': ('image/gif', 'gif'), 'WEBP': ('image/webp', 'webp')}
    if not (data.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8', b'GIF87a', b'GIF89a'))
            or (data[:4] == b'RIFF' and data[8:12] == b'WEBP')):
        raise ApiError('支持 PNG、JPEG、WebP 和 GIF 图片', 415)
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in formats:
                raise ApiError('支持 PNG、JPEG、WebP 和 GIF 图片', 415)
            mime, extension = formats[image.format]
            width, height = image.size
            if width <= 0 or height <= 0:
                raise ApiError('图片无法读取，请重新选择')
            if width * height > MAX_IMAGE_PIXELS:
                raise ApiError('图片尺寸过大，请缩小后重试', 413)
            image.verify()
        # Header verification alone does not detect truncated JPEG pixel data.
        with Image.open(BytesIO(data)) as image:
            image.load()
    except Image.DecompressionBombError:
        raise ApiError('图片尺寸过大，请缩小后重试', 413)
    except (OSError, ValueError, SyntaxError, EOFError):
        raise ApiError('图片数据损坏或不完整，请重新选择原图')
    return mime, extension, width, height


def project_directory(value):
    if not isinstance(value, str) or not value or len(value) > 4096 or '\0' in value or not Path(value).is_absolute():
        raise ApiError('请输入文件夹的绝对路径，例如 /home/user/projects')
    try:
        path = Path(value).resolve(strict=True)
        if not path.is_dir():
            raise ApiError('此路径不是文件夹')
        return path
    except FileNotFoundError:
        raise ApiError('文件夹不存在，请检查路径', 404)
    except PermissionError:
        raise ApiError('没有权限访问此文件夹', 403)
    except (OSError, RuntimeError):
        raise ApiError('无法访问此文件夹，请检查路径')


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex()


def validate_credentials(username, password):
    if not isinstance(username, str) or not re.fullmatch(r'[\w.@-]{3,40}', username):
        raise ApiError('账号需为 3–40 位字母、数字、中文或 . @ _ -')
    if not isinstance(password, str) or not 10 <= len(password) <= 256:
        raise ApiError('密码长度需为 10–256 位')


def preview_file(root, value, data):
    if not value or '\0' in value:
        raise ApiError('文件路径不正确')
    root = Path(root).resolve()
    requested = Path(os.path.normpath(str(root / value)))
    try:
        relative = requested.relative_to(root)
    except ValueError:
        raise ApiError('只能查看当前项目中的文件', 403)
    blocked_parts = {'.git', '.codex', '.ssh', '.aws', '.azure', '.kube', '.gnupg',
                     '.docker', '.npmrc', '.netrc', '.pypirc', 'data', '.env',
                     'auth.json', 'credentials', 'credentials.json'}
    if (not relative.parts or any(part in blocked_parts or part.startswith('.env.')
            or part.endswith(('.pem', '.key', '.p12', '.pfx')) or part.startswith('id_rsa')
            or part.startswith('id_ed25519') for part in requested.parts)
            or requested == data.resolve() or data.resolve() in requested.parents
            or any(Path(p) == requested or Path(p) in requested.parents
                   for p in ('/proc', '/sys', '/dev', '/run', '/etc'))):
        raise ApiError('敏感文件不可预览', 403)
    # Open each path component relative to a held directory descriptor. Refuse symlinks
    # and use fstat on the opened file so path swaps cannot bypass containment checks.
    fd = None
    try:
        fd = os.open(str(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for index, part in enumerate(relative.parts):
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if index < len(relative.parts) - 1:
                flags |= os.O_DIRECTORY
            next_fd = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ApiError('仅支持普通文本文件')
        if info.st_nlink > 1:
            raise ApiError('硬链接文件不可预览', 403)
        if info.st_size > 512000:
            raise ApiError('文件过大，请在本机查看')
        with os.fdopen(fd, 'rb') as file:
            fd = None
            content = file.read(512001)
        if len(content) > 512000:
            raise ApiError('文件过大，请在本机查看')
        return {'path': str(requested), 'text': content.decode('utf-8')}
    except UnicodeDecodeError:
        raise ApiError('仅支持文本文件预览')
    except FileNotFoundError:
        raise ApiError('文件不存在', 404)
    except OSError:
        raise ApiError('文件不可预览（不支持符号链接）', 403)
    finally:
        if fd is not None:
            os.close(fd)


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        self.lock = threading.RLock()
        self.transaction_depth = 0
        self.changed = threading.Condition(self.lock)
        self.db = sqlite3.connect(str(directory / 'web.sqlite3'), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.attachment_directory = (directory / 'attachments').resolve()
        self.attachment_directory.mkdir(mode=0o700, exist_ok=True)
        os.chmod(self.attachment_directory, 0o700)
        seed_projects = not self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='projects'").fetchone()
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY CHECK(id=1), username TEXT,
            salt TEXT, hash TEXT);
          CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, csrf TEXT, expires REAL);
          CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT);
          CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL, created REAL NOT NULL, last_used REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS attachments (id TEXT PRIMARY KEY, filename TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL, width INTEGER NOT NULL,
            height INTEGER NOT NULL, created REAL NOT NULL, thread_id TEXT);
          CREATE TABLE IF NOT EXISTS threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT,
            model TEXT, created REAL, updated REAL, archived INTEGER DEFAULT 0,
            status TEXT DEFAULT 'idle', turn_id TEXT);
          CREATE TABLE IF NOT EXISTS items (seq INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT, item_id TEXT, value TEXT, UNIQUE(thread_id,item_id));
          CREATE INDEX IF NOT EXISTS items_thread_seq ON items(thread_id,seq);
          CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT);
          CREATE TABLE IF NOT EXISTS turns (id TEXT PRIMARY KEY, thread_id TEXT NOT NULL,
            started REAL NOT NULL, completed REAL, status TEXT NOT NULL, reasoning_ms INTEGER NOT NULL DEFAULT 0);
          CREATE INDEX IF NOT EXISTS turns_thread ON turns(thread_id, started);
          CREATE TABLE IF NOT EXISTS auth_limits (bucket TEXT PRIMARY KEY,
            failures INTEGER NOT NULL DEFAULT 0, locked_until REAL NOT NULL DEFAULT 0,
            updated REAL NOT NULL);
        ''')
        columns = {row[1] for row in self.db.execute('PRAGMA table_info(sessions)')}
        if 'last_seen' not in columns:
            self.db.execute('ALTER TABLE sessions ADD COLUMN last_seen REAL NOT NULL DEFAULT 0')
            self.db.execute('UPDATE sessions SET last_seen=?,expires=MIN(expires,?)',
                            (time.time(), time.time() + SESSION_SECONDS))
        attachment_columns = {row[1] for row in self.db.execute('PRAGMA table_info(attachments)')}
        for column, definition in [('kind', "TEXT NOT NULL DEFAULT 'image'"), ('analysis', "TEXT NOT NULL DEFAULT '{}' ")]:
            if column not in attachment_columns:
                self.db.execute('ALTER TABLE attachments ADD COLUMN ' + column + ' ' + definition)
        if not self.one('SELECT id FROM settings WHERE id=1'):
            self.db.execute('INSERT INTO settings VALUES (1,?)', (encode({
                'cwd': str(project_directory(os.environ.get('CODEX_WEB_CWD', str(ROOT)))),
                'model': '', 'effort': 'high', 'sandbox': 'workspace-write',
                'approvalPolicy': 'on-request', 'theme': 'light'}),))
        if seed_projects:
            paths = [self.settings()['cwd']] + [row['cwd'] for row in self.all('SELECT DISTINCT cwd FROM threads')]
            for value in paths:
                try:
                    self.remember_project(project_directory(value))
                except ApiError:
                    pass
        self.db.execute("UPDATE threads SET status='interrupted',turn_id=NULL WHERE status IN ('running','waiting')")
        for row in self.all('SELECT id,thread_id FROM turns WHERE completed IS NULL'):
            self.finish_turn(row['thread_id'], row['id'], 'interrupted', time.time())
        self.db.commit()
        os.chmod(directory / 'web.sqlite3', 0o600)
        self.attachments_pruned_at = 0
        self.prune_unused_attachments()

    def one(self, sql, args=()):
        with self.lock:
            row = self.db.execute(sql, args).fetchone()
            return dict(row) if row else None

    def all(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def write(self, sql, args=()):
        with self.lock:
            self.db.execute(sql, args)
            if not self.transaction_depth:
                self.db.commit()

    @contextmanager
    def transaction(self):
        # Persist an item update and its replay event with one disk commit.
        with self.lock:
            self.transaction_depth += 1
            try:
                yield
                if self.transaction_depth == 1:
                    self.db.commit()
            except Exception:
                if self.transaction_depth == 1:
                    self.db.rollback()
                raise
            finally:
                self.transaction_depth -= 1

    def turns(self, tid):
        return [{'id': row['id'], 'startedAt': row['started'], 'completedAt': row['completed'],
                 'status': row['status'], 'reasoningMs': row['reasoning_ms']}
                for row in self.all('SELECT * FROM turns WHERE thread_id=? ORDER BY started', (tid,))]

    def finish_turn(self, tid, turn_id, status, now):
        # An interrupted reasoning item may never receive item/completed.
        intervals = []
        for row in self.all('SELECT value FROM items WHERE thread_id=?', (tid,)):
            item = json.loads(row['value'])
            if item.get('type') != 'reasoning' or item.get('webTurnId') != turn_id or not item.get('webTiming'):
                continue
            timing = item['webTiming']
            if not timing.get('completedAt'):
                timing['completedAt'] = now
                timing['durationMs'] = round(max(0, now - timing['startedAt']) * 1000)
                self.item(tid, item)
            if not reasoning_duration_available(item):
                continue
            intervals.append((timing['startedAt'], max(timing['startedAt'], timing['completedAt'])))
        total = 0
        end = 0
        for start, stop in sorted(intervals):
            total += max(0, stop - max(start, end))
            end = max(end, stop)
        self.write('UPDATE turns SET completed=?,status=?,reasoning_ms=? WHERE id=? AND thread_id=? AND completed IS NULL',
                   (now, status, round(total * 1000), turn_id, tid))

    def settings(self):
        return json.loads(self.one('SELECT value FROM settings WHERE id=1')['value'])

    def public_attachment(self, row):
        analysis = json.loads(row['analysis'])
        return {'id': row['id'], 'url': '/api/attachments/' + row['id'], 'name': row['name'], 'kind': row['kind'],
                'mimeType': row['mime'], 'size': row['size'], 'width': row['width'], 'height': row['height'],
                'note': analysis.get('note', ''), 'pages': analysis.get('pages', 0)}

    def attachment(self, attachment_id):
        if not isinstance(attachment_id, str) or not re.fullmatch(r'[a-f0-9]{32}', attachment_id):
            raise ApiError('图片附件不正确', 400)
        row = self.one('SELECT * FROM attachments WHERE id=?', (attachment_id,))
        if not row:
            raise ApiError('图片附件不存在，请重新添加', 404)
        return row

    def attachment_bytes(self, row):
        directory_fd = os.open(self.attachment_directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fd = os.open(row['filename'], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        except OSError:
            raise ApiError('图片附件无法读取，请重新添加', 404)
        finally:
            os.close(directory_fd)
        with os.fdopen(fd, 'rb') as file:
            info = os.fstat(file.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size != row['size']:
                raise ApiError('图片附件无法读取，请重新添加', 400)
            return file.read(MAX_FILE_BYTES + 1)

    def attachment_page(self, row, page):
        if page not in json.loads(row['analysis']).get('scanPages', []):
            raise ApiError('页面不存在', 404)
        root_fd = os.open(self.attachment_directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        directory_fd = None
        try:
            directory_fd = os.open(row['id'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
            fd = os.open('page-%d.png' % page, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
            with os.fdopen(fd, 'rb') as file:
                info = os.fstat(file.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_IMAGE_BYTES:
                    raise ApiError('页面无法读取', 404)
                return file.read(MAX_IMAGE_BYTES + 1)
        except OSError:
            raise ApiError('页面无法读取', 404)
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
            os.close(root_fd)

    def remove_attachment_files(self, row):
        if re.fullmatch(r'[a-f0-9]{32}\.[a-z0-9]{1,12}', row['filename']):
            (self.attachment_directory / row['filename']).unlink(missing_ok=True)
        derived = self.attachment_directory / row['id']
        if derived.is_symlink():
            derived.unlink()
        elif derived.exists():
            shutil.rmtree(derived)

    def prune_unused_attachments(self):
        now = time.time()
        if now - self.attachments_pruned_at < 3600:
            return
        with self.transaction():
            rows = self.all('SELECT id,filename FROM attachments WHERE thread_id IS NULL AND created<?', (now - 86400,))
            for row in rows:
                if re.fullmatch(r'[a-f0-9]{32}\.(png|jpg|webp|gif)', row['filename']):
                    self.remove_attachment_files(row)
                elif re.fullmatch(r'[a-f0-9]{32}\.[a-z0-9]{1,12}', row['filename']):
                    self.remove_attachment_files(row)
                self.write('DELETE FROM attachments WHERE id=?', (row['id'],))
        self.attachments_pruned_at = now

    def add_attachment(self, data, name, declared=None, kind='image'):
        self.prune_unused_attachments()
        name = re.sub(r'[\x00-\x1f\x7f]', '', name).replace('\\', '/').rsplit('/', 1)[-1][:200] or '文件'
        if kind == 'image':
            mime, extension, width, height = image_info(data)
            if declared is not None and declared not in (mime, 'application/octet-stream'):
                raise ApiError('图片类型与文件内容不一致', 415)
        else:
            width = height = 0
            extension = Path(name).suffix.lower().lstrip('.')
            if not re.fullmatch(r'[a-z0-9]{1,12}', extension):
                extension = 'bin'
            mime = 'application/pdf' if extension == 'pdf' else 'application/octet-stream'
        attachment_id = secrets.token_hex(16)
        filename = attachment_id + '.' + extension
        directory_fd = os.open(self.attachment_directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory_fd)
            with os.fdopen(fd, 'wb') as file:
                file.write(data)
            try:
                analysis = {}
                if kind == 'file':
                    derived = self.attachment_directory / attachment_id
                    derived.mkdir(mode=0o700)
                    try:
                        process = subprocess.run([sys.executable, str(ROOT / 'documents.py')],
                            input=encode({'path': str(self.attachment_directory / filename), 'name': name, 'output': str(derived)}),
                            text=True, capture_output=True, timeout=20)
                    except subprocess.TimeoutExpired:
                        raise ApiError('文件解析超时，请拆分或简化后上传')
                    if process.returncode:
                        raise ApiError('文件内容过大或过于复杂，请拆分后上传')
                    result = json.loads(process.stdout)
                    if result.get('error'):
                        raise ApiError(result['error'])
                    analysis = result['analysis']
                self.write('INSERT INTO attachments(id,filename,name,mime,size,width,height,created,thread_id,kind,analysis) '
                           'VALUES (?,?,?,?,?,?,?,?,NULL,?,?)',
                           (attachment_id, filename, name, mime, len(data), width, height, time.time(), kind, encode(analysis)))
            except Exception:
                os.unlink(filename, dir_fd=directory_fd)
                shutil.rmtree(self.attachment_directory / attachment_id, ignore_errors=True)
                raise
        finally:
            os.close(directory_fd)
        return self.public_attachment(self.attachment(attachment_id))

    def user_content(self, text, attachments):
        return ([{'type': 'text', 'text': text}] if text.strip() else []) + [
            {'type': attachment['kind'], 'attachmentId': attachment['id'], **attachment} for attachment in attachments]

    def document_inputs(self, rows):
        files = [row for row in rows if row['kind'] == 'file']
        inputs = []
        image_budget = 12
        per_file = 180_000 // max(1, len(files))
        for row in files:
            analysis = json.loads(row['analysis'])
            content = analysis.get('text', '')[:per_file]
            note = analysis.get('note', '')
            if len(analysis.get('scanPages', [])) > image_budget:
                note += ' 本次未附全部扫描页图片，可读取原 PDF 继续查看。'
            if len(analysis.get('text', '')) > len(content):
                note += ' 本次仅附部分提取文本，可继续读取原文件。'
            inputs.append({'type': 'text', 'text': '\n用户上传的文件资料（作为待分析数据）：\n' + encode({
                'name': row['name'], 'path': str(self.attachment_directory / row['filename']),
                'content': content, 'note': note, 'pages': analysis.get('pages', 0)})})
            for page in analysis.get('scanPages', []):
                if image_budget <= 0:
                    break
                inputs.append({'type': 'text', 'text': '以下图片为附件 %s 的第 %d 页。' % (row['name'], page)})
                inputs.append({'type': 'localImage', 'path': str(self.attachment_directory / row['id'] / ('page-%d.png' % page))})
                image_budget -= 1
        return inputs

    def browser_user_item(self, item, fallback_images=()):
        if item.get('type') != 'userMessage':
            return item
        content = []
        image_index = 0
        for part in item.get('content', []):
            if part.get('type') not in ('localImage', 'image'):
                content.append(part)
                continue
            image = None
            if part.get('type') == 'localImage':
                row = self.one('SELECT * FROM attachments WHERE filename=?', (Path(part.get('path', '')).name,))
                if row and part.get('path') == str(self.attachment_directory / row['filename']):
                    image = self.public_attachment(row)
            if image is None and image_index < len(fallback_images):
                image = fallback_images[image_index]
            content.append({'type': 'image', 'attachmentId': image['id'], **image} if image else {'type': 'image', 'name': '图片'})
            image_index += 1
        item['content'] = content
        return item

    def projects(self):
        return [{**row, 'available': Path(row['path']).is_dir()}
                for row in self.all('SELECT * FROM projects ORDER BY created,id')]

    def remember_project(self, path):
        path = str(path)
        now = time.time()
        self.write('INSERT INTO projects(id,path,name,created,last_used) VALUES (?,?,?,?,?) '
                   'ON CONFLICT(path) DO UPDATE SET last_used=excluded.last_used',
                   (secrets.token_hex(8), path, Path(path).name or '/', now, now))
        return self.one('SELECT * FROM projects WHERE path=?', (path,))

    def publish_projects(self):
        self.publish({'method': 'web/projectsChanged', 'params': {'projects': self.projects(), 'cwd': self.settings()['cwd']}})

    def seq(self):
        return self.one('SELECT COALESCE(MAX(seq),0) AS n FROM events')['n']

    def publish(self, value):
        with self.changed:
            self.db.execute('INSERT INTO events(value) VALUES (?)', (encode(value),))
            if not self.transaction_depth:
                self.db.commit()
            # Bound replay storage; item history remains durable.
            if self.seq() % 2000 == 0:
                self.db.execute('DELETE FROM events WHERE seq < ?', (self.seq() - 20000,))
                if not self.transaction_depth:
                    self.db.commit()
            self.changed.notify_all()

    def session(self, token, touch=False):
        if not token or not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
            return None
        with self.lock:
            now = time.time()
            row = self.one('SELECT * FROM sessions WHERE token=? AND expires>? AND last_seen>?',
                           (hashlib.sha256(token.encode()).hexdigest(), now, now - SESSION_IDLE_SECONDS))
            if row and touch and (now - row['last_seen'] >= SESSION_RENEW_SECONDS
                                  or row['expires'] < now + SESSION_SECONDS - SESSION_RENEW_SECONDS):
                row.update(last_seen=now, expires=now + SESSION_SECONDS, renewed=True)
                self.write('UPDATE sessions SET last_seen=?,expires=? WHERE token=?',
                           (row['last_seen'], row['expires'], row['token']))
            return row

    def new_session(self):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self.lock:
            now = time.time()
            self.write('DELETE FROM sessions WHERE expires<=? OR last_seen<=?',
                       (now, now - SESSION_IDLE_SECONDS))
            self.write('INSERT INTO sessions(token,csrf,expires,last_seen) VALUES (?,?,?,?)',
                       (hashlib.sha256(token.encode()).hexdigest(), csrf, now + SESSION_SECONDS, now))
            return token, csrf

    def auth_buckets(self, ip, scope='login'):
        # One administrator: the shared bucket prevents switching IPs or account names to bypass a lock.
        return [scope, scope + ':ip:' + hashlib.sha256(ip.encode()).hexdigest()]

    def lock_status(self, ip, scope='login'):
        now = time.time()
        until = 0
        remaining = LOGIN_FAILURE_LIMIT
        with self.lock:
            for bucket in self.auth_buckets(ip, scope):
                row = self.one('SELECT * FROM auth_limits WHERE bucket=?', (bucket,))
                if not row:
                    continue
                if row['locked_until'] and row['locked_until'] <= now:
                    self.write('DELETE FROM auth_limits WHERE bucket=?', (bucket,))
                    continue
                until = max(until, row['locked_until'])
                remaining = min(remaining, LOGIN_FAILURE_LIMIT - row['failures'])
        return {'retryAfter': max(0, math.ceil(until - now)),
                'lockedUntil': until, 'remainingAttempts': max(0, remaining)}

    def check_auth_lock(self, ip, scope='login'):
        status = self.lock_status(ip, scope)
        if status['retryAfter']:
            action = '登录' if scope == 'login' else '密码修改'
            raise ApiError(action + '已锁定，请在倒计时结束后重试', 423, **status)

    def auth_failure(self, ip, scope='login'):
        with self.lock:
            now = time.time()
            for bucket in self.auth_buckets(ip, scope):
                row = self.one('SELECT failures FROM auth_limits WHERE bucket=?', (bucket,))
                failures = (row['failures'] if row else 0) + 1
                until = now + LOGIN_LOCK_SECONDS if failures >= LOGIN_FAILURE_LIMIT else 0
                self.write('''INSERT INTO auth_limits VALUES (?,?,?,?) ON CONFLICT(bucket)
                  DO UPDATE SET failures=excluded.failures,locked_until=excluded.locked_until,
                    updated=excluded.updated''', (bucket, failures, until, now))
            self.write("DELETE FROM auth_limits WHERE bucket LIKE '%:ip:%' AND updated<? AND locked_until<?",
                       (now - 86400, now))
            status = self.lock_status(ip, scope)
            if status['retryAfter']:
                action = '登录' if scope == 'login' else '密码修改'
                raise ApiError('密码错误已达 6 次，' + action + '锁定 6 分钟', 423, **status)
            message = '账号或密码错误' if scope == 'login' else '当前密码错误'
            raise ApiError(message + f"，还可尝试 {status['remainingAttempts']} 次",
                           401 if scope == 'login' else 403, **status)

    def auth_success(self, ip, scope='login'):
        # The single administrator successfully authenticated: reset all sources in this scope.
        self.write('DELETE FROM auth_limits WHERE bucket=? OR bucket LIKE ?',
                   (scope, scope + ':ip:%'))

    def thread(self, tid):
        row = self.one('SELECT * FROM threads WHERE id=?', (tid,))
        if not row:
            raise ApiError('会话不存在', 404)
        return row

    def item(self, tid, item):
        self.write('''INSERT INTO items(thread_id,item_id,value) VALUES (?,?,?)
          ON CONFLICT(thread_id,item_id) DO UPDATE SET value=excluded.value''',
                   (tid, item['id'], encode(item)))


class CodexBridge:
    def __init__(self, store):
        self.store = store
        self.proc = None
        self.start_lock = threading.RLock()
        self.write_lock = threading.Lock()
        self.pending_lock = threading.RLock()
        self.futures = {}
        self.requests = {}
        self.loaded = set()
        self.counter = 0
        self.generation = 0
        self.pending_images = {}
        self.pending_messages = {}

    def start(self):
        with self.start_lock:
            if self.proc and self.proc.poll() is None:
                return
            env = dict(os.environ)
            for k in ['CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CODEX_REMOTE_PAYLOAD']:
                env.pop(k, None)
            try:
                self.proc = subprocess.Popen([os.environ.get('CODEX_WEB_CODEX_BIN', 'codex'), 'app-server', '--stdio'], cwd=str(ROOT),
                    env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, bufsize=1, start_new_session=True)
            except OSError as e:
                raise ApiError('无法启动 Codex，请确认服务器已安装 Codex', 503) from e
            self.generation += 1
            generation = self.generation
            self.loaded.clear()
            self.requests.clear()
            self.pending_images.clear()
            self.pending_messages.clear()
            threading.Thread(target=self.read, args=(self.proc, generation), daemon=True).start()
            threading.Thread(target=self.drain, args=(self.proc,), daemon=True).start()
            self.call('initialize', {'clientInfo': {'name': 'jiacodex_web', 'title': 'Codex Web',
                      'version': '1.0.0'}, 'capabilities': {'experimentalApi': True}}, start=False)
            self.send({'method': 'initialized'})

    def drain(self, proc):
        # Keep diagnostics server-side; never echo raw configuration or credentials to browsers.
        for _ in proc.stderr:
            pass

    def send(self, obj):
        with self.write_lock:
            if not self.proc or self.proc.poll() is not None:
                raise ApiError('Codex 连接已断开，请重新发送', 503)
            self.proc.stdin.write(encode(obj) + '\n')
            self.proc.stdin.flush()

    def call(self, method, params, start=True):
        if start:
            self.start()
        q = queue.Queue()
        with self.pending_lock:
            self.counter += 1
            rid = self.counter
            self.futures[rid] = q
        try:
            self.send({'id': rid, 'method': method, 'params': params})
            try:
                response = q.get(timeout=45)
            except queue.Empty:
                raise ApiError('Codex 响应超时，请稍后重试', 504)
            if 'error' in response:
                msg = response['error'].get('message', 'Codex 请求失败')
                raise ApiError(msg[:2000], 502)
            return response.get('result', {})
        finally:
            with self.pending_lock:
                self.futures.pop(rid, None)

    def read(self, proc, generation):
        try:
            for line in proc.stdout:
                try:
                    obj = json.loads(line)
                    if 'id' in obj and 'method' not in obj:
                        with self.pending_lock:
                            future = self.futures.get(obj['id'])
                        if future:
                            future.put(obj)
                    elif 'id' in obj:
                        params = obj.get('params', {})
                        tid = params.get('threadId')
                        if not tid or not self.store.one('SELECT id FROM threads WHERE id=?', (tid,)):
                            self.send({'id': obj['id'], 'error': {'code': -32601, 'message': 'Unsupported request'}})
                            continue
                        with self.pending_lock:
                            self.requests[str(obj['id'])] = obj
                        self.store.write("UPDATE threads SET status='waiting' WHERE id=?", (tid,))
                        self.store.publish({'method': 'web/request', 'params': obj})
                    else:
                        self.notification(obj)
                except Exception:
                    LOG.exception('Codex event processing failed')
        finally:
            if generation == self.generation:
                with self.pending_lock:
                    for q in self.futures.values():
                        q.put({'error': {'message': 'Codex 服务已断开'}})
                    self.requests.clear()
                self.loaded.clear()
                self.pending_images.clear()
                self.pending_messages.clear()
                with self.store.transaction():
                    for row in self.store.all('SELECT id,thread_id FROM turns WHERE completed IS NULL'):
                        self.store.finish_turn(row['thread_id'], row['id'], 'interrupted', time.time())
                    self.store.write("UPDATE threads SET status='interrupted',turn_id=NULL WHERE status IN ('running','waiting')")
                    self.store.publish({'method': 'web/disconnected', 'params': {}})

    def notification(self, obj):
        method, p = obj.get('method', ''), obj.get('params', {})
        tid = p.get('threadId')
        if not tid or not self.store.one('SELECT id FROM threads WHERE id=?', (tid,)):
            return
        now = time.time()
        p['webTimestamp'] = now
        with self.store.transaction():
            if method == 'turn/started':
                self.store.write('INSERT OR IGNORE INTO turns(id,thread_id,started,status) VALUES (?,?,?,?)',
                                 (p['turn']['id'], tid, now, 'running'))
                self.store.write("UPDATE threads SET status='running',turn_id=?,updated=? WHERE id=?",
                                 (p['turn']['id'], now, tid))
            elif method == 'turn/completed':
                self.store.finish_turn(tid, p['turn']['id'], p['turn'].get('status', 'completed'), now)
                self.store.write('UPDATE threads SET status=?,turn_id=NULL,updated=? WHERE id=?',
                                 (p['turn'].get('status', 'completed'), now, tid))
                with self.pending_lock:
                    self.requests = {k: v for k, v in self.requests.items()
                                     if v.get('params', {}).get('threadId') != tid}
            elif method in ('item/started', 'item/completed'):
                item = p['item']
                previous = self.store.one('SELECT value FROM items WHERE thread_id=? AND item_id=?',
                                          (tid, item['id']))
                old = json.loads(previous['value']) if previous else {}
                if item.get('type') == 'userMessage':
                    message = self.pending_messages.get(tid)
                    if message:
                        item['content'] = self.store.user_content(message['text'], message['attachments'])
                        item['webAttachments'] = True
                    elif old.get('webAttachments'):
                        item['content'] = old['content']
                        item['webAttachments'] = True
                    else:
                        old_images = [part for part in old.get('content', []) if part.get('attachmentId')]
                        self.store.browser_user_item(item, old_images or self.pending_images.get(tid, []))
                    if method == 'item/completed':
                        self.pending_images.pop(tid, None)
                        self.pending_messages.pop(tid, None)
                item['webTurnId'] = p.get('turnId') or old.get('webTurnId') or self.store.thread(tid)['turn_id']
                item['webTiming'] = dict(old.get('webTiming', {'startedAt': now}))
                # Final snapshots may omit the summaries already streamed to the browser.
                if item['type'] == 'reasoning' and not item.get('summary') and old.get('summary'):
                    item['summary'] = old['summary']
                if method == 'item/completed' and not item['webTiming'].get('completedAt'):
                    item['webTiming']['completedAt'] = now
                    item['webTiming']['durationMs'] = round(max(0, now - item['webTiming']['startedAt']) * 1000)
                    if item['type'] == 'reasoning':
                        item['webTiming']['measurement'] = ('observed' if previous and reasoning_duration_available(item)
                                                             else 'unavailable')
                    if (item['type'] == 'reasoning' and previous
                            and item['webTiming']['measurement'] == 'observed'
                            and not old.get('webTiming', {}).get('completedAt')):
                        self.store.write('UPDATE turns SET reasoning_ms=reasoning_ms+? WHERE id=? AND thread_id=?',
                                         (item['webTiming']['durationMs'], item['webTurnId'], tid))
                self.store.item(tid, item)
            elif method.endswith(('/delta', 'Delta')) and p.get('itemId'):
                row = self.store.one('SELECT value FROM items WHERE thread_id=? AND item_id=?',
                                     (tid, p['itemId']))
                if row:
                    item = json.loads(row['value'])
                    if 'reasoning' in method:
                        if p.get('delta') and item.get('webTiming'):
                            item['webTiming']['streamed'] = True
                        if 'summaryTextDelta' in method:
                            index = max(0, int(p.get('summaryIndex', 0)))
                            summary = item.setdefault('summary', [])
                            while len(summary) <= index:
                                summary.append('')
                            summary[index] += p.get('delta', '')
                    else:
                        field = 'aggregatedOutput' if 'commandExecution' in method else 'text'
                        item[field] = (item.get(field) or '') + p.get('delta', '')
                    self.store.item(tid, item)
            turn_id = p.get('turnId') or (p.get('turn') or {}).get('id') or self.store.thread(tid)['turn_id']
            if turn_id:
                row = self.store.one('SELECT * FROM turns WHERE id=? AND thread_id=?', (turn_id, tid))
                if row:
                    p['webTurn'] = {'id': row['id'], 'startedAt': row['started'], 'completedAt': row['completed'],
                                    'status': row['status'], 'reasoningMs': row['reasoning_ms']}
            self.store.publish(obj)

    def ensure_loaded(self, tid):
        self.start()
        if tid not in self.loaded:
            row = self.store.thread(tid)
            self.call('thread/resume', {'threadId': tid, 'excludeTurns': True,
                        'cwd': row['cwd'], 'approvalPolicy': self.store.settings()['approvalPolicy'],
                        'sandbox': self.store.settings()['sandbox']})
            self.loaded.add(tid)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            os.killpg(self.proc.pid, signal.SIGTERM)


class App:
    def __init__(self, data=DATA):
        self.store = Store(data)
        self.bridge = CodexBridge(self.store)
        self.attempts = {}
        self.rate_lock = threading.Lock()
        self.turn_lock = threading.Lock()
        self.static_assets = {}

    def check_rate(self, ip):
        with self.rate_lock:
            now = time.time()
            self.attempts = {k: [t for t in v if t > now - 900]
                             for k, v in self.attempts.items() if v and v[-1] > now - 900}
            attempts = self.attempts.setdefault(ip, [])
            if len(attempts) >= 10:
                raise ApiError('尝试次数过多，请在 15 分钟后重试', 429)
            attempts.append(now)


class ThreadingHTTPServer(BaseThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 64

    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(64)
        super().__init__(*args, **kwargs)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(15)
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return connection, address

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'CodexWeb'
    sys_version = ''

    @property
    def app(self):
        return self.server.app

    def log_message(self, fmt, *args):
        # Request paths can carry tokens. Log only method and status, never bodies/cookies.
        LOG.info('%s %s', getattr(self, 'command', ''), args[1] if len(args) > 1 else '')

    def headers_common(self, cache='no-store', cookie=None):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        self.send_header('Cache-Control', cache)
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        if cookie is None:
            cookie = getattr(self, 'renew_cookie', None)
        if cookie is not None:
            secure = '; Secure' if os.environ.get('CODEX_WEB_SECURE_COOKIE') == '1' else ''
            self.send_header('Set-Cookie', f'codex_web={cookie}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_SECONDS if cookie else 0}{secure}')

    def check_request_source(self):
        hosts = self.headers.get_all('Host', [])
        if len(hosts) != 1:
            raise ApiError('请求主机不正确', 403)
        try:
            authority = urlparse('//' + hosts[0])
            host = authority.hostname
            port = authority.port or (443 if os.environ.get('CODEX_WEB_SECURE_COOKIE') == '1' else 80)
            if authority.username or authority.password or authority.path or authority.query or authority.fragment:
                raise ValueError()
        except ValueError:
            raise ApiError('请求主机不正确', 403)
        allowed = {'localhost', '127.0.0.1', '::1', self.connection.getsockname()[0]}
        extra_hosts = {h.strip().lower() for h in os.environ.get('CODEX_WEB_ALLOWED_HOSTS', '').split(',') if h.strip()}
        allowed.update(extra_hosts)
        if host not in allowed or (port != self.server.server_port and host not in extra_hosts):
            raise ApiError('请求主机不正确', 403)
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            raise ApiError('拒绝跨站请求', 403)
        origin = self.headers.get('Origin')
        if origin:
            expected_scheme = 'https' if os.environ.get('CODEX_WEB_SECURE_COOKIE') == '1' else 'http'
            if origin != expected_scheme + '://' + hosts[0]:
                raise ApiError('请求来源不正确', 403)

    def api_error(self, error):
        self.close_connection = True
        self.json({'error': str(error), **error.details}, error.status)

    def json(self, value, status=200, cookie=None):
        body = encode(value).encode()
        compressed = len(body) >= 4096 and self.accepts_gzip()
        if compressed:
            body = gzip.compress(body, compresslevel=1)
        self.send_response(status)
        self.headers_common(cookie=cookie)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Vary', 'Accept-Encoding')
        if compressed:
            self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(body)))
        if status in (423, 429) and isinstance(value, dict) and value.get('retryAfter'):
            self.send_header('Retry-After', str(value['retryAfter']))
        if self.close_connection:
            self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def accepts_gzip(self):
        return bool(re.search(r'(?:^|,)\s*gzip\s*(?:;\s*q=(?!0(?:\.0*)?(?:\s*,|\s*$))[^,]+)?\s*(?:,|$)',
                              self.headers.get('Accept-Encoding', '')))

    def thread_snapshot(self, tid, limit=None, before=None):
        store = self.app.store
        # Capture a consistent snapshot, then encode/send after releasing the DB lock.
        with store.lock:
            thread = store.thread(tid)
            if limit is None:
                rows = store.all('SELECT seq,value FROM items WHERE thread_id=? ORDER BY seq', (tid,))
                more = False
            else:
                rows = store.all('SELECT seq,value FROM items WHERE thread_id=?' + (' AND seq<?' if before else '')
                                 + ' ORDER BY seq DESC LIMIT ?', (tid, before, limit + 1) if before else (tid, limit + 1))
                more = len(rows) > limit
                rows = list(reversed(rows[:limit]))
            with self.app.bridge.pending_lock:
                requests = [v for v in self.app.bridge.requests.values() if v['params'].get('threadId') == tid]
            data = {'thread': thread, 'requests': requests, 'turns': store.turns(tid),
                    'serverTime': time.time(), 'seq': store.seq(), 'hasMore': more,
                    'before': rows[0]['seq'] if more and rows else None}
            data['changePaths'] = [row['path'] for row in store.all(
                "SELECT DISTINCT json_extract(change.value,'$.path') AS path FROM items, "
                "json_each(items.value,'$.changes') AS change WHERE items.thread_id=? "
                "AND json_extract(items.value,'$.type')='fileChange'", (tid,)) if row['path']]
        data['items'] = [json.loads(row['value']) for row in rows]
        return data

    def workspace_data(self, session):
        store = self.app.store
        return {'username': store.one('SELECT username FROM account')['username'],
                'csrf': session['csrf'], 'settings': store.settings(), 'projects': store.projects(),
                'threads': store.all('SELECT * FROM threads WHERE archived=0 ORDER BY updated DESC'), 'seq': store.seq()}

    def token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            return cookie['codex_web'].value if 'codex_web' in cookie else ''
        except Exception:
            return ''

    def auth(self, mutate=False):
        session = self.app.store.session(self.token())
        if not session:
            raise ApiError('请先登录', 401)
        if mutate and not hmac.compare_digest(self.headers.get('X-CSRF-Token', '').encode(), session['csrf'].encode()):
            raise ApiError('请求验证失败，请刷新页面', 403)
        session = self.app.store.session(self.token(), touch=True)
        if not session:
            raise ApiError('请先登录', 401)
        if session.get('renewed'):
            self.renew_cookie = self.token()
        return session

    def body(self):
        try:
            if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
                raise ApiError('请求格式不正确')
            size = int(self.headers.get('Content-Length', '0'))
            if size < 0 or size > 256000:
                raise ApiError('请求内容过大', 413)
            if 'application/json' not in self.headers.get('Content-Type', ''):
                raise ApiError('请求格式不正确', 415)
            value = json.loads(self.rfile.read(size))
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except (ValueError, UnicodeDecodeError):
            raise ApiError('请求格式不正确')

    def do_GET(self):
        self.renew_cookie = None
        try:
            self.check_request_source()
            self.get()
        except ApiError as e:
            self.api_error(e)
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            self.close_connection = True
            pass
        except Exception:
            LOG.exception('GET failed')
            self.json({'error': '服务暂时不可用'}, 500)

    def get(self):
        path = urlparse(self.path).path
        store = self.app.store
        if path == '/api/status':
            self.json({'setupRequired': not bool(store.one('SELECT id FROM account')),
                       **store.lock_status(self.client_address[0])})
            return
        if path == '/api/bootstrap':
            session = store.session(self.token(), touch=True)
            if not session:
                self.json({'authenticated': False, 'setupRequired': not bool(store.one('SELECT id FROM account')),
                           **store.lock_status(self.client_address[0])})
            else:
                self.renew_cookie = self.token()
                data = self.workspace_data(session)
                tid = parse_qs(urlparse(self.path).query).get('thread', [''])[0]
                if not tid and data['threads']:
                    tid = data['threads'][0]['id']
                if re.fullmatch(r'[\w-]+', tid) and store.one('SELECT id FROM threads WHERE id=? AND archived=0', (tid,)):
                    data['conversation'] = self.thread_snapshot(tid, limit=80)
                # Connect the stream before this cursor; a newer snapshot ignores older replay events.
                self.json({'authenticated': True, **data})
            return
        if not path.startswith('/api/'):
            names = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/favicon.svg': 'favicon.svg',
                     '/image-upload-worker.js': 'image-upload-worker.js'}
            name = names.get(path)
            if not name:
                raise ApiError('页面不存在', 404)
            asset = STATIC / name
            stamp = asset.stat().st_mtime_ns
            cached = self.app.static_assets.get(name)
            if not cached or cached[0] != stamp:
                original = asset.read_bytes()
                cached = (stamp, original, gzip.compress(original), 'W/"' + hashlib.sha256(original).hexdigest()[:24] + '"')
                self.app.static_assets[name] = cached
            etag = cached[3]
            cache = 'no-store' if name == 'index.html' else 'no-cache'
            if name != 'index.html' and etag in self.headers.get('If-None-Match', '').split(', '):
                self.send_response(304)
                self.headers_common(cache)
                self.send_header('ETag', etag)
                self.send_header('Vary', 'Accept-Encoding')
                self.end_headers()
                return
            compressed = self.accepts_gzip()
            body = cached[2] if compressed else cached[1]
            if name == 'index.html':
                # Paint the saved theme before bootstrap or the deferred JS arrives.
                theme = store.settings().get('theme', 'light')
                if theme not in ('light', 'dark', 'system'):
                    theme = 'light'
                original = cached[1].replace(b'data-theme="light"', ('data-theme="' + theme + '"').encode(), 1)
                etag = 'W/"' + hashlib.sha256(original).hexdigest()[:24] + '"'
                body = gzip.compress(original) if compressed else original
            self.send_response(200)
            self.headers_common(cache)
            self.send_header('ETag', etag)
            self.send_header('Vary', 'Accept-Encoding')
            if compressed:
                self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Type', {'html': 'text/html; charset=utf-8', 'js': 'text/javascript; charset=utf-8',
                            'css': 'text/css; charset=utf-8', 'svg': 'image/svg+xml'}[name.rsplit('.', 1)[1]])
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        session = self.auth()
        if path == '/api/me':
            self.json(self.workspace_data(session))
        elif path == '/api/projects':
            self.json({'projects': store.projects(), 'cwd': store.settings()['cwd']})
        elif path == '/api/directories':
            query = parse_qs(urlparse(self.path).query)
            directory = project_directory(query.get('path', [store.settings()['cwd']])[0])
            try:
                entries = sorted((child for child in directory.iterdir() if not child.name.startswith('.') and child.is_dir()),
                                 key=lambda child: child.name.casefold())
            except PermissionError:
                raise ApiError('没有权限浏览此文件夹', 403)
            except OSError:
                raise ApiError('无法读取此文件夹')
            self.json({'path': str(directory), 'parent': str(directory.parent) if directory.parent != directory else None,
                       'directories': [{'name': child.name, 'path': str(child)} for child in entries[:500]],
                       'truncated': len(entries) > 500})
        elif path == '/api/models':
            self.json(self.app.bridge.call('model/list', {'limit': 100}))
        elif re.fullmatch(r'/api/attachments/[a-f0-9]{32}/preview', path):
            row = store.attachment(path.split('/')[-2])
            analysis = json.loads(row['analysis'])
            self.json({'attachment': store.public_attachment(row), 'text': analysis.get('text', '')[:20000],
                       'truncated': analysis.get('truncated', False) or len(analysis.get('text', '')) > 20000,
                       'pages': [{'number': page, 'url': '/api/attachments/' + row['id'] + '/pages/' + str(page)}
                                 for page in analysis.get('scanPages', [])]})
        elif re.fullmatch(r'/api/attachments/[a-f0-9]{32}/pages/\d+', path):
            row = store.attachment(path.split('/')[-3])
            body = store.attachment_page(row, int(path.rsplit('/', 1)[-1]))
            self.send_response(200)
            self.headers_common()
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif re.fullmatch(r'/api/attachments/[a-f0-9]{32}', path):
            row = store.attachment(path.rsplit('/', 1)[-1])
            body = store.attachment_bytes(row)
            self.send_response(200)
            self.headers_common()
            self.send_header('Content-Type', row['mime'])
            disposition = 'inline' if row['kind'] == 'image' else 'attachment'
            self.send_header('Content-Disposition', disposition + '; filename="' + row['filename'] + '"; filename*=UTF-8\'\'' + quote(row['name']))
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == '/api/threads':
            self.json({'threads': store.all('SELECT * FROM threads WHERE archived=0 ORDER BY updated DESC')})
        elif re.fullmatch(r'/api/threads/[\w-]+/changes', path):
            tid = path.split('/')[-2]
            store.thread(tid)
            rows = store.all("SELECT value FROM items WHERE thread_id=? AND json_extract(value,'$.type')='fileChange' ORDER BY seq", (tid,))
            self.json({'changes': [change for row in rows for change in json.loads(row['value']).get('changes', [])]})
        elif re.fullmatch(r'/api/threads/[\w-]+', path):
            tid = path.rsplit('/', 1)[-1]
            query = parse_qs(urlparse(self.path).query)
            try:
                limit = int(query['limit'][0]) if 'limit' in query else None
                before = int(query['before'][0]) if 'before' in query else None
                if (limit is not None and not 1 <= limit <= 200) or (before is not None and (before < 1 or limit is None)):
                    raise ValueError()
            except ValueError:
                raise ApiError('历史消息分页参数不正确')
            self.json(self.thread_snapshot(tid, limit, before))
        elif path == '/api/events':
            self.events(session)
        elif path == '/api/files':
            params = parse_qs(urlparse(self.path).query)
            row = store.thread(params.get('thread', [''])[0])
            self.json(preview_file(row['cwd'], params.get('path', [''])[0], DATA))
        else:
            raise ApiError('接口不存在', 404)

    def events(self, session):
        store = self.app.store
        query = parse_qs(urlparse(self.path).query)
        try:
            cursor = max(0, int(self.headers.get('Last-Event-ID') or query.get('after', ['0'])[0]))
        except ValueError:
            raise ApiError('事件游标不正确')
        self.send_response(200)
        self.headers_common()
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Connection', 'close')
        self.send_header('X-Accel-Buffering', 'no')
        self.end_headers()
        self.close_connection = True
        self.wfile.write(b': connected\n\n')
        self.wfile.flush()
        while store.session(self.token()):
            with store.changed:
                oldest = store.one('SELECT MIN(seq) AS n FROM events')['n'] or 0
                if cursor and cursor < oldest - 1:
                    packet = {'method': 'web/resync', 'params': {}}
                    cursor = store.seq()
                    rows = [{'seq': cursor, 'value': encode(packet)}]
                else:
                    rows = store.all('SELECT seq,value FROM events WHERE seq>? ORDER BY seq LIMIT 500', (cursor,))
                if not rows:
                    store.changed.wait(timeout=10)
            if rows:
                if not store.session(self.token()):
                    break
                for row in rows:
                    self.wfile.write(f"id: {row['seq']}\ndata: {row['value']}\n\n".encode())
                    cursor = row['seq']
            else:
                self.wfile.write(b': heartbeat\n\n')
            self.wfile.flush()
        self.wfile.write(b'event: expired\ndata: {}\n\n')
        self.wfile.flush()

    def do_POST(self):
        self.renew_cookie = None
        try:
            self.check_request_source()
            self.post()
        except ApiError as e:
            self.api_error(e)
        except (BrokenPipeError, ConnectionResetError, socket.timeout):
            self.close_connection = True
            pass
        except Exception:
            LOG.exception('POST failed')
            self.json({'error': '请求失败，请稍后重试'}, 500)

    def post(self):
        path = urlparse(self.path).path
        store, bridge = self.app.store, self.app.bridge
        if path == '/api/attachments':
            self.auth(mutate=True)
            query = parse_qs(urlparse(self.path).query)
            kind = query.get('kind', ['image'])[0]
            if kind not in ('image', 'file'):
                raise ApiError('附件类型不正确')
            if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
                raise ApiError('图片上传请求不正确')
            try:
                size = int(self.headers['Content-Length'])
            except ValueError:
                raise ApiError('图片上传请求不正确')
            if not 0 < size <= (MAX_IMAGE_BYTES if kind == 'image' else MAX_FILE_BYTES):
                raise ApiError('每张图片最大 10 MB' if kind == 'image' else '每个文件最大 25 MB', 413)
            upload_started = time.monotonic()
            data = self.rfile.read(size)
            received_at = time.monotonic()
            if len(data) != size:
                raise ApiError('图片上传不完整，请重试')
            declared = self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
            name = query.get('name', ['图片' if kind == 'image' else '文件'])[0]
            attachment = store.add_attachment(data, name, declared, kind)
            LOG.info('Attachment upload kind=%s bytes=%d receive_ms=%d process_ms=%d', kind, size,
                     round((received_at - upload_started) * 1000), round((time.monotonic() - received_at) * 1000))
            self.json({'attachment': attachment}, 201)
            return
        b = self.body()
        if path in ('/api/setup', '/api/login'):
            username, password = b.get('username', ''), b.get('password', '')
            with store.lock:
                account = store.one('SELECT * FROM account')
                if path == '/api/setup':
                    if account:
                        raise ApiError('账号已创建，请登录', 409)
                    if (not ipaddress.ip_address(self.client_address[0]).is_loopback
                            or os.environ.get('CODEX_WEB_ALLOWED_HOSTS')
                            or os.environ.get('CODEX_WEB_SECURE_COOKIE') == '1'):
                        raise ApiError('远程部署请在服务器运行 python server.py --init-admin 创建管理员', 403)
                    self.app.check_rate(self.client_address[0])
                    validate_credentials(username, password)
                    salt = secrets.token_hex(16)
                    store.write('INSERT INTO account VALUES (1,?,?,?)',
                                (username, salt, password_hash(password, salt)))
                else:
                    store.check_auth_lock(self.client_address[0])
                    if not isinstance(username, str) or not isinstance(password, str) or len(username) > 256 or len(password) > 256:
                        raise ApiError('请求格式不正确')
                    # Always hash, including unknown account names, to avoid a timing shortcut.
                    candidate = password_hash(password, account['salt'] if account else '0' * 32)
                    valid_password = hmac.compare_digest(candidate, account['hash'] if account else '0' * 64)
                    valid_username = hmac.compare_digest(username.encode(), (account['username'] if account else '').encode())
                    if not account or not (valid_username and valid_password):
                        store.auth_failure(self.client_address[0])
                    store.auth_success(self.client_address[0])
                # Rotate a session when reauthenticating from the same browser.
                if self.token():
                    store.write('DELETE FROM sessions WHERE token=?', (hashlib.sha256(self.token().encode()).hexdigest(),))
                token, csrf = store.new_session()
            self.json(self.workspace_data({'csrf': csrf}), cookie=token)
            return
        self.auth(mutate=True)
        if path == '/api/logout':
            store.write('DELETE FROM sessions WHERE token=?', (hashlib.sha256(self.token().encode()).hexdigest(),))
            self.json({'ok': True}, cookie='')
        elif re.fullmatch(r'/api/attachments/[a-f0-9]{32}/remove', path):
            with store.transaction():
                row = store.attachment(path.split('/')[-2])
                if row['thread_id']:
                    raise ApiError('已发送的图片保留在对话历史中', 409)
                store.remove_attachment_files(row)
                store.write('DELETE FROM attachments WHERE id=?', (row['id'],))
            self.json({'ok': True})
        elif path == '/api/credentials':
            current = b.get('currentPassword', '')
            if not isinstance(current, str) or len(current) > 256:
                raise ApiError('当前密码错误', 403)
            username, password = b.get('username', ''), b.get('password', '')
            validate_credentials(username, password)
            with store.lock:
                # Recheck after taking the lock: a concurrent password change revokes this session.
                self.auth(mutate=True)
                store.check_auth_lock(self.client_address[0], 'credentials')
                account = store.one('SELECT * FROM account')
                if not hmac.compare_digest(password_hash(current, account['salt']), account['hash']):
                    store.auth_failure(self.client_address[0], 'credentials')
                store.auth_success(self.client_address[0], 'credentials')
                store.auth_success(self.client_address[0])
                salt = secrets.token_hex(16)
                store.write('UPDATE account SET username=?,salt=?,hash=? WHERE id=1',
                            (username, salt, password_hash(password, salt)))
                store.write('DELETE FROM sessions')
                token, csrf = store.new_session()
            self.json({'username': username, 'csrf': csrf}, cookie=token)
        elif path == '/api/projects':
            directory = project_directory(b.get('path'))
            with store.transaction():
                existing = store.one('SELECT id FROM projects WHERE path=?', (str(directory),))
                project = store.remember_project(directory)
                settings = store.settings()
                settings['cwd'] = str(directory)
                store.write('UPDATE settings SET value=? WHERE id=1', (encode(settings),))
                store.publish_projects()
            self.json({'project': project, 'projects': store.projects(), 'settings': settings}, 200 if existing else 201)
        elif re.fullmatch(r'/api/projects/[\w-]+/(select|remove)', path):
            project_id, action = path.split('/')[-2:]
            with store.transaction():
                project = store.one('SELECT * FROM projects WHERE id=?', (project_id,))
                if not project:
                    raise ApiError('项目文件夹不在列表中', 404)
                settings = store.settings()
                if action == 'select':
                    directory = project_directory(project['path'])
                    settings['cwd'] = str(directory)
                    store.write('UPDATE projects SET last_used=? WHERE id=?', (time.time(), project_id))
                else:
                    store.write('DELETE FROM projects WHERE id=?', (project_id,))
                    if settings['cwd'] == project['path']:
                        next_project = store.one('SELECT path FROM projects ORDER BY last_used DESC,created DESC LIMIT 1')
                        settings['cwd'] = next_project['path'] if next_project else str(ROOT)
                store.write('UPDATE settings SET value=? WHERE id=1', (encode(settings),))
                store.publish_projects()
            self.json({'projects': store.projects(), 'settings': settings})
        elif path == '/api/settings':
            s = store.settings()
            for key in s:
                if key in b:
                    s[key] = b[key]
            if s['sandbox'] not in ('read-only', 'workspace-write', 'danger-full-access') or s['approvalPolicy'] not in ('on-request', 'never', 'untrusted'):
                raise ApiError('执行权限设置不正确')
            if s['theme'] not in ('light', 'dark', 'system'):
                raise ApiError('主题设置不正确')
            if s['effort'] not in ('low', 'medium', 'high', 'xhigh', 'max', 'ultra'):
                raise ApiError('思考强度不正确')
            if not isinstance(s['model'], str) or len(s['model']) > 100:
                raise ApiError('模型设置不正确')
            if not isinstance(s['cwd'], str) or '\0' in s['cwd'] or not Path(s['cwd']).is_absolute() or not Path(s['cwd']).is_dir():
                raise ApiError('项目目录必须是服务器上已存在的绝对路径')
            s['cwd'] = str(project_directory(s['cwd']))
            with store.transaction():
                store.write('UPDATE settings SET value=? WHERE id=1', (encode(s),))
                if 'cwd' in b:
                    store.remember_project(Path(s['cwd']))
                    store.publish_projects()
            self.json(s)
        elif path == '/api/threads':
            s = store.settings()
            if 'cwd' in b:
                s['cwd'] = str(project_directory(b['cwd']))
            args = {'cwd': s['cwd'], 'sandbox': s['sandbox'], 'approvalPolicy': s['approvalPolicy'],
                    'threadSource': 'codex-web', 'ephemeral': False}
            if s['model']:
                args['model'] = s['model']
            result = bridge.call('thread/start', args)
            t = result['thread']
            now = time.time()
            store.write('INSERT INTO threads(id,title,cwd,model,created,updated) VALUES (?,?,?,?,?,?)',
                        (t['id'], '新对话', t['cwd'], result['model'], now, now))
            bridge.loaded.add(t['id'])
            self.json({'thread': store.thread(t['id'])}, 201)
        elif re.fullmatch(r'/api/threads/[\w-]+/(send|interrupt|rename|archive)', path):
            tid, action = path.split('/')[-2:]
            row = store.thread(tid)
            if action == 'send':
                text = b.get('text', '')
                image_ids = b.get('attachments', [])
                if not isinstance(image_ids, list) or len(image_ids) > MAX_IMAGES or any(not isinstance(value, str) for value in image_ids) or len(set(image_ids)) != len(image_ids):
                    raise ApiError('每条消息最多添加 8 个附件，请检查附件')
                if not isinstance(text, str) or len(text) > 100000 or (not text.strip() and not image_ids):
                    raise ApiError('请输入消息或添加附件，文字最多 100000 个字符')
                with self.app.turn_lock:
                    row = store.thread(tid)
                    if row['archived']:
                        raise ApiError('会话已归档', 409)
                    if row['status'] in ('running', 'waiting'):
                        raise ApiError('请等待当前任务结束，或先停止任务', 409)
                    images = []
                    with store.transaction():
                        for image_id in image_ids:
                            image = store.attachment(image_id)
                            if image['thread_id'] not in (None, tid):
                                raise ApiError('此附件属于其他对话，请重新添加', 409)
                            store.attachment_bytes(image)
                            images.append(image)
                        for image in images:
                            store.write('UPDATE attachments SET thread_id=? WHERE id=?', (tid, image['id']))
                    try:
                        bridge.ensure_loaded(tid)
                    except Exception:
                        with store.transaction():
                            for image in images:
                                if image['thread_id'] is None:
                                    store.write('UPDATE attachments SET thread_id=NULL WHERE id=? AND thread_id=?', (image['id'], tid))
                        raise
                    s = store.settings()
                    inputs = ([{'type': 'text', 'text': text}] if text.strip() else [])
                    inputs += [{'type': 'localImage', 'path': str(store.attachment_directory / image['filename'])} for image in images if image['kind'] == 'image']
                    inputs += store.document_inputs(images)
                    public_attachments = [store.public_attachment(image) for image in images]
                    bridge.pending_images[tid] = [image for image in public_attachments if image['kind'] == 'image']
                    bridge.pending_messages[tid] = {'text': text, 'attachments': public_attachments}
                    args = {'threadId': tid, 'input': inputs,
                            'effort': s['effort'], 'approvalPolicy': s['approvalPolicy']}
                    args['sandboxPolicy'] = {'type': {'read-only': 'readOnly',
                        'workspace-write': 'workspaceWrite', 'danger-full-access': 'dangerFullAccess'}[s['sandbox']]}
                    if s['model']:
                        args['model'] = s['model']
                    request_started = time.time()
                    store.write("UPDATE threads SET status='running',updated=? WHERE id=?", (request_started, tid))
                    try:
                        result = bridge.call('turn/start', args)
                    except Exception:
                        accepted = store.one('SELECT id FROM turns WHERE thread_id=? AND started>=? ORDER BY started DESC LIMIT 1', (tid, request_started))
                        if accepted:
                            result = {'turn': {'id': accepted['id']}}
                        else:
                            with store.transaction():
                                store.write("UPDATE threads SET status='idle',turn_id=NULL WHERE id=?", (tid,))
                                for image in images:
                                    if image['thread_id'] is None:
                                        store.write('UPDATE attachments SET thread_id=NULL WHERE id=? AND thread_id=?', (image['id'], tid))
                            bridge.pending_images.pop(tid, None)
                            bridge.pending_messages.pop(tid, None)
                            raise
                    # turn/started and even turn/completed can arrive before the RPC response.
                    store.write("UPDATE threads SET turn_id=? WHERE id=? AND status IN ('running','waiting') AND turn_id IS NULL",
                                (result['turn']['id'], tid))
                    if row['title'] == '新对话':
                        title = text.strip().split('\n')[0][:35] if text.strip() else ('文件对话' if any(image['kind'] == 'file' for image in images) else '图片对话')
                        store.write('UPDATE threads SET title=? WHERE id=?', (title, tid))
                    self.json(result)
            elif action == 'interrupt':
                if row['turn_id']:
                    bridge.call('turn/interrupt', {'threadId': tid, 'turnId': row['turn_id']})
                self.json({'ok': True})
            elif action == 'rename':
                title = b.get('title', '')
                if not isinstance(title, str) or not 1 <= len(title.strip()) <= 80:
                    raise ApiError('名称需为 1–80 个字符')
                store.write('UPDATE threads SET title=? WHERE id=?', (title.strip(), tid))
                self.json({'ok': True})
            elif action == 'archive':
                if row['status'] in ('running', 'waiting'):
                    raise ApiError('请先停止正在运行的任务', 409)
                store.write('UPDATE threads SET archived=1 WHERE id=?', (tid,))
                self.json({'ok': True})
        elif path == '/api/respond':
            rid = str(b.get('id', ''))
            with bridge.pending_lock:
                request = bridge.requests.get(rid)
            if not request:
                raise ApiError('此请求已处理或已过期', 409)
            method = request['method']
            if method in ('item/commandExecution/requestApproval', 'item/fileChange/requestApproval'):
                decision = b.get('decision')
                if decision not in ('accept', 'decline', 'cancel'):
                    raise ApiError('审批结果不正确')
                result = {'decision': decision}
            elif method == 'item/tool/requestUserInput':
                answers = b.get('answers', {})
                if not isinstance(answers, dict) or any(not isinstance(v, dict) or not isinstance(v.get('answers'), list)
                   or any(not isinstance(a, str) for a in v['answers']) for v in answers.values()):
                    raise ApiError('回答格式不正确')
                result = {'answers': answers}
            elif method == 'item/permissions/requestApproval':
                result = {'permissions': request['params'].get('permissions', {}) if b.get('decision') == 'accept' else {}, 'scope': 'turn'}
            else:
                bridge.send({'id': request['id'], 'error': {'code': -32601, 'message': 'Request unsupported by browser client'}})
                result = None
            if result is not None:
                bridge.send({'id': request['id'], 'result': result})
            with bridge.pending_lock:
                bridge.requests.pop(rid, None)
            tid = request['params']['threadId']
            store.write("UPDATE threads SET status='running' WHERE id=? AND status='waiting'", (tid,))
            store.publish({'method': 'web/responded', 'params': {'threadId': tid, 'id': request['id']}})
            self.json({'ok': True})
        else:
            raise ApiError('接口不存在', 404)


def main():
    global DATA
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', type=Path, help='Literal KEY=value configuration; defaults to .env next to server.py')
    parser.add_argument('--host')
    parser.add_argument('--port', type=int)
    parser.add_argument('--init-admin', action='store_true', help='Create the administrator locally without opening HTTP')
    parser.add_argument('--check', action='store_true', help='Check runtime dependencies without opening HTTP')
    args = parser.parse_args()
    try:
        load_environment(args.env_file or ROOT / '.env', required=args.env_file is not None)
        DATA = Path(os.environ.get('CODEX_WEB_DATA', str(ROOT / 'data'))).expanduser().resolve()
        host = args.host or os.environ.get('CODEX_WEB_HOST', '127.0.0.1')
        port = args.port if args.port is not None else int(os.environ.get('CODEX_WEB_PORT', '8080'))
        if not 1 <= port <= 65535:
            raise ValueError('port must be between 1 and 65535')
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if args.check:
        executable = shutil.which(os.environ.get('CODEX_WEB_CODEX_BIN', 'codex'))
        if not executable:
            parser.exit(1, 'Codex CLI not found; install it or set CODEX_WEB_CODEX_BIN.\n')
        import pymupdf
        result = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode:
            parser.exit(1, 'Codex CLI version check failed.\n')
        print('Python %s; %s; PDF parser %s; runtime checks passed.' %
              (sys.version.split()[0], result.stdout.strip(), pymupdf.VersionBind))
        print('Model authentication/network access is checked when you send a task.')
        return
    if args.init_admin:
        database = DATA / 'web.sqlite3'
        if database.exists():
            # Inspect before Store startup recovery could interrupt a running service.
            with sqlite3.connect('file:' + quote(str(database), safe='/') + '?mode=ro', uri=True) as db:
                if db.execute('SELECT id FROM account').fetchone():
                    parser.exit(1, 'Administrator already exists; use the web settings to change credentials.\n')
        store = Store(DATA)
        try:
            if store.one('SELECT id FROM account'):
                parser.exit(1, 'Administrator already exists; use the web settings to change credentials.\n')
            username = input('Administrator username: ').strip()
            password = getpass.getpass('Password (at least 10 characters): ')
            if password != getpass.getpass('Confirm password: '):
                parser.exit(1, 'Passwords do not match.\n')
            validate_credentials(username, password)
            with store.transaction():
                salt = secrets.token_hex(16)
                store.write('INSERT INTO account VALUES (1,?,?,?)', (username, salt, password_hash(password, salt)))
            print('Administrator created. Start the service and sign in.')
        except ApiError as error:
            parser.exit(1, str(error) + '\n')
        finally:
            store.db.close()
        return
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    app = App()
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    server.app = app
    LOG.info('Codex Web listening on %s:%s', host, port)
    try:
        server.serve_forever()
    finally:
        app.bridge.stop()
        server.server_close()


if __name__ == '__main__':
    main()
