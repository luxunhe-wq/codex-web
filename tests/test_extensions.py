import json
from pathlib import Path
import unittest
from urllib.parse import quote

import test_server
from server import ApiError


class ExtensionTests(unittest.TestCase):
    setUp = test_server.WebTests.setUp
    tearDown = test_server.WebTests.tearDown
    request = test_server.WebTests.request
    setup_account = test_server.WebTests.setup_account

    def fixtures(self):
        self.cwd = self.temp.name
        self.skill_path = str(Path(self.cwd) / 'demo' / 'SKILL.md')
        self.calls = []
        self.enabled = True
        self.plugin_enabled = True
        self.plugin_id = 'demo.tools@local-market'

        def call(method, params, **kwargs):
            self.calls.append((method, params))
            if method == 'plugin/installed':
                return {'marketplaces': [{'name': 'local-market', 'path': '/private/marketplace.json', 'plugins': [
                    {'id': self.plugin_id, 'name': 'demo-tools', 'installed': True, 'enabled': self.plugin_enabled,
                     'source': {'type': 'git', 'url': 'https://private.example'},
                     'interface': {'displayName': 'Demo tools', 'shortDescription': 'Demo only'}},
                    {'id': 'not-installed', 'name': 'other', 'installed': False, 'enabled': False}]}]}
            if method == 'skills/list':
                return {'data': [{'cwd': params['cwds'][0], 'errors': [], 'skills': [
                    {'name': 'demo-skill', 'description': 'A demo skill', 'path': self.skill_path,
                     'scope': 'user', 'enabled': self.enabled,
                     'dependencies': {'tools': [{'url': 'https://private.example'}]}}]}]}
            if method == 'skills/config/write':
                self.enabled = params['enabled']
            if method == 'config/value/write':
                self.plugin_enabled = params['value']
            if method == 'turn/start':
                return {'turn': {'id': 'extension-turn'}}
            return {}
        self.app.bridge.call = call
        self.app.bridge.ensure_loaded = lambda tid: None

    def endpoint(self):
        return '/api/extensions?cwd=' + quote(self.cwd)

    def test_authentication_csrf_and_sanitized_discovery(self):
        self.fixtures()
        self.assertEqual(self.request(self.endpoint())[0], 401)
        self.assertEqual(self.request('/api/extensions/plugin', {'cwd': self.cwd, 'id': self.plugin_id, 'enabled': False})[0], 401)
        self.setup_account()
        status, data, _ = self.request(self.endpoint())
        self.assertEqual(status, 200)
        self.assertEqual(len(data['plugins']['items']), 1)
        self.assertEqual(data['skills']['items'][0]['path'], self.skill_path)
        self.assertNotIn('private.example', json.dumps(data))
        self.assertNotIn('/private/marketplace.json', json.dumps(data))
        self.assertEqual(self.request('/api/extensions/plugin', {'cwd': self.cwd, 'id': self.plugin_id, 'enabled': False}, csrf=False)[0], 403)
        self.assertFalse(any(method.endswith('/write') for method, _ in self.calls))

    def test_plugin_toggle_can_only_write_discovered_plugin_key(self):
        self.fixtures(); self.setup_account()
        self.assertEqual(self.request('/api/extensions/plugin', {'cwd': self.cwd, 'id': self.plugin_id, 'enabled': False})[0], 200)
        writes = [params for method, params in self.calls if method == 'config/value/write']
        self.assertEqual(writes, [{'keyPath': 'plugins."demo.tools@local-market".enabled', 'value': False, 'mergeStrategy': 'upsert'}])
        self.assertFalse(self.request(self.endpoint())[1]['plugins']['items'][0]['enabled'])
        for value in ['model', 'missing', None, ['bad']]:
            status = self.request('/api/extensions/plugin', {'cwd': self.cwd, 'id': value, 'enabled': True})[0]
            self.assertIn(status, [400, 404])
        self.assertEqual(self.request('/api/extensions/plugin', {'cwd': self.cwd, 'id': self.plugin_id, 'enabled': 'false'})[0], 400)
        self.assertEqual(len([params for method, params in self.calls if method == 'config/value/write']), 1)

    def test_skill_toggle_validates_path_and_persists_state(self):
        self.fixtures(); self.setup_account()
        self.assertEqual(self.request('/api/extensions/skill', {'cwd': self.cwd, 'path': self.skill_path, 'enabled': False})[0], 200)
        self.assertFalse(self.request(self.endpoint())[1]['skills']['items'][0]['enabled'])
        self.assertEqual(self.request('/api/extensions/skill', {'cwd': self.cwd, 'path': '/etc/passwd', 'enabled': True})[0], 404)
        self.assertEqual([params for method, params in self.calls if method == 'skills/config/write'], [{'path': self.skill_path, 'enabled': False}])

    def test_running_task_blocks_global_mutations(self):
        self.fixtures(); self.setup_account()
        self.seed_thread('running')
        for kind, selector in [('plugin', {'id': self.plugin_id}), ('skill', {'path': self.skill_path})]:
            self.assertEqual(self.request('/api/extensions/' + kind, {'cwd': self.cwd, 'enabled': False, **selector})[0], 409)
        self.assertFalse(any(method.endswith('/write') for method, _ in self.calls))

    def seed_thread(self, status='idle'):
        self.app.store.write('INSERT INTO threads(id,title,cwd,created,updated,status) VALUES (?,?,?,?,?,?)',
                             ('extension-thread', 'Demo', self.cwd, 1, 1, status))

    def test_native_skill_input_and_ordinary_messages(self):
        self.fixtures(); self.setup_account(); self.seed_thread()
        status = self.request('/api/threads/extension-thread/send', {'text': '$demo-skill Check the page', 'skills': [self.skill_path]})[0]
        self.assertEqual(status, 200)
        turn = next(params for method, params in self.calls if method == 'turn/start')
        self.assertIn({'type': 'skill', 'name': 'demo-skill', 'path': self.skill_path}, turn['input'])
        self.app.store.write("UPDATE threads SET status='idle'")
        self.calls.clear()
        self.assertEqual(self.request('/api/threads/extension-thread/send', {'text': 'Normal message'})[0], 200)
        self.assertFalse(any(method in ('skills/list', 'plugin/installed') for method, _ in self.calls))

    def test_stale_and_invalid_skills_do_not_start_turns(self):
        self.fixtures(); self.setup_account(); self.seed_thread()
        for skills in [['/etc/passwd'], [self.skill_path, self.skill_path], [None], 'bad']:
            status = self.request('/api/threads/extension-thread/send', {'text': 'Check', 'skills': skills})[0]
            self.assertIn(status, [400, 409])
        self.enabled = False
        self.assertEqual(self.request('/api/threads/extension-thread/send', {'text': 'Check', 'skills': [self.skill_path]})[0], 409)
        self.assertFalse(any(method == 'turn/start' for method, _ in self.calls))

    def test_unsupported_and_transient_apis_do_not_break_other_sections(self):
        self.fixtures(); self.setup_account()
        call = self.app.bridge.call
        def unsupported(method, params):
            if method == 'plugin/installed':
                raise ApiError('Method not found', 502)
            return call(method, params)
        self.app.bridge.call = unsupported
        data = self.request(self.endpoint())[1]
        self.assertFalse(data['plugins']['supported'])
        self.assertEqual(len(data['skills']['items']), 1)
        def failed(method, params):
            raise ApiError('Sensitive diagnostics should not be shown', 504)
        self.app.bridge.call = failed
        data = self.request(self.endpoint())[1]
        self.assertTrue(data['plugins']['supported'])
        self.assertNotIn('Sensitive', json.dumps(data))


if __name__ == '__main__':
    unittest.main()
