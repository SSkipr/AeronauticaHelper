'''
      .o.                                    ooooo   ooooo           oooo
     .888.                                   888'   888'           888
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b
   .8' 888.    d88' 88b 888""8P d88' 88b  888ooooo888  d88' 88b  888   888' 88b d88' 88b 888""8P
  .88ooo8888.   888ooo888  888     888   888  888     888  888ooo888  888   888   888 888ooo888  888
 .8'     888.  888    .o  888     888   888  888     888  888    .o  888   888   888 888    .o  888
o.oooooo..o88.oooooo..oPoooo88b    Yo8od8P' o888o   o888o Y8bod8P' o888o  888bod8P' Y8bod8P' d888b
d8P'    Y8 d8P'    Y8 888         "'                                    888
Y88bo.      Y88bo.       888  oooo  oooo  oo.ooooo.  oooo d8b              o888o
 "Y8888o.   "Y8888o.   888 .8P'   888   888' 88b 888""8P
     "Y88b      "Y88b  888888.     888   888   888  888
oo     .d8P oo     .d8P  888 `88b.   888   888   888  888
8""88888P'  8""88888P'  o888o o888o o888o  888bod8P' d888b
                                           888
                                          o888o

https://aeronautica-helper.vercel.app
https://github.com/SSkipr/AeronauticaHelper
Version 4.1.6 Beta
'''

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from copy import deepcopy

_MAX_AIRPORTS = 200
_MAX_DESTINATIONS = 50
_lock = threading.Lock()
_state_cache = {'key': None, 'state': None}
_config = None
_legacy_imported = False
# Saved copy of the server list, and the separate Dev-mode list, both in AeroHelper.env.
_ENV_SAVED_VERSION = 'ROUTES_SAVED_VERSION'
_ENV_SAVED = 'ROUTES_SAVED'
_ENV_DEV_MODE = 'ROUTES_DEV_MODE'
_ENV_DEV = 'ROUTES_DEV'


def normalize_routes(raw):
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key, meta in raw.items():
        if len(out) >= _MAX_AIRPORTS:
            break
        origin = str(key).strip()
        if not origin or not isinstance(meta, dict):
            continue
        full_name = str(meta.get('full_name') or '').strip()
        if not full_name:
            continue
        dests_raw = meta.get('destinations') or {}
        destinations = {}
        if isinstance(dests_raw, dict):
            for dest_key, dest_name in dests_raw.items():
                if len(destinations) >= _MAX_DESTINATIONS:
                    break
                cleaned_key = str(dest_key).strip()
                if isinstance(dest_name, dict):
                    cleaned_name = str(dest_name.get('full_name') or '').strip()
                else:
                    cleaned_name = str(dest_name or '').strip()
                if cleaned_key and cleaned_name:
                    destinations[cleaned_key] = cleaned_name
        if not destinations:
            continue
        dock = str(meta.get('dock') or 'none').strip() or 'none'
        exit_bearing = str(meta.get('exit') or 'none').strip() or 'none'
        try:
            cycles = max(0, int(meta.get('cycles') or 0))
        except (TypeError, ValueError):
            cycles = 0
        out[origin] = {
            'full_name': full_name,
            'destinations': destinations,
            'dock': dock,
            'exit': exit_bearing,
            'cycles': cycles,
        }
    return out


def parse_remote_routes_payload(payload):
    if not isinstance(payload, dict):
        return None
    from AeroHelper.utils.version import sanitize_remote_version
    version = sanitize_remote_version(str(payload.get('version') or ''))
    routes = normalize_routes(payload.get('routes'))
    if not version or not routes:
        return None
    return (version, routes)


def _empty_state():
    return {
        'official_version': '',
        'official_routes': None,
        'dev_mode': False,
        'custom_routes': None,
    }


def _routes_from_json(raw):
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    cleaned = normalize_routes(parsed)
    return cleaned or None


def _cfg():
    global _config, _legacy_imported
    if _config is None:
        from AeroHelper.config import Config
        _config = Config()
    if not _legacy_imported:
        _legacy_imported = True
        _import_legacy_json(_config)
    return _config


def _env_cache_key(cfg):
    return (
        cfg.get(_ENV_SAVED_VERSION) or '',
        cfg.get(_ENV_SAVED) or '',
        cfg.get(_ENV_DEV_MODE) or '',
        cfg.get(_ENV_DEV) or '',
    )


def _state_from_mapping(official_version, official_routes, dev_mode, custom_routes):
    return {
        'official_version': str(official_version or '').strip(),
        'official_routes': normalize_routes(official_routes) if isinstance(official_routes, dict) else None,
        'dev_mode': bool(dev_mode),
        'custom_routes': normalize_routes(custom_routes) if isinstance(custom_routes, dict) else None,
    }


