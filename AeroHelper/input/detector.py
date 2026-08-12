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
Version 4.1.2
'''

import time
from pynput import keyboard
from threading import Lock
from AeroHelper.utils.platform import IS_MACOS

class HumanInterventionDetector:

    def __init__(self, logger=None):
        self.logger = logger
        self.keyboard_listener = None
        self.intervention_detected = False
        self.lock = Lock()
        self.running = False
        self.suspended = False
        self.keyboard_event_count = 0
        self.ignored_keys = {'a', 'd', 's', 'z', 'e', 'w', '5', 'o'}
        self.ignored_key_objects = {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r, keyboard.Key.f10, keyboard.Key.f11, keyboard.Key.backspace, keyboard.Key.delete}

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

    def _on_key_press(self, key):
        self.keyboard_event_count += 1
        if not self.running or self.suspended:
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

    def _stop_listener(self):
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except Exception:
                pass
            self.keyboard_listener = None

    def _start_listener(self):
        if IS_MACOS:
            return False
        try:
            self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press, suppress=False)
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
        self.keyboard_event_count = 0
        if IS_MACOS:
            self._log('warning', 'Human-intervention pause detection is disabled on macOS (use Stop in AeroHelper to end automation). Keyboard listening via pynput is unstable on macOS and is skipped for stability.')
            return
        if self._start_listener():
            self._log('info', 'Human intervention detector started successfully (keyboard only)')
        else:
            self._log('warning', 'Human intervention detection disabled - listener could not start')

    def stop(self):
        self.running = False
        self._stop_listener()
        self._log('info', f'Human intervention detector stopped (keyboard events: {self.keyboard_event_count})')

    def ensure_listener_running(self):
        if IS_MACOS or not self.running:
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

    def reset(self):
        with self.lock:
            self.intervention_detected = False
