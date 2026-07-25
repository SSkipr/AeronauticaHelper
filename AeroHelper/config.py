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
Version 4.1.0
'''

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key, unset_key
HISTORY_LIMIT = 10
AEROHELPER_ENV_BASENAME = 'AeroHelper.env'
UI_BUTTON_ENV_KEYS = {
    'Play': 'AEROHELPER_UI_PLAY',
    'Jobs': 'AEROHELPER_UI_JOBS',
}
DEPRECATED_SHARED_SECRET_KEYS = (
    'AEROHELPER_REGISTRATION_KEY',
    'AEROHELPER_DEVICE_ID',
    'AEROHELPER_DEVICE_TOKEN',
)

def app_data_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def aerohelper_env_path() -> Path:
    return app_data_dir() / AEROHELPER_ENV_BASENAME

def load_aerohelper_env_into_os(override: bool=False) -> Path:
    path = aerohelper_env_path()
    load_dotenv(path, override=override)
    return path
API_BASE = 'https://aeronautica-helper.vercel.app'

class Config:

    def __init__(self):
        self.config_dir = app_data_dir()
        self.env_path = aerohelper_env_path()
        self._ensure_env_file()
        load_aerohelper_env_into_os(override=False)
        self._scrub_deprecated_shared_secrets()

    def _ensure_env_file(self):
        legacy = self.config_dir / '.env'
        if not self.env_path.exists() and legacy.exists():
            try:
                legacy.rename(self.env_path)
            except OSError:
                pass
        if not self.env_path.exists():
            self.env_path.touch()

    def _scrub_deprecated_shared_secrets(self):
        for key in DEPRECATED_SHARED_SECRET_KEYS:
            if key not in os.environ:
                continue
            try:
                unset_key(str(self.env_path), key)
            except Exception:
                pass
            os.environ.pop(key, None)

    def get(self, key, default=None):
        return os.getenv(key, default)

    def set(self, key, value):
        if value is None:
            value = ''
        set_key(str(self.env_path), key, str(value))
        os.environ[key] = str(value)

    @staticmethod
    def _parse_xy(raw):
        if not raw:
            return None
        text = str(raw).strip().strip("'\"")
        if ',' not in text:
            return None
        left, right = text.split(',', 1)
        try:
            return (int(float(left.strip())), int(float(right.strip())))
        except (TypeError, ValueError):
            return None

    def get_ui_button_coords(self, label):
        key = UI_BUTTON_ENV_KEYS.get(label)
        if not key:
            return None
        return self._parse_xy(self.get(key))

    def set_ui_button_coords(self, label, x, y):
        key = UI_BUTTON_ENV_KEYS.get(label)
        if not key:
            return False
        self.set(key, f'{int(x)},{int(y)}')
        return True

    def clear_ui_button_coords(self, label):
        key = UI_BUTTON_ENV_KEYS.get(label)
        if not key:
            return False
        self.set(key, '')
        return True

    def get_webhook_url(self):
        return self.get('WEBHOOK_URL', '')

    def get_aeromulti_dev_webhook_url(self):
        return (self.get('AEROMULTI_DEV_WEBHOOK_URL') or self.get('WEBHOOK_URL') or '').strip()

    def get_aeromulti_public_webhook_url(self):
        return (self.get('AEROMULTI_PUBLIC_WEBHOOK_URL') or '').strip()

    def get_aeromulti_public_digest_webhook_url(self):
        return (self.get('AEROMULTI_PUBLIC_DIGEST_WEBHOOK_URL') or '').strip()

    def get_aeromulti_ingest_secret(self):
        return (self.get('AEROMULTI_INGEST_SECRET') or '').strip()

    def set_webhook_url(self, url):
        self.set('WEBHOOK_URL', url)

    def get_cycle_interval(self):
        return int(self.get('CYCLE_INTERVAL', '15'))

    def set_cycle_interval(self, interval):
        self.set('CYCLE_INTERVAL', str(interval))

    def get_multiplier(self):
        return float(self.get('MULTIPLIER', '1.0'))

    def set_multiplier(self, multiplier):
        self.set('MULTIPLIER', str(multiplier))

    def get_mode(self):
        return self.get('MODE', 'Monitoring')

    def set_mode(self, mode):
        self.set('MODE', mode)

    def get_notification_mode(self):
        return self.get('NOTIFICATION_MODE', 'all')

    def set_notification_mode(self, mode):
        self.set('NOTIFICATION_MODE', mode)

    def get_start_mid_mission(self):
        return self.get('START_MID_MISSION', 'false').lower() == 'true'

    def set_start_mid_mission(self, enabled):
        self.set('START_MID_MISSION', str(enabled).lower())

    def get_monitoring_custom_waypoint(self):
        return self.get('MONITORING_CUSTOM_WAYPOINT', 'false').lower() == 'true'

    def set_monitoring_custom_waypoint(self, enabled):
        self.set('MONITORING_CUSTOM_WAYPOINT', str(enabled).lower())

    def get_autosteer_custom_waypoint(self):
        return self.get('AUTOSTEER_CUSTOM_WAYPOINT', 'false').lower() == 'true'

    def set_autosteer_custom_waypoint(self, enabled):
        self.set('AUTOSTEER_CUSTOM_WAYPOINT', str(enabled).lower())

    def get_monitoring_skip_current_bearing(self):
        return self.get('MONITORING_SKIP_CURRENT_BEARING', 'false').lower() == 'true'

    def set_monitoring_skip_current_bearing(self, enabled):
        self.set('MONITORING_SKIP_CURRENT_BEARING', str(enabled).lower())

    def get_quit_after_5_errors(self):
        return self.get('QUIT_AFTER_5_ERRORS', 'false').lower() == 'true'

    def set_quit_after_5_errors(self, enabled):
        self.set('QUIT_AFTER_5_ERRORS', str(enabled).lower())

    def get_throttle_up_if_not_100(self):
        return self.get('THROTTLE_UP_IF_NOT_100', 'false').lower() == 'true'

    def set_throttle_up_if_not_100(self, enabled):
        self.set('THROTTLE_UP_IF_NOT_100', str(enabled).lower())

    def get_include_screenshots(self):
        return self.get('INCLUDE_SCREENSHOTS', 'false').lower() == 'true'

    def set_include_screenshots(self, enabled):
        self.set('INCLUDE_SCREENSHOTS', str(enabled).lower())

    @staticmethod
    def _parse_csv_names(raw):
        names = []
        for part in (raw or '').replace('\n', ',').replace(';', ',').split(','):
            name = part.strip().strip('"').strip("'")
            if name:
                names.append(name)
        return names

    def get_blocked_executables_text(self):
        return self.get('BLOCKED_EXECUTABLES', '')

    def set_blocked_executables_text(self, value):
        self.set('BLOCKED_EXECUTABLES', value or '')

    def get_blocked_executables(self):
        return self._parse_csv_names(self.get_blocked_executables_text())

    def get_blocked_services_text(self):
        return self.get('BLOCKED_SERVICES', '')

    def set_blocked_services_text(self, value):
        self.set('BLOCKED_SERVICES', value or '')

    def get_blocked_services(self):
        return self._parse_csv_names(self.get_blocked_services_text())

    def _trim_history(self, entries):
        if not isinstance(entries, list):
            return []
        return entries[:HISTORY_LIMIT]

    def get_history(self):
        raw = self.get('AEROHELPER_HISTORY', '[]')
        try:
            entries = json.loads(raw)
        except (TypeError, ValueError):
            entries = []
        trimmed = self._trim_history(entries)
        if trimmed != entries:
            self.set_history(trimmed)
        return trimmed

    def set_history(self, entries):
        trimmed = self._trim_history(entries)
        self.set('AEROHELPER_HISTORY', json.dumps(trimmed, separators=(',', ':')))

    def add_history_entry(self, entry):
        if not isinstance(entry, dict):
            return
        history = self.get_history()
        history.insert(0, entry)
        self.set_history(history)

    def get_consent_accepted(self):
        return self.get('AEROHELPER_CONSENT_ACCEPTED', 'false').lower() == 'true'

    def set_consent_accepted(self, enabled):
        self.set('AEROHELPER_CONSENT_ACCEPTED', str(enabled).lower())

    def get_share_data_with_developer(self):
        return self.get('SHARE_DATA_WITH_DEVELOPER', 'false').lower() == 'true'

    def set_share_data_with_developer(self, enabled):
        self.set('SHARE_DATA_WITH_DEVELOPER', str(enabled).lower())
