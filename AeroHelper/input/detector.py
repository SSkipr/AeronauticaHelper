'''
      .o.                                    ooooo   ooooo           oooo
     .888.                                   888'   888'           888
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b
   .8' 888.    d88' 88b 888""8P d88' 88b  888ooooo888  d88' 88b  888   888' 88b 888""8P
  .88ooo8888.   888ooo888  888     888   888  888     888  888ooo888  888   888   888 888ooo888  888
 .8'     888.  888    .o  888     888   888  888     888  888    .o  888   888   888 888    .o  888
o.oooooo..o88.oooooo..oPoooo88b    Yo8od8P' o888o   o888o Y8bod8P' o888o  888bod8P' Y8bod8P' d888b
d8P'    Y8 d8P'    Y8 888         "'                                    888
    10|Y88bo.      Y88bo.       888  oooo  oooo  oo.ooooo.  oooo d8b              o888o
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

import time
from pynput import keyboard
from threading import Lock
from AeroHelper.config import normalize_hotkey
from AeroHelper.utils.platform import IS_MACOS

_MOD_CTRL = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
_MOD_ALT = {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}
_MOD_SHIFT = {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}
_MOD_WIN = {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r}


def _pynput_key_token(key):
    if key in _MOD_CTRL:
        return 'ctrl'
    if key in _MOD_ALT:
        return 'alt'
    if key in _MOD_SHIFT:
        return 'shift'
    if key in _MOD_WIN:
        return 'win'
    try:
        if hasattr(key, 'char') and key.char:
            ch = key.char.lower()
            if ch.isprintable() and ch != ' ':
                return ch
    except Exception:
        pass
    name = str(key).replace('Key.', '').lower()
    if name.endswith('_l') or name.endswith('_r'):
        name = name[:-2]
    aliases = {'esc': 'esc', 'enter': 'enter', 'return': 'enter', 'space': 'space', 'tab': 'tab'}
    return aliases.get(name, name)


class HumanInterventionDetector:

    def __init__(self, logger=None):
        self.logger = logger
        self.keyboard_listener = None
        self.intervention_detected = False
        self.pause_hotkey_toggled = False
        self.lock = Lock()
        self.running = False
        self.suspended = False
        self.keyboard_event_count = 0
        self.ignored_keys = {'a', 'd', 's', 'z', 'e', 'w', '5', 'o'}
        self.ignored_key_objects = {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r, keyboard.Key.f10, keyboard.Key.f11, keyboard.Key.backspace, keyboard.Key.delete}
        self.pause_hotkey = ''
        self._held_mods = set()
        self._pause_hotkey_armed = True

    def set_pause_hotkey(self, raw):
        with self.lock:
            self.pause_hotkey = normalize_hotkey(raw)
            self._pause_hotkey_armed = True

    def _log(self, level, message):
        if self.logger:
            if level == 'debug':
                self.logger.debug(f'[HUMAN_DETECTOR] {message}')
            elif level == 'info':
                self.logger.info(f'[HUMAN_DETECTOR] {message}')
            elif level == 'warning':
                self.logger.warning(f'[HUMAN_DETECTOR] {message}')
            elif level == 'error':
                self.logger.error(f'[HUMAN_DETECTOR] {message}')

    def suspend(self):
        with self.lock:
            self.suspended = True
            self.intervention_detected = False
        self._log('info', 'Detection suspended')

    def unsuspend(self):
        with self.lock:
            self.suspended = False
            self.intervention_detected = False
        self._log('info', 'Detection resumed')

    def _current_hotkey_spec(self, key):
        token = _pynput_key_token(key)
        if token in ('ctrl', 'alt', 'shift', 'win', 'cmd'):
            return ''
        mods = []
        if 'ctrl' in self._held_mods:
            mods.append('ctrl')
        if 'alt' in self._held_mods:
            mods.append('alt')
        if 'shift' in self._held_mods:
            mods.append('shift')
        if 'win' in self._held_mods or 'cmd' in self._held_mods:
            mods.append('win')
        return '+'.join(mods + [token])

    def _is_pause_hotkey(self, key):
        spec = self.pause_hotkey
        if not spec:
            return False
        current = self._current_hotkey_spec(key)
        if current == spec:
            return True
        if spec.startswith('win+'):
            return current == 'cmd+' + spec[4:] or current == spec
        return False

    def _on_key_press(self, key):
        self.keyboard_event_count += 1
        token = _pynput_key_token(key)
        if token in ('ctrl', 'alt', 'shift', 'win', 'cmd'):
            self._held_mods.add(token)
            return
        if not self.running:
            return
        if self._is_pause_hotkey(key):
            if self._pause_hotkey_armed:
                self._pause_hotkey_armed = False
                with self.lock:
                    self.pause_hotkey_toggled = True
                self._log('info', 'Pause hotkey pressed')
            return
        if self.suspended or IS_MACOS:
            return
        if key in self.ignored_key_objects:
            self._log('debug', f'Key pressed: {key} - ignoring (automation key)')
            return
        try:
            key_name = key.char if hasattr(key, 'char') and key.char else str(key)
        except Exception:
            key_name = str(key)
        if key_name.lower() in self.ignored_keys:
            self._log('debug', f'Key pressed: {key_name} - ignoring (automation key)')
            return
        key_str = str(key).lower()
        if 'shift' in key_str or 'f10' in key_str:
            self._log('debug', f'Key pressed: {key_name} - ignoring (automation key)')
            return
        self._log('info', f'Key pressed: {key_name} - triggering intervention')
        with self.lock:
            self.intervention_detected = True

    def _on_key_release(self, key):
        token = _pynput_key_token(key)
        if token in ('ctrl', 'alt', 'shift', 'win', 'cmd'):
            self._held_mods.discard(token)
            return
        self._pause_hotkey_armed = True

    def _stop_listener(self):
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except Exception:
                pass
            self.keyboard_listener = None

    def _start_listener(self):
        try:
            self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release, suppress=False)
            self.keyboard_listener.start()
            time.sleep(0.2)
            if not self.keyboard_listener.running:
                self._log('warning', 'Keyboard listener failed to stay running')
                self._stop_listener()
                return False
            self._log('info', 'Keyboard listener running')
            return True
        except Exception as e:
            self._log('error', f'Failed to start keyboard listener: {e}')
            import traceback
            if self.logger:
                self.logger.error_detailed('Failed to start human intervention listener', traceback.format_exc())
            self._stop_listener()
            return False

    def start(self):
        self.running = True
        self.intervention_detected = False
        self.pause_hotkey_toggled = False
        self.keyboard_event_count = 0
        self._held_mods = set()
        self._pause_hotkey_armed = True
        if IS_MACOS and not self.pause_hotkey:
            self._log('warning', 'Human-intervention pause detection is disabled on macOS (use Stop in AeroHelper to end automation). Keyboard listening via pynput is unstable on macOS and is skipped for stability.')
            return
        if IS_MACOS:
            self._log('warning', 'Human-intervention pause detection is disabled on macOS; pause hotkey listener will still start.')
        if self._start_listener():
            self._log('info', 'Human intervention detector started successfully (keyboard only)')
        else:
            self._log('warning', 'Human intervention detection disabled - listener could not start')

    def stop(self):
        self.running = False
        self._stop_listener()
        self._log('info', f'Human intervention detector stopped (keyboard events: {self.keyboard_event_count})')

    def ensure_listener_running(self):
        if not self.running:
            return True
        if IS_MACOS and not self.pause_hotkey:
            return True
        listener = self.keyboard_listener
        if listener is not None and listener.running:
            return True
        self._log('warning', 'Keyboard listener stopped unexpectedly - recreating')
        self._stop_listener()
        if self._start_listener():
            self._log('info', 'Keyboard listener recreated successfully')
            return True
        self._log('error', 'Failed to recreate keyboard listener - human intervention detection disabled')
        return False

    def check_intervention(self):
        with self.lock:
            detected = self.intervention_detected
            if detected:
                self.intervention_detected = False
                self._log('info', 'Intervention flag detected and cleared')
            return detected

    def check_pause_hotkey(self):
        with self.lock:
            toggled = self.pause_hotkey_toggled
            if toggled:
                self.pause_hotkey_toggled = False
            return toggled

    def reset(self):
        with self.lock:
            self.intervention_detected = False
            self.pause_hotkey_toggled = False
