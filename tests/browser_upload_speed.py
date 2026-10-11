"""Verify real upload savings, original bytes, progress and bounded concurrency."""
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

from PIL import Image, ImageDraw
from browser_support import chromium_path
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import App, Handler, ThreadingHTTPServer


def main():
    with tempfile.TemporaryDirectory(prefix='codex-upload-speed-') as directory:
        app = App(Path(directory) / 'data')
        app.bridge.call = lambda *args, **kwargs: {'data': []}
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.app = app
        threading.Thread(target=server.serve_forever, daemon=True).start()
        image = Image.effect_noise((1600, 1200), 35).convert('RGBA')
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 100, 100), fill=(0, 0, 0, 0))
        draw.rectangle((200, 200, 1100, 300), fill='white')
        draw.text((210, 220), 'UPLOAD TEST 123456789', fill='black')
        output = BytesIO(); image.save(output, format='PNG'); photo = output.getvalue()
        errors = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path=chromium_path(),
                                            args=['--no-sandbox', '--disable-dev-shm-usage'])
                page = browser.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                page.fill('#auth-username', 'speedadmin'); page.fill('#auth-password', 'isolated-upload-speed-test')
                page.fill('#auth-confirm', 'isolated-upload-speed-test'); page.click('#auth-submit')
                expect(page.locator('#workspace')).to_be_visible()
                session = page.context.new_cdp_session(page)
                session.send('Network.enable')
                session.send('Network.emulateNetworkConditions', {
                    'offline': False, 'latency': 30, 'downloadThroughput': 5 * 1024 * 1024,
                    'uploadThroughput': 512 * 1024,
                })
                started = time.perf_counter()
                page.set_input_files('#image-input', {'name': 'photo.png', 'mimeType': 'image/png', 'buffer': photo})
                expect(page.locator('.attachment-tile.ready')).to_have_count(1, timeout=30000)
                optimized_ms = round((time.perf_counter() - started) * 1000)
                optimized = app.store.all('SELECT * FROM attachments')[0]
                assert optimized['size'] < len(photo) * 0.85, (optimized['size'], len(photo))
                assert (optimized['width'], optimized['height']) == (1600, 1200)
                with Image.open(BytesIO(app.store.attachment_bytes(optimized))) as decoded:
                    assert decoded.convert('RGBA').getpixel((10, 10))[3] == 0
                page.get_by_role('button', name='移除图片 photo.png', exact=True).click()
                page.wait_for_function('state.attachments.length === 0 && activeUploads === 0')
                page.check('#original-image')
                started = time.perf_counter()
                page.set_input_files('#image-input', {'name': 'original.png', 'mimeType': 'image/png', 'buffer': photo})
                expect(page.locator('.attachment-tile.ready')).to_have_count(1, timeout=30000)
                original_ms = round((time.perf_counter() - started) * 1000)
                original = app.store.all('SELECT * FROM attachments WHERE name=?', ('original.png',))[0]
                assert app.store.attachment_bytes(original) == photo
                page.get_by_role('button', name='移除图片 original.png', exact=True).click()
                page.uncheck('#original-image')
                session.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 0,
                            'downloadThroughput': -1, 'uploadThroughput': -1})

                # A browser without workers must still upload the complete original.
                page.evaluate('window.savedWorker = window.Worker; window.Worker = undefined')
                page.set_input_files('#image-input', {'name': 'fallback.png', 'mimeType': 'image/png', 'buffer': photo})
                expect(page.locator('.attachment-tile.ready')).to_have_count(1, timeout=15000)
                fallback = app.store.one('SELECT * FROM attachments WHERE name=?', ('fallback.png',))
                assert app.store.attachment_bytes(fallback) == photo
                page.get_by_role('button', name='移除图片 fallback.png', exact=True).click()
                page.evaluate('() => { window.Worker = window.savedWorker; }')

                # Camera orientation is baked into optimized pixels, never lost.
                oriented = BytesIO(); exif = Image.Exif(); exif[0x0112] = 6
                image.convert('RGB').save(oriented, format='JPEG', quality=99, exif=exif)
                page.set_input_files('#image-input', {'name': 'camera.jpg', 'mimeType': 'image/jpeg', 'buffer': oriented.getvalue()})
                expect(page.locator('.attachment-tile.ready')).to_have_count(1, timeout=15000)
                camera = app.store.one('SELECT * FROM attachments WHERE name=?', ('camera.jpg',))
                assert camera['size'] < len(oriented.getvalue()) * 0.85
                assert (camera['width'], camera['height']) == (1200, 1600)
                page.get_by_role('button', name='移除图片 camera.jpg', exact=True).click()

                animation = BytesIO()
                image.save(animation, format='PNG', save_all=True, append_images=[image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)], duration=100, loop=0)
                page.set_input_files('#image-input', {'name': 'animated.png', 'mimeType': 'image/png', 'buffer': animation.getvalue()})
                expect(page.locator('.attachment-tile.ready')).to_have_count(1, timeout=15000)
                animated = app.store.one('SELECT * FROM attachments WHERE name=?', ('animated.png',))
                assert app.store.attachment_bytes(animated) == animation.getvalue()
                page.get_by_role('button', name='移除图片 animated.png', exact=True).click()

                # Slow server validation makes concurrency, queueing and cancellation observable.
                lock = threading.Lock(); active = 0; maximum = 0
                add = app.store.add_attachment
                def delayed(*args, **kwargs):
                    nonlocal active, maximum
                    with lock:
                        active += 1; maximum = max(maximum, active)
                    try:
                        time.sleep(0.4)
                        return add(*args, **kwargs)
                    finally:
                        with lock: active -= 1
                app.store.add_attachment = delayed
                small = (Path(__file__).parent / 'fixtures/sample.png').read_bytes()
                page.set_input_files('#image-input', [{'name': f'queue-{n}.png', 'mimeType': 'image/png', 'buffer': small} for n in range(8)])
                expect(page.locator('.attachment-caption').filter(has_text='等待上传')).to_have_count(6)
                page.get_by_role('button', name='移除图片 queue-7.png', exact=True).click()
                expect(page.locator('.attachment-tile.ready')).to_have_count(7, timeout=15000)
                assert maximum <= 2, maximum
                assert not app.store.one('SELECT id FROM attachments WHERE name=?', ('queue-7.png',))
                assert not errors, errors
                print(json.dumps({'original_bytes': len(photo), 'optimized_bytes': optimized['size'],
                                  'saved_percent': round((1-optimized['size']/len(photo))*100),
                                  'original_upload_ms': original_ms, 'optimized_upload_ms': optimized_ms,
                                  'max_concurrent_uploads': maximum}), flush=True)
                browser.close()
        finally:
            server.shutdown(); server.server_close(); app.store.db.close()


if __name__ == '__main__':
    main()
