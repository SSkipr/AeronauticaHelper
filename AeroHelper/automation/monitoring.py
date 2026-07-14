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
Version 4.0.0
'''

import time
import os
from AeroHelper.ocr.normal_ocr import NormalOCR
from AeroHelper.ocr.parser import OCRParser
from AeroHelper.utils.screenshot import capture_primary_screen, delete_screenshot
from AeroHelper.input.mouse import Mouse
from AeroHelper.input.keyboard import Keyboard
from AeroHelper.utils.window import get_roblox_window_rect
from AeroHelper.utils.platform import map_screenshot_coords_to_screen
from AeroHelper.notifications.discord import DiscordNotifier

class MonitoringMode:

    def _sleep_if_running(self, seconds):
        remaining = seconds
        while remaining > 0 and self.running:
            time.sleep(min(1, remaining))
            remaining -= 1

    def __init__(self, cycle_interval, webhook_url, logger, human_detector=None, notification_mode='all', custom_waypoint=False, include_screenshots=False, keyboard=None):
        self.cycle_interval = cycle_interval
        self.logger = logger
        self.ocr = NormalOCR(logger=logger)
        self.parser = OCRParser()
        self.mouse = Mouse(logger=logger)
        self.keyboard = keyboard if keyboard is not None else Keyboard()
        self.notifier = DiscordNotifier(webhook_url, logger=logger)
        self.previous_distance = None
        self.running = False
        self.notification_mode = notification_mode
        self.human_detector = human_detector
        self.custom_waypoint = custom_waypoint
        self.include_screenshots = include_screenshots
        self._distance_growing_count = 0

    def _detect_chat_close(self, text):
        return 'hide' in text.lower()

    def _click_chat_close(self, screenshot_path):
        try:
            boxes, text = self.ocr.extract_text(screenshot_path, return_boxes=True)
            if not boxes:
                self.logger.debug('[CHAT CLOSE] No bounding boxes found from EasyOCR')
                return
            target_texts = ['hide']
            found_boxes = []
            for box_data in boxes:
                box_text = box_data['text'].lower().strip()
                box_coords = box_data['box']
                for target in target_texts:
                    if target in box_text:
                        found_boxes.append({'box': box_coords, 'text': box_data['text'], 'confidence': box_data['confidence']})
                        break
            if not found_boxes:
                self.logger.debug("[CHAT CLOSE] 'hide' not found in OCR bounding boxes")
                return
            self.logger.info(f'[CHAT CLOSE] Found {len(found_boxes)} chat close button(s)')
            window_rect = get_roblox_window_rect()
            for i, box_data in enumerate(found_boxes):
                box_coords = box_data['box']
                if len(box_coords) < 4:
                    self.logger.warning(f"[CHAT CLOSE] Invalid bounding box format for '{box_data['text']}': {box_coords}")
                    continue
                x_coords = [point[0] for point in box_coords]
                y_coords = [point[1] for point in box_coords]
                min_x = min(x_coords)
                min_y = min(y_coords)
                offset_x = 10
                offset_y = 5
                screenshot_x = min_x + offset_x
                screenshot_y = min_y + offset_y
                self.logger.info(f"[CHAT CLOSE] Button {i + 1}/{len(found_boxes)}: '{box_data['text']}' - min=({min_x}, {min_y}), offset=({offset_x}, {offset_y}), screenshot_coords=({screenshot_x}, {screenshot_y})")
                click_x, click_y = map_screenshot_coords_to_screen(screenshot_x, screenshot_y, screenshot_path, window_rect)
                self.logger.info(f'[CHAT CLOSE] Clicking button {i + 1} at screen coordinates ({click_x}, {click_y})')
                self.mouse.click(click_x, click_y, smooth=True)
                time.sleep(0.2)
            self.logger.info(f'[CHAT CLOSE] Successfully clicked {len(found_boxes)} chat close button(s)')
        except Exception as e:
            self.logger.error(f'[CHAT CLOSE] Error clicking chat close: {str(e)}')
            import traceback
            self.logger.error_detailed(f'[CHAT CLOSE] Exception details', traceback.format_exc())

    def execute_cycle(self):
        if not self.running:
            return None
        cycle_start = time.perf_counter()
        screenshot_path = None
        screenshot_sent = False
        try:
            try:
                screenshot_path = capture_primary_screen()
            except Exception as capture_error:
                self.logger.warning(f'Primary screenshot capture failed, trying PIL fallback: {capture_error}')
                try:
                    from AeroHelper.utils.screenshot import capture_screen_pil
                    screenshot_path = capture_screen_pil()
                    self.logger.info('Successfully used PIL screenshot fallback')
                except Exception as pil_error:
                    import traceback
                    error_msg = f'Screenshot capture failed completely. Primary error: {capture_error}. PIL error: {pil_error}'
                    self.logger.error_detailed(error_msg, f'Full traceback:\n{traceback.format_exc()}')
                    return {'action': 'error', 'error': f'Screenshot capture failed: {error_msg}'}
            if not screenshot_path or not os.path.exists(screenshot_path):
                error_msg = f'Screenshot file does not exist: {screenshot_path}'
                self.logger.error_detailed(error_msg, 'Screenshot path validation failed')
                return {'action': 'error', 'error': error_msg}
            text = self.ocr.extract_text(screenshot_path)
            self.logger.log_ocr(text)
            if self.ocr.detect_return_to_lobby(text):
                self.logger.warning('Return to Lobby detected - pausing')
                return {'action': 'pause', 'reason': 'Return to Lobby detected'}
            if self.ocr.detect_disconnected(text):
                self.logger.warning('Disconnected detected - entering reconnect mode')
                return {'action': 'reconnect'}
            data = self.parser.parse(text)
            self.logger.log_parsed(data.to_dict())
            if not data.valid:
                self.logger.warning('Invalid data detected - nm/NM or knots not found')
                return {'action': 'pause', 'reason': 'Invalid game state'}
            if data.icao_code is not None and data.icao_code.upper() != 'DEST':
                self.logger.warning(f'Waypoint detected (ICAO: {data.icao_code}) - pausing to avoid distance calculation errors')
                return {'action': 'pause', 'reason': f'Waypoint detected: {data.icao_code}'}
            if self.previous_distance is not None and data.distance is not None and (data.distance > self.previous_distance):
                self._distance_growing_count += 1
                if self._distance_growing_count >= 10:
                    if self.custom_waypoint:
                        self.logger.warning('[MONITORING] Vehicle going away for 10 cycles (custom waypoint - no stop)')
                        self.notifier.send_warning('Monitoring', 'Vehicle has been moving away from destination for 10 cycles. You may be routing around land.', ping=False)
                        self._distance_growing_count = 0
                    else:
                        self.logger.warning('[MONITORING] Vehicle going away for 10 cycles - stopping')
                        self.keyboard.press_z()
                        self.notifier.send_warning('Monitoring', 'Vehicle has been moving away from destination for 10 cycles. Vehicle stopped. Please check heading and resume.', ping=True)
                        return {'action': 'pause', 'reason': 'Vehicle going away - stopped after 10 cycles'}
            else:
                self._distance_growing_count = 0
            self.mouse.click_center(smooth=True)
            self.keyboard.tap('5')
            self.keyboard.shift_f10_sequence()
            self._click_chat_close(screenshot_path)
            urgent = self._is_urgent(data)
            autosteer_enabled = False
            notification_mode = self.notification_mode.lower()
            if notification_mode in ('urgent-only', 'urgent'):
                if urgent:
                    self.logger.debug('[MONITORING] Urgent-only mode: sending urgent alert')
                    self.notifier.send_urgent_alert(data, self.previous_distance, autosteer_enabled, mode='Monitoring')
                else:
                    self.logger.debug('[MONITORING] Skipping notification (Urgent-only mode, no urgent condition)')
            else:
                self.logger.debug('[MONITORING] All mode: sending status update')
                cycle_duration = time.perf_counter() - cycle_start
                scr = screenshot_path if self.include_screenshots else None
                self.notifier.send_status_update(data, self.previous_distance, screenshot_path=scr, cycle_duration_sec=cycle_duration, mode='Monitoring')
                screenshot_sent = self.include_screenshots and screenshot_path
                if urgent:
                    self.logger.debug('[MONITORING] All mode: sending urgent alert')
                    self.notifier.send_urgent_alert(data, self.previous_distance, autosteer_enabled, mode='Monitoring')
            self.previous_distance = data.distance
            cycle_duration = time.perf_counter() - cycle_start
            self.logger.debug(f'[MONITORING] Cycle completed in {cycle_duration:.2f}s')
            if screenshot_path and screenshot_sent:
                try:
                    delete_screenshot(screenshot_path)
                except Exception as cleanup_error:
                    self.logger.warning(f'Failed to delete screenshot {screenshot_path}: {cleanup_error}')
            return {'action': 'continue', 'data': data}
        except Exception as e:
            import traceback
            error_msg = f'Error in monitoring cycle: {str(e)}'
            self.logger.error_detailed(error_msg, f'Full traceback:\n{traceback.format_exc()}')
            return {'action': 'error', 'error': str(e)}
        finally:
            if screenshot_path and (not screenshot_sent):
                try:
                    delete_screenshot(screenshot_path)
                except Exception as cleanup_error:
                    self.logger.warning(f'Failed to delete screenshot {screenshot_path}: {cleanup_error}')

    def _is_urgent(self, data):
        if data.heading is not None and data.target_bearing is not None:
            diff = abs(data.heading - data.target_bearing)
            if diff >= 5:
                return True
        if data.fuel is not None and data.fuel < 10:
            return True
        if data.throttle is not None and data.throttle == 0:
            return True
        if self.previous_distance is not None and data.distance is not None:
            if abs(data.distance - self.previous_distance) < 0.01:
                return True
        return False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
