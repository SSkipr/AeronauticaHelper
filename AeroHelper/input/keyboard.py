'''
      .o.                                    ooooo   ooooo           oooo
     .888.                                   888'   888'           888
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b
   .8' 888.    d88' 88b 888""8P d88' 88b  888ooooo888  d88' 88b  888   888' 88b d88' 88b 888""8P
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
Version 4.0.3
'''

import threading
from pynput.keyboard import Key, KeyCode, Controller as KeyboardController
import time
from AeroHelper.utils.platform import IS_MACOS, IS_WINDOWS

_PYDIRECTINPUT_AVAILABLE = False
if IS_WINDOWS:
    try:
        import pydirectinput
        pydirectinput.PAUSE = 0
        pydirectinput.FAILSAFE = False
        _PYDIRECTINPUT_AVAILABLE = True
    except Exception:
        _PYDIRECTINPUT_AVAILABLE = False

_MAC_DIGIT_VK = {
    '0': 0x1D, '1': 0x12, '2': 0x13, '3': 0x14, '4': 0x15,
    '5': 0x17, '6': 0x16, '7': 0x1A, '8': 0x1C, '9': 0x19,
}

_PYNPUT_KEY_NAMES = {
    Key.shift: 'shift',
    Key.shift_l: 'shift',
    Key.shift_r: 'shift',
    Key.ctrl: 'ctrl',
    Key.ctrl_l: 'ctrl',
    Key.ctrl_r: 'ctrl',
    Key.alt: 'alt',
    Key.alt_l: 'alt',
    Key.alt_r: 'alt',
    Key.cmd: 'winleft',
    Key.cmd_l: 'winleft',
    Key.cmd_r: 'winright',
    Key.f10: 'f10',
    Key.f11: 'f11',
    Key.backspace: 'backspace',
    Key.delete: 'delete',
    Key.enter: 'enter',
    Key.space: 'space',
    Key.tab: 'tab',
    Key.esc: 'esc',
}

def _resolve_pynput_key(key):
    if IS_MACOS and isinstance(key, str) and len(key) == 1:
        vk = _MAC_DIGIT_VK.get(key)
        if vk is not None:
            return KeyCode.from_vk(vk)
    return key

_controller = None
_controller_lock = threading.Lock()

def _main_thread():
    return threading.current_thread() is threading.main_thread()

def ensure_keyboard_controller():
    global _controller
    if _controller is not None:
        return _controller
    with _controller_lock:
        if _controller is None:
            if IS_MACOS and (not _main_thread()):
                raise RuntimeError('KeyboardController must be initialized on the main thread on macOS')
            _controller = KeyboardController()
        return _controller

def _pynput_key_name(key):
    if isinstance(key, str):
        if key == ' ':
            return 'space'
        return key.lower() if len(key) == 1 else key
    mapped = _PYNPUT_KEY_NAMES.get(key)
    if mapped:
        return mapped
    name = getattr(key, 'name', None)
    if name:
        return name.lower()
    return str(key).replace('Key.', '').lower()

