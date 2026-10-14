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

import time
from pynput.keyboard import Key
from AeroHelper.utils.halt import interruptible_sleep, is_halted
from AeroHelper.utils.roblox import close_roblox, launch_aeronautica
from AeroHelper.utils.window import bring_roblox_to_front, get_roblox_window_rect, is_roblox_f11_fullscreen
from AeroHelper.utils.screenshot import capture_primary_screen, delete_screenshot
from AeroHelper.utils.platform import map_screenshot_coords_to_screen
from AeroHelper.ocr.normal_ocr import NormalOCR
from AeroHelper.input.mouse import Mouse
from AeroHelper.input.keyboard import Keyboard
from AeroHelper.notifications.discord import DiscordNotifier

class ReconnectHandler:

    def __init__(self, webhook_url, logger, human_detector=None, include_screenshots=False, keyboard=None):
        self.webhook_url = webhook_url
        self.logger = logger
        self.ocr = NormalOCR(logger=logger)
        self.mouse = Mouse(logger=logger)
        self.keyboard = keyboard if keyboard is not None else Keyboard()
        self.notifier = DiscordNotifier(webhook_url, logger=logger)
        self.human_detector = human_detector
        self.include_screenshots = include_screenshots

    def _stopped(self, stop_check):
        return stop_check is not None and stop_check()

    def _sleep(self, seconds, stop_check=None):
        remaining = float(seconds)
        while remaining > 0:
            if self._stopped(stop_check) or is_halted():
                return False
            step = remaining if stop_check is None else min(0.25, remaining)
            if not interruptible_sleep(step):
                return False
            remaining -= step
        return not self._stopped(stop_check) and not is_halted()

    def _reconnect_notify(self, stage, message):
        path = None
        try:
            path = capture_primary_screen()
        except Exception as e:
            self.logger.warning(f'[RECONNECT] Could not capture reconnect screenshot: {e}')
        try:
            self.notifier.send_reconnect_update(stage, message, screenshot_path=path)
        finally:
            if path:
                delete_screenshot(path)

    def _find_text_on_screen(self, text_to_find):
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            ocr_text = self.ocr.extract_text(screenshot_path)
            text_lower = ocr_text.lower()
            search_lower = text_to_find.lower()
            return search_lower in text_lower
        except Exception:
            return False
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _click_single_match(self, target, stop_check=None, screenshot_path=None):
        cx, cy = target['center']
        if screenshot_path:
            cx, cy = map_screenshot_coords_to_screen(cx, cy, screenshot_path, get_roblox_window_rect())
        self.mouse.click(cx, cy, smooth=True)
        if not self._sleep(1, stop_check):
            return False
        self.mouse.click(cx, cy, smooth=True)
        return self._sleep(1, stop_check)

    def _is_reconnect_button_text(self, text):
        normalized = text.strip().lower().rstrip('.:')
        return normalized == 'reconnect'

    def _try_optional_reconnect(self, max_retries=1, wait_between=20, stop_check=None):
        for attempt in range(max_retries):
            if self._stopped(stop_check):
                return False
            if max_retries > 1:
                self.logger.info(
                    f"[RECONNECT] Looking for optional Reconnect "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
            screenshot_path = None
            try:
                screenshot_path = capture_primary_screen()
                if self._stopped(stop_check):
                    return False
                matches = self.ocr.find_text_boxes(screenshot_path, 'Reconnect', match_mode='exact')
                if not matches:
                    matches = self.ocr.find_text_boxes(screenshot_path, 'Reconnect', match_mode='word')
                matches = [m for m in matches if self._is_reconnect_button_text(m.get('text', ''))]
                if matches:
                    target = max(matches, key=lambda m: m.get('confidence', 0))
                    self.logger.info(
                        f"[RECONNECT] Clicking optional Reconnect at {target['center']} "
                        f"(text='{target.get('text', '?')}', conf={target.get('confidence', 0):.2f})"
                    )
                    clicked = self._click_single_match(target, stop_check, screenshot_path=screenshot_path)
                    if clicked:
                        self.logger.info('[RECONNECT] Optional Reconnect clicked')
                    return clicked
                self.logger.info('[RECONNECT] Optional Reconnect button not found')
            except Exception as e:
                self.logger.error(f'Error clicking optional Reconnect: {e}')
            finally:
                if screenshot_path:
                    delete_screenshot(screenshot_path)
            if attempt < max_retries - 1:
                if not self._sleep(wait_between, stop_check):
                    return False
        return False

    def _click_text(self, text_to_find, max_retries=3, wait_between=20, stop_check=None):
        for attempt in range(max_retries):
            if self._stopped(stop_check):
                return False
            self.logger.info(f"Attempting to click '{text_to_find}' (attempt {attempt + 1}/{max_retries})")
            screenshot_path = None
            try:
                screenshot_path = capture_primary_screen()
                matches = self.ocr.find_text_boxes(screenshot_path, text_to_find, match_mode='contains')
                if matches:
                    target = matches[0]
                    self.logger.info(f"[RECONNECT] Found '{text_to_find}' at {target['center']} (text='{target.get('text', '?')}', conf={target.get('confidence', 0):.2f})")
                    if self._click_single_match(target, stop_check, screenshot_path=screenshot_path):
                        return True
                    return False
                ocr_text = self.ocr.extract_text(screenshot_path)
                if text_to_find.lower() in ocr_text.lower():
                    self.logger.info(f"[RECONNECT] '{text_to_find}' present in OCR text but no bbox - clicking window center")
                    self.mouse.click_center(smooth=True)
                    if not self._sleep(1, stop_check):
                        return False
                    self.mouse.click_center(smooth=True)
                    if not self._sleep(1, stop_check):
                        return False
                    return True
            except Exception as e:
                self.logger.error(f'Error clicking text: {e}')
            finally:
                if screenshot_path:
                    delete_screenshot(screenshot_path)
            if attempt < max_retries - 1:
                if not self._sleep(wait_between, stop_check):
                    return False
        return False

    def _ocr_screen_text(self, stop_check=None):
        screenshot_path = None
        try:
            if self._stopped(stop_check):
                return ''
            screenshot_path = capture_primary_screen()
            if not screenshot_path:
                return ''
            return self.ocr.extract_text(screenshot_path) or ''
        except Exception as e:
            self.logger.warning(f'[RECONNECT] OCR failed: {e}')
            return ''
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _mission_already_active(self, stop_check=None):
        text = self._ocr_screen_text(stop_check)
        return bool(text) and self.ocr.detect_active_mission(text)

    def _is_offline_text(self, text):
        return bool(text) and self.ocr.detect_offline(text)

    def _wait_while_offline(self, stop_check=None):
        notified = False
        while not self._stopped(stop_check):
            text = self._ocr_screen_text(stop_check)
            if self.ocr.detect_active_mission(text):
                return 'active'
            if not self._is_offline_text(text):
                return 'ready'
            if not notified:
                self._reconnect_notify('WAIT', 'Game offline — waiting')
                notified = True
            self.logger.info('[RECONNECT] Offline detected - waiting instead of quitting')
            if not self._sleep(15, stop_check):
                return 'stopped'
        return 'stopped'

    def _run_close_launch_join(self, stop_check=None):
        if self._mission_already_active(stop_check):
            self.logger.info('[RECONNECT] Mission HUD already visible - treating as success')
            self._reconnect_notify('7', 'Already in mission')
            return 'success'
        offline_state = self._wait_while_offline(stop_check)
        if offline_state == 'stopped':
            return 'stopped'
        if offline_state == 'active':
            self._reconnect_notify('7', 'Already in mission')
            return 'success'
        self.logger.info('[RECONNECT] Starting reconnection procedure')
        self._reconnect_notify('1', 'Closing Roblox')
        self.logger.info('[RECONNECT] Closing Roblox application')
        close_roblox()
        self.logger.info('[RECONNECT] Waiting 10 seconds after closing Roblox')
        if not self._sleep(10, stop_check):
            return 'stopped'
        self.logger.info('[RECONNECT] Launching Aeronautica via Roblox API (Place ID: 6647962258)')
        self._reconnect_notify('2', 'Launching Aeronautica')
        if not launch_aeronautica():
            self.logger.error('[RECONNECT] Failed to launch Aeronautica')
            self._reconnect_notify('ERROR', 'Failed to launch Aeronautica')
            text = self._ocr_screen_text(stop_check)
            if self._is_offline_text(text):
                return 'offline'
            return 'error'
        self.logger.info('[RECONNECT] Waiting 30 seconds for game to launch')
        if not self._sleep(30, stop_check):
            return 'stopped'
        needs_f11 = not is_roblox_f11_fullscreen()
        if bring_roblox_to_front():
            self.logger.info('[RECONNECT] Brought Roblox window to front')
            if not self._sleep(0.3, stop_check):
                return 'stopped'
            if needs_f11:
                self.logger.info('[RECONNECT] Roblox not F11 fullscreen, pressing F11')
                self.keyboard.press(Key.f11)
                self.keyboard.release(Key.f11)
                if not self._sleep(0.5, stop_check):
                    return 'stopped'
            else:
                self.logger.info('[RECONNECT] Roblox already F11 fullscreen')
        else:
            self.logger.warning('[RECONNECT] Failed to bring Roblox window to front')
        if self._mission_already_active(stop_check):
            self.logger.info('[RECONNECT] Mission HUD visible after launch - treating as success')
            self._reconnect_notify('7', 'Already in mission')
            return 'success'
        self.logger.info(
            '[RECONNECT] Looking for optional Reconnect button '
            '(max 3 retries, 20s between attempts)'
        )
        self._reconnect_notify('2b', 'Looking for optional Reconnect button')
        if self._try_optional_reconnect(max_retries=3, wait_between=20, stop_check=stop_check):
            self.logger.info('[RECONNECT] Optional Reconnect clicked - waiting 15s before Join')
            if not self._sleep(15, stop_check):
                return 'stopped'
        else:
            if self._stopped(stop_check):
                return 'stopped'
            self.logger.info('[RECONNECT] Optional Reconnect not found; continuing to Join')
        self.logger.info('[RECONNECT] Looking for Join button (mandatory, max 3 retries, 20s between attempts)')
        self._reconnect_notify('3', 'Looking for Join button')
        joined = self._click_text('Join', max_retries=3, wait_between=20, stop_check=stop_check)
        if self._stopped(stop_check):
            return 'stopped'
        if not joined:
            if self._mission_already_active(stop_check):
                self.logger.info('[RECONNECT] Join missed but mission HUD is active - treating as success')
                self._reconnect_notify('7', 'Already in mission')
                return 'success'
            self.logger.error('[RECONNECT] Failed to click Join after 3 attempts')
            self._reconnect_notify('ERROR', 'Failed to click Join')
            return 'error'
        self.logger.info('[RECONNECT] Join clicked successfully')
        self._reconnect_notify('4', 'Join clicked - waiting for game to load')
        self.logger.info('[RECONNECT] Waiting 60 seconds for game to load')
        if not self._sleep(60, stop_check):
            return 'stopped'
        continue_flight = False
        self.logger.info("[RECONNECT] Looking for optional 'Continue Flight' button")
        self._reconnect_notify('5', 'Looking for Continue Flight button (optional)')
        if self._click_text('Continue Flight', max_retries=2, wait_between=5, stop_check=stop_check):
            continue_flight = True
            self.logger.info('[RECONNECT] Continue Flight clicked successfully')
        else:
            if self._stopped(stop_check):
                return 'stopped'
            self.logger.info('[RECONNECT] Continue Flight not found; continuing')
        self._reconnect_notify('5c', 'Looking for optional Reconnect button')
        self._try_optional_reconnect(stop_check=stop_check)
        hud = self._mission_already_active(stop_check)
        if not continue_flight and not hud:
            self.logger.error('[RECONNECT] No mission HUD or Continue Flight after Join')
            self._reconnect_notify('ERROR', 'Mission HUD not found after Join')
            return 'error'
        self._reconnect_notify('5b', 'Waiting before E+W')
        self.logger.info('[RECONNECT] Waiting 20 seconds before final actions')
        if not self._sleep(20, stop_check):
            return 'stopped'
        self.logger.info('[RECONNECT] Pressing E key')
        self._reconnect_notify('6', 'Pressing E — waiting 15s, then holding W')
        self.keyboard.press_e()
        self.logger.info('[RECONNECT] Waiting 15 seconds after E before holding W')
        if not self._sleep(15, stop_check):
            return 'stopped'
        self.logger.info('[RECONNECT] Holding W key for 10 seconds')
        self.keyboard.hold_w(10, stop_check=stop_check)
        if self._stopped(stop_check):
            return 'stopped'
        self.logger.info('[RECONNECT] Reconnection procedure completed successfully')
        self._reconnect_notify('7', 'Reconnection completed successfully')
        return 'success'

    def execute_reconnect(self, stop_check=None):
        try:
            if self._stopped(stop_check):
                return False
            failures = 0
            while failures < 3:
                if self._stopped(stop_check):
                    return False
                if failures > 0:
                    retry_n = failures + 1
                    self.logger.info(f'[RECONNECT] retry {retry_n}/3 in 3 minutes')
                    self._reconnect_notify('RETRY', f'retry {retry_n}/3 in 3 minutes')
                    if not self._sleep(180, stop_check):
                        return False
                    if self._mission_already_active(stop_check):
                        self._reconnect_notify('7', 'Already in mission')
                        return True
                result = self._run_close_launch_join(stop_check)
                if result == 'success':
                    return True
                if result == 'stopped':
                    return False
                if result == 'offline':
                    self.logger.info('[RECONNECT] Offline or launch failed - waiting without counting a failure')
                    wait_state = self._wait_while_offline(stop_check)
                    if wait_state == 'stopped':
                        return False
                    if wait_state == 'active':
                        return True
                    continue
                failures += 1
            self._reconnect_notify('ERROR', 'Reconnection failed after 3 attempts')
            return False
        except Exception as e:
            import traceback
            self.logger.error(f'[RECONNECT] Error in reconnection procedure: {str(e)}')
            self.logger.error_detailed(f'[RECONNECT] Reconnection failed', f'Full traceback:\n{traceback.format_exc()}')
            self._reconnect_notify('ERROR', f'Reconnection failed: {str(e)}')
            return False
