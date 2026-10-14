"""Narrow adapter for Codex's installed plugin and skill APIs.

Never expose full configuration or accept arbitrary configuration keys from a browser.
"""
import json


class Extensions:
    def __init__(self, bridge, error_type):
        self.bridge = bridge
        self.error_type = error_type

    def _read(self, method, params, kind):
        try:
            return self.bridge.call(method, params)
        except self.error_type as error:
            message = str(error).lower()
            if any(marker in message for marker in ('method not found', 'unknown method', 'unsupported method', 'unknown variant', 'unrecognized method')):
                raise self.error_type('当前 Codex 版本不支持此插件或技能接口，请升级 Codex', 501) from error
            raise self.error_type(kind + '暂时无法读取，请稍后刷新重试', error.status) from error

    def plugins(self, cwd):
        result = self._read('plugin/installed', {'cwds': [cwd]}, '插件列表')
        plugins = []
        for market in result.get('marketplaces', []):
            for plugin in market.get('plugins', []):
                if not plugin.get('installed'):
                    continue
                interface = plugin.get('interface') or {}
                plugins.append({'id': plugin['id'], 'name': plugin['name'],
                                'displayName': interface.get('displayName') or plugin['name'],
                                'description': interface.get('shortDescription') or '',
                                'marketplace': (market.get('interface') or {}).get('displayName') or market['name'],
                                'enabled': bool(plugin.get('enabled')),
                                'available': plugin.get('availability', 'AVAILABLE') == 'AVAILABLE',
                                'version': plugin.get('localVersion') or plugin.get('version') or '',
                                'capabilities': interface.get('capabilities') or []})
        return {'items': plugins, 'warningCount': len(result.get('marketplaceLoadErrors', []))}

    def skills(self, cwd, refresh=False):
        result = self._read('skills/list', {'cwds': [cwd], 'forceReload': refresh}, '技能列表')
        skills, warnings = {}, 0
        for entry in result.get('data', []):
            warnings += len(entry.get('errors', []))
            for skill in entry.get('skills', []):
                interface = skill.get('interface') or {}
                skills[skill['path']] = {'name': skill['name'], 'path': skill['path'],
                                        'displayName': interface.get('displayName') or skill['name'],
                                        'description': interface.get('shortDescription') or skill.get('shortDescription') or skill.get('description', ''),
                                        'enabled': bool(skill.get('enabled')), 'scope': skill.get('scope', ''),
                                        'pluginId': skill.get('pluginId'),
                                        'defaultPrompt': interface.get('defaultPrompt') or ''}
        return {'items': list(skills.values()), 'warningCount': warnings}

    def snapshot(self, cwd, refresh=False):
        data = {'cwd': cwd}
        for kind, load in [('plugins', lambda: self.plugins(cwd)), ('skills', lambda: self.skills(cwd, refresh))]:
            try:
                data[kind] = {'supported': True, **load()}
            except self.error_type as error:
                data[kind] = {'supported': error.status != 501, 'items': [], 'error': str(error)}
        return data

    def set_plugin(self, cwd, plugin_id, enabled):
        if not isinstance(plugin_id, str) or len(plugin_id) > 512 or not isinstance(enabled, bool):
            raise self.error_type('插件设置不正确')
        plugin = next((item for item in self.plugins(cwd)['items'] if item['id'] == plugin_id), None)
        if not plugin:
            raise self.error_type('插件尚未安装或已被移除，请刷新列表', 404)
        if enabled and not plugin['available']:
            raise self.error_type('此插件当前不可用，请检查 Codex 账号或管理员配置', 409)
        # Quote the complete plugin ID so dots cannot become arbitrary config paths.
        self._read('config/value/write', {'keyPath': 'plugins.' + json.dumps(plugin_id, ensure_ascii=False) + '.enabled',
                                        'value': enabled, 'mergeStrategy': 'upsert'}, '插件设置')

    def set_skill(self, cwd, path, enabled):
        if not isinstance(path, str) or len(path) > 4096 or not isinstance(enabled, bool):
            raise self.error_type('技能设置不正确')
        if not any(item['path'] == path for item in self.skills(cwd, True)['items']):
            raise self.error_type('技能不存在或已被移除，请刷新列表', 404)
        self._read('skills/config/write', {'path': path, 'enabled': enabled}, '技能设置')

    def inputs(self, cwd, paths):
        if not isinstance(paths, list) or len(paths) > 8 or any(not isinstance(path, str) for path in paths) or len(set(paths)) != len(paths):
            raise self.error_type('技能选择不正确')
        if not paths:
            return []
        visible = {item['path']: item for item in self.skills(cwd, True)['items']}
        inputs = []
        for path in paths:
            skill = visible.get(path)
            if not skill or not skill['enabled']:
                raise self.error_type('所选技能已禁用或不属于当前项目，请重新选择', 409)
            inputs.append({'type': 'skill', 'name': skill['name'], 'path': skill['path']})
        return inputs