class Keyboard:

    def __init__(self, logger=None):
        self.logger = logger
        self._select_all_modifier = Key.cmd if IS_MACOS else Key.ctrl
        self.using_pydirectinput = False
        if _PYDIRECTINPUT_AVAILABLE:
            self.using_pydirectinput = True
            self._log('info', 'Using PyDirectInput for keyboard control')
        else:
            ensure_keyboard_controller()
            self._log('info', 'Using pynput for keyboard control')

    def _log(self, level, message):
        if self.logger:
            if level == 'debug':
                self.logger.debug(f'[KEYBOARD] {message}')
            elif level == 'info':
                self.logger.info(f'[KEYBOARD] {message}')
            elif level == 'warning':
                self.logger.warning(f'[KEYBOARD] {message}')
            elif level == 'error':
                self.logger.error(f'[KEYBOARD] {message}')

    @property
    def controller(self):
        return ensure_keyboard_controller()

    def _press_pydirectinput(self, key):
        pydirectinput.keyDown(_pynput_key_name(key))

    def _release_pydirectinput(self, key):
        pydirectinput.keyUp(_pynput_key_name(key))

    def press(self, key):
        try:
            if self.using_pydirectinput:
                self._press_pydirectinput(key)
            else:
                self.controller.press(_resolve_pynput_key(key))
        except Exception as e:
            self._log('error', f'press({key!r}) failed: {e}')

    def release(self, key):
        try:
            if self.using_pydirectinput:
                self._release_pydirectinput(key)
            else:
                self.controller.release(_resolve_pynput_key(key))
        except Exception as e:
            self._log('error', f'release({key!r}) failed: {e}')

    def release_modifiers(self):
        for key in (Key.shift_l, Key.shift_r, Key.shift, Key.ctrl_l, Key.ctrl_r, Key.alt_l, Key.alt_r, Key.cmd, Key.cmd_l, Key.cmd_r):
            self.release(key)

    def tap(self, key):
        if isinstance(key, str) and len(key) == 1 and key not in 'abcdefghijklmnopqrstuvwxyz0123456789':
            self.type_text(key, delay=0)
            return
        if isinstance(key, str) and len(key) == 1 and key in '0123456789':
            self.release_modifiers()
            time.sleep(0.02)
        self.press(key)
        time.sleep(0.05)
        self.release(key)

    def hold(self, key, duration, stop_check=None):
        self.press(key)
        try:
            if stop_check:
                elapsed = 0
                chunk = 0.3
                while elapsed < duration and (not stop_check()):
                    time.sleep(min(chunk, duration - elapsed))
                    elapsed += chunk
            else:
                time.sleep(duration)
        finally:
            self.release(key)

    def release_all(self):
        for key in ('w', 'a', 's', 'd', 'z', 'o', 'e'):
            self.release(key)
        self.release_modifiers()
        self.release(Key.f11)

    def press_z(self):
        self.tap('z')

    def press_e(self):
        self.tap('e')

    def hold_w(self, duration, stop_check=None):
        self.hold('w', duration, stop_check)

    def throttle_40_percent(self):
        self.press(Key.shift_l)
        time.sleep(0.05)
        try:
            for _ in range(40):
                self.press('w')
                self.release('w')
                time.sleep(0.05)
        finally:
            self.release(Key.shift_l)
            self.release(Key.shift_r)
            self.release(Key.shift)

    def shift_s_taps(self, count):
        self.press(Key.shift_l)
        time.sleep(0.05)
        try:
            for _ in range(count):
                self.press('s')
                self.release('s')
                time.sleep(0.05)
        finally:
            self.release(Key.shift_l)
            self.release(Key.shift_r)
            self.release(Key.shift)

    def hold_a(self, duration, stop_check=None):
        self.hold('a', duration, stop_check)

    def hold_d(self, duration, stop_check=None):
        self.hold('d', duration, stop_check)

    def hold_o(self, duration, stop_check=None):
        self.hold('o', duration, stop_check)

    def hold_z(self, duration, stop_check=None):
        self.hold('z', duration, stop_check)

    _SHIFT_SYMBOLS = {
        '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
        '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
        '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\',
        ':': ';', '"': "'", '<': ',', '>': '.', '?': '/',
        '~': '`',
    }

    def _type_char_pydirectinput(self, char):
        if char == ' ':
            pydirectinput.press('space')
            return
        if char.isupper():
            pydirectinput.keyDown('shift')
            try:
                pydirectinput.press(char.lower())
            finally:
                pydirectinput.keyUp('shift')
            return
        shifted = self._SHIFT_SYMBOLS.get(char)
        if shifted is not None:
            pydirectinput.keyDown('shift')
            try:
                pydirectinput.press(shifted)
            finally:
                pydirectinput.keyUp('shift')
            return
        key = char.lower() if char.isalpha() else char
        if key == ' ':
            key = 'space'
        pydirectinput.press(key)

    def type_text(self, text, delay=0.05):
        text = str(text or '')
        if not text:
            return
        interval = max(0.0, float(delay))
        try:
            ensure_keyboard_controller()
            for char in text:
                self.controller.type(char)
                if interval:
                    time.sleep(interval)
            return
        except Exception as e:
            self._log('warning', f'pynput type failed ({e}), using Shift-aware DirectInput')
        if not self.using_pydirectinput:
            self._log('error', 'type_text: no keyboard backend available')
            return
        for char in text:
            try:
                self._type_char_pydirectinput(char)
            except Exception as e:
                self._log('error', f'type_text char {char!r} failed: {e}')
            if interval:
                time.sleep(interval)

    def select_all(self):
        mod = self._select_all_modifier
        self.press(mod)
        time.sleep(0.03)
        self.press('a')
        time.sleep(0.03)
        self.release('a')
        self.release(mod)
        time.sleep(0.12)

    def clear_input(self, count=30):
        self.select_all()
        self.tap(Key.backspace)
        time.sleep(0.1)

    def select_all_and_type(self, text, delay=0.05):
        self.select_all()
        time.sleep(0.15)
        self.type_text(text, delay)

    def shift_f10_sequence(self):
        self.press(Key.shift_l)
        try:
            for _ in range(10):
                self.press(Key.f10)
                self.release(Key.f10)
                time.sleep(0.05)
        finally:
            self.release(Key.shift_l)
            self.release(Key.shift_r)
            self.release(Key.shift)
            time.sleep(0.02)
