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
Version 4.1.4
'''

import os
import re
import time
from AeroHelper.automation.autosteer import AutoSteerMode
from AeroHelper.utils.screenshot import capture_primary_screen, delete_screenshot
from AeroHelper.utils.window import get_roblox_window_center, get_roblox_window_rect
from AeroHelper.utils.bearing import HeadingEWMA, DistanceEWMA, shortest_angle_diff_abs
from AeroHelper.utils.icao import is_junk_icao_token

_PLAY_TO_JOBS_OFFSET_X = 280
_PLAY_TO_JOBS_OFFSET_Y = 0
_TURNAROUND_YES_MAX_CLICKS = 5

DOCK_BEARINGS = {
    'Leovetsk':           {'dock': 'none',   'exit': 'none', 'cycles': 0},
    'Tierdam':            {'dock': 'none',   'exit': '230', 'cycles': 5},
    'Auchenburgh':        {'dock': 'none',   'exit': 'none', 'cycles': 0},
    'Sandris':            {'dock': 'none',   'exit': 'none', 'cycles': 0},
    'Tenang':             {'dock': 'none',   'exit': 'none', 'cycles': 0},
    'Norman':             {'dock': 'none',   'exit': 'none', 'cycles': 0},
    'Pembroke Plantation':{'dock': 'none',   'exit': 'none', 'cycles': 0},
    'Hemera Sound':       {'dock': 'none',   'exit': 'none', 'cycles': 0}
}

SUPPORTED_AIRPORTS = {
    'Leovetsk': {
        'full_name': 'Leovetsk International',
        'destinations': {
            'Auchenburgh': 'Auchenburgh Airport',
            'Tierdam': 'Tierdam Airfield'
        }
    },
    'Tierdam': {
        'full_name': 'Tierdam Airfield',
        'destinations': {
            'Leovetsk': 'Leovetsk International'
        }
    },
    'Auchenburgh': {
        'full_name': 'Auchenburgh Airport',
        'destinations': {
            'Leovetsk': 'Leovetsk International'
        }
    },
    'Sandris': {
        'full_name': 'Sandris International',
        'destinations': {
            'Tenang': 'Tenang Island Airport'
        }
    },
    'Tenang': {
        'full_name': 'Tenang Island Airport',
        'destinations': {
            'Sandris': 'Sandris International'
        }
    },
    'Norman': {
        'full_name': 'Norman  International',
        'destinations': {
            'Pembroke Plantation': 'Pembroke Plantation',
            'Hemera Sound': 'Hemera Sound Airfield'
        }
    },
    'Pembroke Plantation': {
        'full_name': 'Pembroke Plantation',
        'destinations': {
            'Norman': 'Norman International'
        }
    },
    'Hemera Sound': {
        'full_name': 'Hemera Sound Airfield',
        'destinations': {
            'Norman': 'Norman International'
        }
    }
}

_CURRENTLY_AT_AIRPORT_WORD_STOPWORDS = frozenset({'airfield', 'airport', 'international', 'regional', 'municipal', 'national', 'civil'})
PHASE1_SPAWN_MAX_RETRIES = 2

class ReconnectRequested(Exception):
    pass

class AutoPilotMode(AutoSteerMode):
    PHASE_1 = 'phase_1'
    UNDOCKING = 'undocking'
    AUTOSTEER = 'autosteer'
    DOCKING_ALIGNMENT = 'docking_alignment'
    PHASE_2 = 'phase_2'
    DOCK_ALIGNMENT_START_NM = 5
    FINAL_APPROACH_NM_PER_MULT = 0.4

    def __init__(self, cycle_interval, webhook_url, multiplier, logger, human_detector=None, start_mid_mission=False, include_screenshots=False, history_callback=None, keyboard=None, throttle_up_if_not_100=False, intelligent_steering=False):
        super().__init__(cycle_interval, webhook_url, multiplier, logger, human_detector, include_screenshots=include_screenshots, keyboard=keyboard, throttle_up_if_not_100=throttle_up_if_not_100, intelligent_steering=intelligent_steering)
        self.notification_display_mode = 'AutoPilot'
        self.requires_dest = True
        self.start_mid_mission = start_mid_mission
        self.first_loop = True
        self.current_airport = None
        self.selected_destination = None
        self.selected_destination_full = None
        self.selected_wp = None
        self.selected_money = None
        self.history_callback = history_callback
        self.search_coordinates = None
        self.mission_count = 0
        self._ui_button_coords = {}
        self._ui_config = None
        self.undocking_cycles = 0
        self.heading_ewma = HeadingEWMA(alpha=0.35)
        self.distance_ewma = DistanceEWMA(alpha=0.35)
        self._phase2_consecutive_under = 0
        self._dock_fallback_warning_sent = False
        self._approach_entry_bearing = None
        self._distance_growing_count = 0
        self._dock_throttle_50_done = False
        self._dock_throttle_30_done = False
        self._phase2_long_z_retry_consumed = False
        self._destination_detect_attempts = 0
        self._last_confirmed_icao_code = None
        self._last_confirmed_target_bearing = None
        self._pending_icao_code = None
        self._pending_icao_cycles = 0
        self._pending_bearing = None
        self._pending_bearing_cycles = 0
        if start_mid_mission:
            self.autopilot_phase = self.AUTOSTEER
        else:
            self.autopilot_phase = self.PHASE_1

    def execute_cycle(self):
        if not self.running:
            return None
        try:
            if self.autopilot_phase == self.PHASE_1:
                return self._execute_phase_1()
            elif self.autopilot_phase == self.UNDOCKING:
                return self._execute_undocking()
            elif self.autopilot_phase == self.AUTOSTEER:
                return self._execute_autosteer_cycle()
            elif self.autopilot_phase == self.DOCKING_ALIGNMENT:
                return self._execute_docking_alignment()
            elif self.autopilot_phase == self.PHASE_2:
                return self._execute_phase_2()
        except ReconnectRequested:
            return {'action': 'reconnect'}
        return None

    def _check_distance_growing(self, data, prev_distance):
        if data is None or data.distance is None or prev_distance is None:
            return None
        if data.distance > prev_distance:
            self._distance_growing_count += 1
            if self._distance_growing_count >= 10:
                self.logger.warning('[AUTOPILOT] Vehicle going away for 10 cycles - stopping')
                self.keyboard.press_z()
                self.notifier.send_warning('AutoPilot', 'Vehicle has been moving away from destination for 10 cycles. Vehicle stopped. Please check heading and resume.', ping=True)
                return {'action': 'pause', 'reason': 'Vehicle going away - stopped after 10 cycles', 'stop_automation': True}
        else:
            self._distance_growing_count = 0
        return None

    def _filter_icao_for_autopilot(self, data):
        if self.override_icao_code is not None:
            return None
        if self.autopilot_phase not in (self.AUTOSTEER, self.DOCKING_ALIGNMENT):
            return None
        current_code = (data.icao_code or '').upper().strip() if data.icao_code else ''
        if current_code and is_junk_icao_token(current_code):
            data.icao_code = None
            data.target_bearing = None
            current_code = ''
        if self._last_confirmed_icao_code and is_junk_icao_token(self._last_confirmed_icao_code):
            self._last_confirmed_icao_code = None
            self._last_confirmed_target_bearing = None
        if not current_code:
            if self._last_confirmed_icao_code and self._last_confirmed_target_bearing is not None:
                return (self._last_confirmed_icao_code, self._last_confirmed_target_bearing)
            return None
        if self._last_confirmed_icao_code is None:
            self._last_confirmed_icao_code = current_code
            self._last_confirmed_target_bearing = data.target_bearing
            return None
        last_norm = (self._last_confirmed_icao_code or '').upper().strip()
        if current_code == last_norm:
            return self._autopilot_same_code_bearing(data)
        if self._pending_icao_code != current_code:
            self._pending_icao_code = current_code
            self._pending_icao_cycles = 1
            self.logger.warning(f'[AUTOPILOT] Target code changed {last_norm} -> {current_code}. Waiting 3 cycles before accepting. Using previous: {last_norm}')
            self._notify_autopilot('Target Change', f'Target changed from {last_norm} to {current_code}. Waiting 3 cycles to confirm. Using previous target.')
            return (self._last_confirmed_icao_code, self._last_confirmed_target_bearing)
        self._pending_icao_cycles += 1
        if self._pending_icao_cycles >= 3:
            self.logger.info(f'[AUTOPILOT] Target code {current_code} confirmed after 3 cycles - accepting')
            self._last_confirmed_icao_code = current_code
            self._last_confirmed_target_bearing = data.target_bearing
            self._pending_icao_code = None
            self._pending_icao_cycles = 0
            self._pending_bearing = None
            self._pending_bearing_cycles = 0
            return None
        return (self._last_confirmed_icao_code, self._last_confirmed_target_bearing)

    def _autopilot_same_code_bearing(self, data):
        new_b = data.target_bearing
        old_b = self._last_confirmed_target_bearing
        self._pending_icao_code = None
        self._pending_icao_cycles = 0
        if old_b is None or new_b is None:
            self._pending_bearing = None
            self._pending_bearing_cycles = 0
            self._last_confirmed_target_bearing = new_b
            return None
        delta = shortest_angle_diff_abs(new_b, old_b)
        if delta <= 40:
            self._pending_bearing = None
            self._pending_bearing_cycles = 0
            self._last_confirmed_target_bearing = new_b
            return None
        if self._pending_bearing != new_b:
            self._pending_bearing = new_b
            self._pending_bearing_cycles = 1
            self.logger.warning(
                f'[AUTOPILOT] DEST jumped {old_b}° -> {new_b}°; keeping {old_b}° until confirmed'
            )
            return (self._last_confirmed_icao_code, old_b)
        self._pending_bearing_cycles += 1
        if self._pending_bearing_cycles >= 3:
            self._last_confirmed_target_bearing = new_b
            self._pending_bearing = None
            self._pending_bearing_cycles = 0
            return None
        return (self._last_confirmed_icao_code, old_b)

    def _reset_icao_filter(self):
        self._last_confirmed_icao_code = None
        self._last_confirmed_target_bearing = None
        self._pending_icao_code = None
        self._pending_icao_cycles = 0
        self._pending_bearing = None
        self._pending_bearing_cycles = 0
        self._dock_throttle_50_done = False
        self._dock_throttle_30_done = False
        self._phase2_long_z_retry_consumed = False

    def _reset_dock_throttle_flags(self):
        self._dock_throttle_50_done = False
        self._dock_throttle_30_done = False

    def _restart_docking_approach(self, reason_msg):
        self.logger.info(f'[AUTOPILOT] Restarting docking approach: {reason_msg}')
        self.override_target_bearing = None
        self.override_icao_code = None
        self.override_heading = None
        self._reset_dock_throttle_flags()
        self._phase2_consecutive_under = 0
        self._dock_fallback_warning_sent = False
        self.autopilot_phase = self.DOCKING_ALIGNMENT
        self._notify_autopilot(
            'Docking',
            'Restarting dock approach (autosteer + throttle reductions)',
            details=reason_msg,
        )
        return {'action': 'continue'}

    def _notify_autopilot(self, phase, message, details=None, ping=False, screenshot_path=None, embed_color=None):
        path = screenshot_path
        if path is None and self.include_screenshots:
            path = capture_primary_screen()
        try:
            self.notifier.send_autopilot_update(phase, message, details=details, ping=ping, screenshot_path=path if self.include_screenshots else None, embed_color=embed_color)
        finally:
            if path:
                delete_screenshot(path)

    def _dock_distance_raw_or_smoothed(self, data, distance_sm):
        if data is not None and data.distance is not None:
            return data.distance
        return distance_sm

    def _phase2_transport_prompt_visible(self, ocr_text):
        if not ocr_text or not isinstance(ocr_text, str):
            return False
        return 'transport your vehicle' in ocr_text.lower()

    def _raise_if_disconnected(self, text, context):
        if self.ocr.detect_disconnected(text):
            self.logger.warning(f'[AUTOPILOT] Disconnected detected during {context} - entering reconnect mode')
            raise ReconnectRequested()

    def _inspect_phase2_dock_ready(self):
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path:
                return {'color': 'not_found', 'path': None, 'center': None}
            text = self.ocr.extract_text(screenshot_path)
            self._raise_if_disconnected(text, 'phase 2 dock readiness check')
            has_transport = self._phase2_transport_prompt_visible(text)
            if has_transport:
                self.logger.info("[AUTOPILOT] Phase 2: 'transport your vehicle' present - treat as not ready (red branch)")
                return {'color': 'red', 'path': screenshot_path, 'center': None}
            self.logger.info("[AUTOPILOT] Phase 2: 'transport your vehicle' absent - treat as ready to end sail (white branch)")
            return {'color': 'white', 'path': screenshot_path, 'center': None}
        except ReconnectRequested:
            if screenshot_path:
                delete_screenshot(screenshot_path)
            raise
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] inspect_phase2_dock_ready error: {str(e)}')
            return {'color': 'not_found', 'path': screenshot_path, 'center': None}

    def _delete_screenshot_if_present(self, screenshot_path):
        if screenshot_path:
            delete_screenshot(screenshot_path)

    def _execute_autosteer_cycle(self):
        prev_distance = self.previous_distance
        result = super().execute_cycle()
        if result is None:
            return result
        action = result.get('action')
        if action == 'continue':
            data = result.get('data')
            pause_result = self._check_distance_growing(data, prev_distance)
            if pause_result:
                return pause_result
        if action == 'pause' and result.get('reason') == 'Return to Lobby detected':
            self.logger.info('[AUTOPILOT] Return to Lobby detected during AutoSteer - transitioning to Phase 1')
            self._distance_growing_count = 0
            self._reset_icao_filter()
            self.autopilot_phase = self.PHASE_1
            return {'action': 'continue'}
        if action == 'continue':
            data = result.get('data')
            if data:
                distance_sm = self.distance_ewma.update(data.distance)
                if data.heading is not None:
                    self.heading_ewma.update(data.heading)
            else:
                distance_sm = self.distance_ewma.value
            raw_dist = data.distance if data else None
            dock_bearing = self._get_dock_bearing()
            if distance_sm is not None and distance_sm <= 10:
                if self.selected_destination is None and self.start_mid_mission:
                    dest_key = self._try_detect_destination_mid_mission()
                    if dest_key is not None:
                        if dest_key in DOCK_BEARINGS:
                            self.selected_destination = dest_key
                            self.selected_destination_full = SUPPORTED_AIRPORTS.get(dest_key, {}).get('full_name', dest_key)
                            self.logger.info(f'[AUTOPILOT] Start Mid-Mission: Detected destination {self.selected_destination_full}')
                            self._notify_autopilot('Start Mid-Mission', f'Destination detected and supported: {self.selected_destination_full}')
                        else:
                            err = f"Destination '{dest_key}' is not supported. Supported: {list(DOCK_BEARINGS.keys())}"
                            self.logger.error(f'[AUTOPILOT] {err}')
                            self.notifier.send_error(err)
                            return {'action': 'error', 'error': err}
                    else:
                        self._destination_detect_attempts += 1
                        self.logger.warning(f'[AUTOPILOT] Could not detect destination (attempt {self._destination_detect_attempts}/3)')
                        if self._destination_detect_attempts >= 3:
                            err = "Failed to detect destination after 3 attempts. Look for 'transport to [name]' or 'transport your vehicle to [name] safely' on screen."
                            self.logger.error(f'[AUTOPILOT] {err}')
                            self.notifier.send_error(err)
                            return {'action': 'error', 'error': err}
                        return result
                    dock_bearing = self._get_dock_bearing()
            near_dock = (
                distance_sm is not None and distance_sm <= self.DOCK_ALIGNMENT_START_NM
                or raw_dist is not None and raw_dist <= self.DOCK_ALIGNMENT_START_NM
            )
            if near_dock:
                entry_bearing = None
                if data and data.target_bearing is not None:
                    entry_bearing = data.target_bearing
                elif self.heading_ewma.value is not None:
                    entry_bearing = self.heading_ewma.value
                self._approach_entry_bearing = entry_bearing
                self._reset_dock_throttle_flags()
                self._dock_fallback_warning_sent = False
                self._phase2_long_z_retry_consumed = False
                self.autopilot_phase = self.DOCKING_ALIGNMENT
                dock_nm = self.DOCK_ALIGNMENT_START_NM
                if dock_bearing is not None:
                    self.logger.info(f'[AUTOPILOT] Distance ≤ {dock_nm}nm - Dock Alignment (entry {entry_bearing}°, dock {dock_bearing}°)')
                    self._notify_autopilot('Docking', f'Dock alignment at ≤{dock_nm}nm (entry {entry_bearing}° → dock {dock_bearing}°)')
                else:
                    self.logger.info(f'[AUTOPILOT] Distance ≤ {dock_nm}nm - Dock Alignment with DEST/OCR (entry {entry_bearing}°)')
                    self._notify_autopilot('Docking', f'Dock alignment at ≤{dock_nm}nm (entry {entry_bearing}°); DEST/OCR steering (no dock table bearing)')
                return {'action': 'continue'}
        return result

    def _take_screenshot_and_ocr(self):
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return (None, '', None)
            text = self.ocr.extract_text(screenshot_path)
            self._raise_if_disconnected(text, 'AutoPilot OCR step')
            return (screenshot_path, text, None)
        except ReconnectRequested:
            if screenshot_path:
                delete_screenshot(screenshot_path)
            raise
        except Exception as e:
            if screenshot_path:
                delete_screenshot(screenshot_path)
            return (None, '', str(e))

    def _read_parsed_screen_data(self):
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return None
            text = self.ocr.extract_text(screenshot_path)
            self._raise_if_disconnected(text, 'parsed data refresh')
            return self.parser.parse(text, previous_distance=self.previous_distance)
        except ReconnectRequested:
            raise
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] read_parsed_screen_data error: {str(e)}')
            return None
        finally:
            self._delete_screenshot_if_present(screenshot_path)

    def _close_chat_ui(self):
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if screenshot_path:
                self._click_chat_close(screenshot_path)
        finally:
            self._delete_screenshot_if_present(screenshot_path)

    def _screen_center_to_click_coords(self, center_x, center_y, screenshot_path):
        from AeroHelper.utils.platform import map_screenshot_coords_to_screen
        return map_screenshot_coords_to_screen(center_x, center_y, screenshot_path, get_roblox_window_rect())

    def _find_and_click_all_text_instances(self, target_text, match_mode='contains', inter_click_sleep=0.35):
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return 0
            if not self.running:
                return 0
            matches = self.ocr.find_text_boxes(screenshot_path, target_text, match_mode=match_mode)
            if not matches:
                self.logger.warning(f"[AUTOPILOT] find_and_click_all: '{target_text}' - no matches")
                return 0
            ordered = sorted(matches, key=lambda m: (m['center'][1], m['center'][0]))
            search_xy = self.search_coordinates
            clicked = 0
            n = len(ordered)
            for idx, target in enumerate(ordered, start=1):
                if not self.running:
                    return clicked
                center_x, center_y = target['center']
                click_x, click_y = self._screen_center_to_click_coords(center_x, center_y, screenshot_path)
                if search_xy:
                    sx, sy = search_xy
                    if abs(click_x - sx) <= 55 and abs(click_y - sy) <= 40:
                        self.logger.info(f"[AUTOPILOT] Skipping search-field match '{target['text']}' at ({click_x}, {click_y})")
                        continue
                self.logger.info(f"[AUTOPILOT] Clicking '{target['text']}' ({idx}/{n}) at ({click_x}, {click_y})")
                self.mouse.click(click_x, click_y, smooth=True)
                clicked += 1
                if idx < n:
                    time.sleep(inter_click_sleep)
            if clicked == 0:
                self.logger.warning(f"[AUTOPILOT] find_and_click_all: '{target_text}' - only search-field matches")
            return clicked
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] find_and_click_all error: {str(e)}')
            return 0
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _match_box_area(self, match):
        box = match.get('box')
        if not box:
            return 0
        try:
            xs = [point[0] for point in box]
            ys = [point[1] for point in box]
            return max(0.0, max(xs) - min(xs)) * max(0.0, max(ys) - min(ys))
        except (TypeError, ValueError, IndexError):
            return 0

    def _screenshot_size(self, screenshot_path):
        if not screenshot_path:
            return None
        try:
            from PIL import Image
            with Image.open(screenshot_path) as img:
                w, h = img.size
            if w > 0 and h > 0:
                return (w, h)
        except Exception:
            return None
        return None

    def _screenshot_center_px(self, screenshot_path):
        size = self._screenshot_size(screenshot_path)
        if not size:
            return None
        return (size[0] / 2.0, size[1] / 2.0)

    def _filter_matches_region(self, matches, screenshot_path, region):
        if not region or not matches:
            return matches
        size = self._screenshot_size(screenshot_path)
        if not size:
            return matches
        w, h = size
        kept = []
        for m in matches:
            x, y = m.get('center') or (0, 0)
            if region == 'left' and x <= w * 0.45:
                kept.append(m)
            elif region == 'center' and w * 0.22 <= x <= w * 0.78 and h * 0.18 <= y <= h * 0.82:
                kept.append(m)
        return kept

    def _filter_yes_matches(self, matches):
        safe = []
        for m in matches:
            tl = (m.get('text') or '').strip().lower()
            if not tl or not re.search(r'\byes\b', tl):
                continue
            if re.search(r'\b(vehicles?|trade|players?|settings?|licenses?)\b', tl):
                continue
            safe.append(m)
        return safe

    def _pick_yes_match(self, matches, screenshot_path=None):
        if not matches:
            return None
        center = self._screenshot_center_px(screenshot_path)

        def sort_key(m):
            area = self._match_box_area(m)
            mx, my = m.get('center') or (0, 0)
            if center is not None:
                dist = (mx - center[0]) ** 2 + (my - center[1]) ** 2
            else:
                dist = 0
            if 1200 <= area <= 25000:
                size_pen = 0
            elif area < 400:
                size_pen = 3
            else:
                size_pen = 1
            return (size_pen, dist, abs(area - 6000))

        return min(matches, key=sort_key)

    def _filter_ui_button_matches(self, matches, target_text, match_mode, screenshot_path=None):

        if not matches:
            return matches
        target_lc = target_text.strip().lower()
        if target_lc not in ('back', 'yes', 'begin', 'play', 'jobs', 'turnaround', 'search'):
            return matches
        if target_lc == 'yes':
            yes_matches = self._filter_yes_matches(matches)
            picked = self._pick_yes_match(yes_matches, screenshot_path)
            return [picked] if picked else []
        if target_lc == 'back':
            safe = []
            for m in matches:
                raw = (m.get('text') or '').strip()
                tl = raw.lower()
                if 'welcome' in tl:
                    continue
                if match_mode == 'exact' and tl != 'back':
                    continue
                if not re.search(r'\bback\b', tl):
                    continue
                safe.append(m)
            matches = safe
        preferred = [m for m in matches if (m.get('text') or '').strip().lower() == target_lc]
        if not preferred and target_lc == 'jobs':
            preferred = [m for m in matches if (m.get('text') or '').strip().lower().startswith('jobs')]
        if not preferred and target_lc == 'turnaround':
            preferred = [m for m in matches if (m.get('text') or '').strip().lower().startswith('turnaround')]
        if not preferred and target_lc == 'back':
            preferred = [m for m in matches if re.match(r'^back\b', (m.get('text') or '').strip(), re.IGNORECASE)]
        if preferred:
            return preferred
        if target_lc == 'back':
            return []
        return matches

    def _ui_config_instance(self):
        if self._ui_config is None:
            from AeroHelper.config import Config
            self._ui_config = Config()
        return self._ui_config

    def _get_cached_ui_coords(self, label):
        cached = self._ui_button_coords.get(label)
        if cached:
            return cached
        try:
            coords = self._ui_config_instance().get_ui_button_coords(label)
            if coords:
                self._ui_button_coords[label] = coords
            return coords
        except Exception:
            return None

    def _save_cached_ui_coords(self, label, x, y):
        coords = (int(x), int(y))
        self._ui_button_coords[label] = coords
        try:
            self._ui_config_instance().set_ui_button_coords(label, coords[0], coords[1])
        except Exception as e:
            self.logger.debug(f"[AUTOPILOT] Could not persist '{label}' coords: {e}")
        return coords

    def _clear_cached_ui_coords(self, *labels):
        for label in labels:
            self._ui_button_coords.pop(label, None)
            try:
                self._ui_config_instance().clear_ui_button_coords(label)
            except Exception:
                pass

    def _locate_ui_label(self, target_text, match_mode='word', prefer_windows=True, region=None):

        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return None
            matches = self.ocr.find_text_boxes(
                screenshot_path, target_text, match_mode=match_mode, prefer_windows=prefer_windows
            )
            if not matches and match_mode == 'word':
                matches = self.ocr.find_text_boxes(
                    screenshot_path, target_text, match_mode='contains', prefer_windows=prefer_windows
                )
            matches = self._filter_matches_region(matches, screenshot_path, region)
            if match_mode in ('contains', 'word', 'exact'):
                matches = self._filter_ui_button_matches(
                    matches, target_text, match_mode, screenshot_path=screenshot_path
                )
            if not matches:
                return None
            target = matches[0]
            center_x, center_y = target['center']
            click_x, click_y = self._screen_center_to_click_coords(center_x, center_y, screenshot_path)
            return (click_x, click_y, (center_x, center_y))
        except Exception as e:
            self.logger.error(f"[AUTOPILOT] locate_ui_label('{target_text}') error: {e}")
            return None
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _pick_jobs_match(self, matches):

        if not matches:
            return None

        def sort_key(m):
            text = m.get('text') or ''
            cy = m['center'][1]
            cx = m['center'][0]
            has_count = '(' in text or bool(re.search(r'\d', text))
            return (0 if has_count else 1, abs(cy - 600), abs(cx - 400))

        return min(matches, key=sort_key)

    def _snap_jobs_coords_fast(self):

        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return None
            matches = self.ocr.find_text_boxes(
                screenshot_path, 'Jobs', match_mode='word', prefer_windows=True, allow_easyocr=False
            )
            matches = self._filter_matches_region(matches, screenshot_path, 'left')
            matches = self._filter_ui_button_matches(
                matches, 'Jobs', 'word', screenshot_path=screenshot_path
            )
            if not matches:
                matches = self.ocr.find_text_boxes(
                    screenshot_path, 'Jobs', match_mode='contains', prefer_windows=True, allow_easyocr=False
                )
                matches = self._filter_matches_region(matches, screenshot_path, 'left')
                matches = self._filter_ui_button_matches(
                    matches, 'Jobs', 'contains', screenshot_path=screenshot_path
                )
            picked = self._pick_jobs_match(matches)
            if not picked:
                return None
            cx, cy = picked['center']
            click = self._screen_center_to_click_coords(cx, cy, screenshot_path)
            self.logger.info(f"[AUTOPILOT] Jobs snap (WinRT) '{picked.get('text')}' at {click}")
            return click
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] snap_jobs_coords_fast error: {e}')
            return None
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _jobs_geometry_from_play(self, play_xy):
        if not play_xy:
            return None
        return (int(play_xy[0]) + _PLAY_TO_JOBS_OFFSET_X, int(play_xy[1]) + _PLAY_TO_JOBS_OFFSET_Y)

    def _search_field_visible(self, screenshot_path=None):
        own_screenshot = screenshot_path is None
        try:
            if own_screenshot:
                screenshot_path = capture_primary_screen()
            if not screenshot_path:
                return False
            for mode in ('exact', 'contains', 'word'):
                matches = self.ocr.find_text_boxes(
                    screenshot_path, 'Search', match_mode=mode, prefer_windows=True, allow_easyocr=False
                )
                if matches:
                    return True
            return False
        except Exception:
            return False
        finally:
            if own_screenshot and screenshot_path:
                delete_screenshot(screenshot_path)

    def _jobs_panel_ready(self):

        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path:
                return False
            if self._search_field_visible(screenshot_path):
                return True
            for label in ('Sorting by', 'Jobs ('):
                matches = self.ocr.find_text_boxes(
                    screenshot_path, label, match_mode='contains', prefer_windows=True, allow_easyocr=False
                )
                if matches:
                    return True
            return False
        except Exception:
            return False
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _activate_search_from_cache(self):
        cached = self._get_cached_ui_coords('Search')
        if not cached:
            return False
        self.search_coordinates = cached
        self.logger.info(f'[AUTOPILOT] Using cached Search coords {cached} (placeholder not visible)')
        self.mouse.click(cached[0], cached[1], smooth=True)
        time.sleep(0.35)
        self.keyboard.clear_input()
        time.sleep(0.3)
        return True

    def _click_jobs_at(self, jobs_xy, *, double=True, persist=True):
        jx, jy = int(jobs_xy[0]), int(jobs_xy[1])
        self.logger.info(f"[AUTOPILOT] Clicking Jobs at ({jx}, {jy})")
        self.mouse.click(jx, jy, smooth=True)
        if double:
            time.sleep(0.35)
            self.mouse.click(jx, jy, smooth=True)
        if persist:
            self._save_cached_ui_coords('Jobs', jx, jy)
        return True

    def _open_jobs_from_play_menu(self, play_xy):

        px, py = int(play_xy[0]), int(play_xy[1])
        self.logger.info(f"[AUTOPILOT] Play→Jobs: hover Play at ({px}, {py})")
        self.mouse.hover(px, py, dwell=0.55)
        time.sleep(0.35)
        if not self.running:
            return False

        self.logger.info(f"[AUTOPILOT] Play→Jobs: click Play at ({px}, {py})")
        self.mouse.click(px, py, smooth=True)
        time.sleep(0.5)
        if not self.running:
            return False


        self.mouse.move_to(px, py, natural=True)
        time.sleep(0.12)
        jobs_xy = self._snap_jobs_coords_fast()
        if not jobs_xy:
            self.logger.info('[AUTOPILOT] Play→Jobs: re-hover Play and snap again')
            self.mouse.hover(px, py, dwell=0.45)
            time.sleep(0.2)
            jobs_xy = self._snap_jobs_coords_fast()
        if not jobs_xy:
            jobs_xy = self._jobs_geometry_from_play(play_xy)
            if jobs_xy:
                self.logger.warning(f'[AUTOPILOT] Play→Jobs: Jobs OCR miss - geometry {jobs_xy}')
                self.mouse.hover(px, py, dwell=0.25)
                time.sleep(0.1)
        if not jobs_xy:
            return False


        self._click_jobs_at(jobs_xy, double=True, persist=True)
        return True

    def _try_cached_play_to_jobs(self):

        play = self._get_cached_ui_coords('Play')
        jobs = self._get_cached_ui_coords('Jobs')
        if not play or not jobs:
            return False
        self.logger.info(f'[AUTOPILOT] Cached Play→Jobs Play={play} Jobs={jobs}')
        self.mouse.hover(play[0], play[1], dwell=0.45)
        time.sleep(0.35)
        if not self.running:
            return False
        self.mouse.click(play[0], play[1], smooth=True)
        time.sleep(0.5)
        if not self.running:
            return False
        self.mouse.click(jobs[0], jobs[1], smooth=True)
        time.sleep(0.35)
        self.mouse.click(jobs[0], jobs[1], smooth=True)
        time.sleep(0.8)
        if self._jobs_panel_ready():
            return True
        self.logger.warning('[AUTOPILOT] Cached Jobs did not open Search - clearing Jobs cache')
        self._clear_cached_ui_coords('Jobs')
        return False

    def _click_back_button(self):

        from AeroHelper.utils.window import bring_roblox_to_front
        bring_roblox_to_front()
        success, _ = self._find_and_click_text('Back', match_mode='exact')
        if not success:
            success, _ = self._find_and_click_text('Back', match_mode='word')
            if success:
                self.logger.warning("[AUTOPILOT] Used word match for Back - verify it was the UI button")
        return success

    def _find_and_click_text(self, target_text, instance=1, match_mode='contains', screenshot_path=None, smooth=True, prefer_windows=False, region=None):
        own_screenshot = screenshot_path is None
        try:
            if not self.running:
                return (False, None)
            if own_screenshot:
                screenshot_path = capture_primary_screen()
                if not screenshot_path or not os.path.exists(screenshot_path):
                    return (False, None)
            matches = self.ocr.find_text_boxes(
                screenshot_path, target_text, match_mode=match_mode, prefer_windows=prefer_windows
            )
            matches = self._filter_matches_region(matches, screenshot_path, region)
            if match_mode in ('contains', 'word', 'exact'):
                matches = self._filter_ui_button_matches(
                    matches, target_text, match_mode, screenshot_path=screenshot_path
                )
            if not matches or len(matches) < instance:
                self.logger.warning(f"[AUTOPILOT] find_and_click: '{target_text}' instance {instance} not found (found {len(matches) if matches else 0} matches)")
                return (False, screenshot_path if not own_screenshot else None)
            if not self.running:
                return (False, screenshot_path if not own_screenshot else None)
            target = matches[instance - 1]
            center_x, center_y = target['center']
            click_x, click_y = self._screen_center_to_click_coords(center_x, center_y, screenshot_path)
            self.logger.info(f"[AUTOPILOT] Clicking '{target['text']}' (instance {instance}) at ({click_x}, {click_y})")
            self.mouse.click(click_x, click_y, smooth=smooth)
            return (True, screenshot_path if not own_screenshot else None)
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] find_and_click error: {str(e)}')
            return (False, None)
        finally:
            if own_screenshot and screenshot_path:
                delete_screenshot(screenshot_path)

    def _hover_text(self, target_text, instance=1, match_mode='contains', click=False, dwell=0.55, smooth=True, region=None):

        screenshot_path = None
        try:
            if not self.running:
                return False
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return False
            matches = self.ocr.find_text_boxes(screenshot_path, target_text, match_mode=match_mode)
            matches = self._filter_matches_region(matches, screenshot_path, region)
            if match_mode in ('contains', 'word', 'exact'):
                matches = self._filter_ui_button_matches(
                    matches, target_text, match_mode, screenshot_path=screenshot_path
                )
            if not matches or len(matches) < instance:
                self.logger.warning(f"[AUTOPILOT] hover_text: '{target_text}' instance {instance} not found (found {len(matches) if matches else 0} matches)")
                return False
            if not self.running:
                return False
            target = matches[instance - 1]
            center_x, center_y = target['center']
            click_x, click_y = self._screen_center_to_click_coords(center_x, center_y, screenshot_path)
            mode = 'click-activate' if click else 'hover'
            self.logger.info(f"[AUTOPILOT] Hovering '{target['text']}' (instance {instance}, {mode}) at ({click_x}, {click_y})")
            if click:
                self.mouse.click(click_x, click_y, smooth=smooth)
                time.sleep(0.25)
                self.mouse.move_to(click_x, click_y, natural=smooth)
            else:
                self.mouse.hover(click_x, click_y, dwell=dwell)
            return True
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] hover_text error: {str(e)}')
            return False
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _store_click_coordinates(self, target_text, match_mode='contains'):
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return None
            matches = self.ocr.find_text_boxes(screenshot_path, target_text, match_mode=match_mode)
            if match_mode in ('contains', 'word', 'exact'):
                matches = self._filter_ui_button_matches(
                    matches, target_text, match_mode, screenshot_path=screenshot_path
                )
            if not matches:
                return None
            target = matches[0]
            center_x, center_y = target['center']
            return self._screen_center_to_click_coords(center_x, center_y, screenshot_path)
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] store_click_coordinates error: {str(e)}')
            return None
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _read_distance(self):
        data = self._read_parsed_screen_data()
        if data is None:
            return None
        return data.distance

    def _phase1_give_up(self, reason, details=None):
        self.logger.error(f'[AUTOPILOT] Phase 1 failed ({reason}) - stopping for human intervention')
        self._notify_autopilot('Phase 1', 'Phase 1 failed - human intervention required', details=details or reason, ping=True, embed_color=16711680)
        return {'action': 'pause', 'reason': f'Phase 1 failed: {reason}', 'details': details or '', 'stop_automation': True}

    def _verify_mission_game_state_after_begin(self, attempts=4, settle_secs=2.0):
        from AeroHelper.utils.window import bring_roblox_to_front
        bring_roblox_to_front()
        for attempt in range(1, attempts + 1):
            if attempt > 1:
                self._sleep_if_running(settle_secs)
            screenshot_path, text, _ = self._take_screenshot_and_ocr()
            try:
                if not text:
                    self.logger.warning(f'[AUTOPILOT] Post-Begin verify ({attempt}/{attempts}): no OCR text')
                    continue
                if self.ocr.detect_active_mission(text):
                    detail = 'Abandon Job' if self.ocr.detect_abandon_job(text) else 'mission HUD (End Sail / Controls)'
                    self.logger.info(f'[AUTOPILOT] Post-Begin verify: active mission confirmed ({detail})')
                    return True
                self.logger.warning(f'[AUTOPILOT] Post-Begin verify ({attempt}/{attempts}): mission HUD not confirmed yet')
            finally:
                if screenshot_path:
                    delete_screenshot(screenshot_path)
        self.logger.warning('[AUTOPILOT] Post-Begin verify: mission not confirmed after retries (Begin may not have registered)')
        return False

    def _execute_phase_1(self):
        self.logger.info('[AUTOPILOT] ===== PHASE 1 - Spawning & Route Selection =====')
        self._notify_autopilot('Phase 1', 'Spawning sequence started', details=f'include_screenshots={self.include_screenshots}, start_mid_mission={self.start_mid_mission}')
        if self.human_detector:
            self.human_detector.suspend()
        try:
            for spawn_attempt in range(1, PHASE1_SPAWN_MAX_RETRIES + 1):
                if spawn_attempt > 1:
                    self.logger.info(f'[AUTOPILOT] Retrying full spawning sequence (attempt {spawn_attempt}/{PHASE1_SPAWN_MAX_RETRIES})')
                    self._notify_autopilot('Phase 1', f'Restarting spawning sequence ({spawn_attempt}/{PHASE1_SPAWN_MAX_RETRIES})', details='Begin did not produce valid game state; retrying from Step 1')
                    if self._verify_mission_game_state_after_begin(attempts=2, settle_secs=1.5):
                        self.logger.info('[AUTOPILOT] Mission already active on retry - skipping re-spawn, starting motors')
                        self._notify_autopilot('Phase 1', 'Mission already active', details='Skipping Phase 1 restart; starting motors')
                        break
                if not self.running:
                    return None
                self.logger.info('[AUTOPILOT] Step 1: Close Chat')
                self._close_chat_ui()
                self._sleep_if_running(1)
                if not self.running:
                    return None
                self._notify_autopilot('Phase 1', 'Closed chat / UI prep', details='Step 1 complete')
                self.logger.info('[AUTOPILOT] Step 2: Detect Current Airport')
                self.current_airport = self._detect_current_airport()
                if self.current_airport is None:
                    fail = getattr(self, '_airport_detect_fail_reason', None) or 'Could not detect current airport'
                    self.logger.error(f'[AUTOPILOT] Failed to detect current airport: {fail}')
                    return self._phase1_give_up(
                        fail,
                        details='Go to a supported AutoPilot route airport (or enable Start Mid-Mission) and resume',
                    )
                self.logger.info(f'[AUTOPILOT] Detected airport: {self.current_airport}')
                ap_name = SUPPORTED_AIRPORTS[self.current_airport]['full_name']
                self._notify_autopilot('Phase 1', f'Airport detected: {ap_name}', details=f'icao_key={self.current_airport}')
                self.logger.info('[AUTOPILOT] Step 3: Vehicle Preparation')
                if not self._vehicle_preparation():
                    self.logger.error('[AUTOPILOT] Vehicle preparation failed - Turnaround confirm still open')
                    return self._phase1_give_up(
                        'Turnaround Yes confirm failed',
                        details='Confirm Turnaround dialog still open; click Yes or dismiss it, then resume',
                    )
                self._notify_autopilot('Phase 1', 'Vehicle preparation finished', details='Turnaround/Yes if present')
                self.logger.info('[AUTOPILOT] Step 4: Job Search')
                if not self._job_search():
                    self.logger.error('[AUTOPILOT] Job search failed')
                    return self._phase1_error_recovery('Job search failed')
                self.logger.info('[AUTOPILOT] Step 5: Route Evaluation')
                route_data = self._evaluate_routes()
                if not route_data:
                    self.logger.error('[AUTOPILOT] Route evaluation failed - no valid routes found')
                    return self._phase1_error_recovery('Route evaluation failed')
                self.logger.info('[AUTOPILOT] Step 6: Route Selection')
                if not self._select_best_route(route_data):
                    self.logger.error('[AUTOPILOT] Route selection failed')
                    return self._phase1_error_recovery('Route selection failed')
                if self._verify_mission_game_state_after_begin():
                    break
                self._notify_autopilot('Phase 1', 'Begin did not start mission', details=f'Mission HUD not confirmed after Begin (attempt {spawn_attempt}/{PHASE1_SPAWN_MAX_RETRIES})')
                if spawn_attempt >= PHASE1_SPAWN_MAX_RETRIES:
                    return self._phase1_give_up('Mission did not start after Begin', details='Mission HUD not detected after retries')
                if self._click_back_button():
                    self.logger.info('[AUTOPILOT] Clicked Back before spawn retry')
                    self._notify_autopilot('Phase 1', 'Clicked Back', details='Leaving job UI before spawn retry')
                    self._sleep_if_running(2)
                else:
                    self.logger.warning('[AUTOPILOT] Back not found before spawn retry - continuing anyway')
            self.logger.info('[AUTOPILOT] Step 7: Start Motors')
            self._start_motors()
            pending_mission = self.mission_count + 1
            self.logger.info(f'[AUTOPILOT] Phase 1 complete - pending mission #{pending_mission} to {self.selected_destination} (WP: {self.selected_wp}, Money: {self.selected_money})')
            undock_cycles = self._get_undocking_cycles()
            next_phase = 'undocking' if undock_cycles > 0 else 'AutoSteer'
            self._notify_autopilot('Phase 1 Complete', f'Route accepted - {next_phase} next; controlling to {self.selected_destination_full}', details=f'Pending mission #{pending_mission}; undock_cycles={undock_cycles}; WP: {self.selected_wp}, Money: {self.selected_money}, Destination key: {self.selected_destination}')
            self._begin_post_phase1_navigation()
            return {'action': 'continue'}
        except Exception as e:
            import traceback
            self.logger.error(f'[AUTOPILOT] Phase 1 exception: {str(e)}')
            self.logger.error_detailed('[AUTOPILOT] Phase 1 traceback', traceback.format_exc())
            return self._phase1_give_up(f'Phase 1 unhandled error: {str(e)}', details=traceback.format_exc())
        finally:
            if self.human_detector:
                self.human_detector.unsuspend()

    def _detect_current_airport(self):
        screenshot_path = None
        self._airport_detect_fail_reason = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path:
                return None
            text = self.ocr.extract_text(screenshot_path)
            self._raise_if_disconnected(text, 'current airport detection')
            if not text:
                return None
            label, candidate = self._extract_currently_at_label(text)
            currently_at = self._match_currently_at_candidate(candidate) if candidate else None
            if currently_at:
                self.logger.info(f"[AUTOPILOT] Detected 'currently at' airport: {currently_at}")
                return currently_at
            if label:
                reason = f'Detected {label} - not a supported AutoPilot route'
                self._airport_detect_fail_reason = reason
                self.logger.warning(f'[AUTOPILOT] {reason}')
                return None
            found_airports = []
            for airport_key in SUPPORTED_AIRPORTS:
                pattern = re.compile('\\b' + re.escape(airport_key) + '\\b', re.IGNORECASE)
                if pattern.search(text):
                    found_airports.append(airport_key)
            if len(found_airports) == 1:
                return found_airports[0]
            if len(found_airports) == 0:
                self._airport_detect_fail_reason = 'Could not detect current airport'
                self.logger.warning(f'[AUTOPILOT] No supported airport found in OCR text: {text}')
                return None
            self._airport_detect_fail_reason = f'Multiple supported airports visible ({", ".join(found_airports)})'
            self.logger.warning(f"[AUTOPILOT] Multiple supported airports visible {found_airports} and no 'currently at' line was recognized - giving up on detection")
            return None
        except ReconnectRequested:
            raise
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] Airport detection error: {str(e)}')
            return None
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _extract_currently_at_label(self, text):
        if not text:
            return (None, None)
        patterns = [
            re.compile('currently\\s+at\\s+([^\\n\\r,\\.]+?)\\s+air(?:port|field)', re.IGNORECASE),
            re.compile('you\\s+are\\s+at\\s+([^\\n\\r,\\.]+?)\\s+air(?:port|field)', re.IGNORECASE),
            re.compile('currently\\s+at\\s+([^\\n\\r,\\.]+)', re.IGNORECASE),
        ]
        for pat in patterns:
            m = pat.search(text)
            if not m:
                continue
            raw = m.group(1).strip()
            icao = ''
            icao_m = re.search('\\(([A-Za-z0-9]{3,4})\\)', text[m.start():m.end() + 24])
            if icao_m:
                icao = icao_m.group(1).upper()
            else:
                icao_m = re.search('\\(([A-Za-z0-9]{3,4})\\)', raw)
                if icao_m:
                    icao = icao_m.group(1).upper()
                    raw = (raw[:icao_m.start()] + raw[icao_m.end():]).strip()
            candidate = raw.lower()
            name = re.sub('\\s+', ' ', raw).strip()
            name_bits = re.split('(?i)\\b(?:profile|vehicle|boat|ship|class)\\b', name)
            if len(name_bits) > 1 and name_bits[-1].strip():
                name = name_bits[-1].strip(' -/:')
            name = name.title() if name else raw.title()
            label = f'{name} ({icao})' if icao else name
            return (label, candidate)
        return (None, None)

    def _match_currently_at_candidate(self, candidate):
        if not candidate:
            return None
        for airport_key, info in SUPPORTED_AIRPORTS.items():
            key_lc = airport_key.lower()
            full_lc = info.get('full_name', '').lower()
            if key_lc and key_lc in candidate:
                return airport_key
            if full_lc and full_lc in candidate:
                return airport_key
            for word in full_lc.split():
                word = re.sub('^[^a-z0-9]+|[^a-z0-9]+$', '', word)
                if word in _CURRENTLY_AT_AIRPORT_WORD_STOPWORDS:
                    continue
                if len(word) >= 4 and word in candidate:
                    return airport_key
        return None

    def _click_turnaround_button(self):
        success, _ = self._find_and_click_text(
            'Turnaround', match_mode='word', smooth=False, region='left', prefer_windows=True
        )
        if not success:
            success, _ = self._find_and_click_text(
                'Turnaround', match_mode='contains', smooth=False, region='left', prefer_windows=True
            )
        return success

    def _try_click_yes(self):

        if not self.running:
            return False
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return False
            matches = self.ocr.find_text_boxes(
                screenshot_path, 'Yes', match_mode='word', prefer_windows=True
            )
            matches = self._filter_matches_region(matches, screenshot_path, 'center')
            matches = self._filter_ui_button_matches(
                matches, 'Yes', 'word', screenshot_path=screenshot_path
            )
            if not matches:
                self.logger.warning("[AUTOPILOT] hover_click: 'Yes' not found")
                return False
            target = matches[0]
            center_x, center_y = target['center']
            click_x, click_y = self._screen_center_to_click_coords(center_x, center_y, screenshot_path)
            self.logger.info(f"[AUTOPILOT] Hover+click 'Yes' at ({click_x}, {click_y})")
            self.mouse.hover(click_x, click_y, dwell=0.35)
            if not self.running:
                return False
            self.mouse.click(click_x, click_y, smooth=False)
            return True
        except Exception as e:
            self.logger.error(f'[AUTOPILOT] hover+click Yes error: {e}')
            return False
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _confirm_turnaround_visible(self, text):
        if not text:
            return False
        return bool(re.search(
            r'confirm\s+turnaround|are you sure you want to perform a turnaround',
            text,
            re.I,
        ))

    def _turnaround_success_visible(self, text):
        if not text:
            return False
        return bool(re.search(
            r'successfully\s+turned|turned\s+vehicle\s+around',
            text,
            re.I,
        ))

    def _inspect_turnaround_result(self):

        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                return False, False
            try:
                native = self.ocr._native_ocr_extract(screenshot_path) or ''
            except Exception:
                native = ''
            if self._turnaround_success_visible(native):
                return False, True
            if self._confirm_turnaround_visible(native):
                return True, False
            for target in ('Confirm Turnaround', 'Are you sure'):
                matches = self.ocr.find_text_boxes(
                    screenshot_path,
                    target,
                    match_mode='contains',
                    prefer_windows=True,
                    allow_easyocr=False,
                )
                if matches:
                    return True, False
            return False, False
        except Exception as e:
            self.logger.warning(f'[AUTOPILOT] Confirm Turnaround check failed: {e}')
            return False, False
        finally:
            if screenshot_path:
                delete_screenshot(screenshot_path)

    def _wait_for_confirm_dialog(self, attempts=5):
        for attempt in range(attempts):
            if not self.running:
                return False
            confirm_left, success_toast = self._inspect_turnaround_result()
            if success_toast or confirm_left:
                return True
            time.sleep(0.4)
        return False

    def _wait_for_turnaround_settle(self):

        clicks = 0
        while clicks < _TURNAROUND_YES_MAX_CLICKS and self.running:
            confirm_left, success_toast = self._inspect_turnaround_result()
            if success_toast:
                self.logger.info('[AUTOPILOT] Turnaround success toast visible')
                return True, True
            if clicks > 0 and not confirm_left:
                return True, False
            if not self._try_click_yes():
                self.logger.info('[AUTOPILOT] Yes OCR miss - clicking dialog center')
                self._click_centered_yes_fallback()
            clicks += 1
            self.logger.info(
                f"[AUTOPILOT] Clicked Yes ({clicks}/{_TURNAROUND_YES_MAX_CLICKS})"
            )
            self._sleep_if_running(0.8)
        confirm_left, success_toast = self._inspect_turnaround_result()
        if success_toast:
            self.logger.info('[AUTOPILOT] Turnaround success toast visible')
            return True, True
        if not confirm_left:
            return True, False
        self.logger.warning('[AUTOPILOT] Turnaround confirm still visible after Yes')
        self._notify_autopilot(
            'Phase 1',
            'Confirm Turnaround still open',
            details=f'Yes click missed after {_TURNAROUND_YES_MAX_CLICKS} tries; stopping before Jobs',
        )
        return False, False

    def _click_centered_yes_fallback(self):
        if not self.running:
            return False
        center = get_roblox_window_center()
        if not center:
            return False
        x, y = int(center[0]), int(center[1]) + 40
        self.logger.info(f'[AUTOPILOT] Clicking centered Yes fallback at ({x}, {y})')
        self.mouse.click(x, y, smooth=False)
        return True

    def _vehicle_preparation(self):
        self.logger.info("[AUTOPILOT] Hovering 'Your Current Vehicle'")

        self._hover_text('Your Current Vehicle', click=False, dwell=0.7, region='left')
        time.sleep(0.45)
        self._notify_autopilot('Phase 1', 'Hovered Your Current Vehicle', details='Vehicle menu prep')
        screenshot_path, text, _ = self._take_screenshot_and_ocr()
        if screenshot_path:
            delete_screenshot(screenshot_path)
        turnaround_found = False
        for attempt in range(2):
            if not self.running:
                return False
            if attempt > 0:
                self._hover_text('Your Current Vehicle', click=False, dwell=0.7, region='left')
                time.sleep(0.45)
            self.logger.info(f"[AUTOPILOT] Looking for 'Turnaround' (attempt {attempt + 1}/2)")
            if self._click_turnaround_button():
                turnaround_found = True
                self._notify_autopilot('Phase 1', 'Clicked Turnaround', details=f'attempt {attempt + 1}/2')
                break
            time.sleep(1)
            screenshot_path, text, _ = self._take_screenshot_and_ocr()
            if screenshot_path:
                delete_screenshot(screenshot_path)
        if not turnaround_found:
            self.logger.info('[AUTOPILOT] Turnaround not found after 2 attempts - skipping')
            self._notify_autopilot('Phase 1', 'Turnaround not found', details='Skipped; continuing')
            return True
        confirm_up = self._wait_for_confirm_dialog()
        for reclick in range(2):
            if confirm_up or not self.running:
                break
            self.logger.info(f"[AUTOPILOT] Confirm dialog not visible - reclicking Turnaround ({reclick + 1}/2)")
            self._hover_text('Your Current Vehicle', click=False, dwell=0.7, region='left')
            time.sleep(0.45)
            if not self._click_turnaround_button():
                self.logger.warning('[AUTOPILOT] Turnaround not found for reclick')
                continue
            self._notify_autopilot('Phase 1', 'Reclicked Turnaround', details=f'reclick {reclick + 1}/2')
            confirm_up = self._wait_for_confirm_dialog()
        if not confirm_up:
            self.logger.warning('[AUTOPILOT] Turnaround click did not open confirm dialog')
            self._notify_autopilot('Phase 1', 'Turnaround confirm never opened', details='Continuing without Yes')
            return True
        settled, saw_success = self._wait_for_turnaround_settle()
        if not settled:
            return False
        if saw_success:
            self._notify_autopilot('Phase 1', 'Clicked Yes', details='Confirmed Turnaround')
        else:
            self._notify_autopilot('Phase 1', 'Clicked Yes', details='Confirm dialog closed')
        self._sleep_if_running(2)
        return True

    def _job_search(self):
        from AeroHelper.utils.window import bring_roblox_to_front
        bring_roblox_to_front()
        jobs_ok = False

        if self._try_cached_play_to_jobs():
            jobs_ok = True

        for attempt in range(1, 4):
            if jobs_ok:
                break
            if not self.running:
                return False
            self.logger.info(f'[AUTOPILOT] Opening Play → Jobs (attempt {attempt}/3)')
            located = self._locate_ui_label('Play', match_mode='word', prefer_windows=True, region='left')
            if not located:
                self.logger.warning(
                    f'[AUTOPILOT] Play not found (attempt {attempt}/3) - close Discord overlay/modals, then retry'
                )
                time.sleep(0.5)
                continue
            play_xy = (located[0], located[1])
            self._save_cached_ui_coords('Play', play_xy[0], play_xy[1])

            if not self._open_jobs_from_play_menu(play_xy):
                self.logger.warning(f'[AUTOPILOT] Play → Jobs sequence failed ({attempt}/3)')
                time.sleep(0.5)
                continue


            for _ in range(8):
                if not self.running:
                    return False
                if self._jobs_panel_ready():
                    jobs_ok = True
                    break
                time.sleep(0.75)
            if jobs_ok:
                break
            self.logger.warning('[AUTOPILOT] Jobs clicked but Search not visible - retrying')
            self._clear_cached_ui_coords('Jobs')
            time.sleep(0.5)

        if not jobs_ok:
            self.logger.error(
                "[AUTOPILOT] 'Jobs' button not found - keep Roblox focused, close Discord overlay / "
                'Special Naming modals, ensure lobby Play flyout can open'
            )
            self._notify_autopilot(
                'Phase 1',
                'Jobs button not found',
                details='Play→Jobs sequence failed; close overlays and retry',
            )
            return False

        self._notify_autopilot('Phase 1', 'Clicked Jobs', details='Jobs UI opening')
        self.logger.info('[AUTOPILOT] Waiting for jobs panel / Search')
        self.search_coordinates = self._store_click_coordinates('Search', match_mode='exact')
        if not self.search_coordinates:

            self._sleep_if_running(2)
            self.search_coordinates = self._store_click_coordinates('Search', match_mode='exact')
        if not self.search_coordinates:
            self.search_coordinates = self._store_click_coordinates('Search', match_mode='contains')
        if not self.search_coordinates:
            if self._activate_search_from_cache():
                self._notify_autopilot(
                    'Phase 1',
                    'Used cached Search field',
                    details='Placeholder hidden (leftover text); clicked cache and cleared',
                )
                time.sleep(1)
                return True
            self.logger.error(
                '[AUTOPILOT] Could not find Search button to store coordinates - '
                'ensure Jobs list is open and visible (no Discord overlay)'
            )
            self._clear_cached_ui_coords('Jobs')
            self._notify_autopilot(
                'Phase 1',
                'Search field coordinates failed',
                details='Jobs opened but Search not visible; cleared Jobs cache',
            )
            return False
        self._save_cached_ui_coords('Search', self.search_coordinates[0], self.search_coordinates[1])
        self.logger.info(f'[AUTOPILOT] Stored search coordinates: {self.search_coordinates}')
        self._notify_autopilot('Phase 1', 'Stored Search field position', details=f'screen_coords={self.search_coordinates}')
        self.logger.info("[AUTOPILOT] Clicking 'Search'")
        self.mouse.click(self.search_coordinates[0], self.search_coordinates[1], smooth=True)
        time.sleep(0.35)
        success, _ = self._find_and_click_text('Search', match_mode='exact')
        if not success:
            success, _ = self._find_and_click_text('Search', match_mode='contains')
        if not success:

            self.logger.warning("[AUTOPILOT] Search OCR click miss - used stored coordinates")
        self._notify_autopilot('Phase 1', 'Clicked Search', details='Search field active for typing')
        time.sleep(1)
        return True

    def _phase1_normalize_mission_ocr(self, text):
        tl = (text or '').lower()
        for old, new in (
            ('and/orgoodsto', 'and/or goods to'),
            ('and/or goodsto', 'and/or goods to'),
            ('goodsto', 'goods to'),
            ('transportto', 'transport to'),
            ('transportpassengers', 'transport passengers'),
        ):
            tl = tl.replace(old, new)
        return tl

    def _phase1_mission_blurb_snippets(self, tl):
        snippets = []
        patterns = (
            'goods\\s+to\\s+(.+?)(?:\\s+safely|\\s+distance\\s*:)',
            'your\\s+vehicle\\s+to\\s+(.+?)(?:\\s+safely|\\s+distance\\s*:)',
            'passengers\\s+and\\s*/?\\s*or\\s+goods\\s+to\\s+(.+?)(?:\\s+safely|\\s+distance\\s*:)',
            'passengers\\s+and\\w+\\s+to\\s+(.+?)(?:\\s+safely|\\s+distance\\s*:)',
            'transport\\s+to\\s+(.+?)\\s+transport\\s+passengers',
        )
        for pat in patterns:
            for m in re.finditer(pat, tl, re.IGNORECASE | re.DOTALL):
                snippets.append(m.group(0).lower())
        out = []
        seen = set()
        for s in snippets:
            s = s.strip()
            if len(s) < 12 or s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out

    def _phase1_destination_in_mission_snippet(self, snippet, dest_key, dest_full_name):
        dk = (dest_key or '').lower().strip()
        df = (dest_full_name or '').lower().strip()
        if dk and len(dk) >= 3 and (dk in snippet):
            return True
        if df and len(df) >= 3 and (df in snippet):
            return True
        for part in df.split():
            pl = re.sub('^[^a-z0-9]+|[^a-z0-9]+$', '', part.lower())
            if len(pl) >= 4 and pl in snippet:
                return True
        return False

    def _phase1_mission_description_matches_destination(self, ocr_text, dest_key, dest_full_name):
        if not ocr_text or not isinstance(ocr_text, str):
            return False
        tl = self._phase1_normalize_mission_ocr(ocr_text)
        snippets = self._phase1_mission_blurb_snippets(tl)
        if snippets and any((self._phase1_destination_in_mission_snippet(s, dest_key, dest_full_name) for s in snippets)):
            return True
        if not re.search(r'distance\s*:\s*[\d.]+', tl):
            return False
        if not re.search(r'(?:edit\s+route|estimated\s+time\s+enroute|begin)', tl):
            return False
        transport_to = re.search(
            rf'transport\s+to\s+(.{{0,80}}?)(?:\s+transport\s+passengers|\s+distance\s*:)',
            tl,
            re.IGNORECASE | re.DOTALL,
        )
        if transport_to and self._phase1_destination_in_mission_snippet(transport_to.group(0), dest_key, dest_full_name):
            return True
        return False

    def _phase1_recover_jobs_ui_after_refresh(self, dest_key):
        self.logger.warning(f'[AUTOPILOT] Jobs UI may have refreshed - click did not open mission for {dest_key}; recovering')
        self._notify_autopilot('Phase 1', 'Dealership / jobs list refreshed while selecting a destination - recovering', details=f'Restarting from Play → Jobs → Search (was selecting {dest_key})')
        self._clear_search_and_reset()
        if self._click_back_button():
            self.logger.info('[AUTOPILOT] Recovery: clicked Back')
            self._sleep_if_running(2)
        else:
            self.logger.warning('[AUTOPILOT] Recovery: Back not found - continuing to re-open Jobs')
        return self._job_search()

    def _evaluate_routes(self):
        if self.current_airport not in SUPPORTED_AIRPORTS:
            self.logger.error(f"[AUTOPILOT] Airport '{self.current_airport}' not in supported airports")
            return None
        destinations = SUPPORTED_AIRPORTS[self.current_airport]['destinations']
        route_data = {}
        self._clear_search_and_reset()
        self._notify_autopilot('Phase 1', 'Route evaluation started', details=f'{len(destinations)} destination(s) from {self.current_airport}')
        dest_items = list(destinations.items())
        max_recoveries = 2
        recoveries_used = 0
        i = 0
        while i < len(dest_items):
            if not self.running:
                return None
            dest_key, dest_full_name = dest_items[i]
            self.logger.info(f'[AUTOPILOT] Evaluating route to {dest_full_name}')
            self.logger.info(f'[AUTOPILOT] Typing destination: {dest_full_name}')
            self.keyboard.select_all_and_type(dest_full_name, delay=0.05)
            self._sleep_if_running(2)
            self._notify_autopilot('Phase 1', f'Typed destination: {dest_full_name}', details=f'search_key={dest_key}')
            screenshot_path, text, _ = self._take_screenshot_and_ocr()
            if screenshot_path:
                delete_screenshot(screenshot_path)
            self.logger.info(f"[AUTOPILOT] Clicking all search hits for '{dest_key}'")
            clicked = self._find_and_click_all_text_instances(dest_key)
            if clicked == 0:
                self.logger.info(f"[AUTOPILOT] No hits for '{dest_key}', trying full name '{dest_full_name}'")
                clicked = self._find_and_click_all_text_instances(dest_full_name)
            success = clicked > 0
            if not success:
                self.logger.warning(f"[AUTOPILOT] Could not click destination '{dest_key}' - skipping")
                self._notify_autopilot('Phase 1', f'Could not select listing: {dest_key}', details='Skipped this route')
                self._clear_search_and_reset()
                i += 1
                continue
            self._notify_autopilot('Phase 1', f'Clicked {clicked} OCR hit(s) for: {dest_key}', details='Reading WP/Money')
            self._sleep_if_running(2)
            screenshot_path, text, _ = self._take_screenshot_and_ocr()
            try:
                if not self._phase1_mission_description_matches_destination(text, dest_key, dest_full_name):
                    self.logger.warning(f'[AUTOPILOT] Mission text not confirmed for {dest_key} (expected transport blurb including destination)')
                    recoveries_used += 1
                    if recoveries_used > max_recoveries:
                        self.logger.error('[AUTOPILOT] Too many jobs-UI recoveries during route evaluation')
                        self._notify_autopilot('Phase 1', 'Route evaluation aborted - repeated UI refresh recovery failures', embed_color=16711680)
                        return None
                    if not self._phase1_recover_jobs_ui_after_refresh(dest_key):
                        return None
                    self._notify_autopilot('Phase 1', 'Jobs UI recovered', details=f'Retrying {dest_key}; keeping {len(route_data)} prior quote(s)')
                    continue
                self.logger.info(f'[AUTOPILOT] OCR confirmed transport mission blurb for {dest_key}')
                wp, money = (None, None)
                if text:
                    wp, money = self.ocr.extract_wp_money(text)
            finally:
                if screenshot_path:
                    delete_screenshot(screenshot_path)
            self.logger.info(f'[AUTOPILOT] Route to {dest_key}: WP={wp}, Money={money}')
            self._notify_autopilot('Phase 1', f'Quote recorded: {dest_key}', details=f'WP={wp}, Money={money}')
            route_data[dest_key] = {'full_name': dest_full_name, 'wp': wp, 'money': money}
            self._clear_search_and_reset()
            i += 1
        if not route_data:
            return None
        return route_data

    def _clear_search_and_reset(self):
        if self.search_coordinates:
            self.logger.info(f'[AUTOPILOT] Clicking stored search coordinates: {self.search_coordinates}')
            self.mouse.click(self.search_coordinates[0], self.search_coordinates[1], smooth=True)
            time.sleep(0.5)
        self.keyboard.clear_input(30)
        time.sleep(0.5)

    def _select_best_route(self, route_data):
        best_dest = None
        best_wp = -1
        for dest_key, data in route_data.items():
            wp = data.get('wp')
            if wp is not None and wp > best_wp:
                best_wp = wp
                best_dest = dest_key
        if best_dest is None:
            best_dest = list(route_data.keys())[0]
        self.selected_destination = best_dest
        self.selected_destination_full = route_data[best_dest]['full_name']
        self.selected_wp = route_data[best_dest].get('wp')
        self.selected_money = route_data[best_dest].get('money')
        self.logger.info(f'[AUTOPILOT] Selected route: {self.selected_destination_full} (WP: {self.selected_wp}, Money: {self.selected_money})')
        self._notify_autopilot('Phase 1', f'Best route chosen: {self.selected_destination_full}', details=f'WP={self.selected_wp}, Money={self.selected_money}')
        self._clear_search_and_reset()
        self.logger.info(f'[AUTOPILOT] Typing destination: {self.selected_destination_full}')
        self.keyboard.select_all_and_type(self.selected_destination_full, delay=0.05)
        self._sleep_if_running(2)
        self._notify_autopilot('Phase 1', f'Typed selected route: {self.selected_destination_full}', details='Re-search for confirm')
        self.logger.info(f'[AUTOPILOT] Clicking all search hits for: {self.selected_destination}')
        clicked = self._find_and_click_all_text_instances(self.selected_destination)
        if clicked == 0:
            clicked = self._find_and_click_all_text_instances(self.selected_destination_full)
        success = clicked > 0
        if not success:
            self.logger.error('[AUTOPILOT] Could not click destination in search results')
            self._notify_autopilot('Phase 1', 'Failed to click chosen destination row')
            return False
        self._notify_autopilot('Phase 1', f'Clicked {clicked} OCR hit(s): {self.selected_destination}', details='Await Begin')
        time.sleep(1)
        self._clear_search_and_reset()
        self.logger.info("[AUTOPILOT] Clicking 'Begin'")
        for attempt in range(3):
            success, _ = self._find_and_click_text('Begin')
            if success:
                self._notify_autopilot('Phase 1', 'Clicked Begin', details=f'attempt {attempt + 1}/3')
                break
            time.sleep(1)
        else:
            self.logger.error("[AUTOPILOT] 'Begin' button not found")
            self._notify_autopilot('Phase 1', 'Begin not found')
            return False
        self._sleep_if_running(2)
        return True

    def _start_motors(self):
        from AeroHelper.utils.window import bring_roblox_to_front
        bring_roblox_to_front()
        self._sleep_if_running(5)
        self._notify_autopilot('Phase 1', 'Start motors: pre-delay complete', details='5s settle')
        bring_roblox_to_front()
        self.logger.info('[AUTOPILOT] Hold O for 0.75s')
        self.keyboard.hold_o(0.75, lambda: not self.running)
        time.sleep(0.5)
        self._notify_autopilot('Phase 1', 'Held O (ignition)', details='0.75s')
        self.logger.info('[AUTOPILOT] Pressing E')
        self.keyboard.press_e()
        time.sleep(0.5)
        self._notify_autopilot('Phase 1', 'Pressed E', details='Engine engage')
        self.logger.info('[AUTOPILOT] Waiting 30 seconds for engine warmup')
        self._sleep_if_running(30)
        self._notify_autopilot('Phase 1', 'Engine warmup wait complete', details='30s')
        bring_roblox_to_front()
        undock_cycles = self._get_undocking_cycles()
        if undock_cycles > 0:
            self.logger.info('[AUTOPILOT] Shift+40x W for 40%% throttle (safer dock exit)')
            self.keyboard.throttle_40_percent()
            self._notify_autopilot('Phase 1', 'Applied ~40% throttle', details='Shift+W ×40 (undocking airport)')
        else:
            self.logger.info('[AUTOPILOT] No undocking cycles - skipping 40%% throttle (full throttle after Phase 1)')
            self._notify_autopilot('Phase 1', 'Skipping 40% throttle', details='No undocking; full throttle next')

    def _begin_post_phase1_navigation(self):
        from AeroHelper.utils.window import bring_roblox_to_front
        self._undocking_status_sent = False
        self.undocking_cycles = 0
        cycles = self._get_undocking_cycles()
        if cycles > 0:
            self.autopilot_phase = self.UNDOCKING
            self.logger.info(f'[AUTOPILOT] Undocking enabled for {self.current_airport}: {cycles} cycles')
        else:
            self.autopilot_phase = self.AUTOSTEER
            self.logger.info(f'[AUTOPILOT] No undocking cycles for {self.current_airport} - applying full throttle then AutoSteer')
            self.logger.info('[AUTOPILOT] Holding W for 10 seconds (full throttle)')
            bring_roblox_to_front()
            self.keyboard.hold_w(10, lambda: not self.running)
            self._notify_autopilot('Phase 1', 'Full throttle applied', details='No undocking; hold_w(10)')
        self.first_loop = False

    def _phase1_error_recovery(self, reason='Phase 1 failed'):
        self.logger.info('[AUTOPILOT] Error recovery: OCR + Click Back + Restart job search')
        self._notify_autopilot('Phase 1', 'Error recovery started', details=f'Back + retry job flow ({reason})')
        screenshot_path, _text, _ = self._take_screenshot_and_ocr()
        if screenshot_path:
            delete_screenshot(screenshot_path)

        back_clicked = self._click_back_button()
        if back_clicked:
            self.logger.info("[AUTOPILOT] Clicked 'Back' - retrying job search")
            self._sleep_if_running(2)
        else:
            self.logger.info("[AUTOPILOT] No safe Back button (or already on lobby) - retrying Play → Jobs")
        if self._job_search():
            route_data = self._evaluate_routes()
            if route_data and self._select_best_route(route_data):
                if self._verify_mission_game_state_after_begin():
                    self._start_motors()
                    self._begin_post_phase1_navigation()
                    return {'action': 'continue'}
                self.logger.warning('[AUTOPILOT] Error recovery: mission HUD not confirmed after Begin')
                self._notify_autopilot('Phase 1', 'Begin did not start mission during recovery', details='Mission HUD not detected after Begin')
        self.logger.error('[AUTOPILOT] Error recovery failed')
        return self._phase1_give_up(reason)

    def _execute_undocking(self):
        total_undocking_cycles = self._get_undocking_cycles()
        if total_undocking_cycles <= 0:
            self.logger.info('[AUTOPILOT] Undocking cycles=0 - skipping to AutoSteer')
            self.autopilot_phase = self.AUTOSTEER
            return {'action': 'continue'}
        self.logger.info('[AUTOPILOT] ===== UNDOCKING - Thrust away, steer to EXIT_BEARING =====')
        current_undocking_cycle = self.undocking_cycles + 1
        self._notify_autopilot('Undocking', 'Leaving harbor', details=f'Undocking cycle {current_undocking_cycle}/{total_undocking_cycles}; exit bearing or DEST per airport table')
        exit_bearing = self._get_exit_bearing()
        if exit_bearing is not None:
            self.override_target_bearing = exit_bearing
            self.override_icao_code = 'UNDOCK'
            self.undocking_steering_multiplier = 2
            self.logger.info(f'[AUTOPILOT] Undocking: Target EXIT_BEARING={exit_bearing}°')
        else:
            self.override_target_bearing = None
            self.override_icao_code = None
            self.logger.info('[AUTOPILOT] No EXIT_BEARING - using DEST target bearing from OCR')
        result = super().execute_cycle()
        if result is None:
            return None
        action = result.get('action')
        if action == 'pause' and result.get('reason') == 'Return to Lobby detected':
            self.override_target_bearing = None
            self.override_icao_code = None
            self.undocking_steering_multiplier = 1.0
            self.undocking_cycles = 0
            self._undocking_status_sent = False
            self._reset_icao_filter()
            self.autopilot_phase = self.PHASE_1
            return {'action': 'continue'}
        if action != 'continue':
            return result
        self.undocking_cycles += 1
        if self.undocking_cycles >= total_undocking_cycles:
            self.logger.info('[AUTOPILOT] Clear of harbor zone - resuming normal navigation')
            self.override_target_bearing = None
            self.override_icao_code = None
            self.undocking_steering_multiplier = 1.0
            self.undocking_cycles = 0
            self._undocking_status_sent = False
            self.autopilot_phase = self.AUTOSTEER
            self._notify_autopilot('Undocking', 'Undocked - harbor clear', details=f'Completed {total_undocking_cycles}/{total_undocking_cycles} undocking cycles')
            self.logger.info('[AUTOPILOT] Holding W for 10 seconds (full throttle)')
            self.keyboard.hold_w(10, lambda: not self.running)
        return {'action': 'continue'}

    def _extract_destination_from_text(self, text):
        if not text or not isinstance(text, str):
            return None
        patterns = [re.compile('transport\\s+to\\s+(.+?)(?:\\.|$)', re.IGNORECASE), re.compile('transport\\s+your\\s+vehicle\\s+to\\s+(.+?)\\s+safely', re.IGNORECASE), re.compile('transport\\s+your\\s+vehicle\\s+to\\s+(.+?)\\s+safeley', re.IGNORECASE), re.compile('transport\\s+your\\s+vehicle\\s+to\\s+(.+?)(?:\\.|$)', re.IGNORECASE)]
        extracted = None
        for pat in patterns:
            m = pat.search(text)
            if m:
                extracted = m.group(1).strip()
                extracted = re.sub('\\bairport\\b', '', extracted, flags=re.IGNORECASE).strip()
                extracted = re.sub('\\s+', ' ', extracted).strip()
                if extracted:
                    break
        if not extracted:
            return None
        extracted_norm = extracted.lower()
        for key in DOCK_BEARINGS:
            key_norm = key.lower()
            full_name = SUPPORTED_AIRPORTS.get(key, {}).get('full_name', '')
            full_norm = full_name.lower()
            if extracted_norm == key_norm or extracted_norm == full_norm:
                return key
            if key_norm in extracted_norm or full_norm in extracted_norm:
                return key
        return None

    def _try_detect_destination_mid_mission(self):
        screenshot_path, text, _ = self._take_screenshot_and_ocr()
        if screenshot_path:
            delete_screenshot(screenshot_path)
        dest_key = self._extract_destination_from_text(text)
        return dest_key

    def _resolved_destination_key(self):
        if self.selected_destination:
            k = str(self.selected_destination).strip()
            if k in DOCK_BEARINGS:
                return k
            kl = k.lower()
            for key in DOCK_BEARINGS:
                if key.lower() == kl:
                    return key
        if self.selected_destination_full:
            full = str(self.selected_destination_full).strip().lower()
            for key in DOCK_BEARINGS:
                if key.lower() == full:
                    return key
                meta = SUPPORTED_AIRPORTS.get(key) or {}
                fn = meta.get('full_name', '')
                if not fn:
                    continue
                fnl = fn.lower()
                if full == fnl or full.startswith(fnl) or fnl in full:
                    return key
        return None

    def _coerce_table_bearing(self, val):
        if val is None or val == 'none':
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    def _get_dock_bearing(self):
        key = self._resolved_destination_key()
        if not key:
            return None
        return self._coerce_table_bearing(DOCK_BEARINGS[key].get('dock'))

    def _get_exit_bearing(self):
        if self.current_airport and self.current_airport in DOCK_BEARINGS:
            return self._coerce_table_bearing(DOCK_BEARINGS[self.current_airport].get('exit'))
        return None

    def _get_undocking_cycles(self):
        if self.current_airport and self.current_airport in DOCK_BEARINGS:
            val = DOCK_BEARINGS[self.current_airport].get('cycles')
            if val is not None:
                try:
                    return max(0, int(val))
                except (TypeError, ValueError):
                    return 0
        return 0

    def _execute_docking_alignment(self):
        dock_bearing = self._get_dock_bearing()
        distance_sm = self.distance_ewma.value
        heading_sm = self.heading_ewma.value
        if dock_bearing is None:
            self.logger.warning('[AUTOPILOT] No DOCK_BEARING for destination, using OCR target')
            self.override_target_bearing = None
            self.override_icao_code = None
            self.override_heading = heading_sm
        else:
            self._dock_fallback_warning_sent = False
            self.override_target_bearing = dock_bearing
            self.override_icao_code = 'DOCK'
            self.override_heading = heading_sm
        prev_distance = self.previous_distance
        result = super().execute_cycle()
        if result is None:
            return None
        action = result.get('action')
        if action == 'pause' and result.get('reason') == 'Return to Lobby detected':
            self.override_target_bearing = None
            self.override_icao_code = None
            self.override_heading = None
            self._approach_entry_bearing = None
            self._distance_growing_count = 0
            self.heading_ewma.reset()
            self.distance_ewma.reset()
            self._reset_icao_filter()
            self.autopilot_phase = self.PHASE_1
            return {'action': 'continue'}
        if action == 'continue':
            data = result.get('data')
            pause_result = self._check_distance_growing(data, prev_distance)
            if pause_result:
                return pause_result
        if action != 'continue':
            return result
        data = result.get('data')
        if data:
            if data.distance is not None:
                distance_sm = self.distance_ewma.update(data.distance)
            else:
                distance_sm = self.distance_ewma.update(self._read_distance())
            if data.heading is not None:
                self.heading_ewma.update(data.heading)
        else:
            distance_sm = self.distance_ewma.update(self._read_distance())
        eff = self._dock_distance_raw_or_smoothed(data, distance_sm)
        if eff is not None:
            if not self._dock_throttle_50_done and eff <= 3.0:
                self.keyboard.shift_s_taps(50)
                self._dock_throttle_50_done = True
                self.logger.info('[AUTOPILOT] Distance ≤ 3nm - Shift+S ×50 throttle reduction')
                self._notify_autopilot('Docking', 'Throttle reduction at ≤3nm (Shift+S ×50)', details=f'distance_nm≈{eff}')
            if not self._dock_throttle_30_done and eff <= 1.5:
                self.keyboard.shift_s_taps(20)
                self._dock_throttle_30_done = True
                self.logger.info('[AUTOPILOT] Distance ≤ 1.5nm - Shift+S ×20 throttle reduction')
                self._notify_autopilot('Docking', 'Throttle reduction at ≤1.5nm (Shift+S ×20)', details=f'distance_nm≈{eff}')
        thr = self.FINAL_APPROACH_NM_PER_MULT * self.multiplier
        if eff is not None and eff <= thr:
            self.override_target_bearing = None
            self.override_icao_code = None
            self.override_heading = None
            self._approach_entry_bearing = None
            self._phase2_consecutive_under = 0
            self.autopilot_phase = self.PHASE_2
            self.logger.info(f'[AUTOPILOT] Distance ≤ {thr}nm - transitioning to Final Dock')
            self._notify_autopilot('Docking', f'Final approach - distance ≤ {thr}nm (multiplier)', details=f'distance_nm≈{eff}')
            return {'action': 'continue'}
        return result

    def _execute_phase_2(self):
        self.logger.info('[AUTOPILOT] ===== FINAL DOCK CHECK =====')
        self._notify_autopilot('Final Dock', 'Stopping and waiting (Z + 30s)')
        try:
            while True:
                if not self.running:
                    return {'action': 'continue'}
                self.logger.info('[AUTOPILOT] Final dock: Z then 30s wait')
                self.keyboard.press_z()
                self._sleep_if_running(30)
                if not self.running:
                    return {'action': 'continue'}
                for attempt in range(5):
                    if not self.running:
                        return {'action': 'continue'}
                    insp = self._inspect_phase2_dock_ready()
                    path = insp['path']
                    color = insp['color']
                    if color == 'white':
                        branch_msg = 'no transport prompt - completing'
                    elif color == 'red':
                        branch_msg = 'transport prompt visible - push+Z'
                    else:
                        branch_msg = 'OCR unclear - cautious push'
                    self._notify_autopilot('Final Dock', f'Attempt {attempt + 1}/5: {branch_msg}', screenshot_path=path)
                    if color == 'white':
                        self.logger.info('[AUTOPILOT] No transport prompt - double-click End Sail (single OCR pass)')
                        self._click_end_sail(repeat=2, inter_click=0.12)
                        time.sleep(0.35)
                        self._notify_autopilot('Final Dock', 'Dock ready - mission completing')
                        self._mission_complete()
                        self.heading_ewma.reset()
                        self.distance_ewma.reset()
                        self._reset_icao_filter()
                        self.autopilot_phase = self.PHASE_1
                        self.override_target_bearing = None
                        return {'action': 'continue'}
                    if color != 'white':
                        distance = self._read_distance()
                        if distance is None or distance > 0.1:
                            self.logger.info(f'[AUTOPILOT] Not ready (state=Transport Prompt Visible, dist={distance}) - W 15s, wait {10 * self.multiplier:.0f}s, Z')
                            self.keyboard.hold_w(15, lambda: not self.running)
                            if not self.running:
                                return {'action': 'continue'}
                            self._sleep_if_running(10 * self.multiplier)
                            if not self.running:
                                return {'action': 'continue'}
                            self.keyboard.press_z()
                if not self._phase2_long_z_retry_consumed:
                    self._phase2_long_z_retry_consumed = True
                    return self._restart_docking_approach(
                        'Phase 2 failed 5 attempts; rerunning dock alignment through final approach',
                    )
                self.logger.warning('[AUTOPILOT] Final dock failed after dock-approach retry - pausing')
                self._notify_autopilot('Final Dock', 'Docking failed after second round - manual intervention required', ping=True, embed_color=16711680)
                self.override_target_bearing = None
                return {'action': 'pause', 'reason': 'Final dock failed after dock-approach retry - manual intervention required', 'stop_automation': True}
        except Exception as e:
            import traceback
            self.logger.error(f'[AUTOPILOT] Final Dock exception: {str(e)}')
            self.logger.error_detailed('[AUTOPILOT] Final Dock traceback', traceback.format_exc())
            self._notify_autopilot('Final Dock', f'Error: {str(e)}', ping=True, embed_color=16711680)
            return {'action': 'pause', 'reason': f'Final Dock error: {str(e)}', 'stop_automation': True}
        finally:
            self.override_target_bearing = None

    def _click_end_sail_fallback(self, repeat, inter_click):
        success, _ = self._find_and_click_text('End Sail')
        if not success:
            self._find_and_click_text('End')
            self._find_and_click_text('End')
            time.sleep(0.1)
            self._find_and_click_text('End')
            time.sleep(0.5)
            self._find_and_click_text('End')
            return
        for _ in range(1, repeat):
            time.sleep(inter_click)
            self._find_and_click_text('End Sail')

    def _click_end_sail(self, repeat=1, inter_click=0.12):
        screenshot_path = None
        try:
            screenshot_path = capture_primary_screen()
            if not screenshot_path or not os.path.exists(screenshot_path):
                self._click_end_sail_fallback(repeat, inter_click)
                return
            matches = []
            for phrase in ('End Sail', 'Confirm End Sail', 'End sail'):
                matches = self.ocr.find_text_boxes(screenshot_path, phrase, match_mode='contains')
                if matches:
                    break
            if not matches:
                delete_screenshot(screenshot_path)
                screenshot_path = None
                self._click_end_sail_fallback(repeat, inter_click)
                return
            best = max(matches, key=lambda m: m['center'][1])
            cx, cy = best['center']
            click_x, click_y = self._screen_center_to_click_coords(cx, cy, screenshot_path)
            self.logger.info(f"[AUTOPILOT] End Sail ×{repeat} at ({click_x}, {click_y}) (matched '{best['text']}')")
            for i in range(repeat):
                self.mouse.click(click_x, click_y, smooth=True)
                if i + 1 < repeat:
                    time.sleep(inter_click)
        finally:
            if screenshot_path and os.path.exists(screenshot_path):
                delete_screenshot(screenshot_path)

    def _mission_complete(self):
        self.mission_count += 1
        self.logger.info(f'[AUTOPILOT] Mission #{self.mission_count} complete! Destination: {self.selected_destination_full}, WP: {self.selected_wp}, Money: {self.selected_money}')
        if self.history_callback:
            try:
                self.history_callback({'event': 'Mission Complete', 'mode': 'AutoPilot', 'result': 'Completed', 'details': {'mission': self.mission_count, 'destination': self.selected_destination_full, 'destination_key': self.selected_destination, 'wp': self.selected_wp, 'money': self.selected_money}})
            except Exception as e:
                self.logger.warning(f'[HISTORY] Failed to record mission complete: {e}')
        self.notifier.send_mission_complete(self.selected_destination_full, wp=self.selected_wp, money=self.selected_money, mission_number=self.mission_count)