def _store(cfg, state):
    saved = state.get('official_routes') or None
    custom = state.get('custom_routes') or None
    cfg.set(_ENV_SAVED_VERSION, state.get('official_version') or '')
    cfg.set(_ENV_SAVED, json.dumps(saved) if saved else '')
    cfg.set(_ENV_DEV_MODE, 'true' if state.get('dev_mode') else 'false')
    cfg.set(_ENV_DEV, json.dumps(custom) if custom else '')
    _state_cache['key'] = _env_cache_key(cfg)
    _state_cache['state'] = _state_from_mapping(
        state.get('official_version'),
        saved,
        state.get('dev_mode'),
        custom,
    )


def _import_legacy_json(cfg):
    from AeroHelper.config import app_data_dir
    path = app_data_dir() / 'official_routes.json'
    if not path.is_file():
        return
    already = any(cfg.get(key) for key in (_ENV_SAVED_VERSION, _ENV_SAVED, _ENV_DEV_MODE, _ENV_DEV))
    parsed = None
    if not already:
        try:
            parsed = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            parsed = None
    if isinstance(parsed, dict):
        _store(cfg, _state_from_mapping(
            parsed.get('official_version'),
            parsed.get('official_routes'),
            parsed.get('dev_mode'),
            parsed.get('custom_routes'),
        ))
    try:
        path.unlink()
    except OSError:
        pass
    tmp = path.with_suffix('.json.tmp')
    if tmp.is_file():
        try:
            tmp.unlink()
        except OSError:
            pass


def _load_state():
    cfg = _cfg()
    key = _env_cache_key(cfg)
    if _state_cache['key'] == key and _state_cache['state'] is not None:
        return _state_cache['state']
    state = _state_from_mapping(
        cfg.get(_ENV_SAVED_VERSION),
        _routes_from_json(cfg.get(_ENV_SAVED)),
        str(cfg.get(_ENV_DEV_MODE) or '').strip().lower() == 'true',
        _routes_from_json(cfg.get(_ENV_DEV)),
    )
    _state_cache['key'] = key
    _state_cache['state'] = state
    return state


def _write_state(state):
    _store(_cfg(), state)


def local_official_version():
    with _lock:
        return (_load_state().get('official_version') or '').strip()


def official_routes():
    with _lock:
        stored = _load_state().get('official_routes')
    if stored:
        return deepcopy(stored)
    return {}


def fetch_remote_routes(timeout=10):
    import json
    from urllib.request import urlopen
    from AeroHelper.config import API_BASE
    with urlopen(f'{API_BASE}/api/routes', timeout=timeout) as response:
        payload = json.loads(response.read().decode('utf-8', errors='replace'))
    parsed = parse_remote_routes_payload(payload)
    if not parsed:
        raise ValueError('The routes list from the server was empty or invalid')
    return parsed


def routes_dev_mode():
    with _lock:
        return bool(_load_state().get('dev_mode'))


def custom_routes():
    with _lock:
        stored = _load_state().get('custom_routes')
    if stored:
        return deepcopy(stored)
    return {}


def set_routes_dev_mode(enabled):
    with _lock:
        state = dict(_load_state())
        state['dev_mode'] = bool(enabled)
        _write_state(state)


def save_official_routes(version, routes):
    cleaned = normalize_routes(routes)
    if not cleaned:
        raise ValueError('Official routes payload was empty')
    from AeroHelper.utils.version import sanitize_remote_version
    safe_version = sanitize_remote_version(str(version or ''))
    if not safe_version:
        raise ValueError('Official routes version was invalid')
    with _lock:
        state = dict(_load_state())
        state['official_version'] = safe_version
        state['official_routes'] = cleaned
        _write_state(state)


def save_custom_routes(routes):
    cleaned = normalize_routes(routes)
    if not cleaned:
        raise ValueError('Custom routes were empty')
    with _lock:
        state = dict(_load_state())
        state['dev_mode'] = True
        state['custom_routes'] = cleaned
        _write_state(state)


def _active_routes():
    with _lock:
        state = _load_state()
        if state.get('dev_mode') and state.get('custom_routes'):
            return deepcopy(state['custom_routes'])
        if state.get('official_routes'):
            return deepcopy(state['official_routes'])
    return {}


def active_airports():
    airports = {}
    for key, meta in _active_routes().items():
        airports[key] = {
            'full_name': meta['full_name'],
            'destinations': dict(meta['destinations']),
        }
    return airports


def active_dock_bearings():
    docks = {}
    for key, meta in _active_routes().items():
        docks[key] = {
            'dock': meta.get('dock') or 'none',
            'exit': meta.get('exit') or 'none',
            'cycles': meta.get('cycles') or 0,
        }
    return docks


class _LiveMapping(Mapping):

    def __init__(self, loader):
        self._loader = loader

    def _data(self):
        return self._loader()

    def __getitem__(self, key):
        return self._data()[key]

    def __iter__(self):
        return iter(self._data())

    def __len__(self):
        return len(self._data())

    def get(self, key, default=None):
        return self._data().get(key, default)


SUPPORTED_AIRPORTS = _LiveMapping(active_airports)
DOCK_BEARINGS = _LiveMapping(active_dock_bearings)
