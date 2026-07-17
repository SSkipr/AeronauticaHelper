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
Version 4.0.3
'''

import time
import random
from pynput.mouse import Button, Controller as MouseController
from AeroHelper.utils.platform import IS_WINDOWS
from AeroHelper.utils.window import get_roblox_window_center, get_roblox_window_rect
_MOUSEKEY_AVAILABLE = False
if IS_WINDOWS:
    try:
        from mousekey import MouseKey
        _MOUSEKEY_AVAILABLE = True
    except Exception:
        _MOUSEKEY_AVAILABLE = False

class Mouse:

    def __init__(self, logger=None):
        self.logger = logger
        self.using_mousekey = False
        self.controller = MouseController()
        if _MOUSEKEY_AVAILABLE:
            try:
                self.mouse = MouseKey()
                self.using_mousekey = True
                self._log('info', 'Using MouseKey for mouse control')
            except Exception as e:
                self._log('warning', f'Failed to initialize MouseKey: {e}, falling back to pynput')
                self.using_mousekey = False
        else:
            self._log('info', 'Using pynput for mouse control')

    def _log(self, level, message):
        if self.logger:
            if level == 'debug':
                self.logger.debug(f'[MOUSE] {message}')
            elif level == 'info':
                self.logger.info(f'[MOUSE] {message}')
            elif level == 'warning':
                self.logger.warning(f'[MOUSE] {message}')
            elif level == 'error':
                self.logger.error(f'[MOUSE] {message}')

    def get_roblox_window_center(self):
        center = get_roblox_window_center()
        self._log('debug', f'Roblox window center: {center}')
        return center

    def get_screen_center(self):
        return self.get_roblox_window_center()

    def _move_slightly(self, x, y, variation=3):
        offset_x = random.randint(-variation, variation)
        offset_y = random.randint(-variation, variation)
        adjusted_x = x + offset_x
        adjusted_y = y + offset_y
        self._log('debug', f'Moving slightly: ({x}, {y}) -> ({adjusted_x}, {adjusted_y}), offset=({offset_x}, {offset_y})')
        try:
            self.controller.position = (adjusted_x, adjusted_y)
            time.sleep(0.05)
        except Exception as e:
            self._log('error', f'Error moving mouse slightly: {e}')
        return (adjusted_x, adjusted_y)

    def move_to(self, x, y):
        try:
            self.controller.position = (int(x), int(y))
        except Exception as e:
            self._log('error', f'Error moving mouse: {str(e)}')

    def _click_pynput(self, x, y):
        self.controller.position = (x, y)
        time.sleep(0.1)
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        final_x, final_y = (x + offset_x, y + offset_y)
        self.controller.position = (final_x, final_y)
        time.sleep(0.05)
        self.controller.click(Button.left, 1)
        self._log('debug', f'Clicked at ({final_x}, {final_y}) using pynput')

    def click(self, x, y, smooth=True):
        try:
            x, y = (int(x), int(y))
            if x < 0 or y < 0:
                self._log('warning', f'Invalid coordinates ({x}, {y}), using pynput')
                self._click_pynput(max(0, x), max(0, y))
                return
            if self.using_mousekey:
                try:
                    self.mouse.left_click_xy_natural(
                        x,
                        y,
                        delay=0.2,
                        min_variation=2,
                        max_variation=5,
                        use_every=1,
                        sleeptime=(0.02, 0.05),
                        print_coords=False,
                        percent=90,
                    )
                    self._log('debug', f'Clicked at ({x}, {y}) using MouseKey')
                except Exception as e:
                    self._log('debug', f'MouseKey click failed ({e}); using pynput')
                    self._click_pynput(x, y)
            else:
                self._click_pynput(x, y)
        except Exception as e:
            self._log('error', f'Error clicking: {str(e)}')
            import traceback
            if self.logger:
                self.logger.error_detailed('[MOUSE] Click error', traceback.format_exc())

    def click_center(self, smooth=True):
        center = self.get_roblox_window_center()
        self._log('info', f'Clicking center of Roblox window at ({center[0]}, {center[1]})')
        self.click(center[0], center[1], smooth=smooth)

    def click_relative_to_window(self, rel_x, rel_y, smooth=True):
        window_rect = get_roblox_window_rect()
        if window_rect is None:
            self._log('warning', 'Roblox window not found, using screen center')
            center = self.get_screen_center()
            self.click(center[0], center[1], smooth=smooth)
            return
        left, top, right, bottom = window_rect
        width = right - left
        height = bottom - top
        abs_x = left + int(width * rel_x)
        abs_y = top + int(height * rel_y)
        self._log('debug', f'Clicking relative position ({rel_x}, {rel_y}) -> absolute ({abs_x}, {abs_y})')
        self.click(abs_x, abs_y, smooth=smooth)

    def hover(self, x, y, dwell=0.55):
        """Move cursor onto a target without clicking (keeps Play flyouts open)."""
        try:
            x, y = (int(x), int(y))
            self.move_to(x, y)
            time.sleep(0.12)
            offset_x = random.randint(-2, 2)
            offset_y = random.randint(-2, 2)
            self.move_to(x + offset_x, y + offset_y)
            time.sleep(max(0.15, float(dwell)))
            self.move_to(x, y)
            self._log('debug', f'Hovered at ({x}, {y}) dwell={dwell:.2f}s (no click)')
        except Exception as e:
            self._log('error', f'Error hovering: {str(e)}')

    def right_click_drag(self, start_x, start_y, end_x, end_y, duration=1.0):
        try:
            self.controller.position = (start_x, start_y)
            time.sleep(0.1)
            self.controller.press(Button.right)
            time.sleep(0.1)
            steps = max(int(duration / 0.02), 10)
            dx = (end_x - start_x) / steps
            dy = (end_y - start_y) / steps
            for i in range(steps):
                cx = int(start_x + dx * (i + 1))
                cy = int(start_y + dy * (i + 1))
                self.controller.position = (cx, cy)
                time.sleep(duration / steps)
            self.controller.release(Button.right)
            self._log('debug', f'Right-click dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})')
        except Exception as e:
            self._log('error', f'Error in right-click drag: {str(e)}')

    def get_position(self):
        try:
            return self.controller.position
        except Exception as e:
            self._log('error', f'Error getting mouse position: {e}')
            return (0, 0)
