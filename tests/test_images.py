import http.client
from io import BytesIO
import json
import os
from pathlib import Path
import struct
import sys
import time
import unittest
from urllib.parse import quote
import zlib
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_server
from server import ApiError, MAX_IMAGE_BYTES, Store

FIXTURES = Path(__file__).parent / 'fixtures'


class ImageTests(unittest.TestCase):
    setUp = test_server.WebTests.setUp
    tearDown = test_server.WebTests.tearDown
    request = test_server.WebTests.request
    setup_account = test_server.WebTests.setup_account

    def upload(self, data=None, mime='image/png', name='图片.png', **headers):
        if data is None:
            data = (FIXTURES / 'sample.png').read_bytes()
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        values = {'Cookie': self.cookie, 'X-CSRF-Token': self.csrf, 'Content-Type': mime, **headers}
        connection.request('POST', '/api/attachments?name=' + quote(name), body=data, headers=values)
        response = connection.getresponse()
        result = json.loads(response.read())
        status = response.status
        connection.close()
        return status, result

    def thread(self):
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated) VALUES (?,?,?,?,?)',
                             ('image-thread', '新对话', self.temp.name, 1, 1))
        self.app.bridge.ensure_loaded = lambda tid: None

    def test_image_upload_requires_login_csrf_and_valid_raster(self):
        self.assertEqual(self.upload()[0], 401)
        self.setup_account()
        self.assertEqual(self.upload(**{'X-CSRF-Token': ''})[0], 403)
        self.assertEqual(self.upload(b'<svg onload="alert(1)"></svg>', 'image/svg+xml')[0], 415)
        self.assertEqual(self.upload(b'not an image')[0], 415)
        self.assertEqual(self.upload(mime='image/jpeg')[0], 415)
        self.assertEqual(self.upload(**{'Content-Length': str(MAX_IMAGE_BYTES + 1)})[0], 413)
        for extension, mime in [('png', 'image/png'), ('jpg', 'image/jpeg'), ('webp', 'image/webp'), ('gif', 'image/gif')]:
            status, data = self.upload((FIXTURES / ('sample.' + extension)).read_bytes(), mime, 'sample.' + extension)
            self.assertEqual(status, 201, data)
            self.assertEqual(data['attachment']['mimeType'], mime)
            self.assertEqual((data['attachment']['width'], data['attachment']['height']), (32, 24))

    def test_image_bytes_are_private_persistent_and_not_arbitrary_files(self):
        self.setup_account()
        image = self.upload(name='../<img onerror=alert(1)>.png')[1]['attachment']
        self.assertNotIn('filename', image)
        self.assertEqual(self.request(image['url'], cookie='')[0], 401)
        status, data, _ = self.request(image['url'])
        self.assertEqual(status, 200)
        self.assertEqual(data, (FIXTURES / 'sample.png').read_bytes())
        row = self.app.store.attachment(image['id'])
        file = self.app.store.attachment_directory / row['filename']
        self.assertEqual(os.stat(file).st_mode & 0o777, 0o600)
        reopened = Store(Path(self.temp.name))
        self.assertEqual(reopened.attachment_bytes(reopened.attachment(image['id'])), data)
        reopened.db.close()
        file.unlink()
        file.symlink_to('/etc/passwd')
        self.assertEqual(self.request(image['url'])[0], 404)
        self.assertEqual(self.request('/api/attachments/not-a-file')[0], 404)

    def test_decodable_images_with_trailing_camera_data_can_upload(self):
        self.setup_account()
        for extension, mime in [('jpg', 'image/jpeg'), ('png', 'image/png'),
                                ('gif', 'image/gif'), ('webp', 'image/webp')]:
            with self.subTest(extension=extension):
                original = (FIXTURES / ('sample.' + extension)).read_bytes()
                data = original + b'\0\0Camera metadata after image end\0'
                status, result = self.upload(data, mime, 'camera.' + extension)
                self.assertEqual(status, 201, result)
                self.assertEqual(self.request(result['attachment']['url'])[1], data)

    def test_progressive_jpeg_with_exif_and_trailing_data_can_upload(self):
        self.setup_account()
        output = BytesIO()
        exif = Image.Exif()
        exif[0x0112] = 6  # Common phone camera orientation tag.
        with Image.new('RGB', (1600, 1200), '#3d71a8') as photo:
            photo.save(output, format='JPEG', progressive=True, exif=exif)
        data = output.getvalue() + b'\0' * 32
        status, result = self.upload(data, 'image/jpeg', 'phone-photo.jpg')
        self.assertEqual(status, 201, result)
        self.assertEqual((result['attachment']['width'], result['attachment']['height']), (1600, 1200))

    def test_native_image_input_history_and_image_only_messages(self):
        self.setup_account()
        self.thread()
        image = self.upload()[1]['attachment']
        seen = []
        def call(method, params):
            seen.append(params)
            self.app.bridge.notification({'method': 'turn/started', 'params': {'threadId': 'image-thread', 'turn': {'id': 'image-turn'}}})
            self.app.bridge.notification({'method': 'item/started', 'params': {'threadId': 'image-thread', 'turnId': 'image-turn',
                                         'item': {'id': 'image-user', 'type': 'userMessage', 'content': params['input']}}})
            # Some versions return data URLs in the final snapshot; normalize them back to saved references.
            self.app.bridge.notification({'method': 'item/completed', 'params': {'threadId': 'image-thread', 'turnId': 'image-turn',
                                         'item': {'id': 'image-user', 'type': 'userMessage', 'content': [{'type': 'image', 'url': 'data:image/png;base64,not-stored'}]}}})
            self.app.bridge.notification({'method': 'turn/completed', 'params': {'threadId': 'image-thread', 'turn': {'id': 'image-turn', 'status': 'completed'}}})
            return {'turn': {'id': 'image-turn'}}
        self.app.bridge.call = call
        status, _, _ = self.request('/api/threads/image-thread/send', {'text': '', 'attachments': [image['id']]})
        self.assertEqual(status, 200)
        self.assertEqual(seen[0]['input'][0]['type'], 'localImage')
        self.assertEqual(Path(seen[0]['input'][0]['path']).read_bytes(), (FIXTURES / 'sample.png').read_bytes())
        history = self.request('/api/threads/image-thread')[1]
        self.assertEqual(history['items'][0]['content'][0]['url'], image['url'])
        self.assertNotIn('data:image', json.dumps(history))
        self.assertNotIn(str(self.app.store.attachment_directory), json.dumps(history))
        self.assertEqual(history['thread']['title'], '图片对话')
        self.assertEqual(self.request('/api/attachments/' + image['id'] + '/remove', {})[0], 409)

    def test_invalid_attachments_and_failed_send_can_be_removed(self):
        self.setup_account()
        self.thread()
        image = self.upload()[1]['attachment']
        for value in [['/etc/passwd'], [image['id']] * 9, [image['id']] * 2, [None], {}]:
            self.assertEqual(self.request('/api/threads/image-thread/send', {'text': 'test', 'attachments': value})[0], 400)
        self.app.bridge.call = lambda *args: (_ for _ in ()).throw(ApiError('model unavailable', 502))
        self.assertEqual(self.request('/api/threads/image-thread/send', {'text': 'test', 'attachments': [image['id']]})[0], 502)
        self.assertIsNone(self.app.store.attachment(image['id'])['thread_id'])
        self.assertEqual(self.request('/api/attachments/' + image['id'] + '/remove', {})[0], 200)
        self.assertEqual(self.request(image['url'])[0], 404)

    def test_oversized_dimensions_and_truncated_image_are_rejected(self):
        self.setup_account()
        for extension, mime in [('png', 'image/png'), ('jpg', 'image/jpeg'),
                                ('gif', 'image/gif'), ('webp', 'image/webp')]:
            with self.subTest(extension=extension):
                self.assertEqual(self.upload((FIXTURES / ('sample.' + extension)).read_bytes()[:-5], mime)[0], 400)
        # A closing marker cannot make missing JPEG pixel data valid.
        jpeg = (FIXTURES / 'sample.jpg').read_bytes()
        self.assertEqual(self.upload(jpeg[:jpeg.index(b'\xff\xda')] + b'\xff\xd9', 'image/jpeg')[0], 400)
        data = bytearray((FIXTURES / 'sample.png').read_bytes())
        data[16:24] = struct.pack('>II', 50000, 50000)
        data[29:33] = struct.pack('>I', zlib.crc32(data[12:29]))
        self.assertEqual(self.upload(bytes(data))[0], 413)

    def test_unused_upload_cleanup_preserves_sent_images(self):
        self.setup_account()
        pending = self.upload()[1]['attachment']
        sent = self.upload()[1]['attachment']
        self.app.store.write('UPDATE attachments SET created=?', (time.time() - 90000,))
        self.app.store.write('UPDATE attachments SET thread_id=? WHERE id=?', ('saved-thread', sent['id']))
        self.app.store.attachments_pruned_at = 0
        self.app.store.prune_unused_attachments()
        self.assertEqual(self.request(pending['url'])[0], 404)
        self.assertEqual(self.request(sent['url'])[0], 200)


if __name__ == '__main__':
    unittest.main()
