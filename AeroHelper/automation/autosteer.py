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
Version 4.0.2
'''

import math
import os
import time
from AeroHelper.automation.monitoring import MonitoringMode
from AeroHelper.utils.bearing import shortest_angle_diff_signed
from AeroHelper.utils.screenshot import capture_primary_screen, capture_screen_pil, delete_screenshot
from AeroHelper.utils.window import bring_roblox_to_front
TURN_WMAX_DEG_PER_S = 1
TURN_T_RAMP_S = 5.28
TURN_HOLD_TRIM_S = 0
TURN_HOLD_MIN_S = 0.05
THROTTLE_HOLD_STRENGTH = 0.5
STUCK_HEADING_EPS_DEG = 1.0
STUCK_HEADING_CYCLES = 3
STUCK_HEADING_MIN_DIFF_DEG = 2.0
STOP_DISTANCE_NM = 1.0

class AutoSteerMode(MonitoringMode):

    def __init__(self, cycle_interval, webhook_url, multiplier, logger, human_detector=None, custom_waypoint=False, include_screenshots=False, keyboard=None):
        super().__init__(cycle_interval, webhook_url, logger, human_detector, custom_waypoint=custom_waypoint, include_screenshots=include_screenshots, keyboard=keyboard)
        self.multiplier = multiplier
        self.steering_history = []
        self.oscillation_alert_sent = False
        self.override_target_bearing = None
        self.override_icao_code = None
        self.override_heading = None
        self.requires_dest = False
        self.notification_display_mode = 'AutoSteer'
        self.undocking_steering_multiplier = 1.0
        self._undocking_status_sent = False
        self._heading_stagnation_ref = None
        self._heading_stagnation_cycles = 0
        self.last_ship_status = None

    def _record_ship_status(self, data, target_bearing, heading_for_steer, direction=None, duration=None, diff=None, model_h0=None):
        target_code = self.override_icao_code if self.override_icao_code is not None else data.icao_code
        self.last_ship_status = {
            'heading': data.heading,
            'steer_heading': heading_for_steer,
            'target_bearing': target_bearing,
            'target': target_code,
            'distance_nm': data.distance,
            'speed_kt': data.speed,
            'throttle_pct': data.throttle,
            'fuel_pct': data.fuel,
            'heading_diff': round(diff, 1) if diff is not None else None,
            'steer_direction': direction.upper() if direction else None,
            'steer_duration_s': round(duration, 2) if duration is not None else None,
            'model_h0_s': round(model_h0, 2) if model_h0 is not None else None,
            'multiplier': self.multiplier,
        }

    def _reset_heading_stagnation(self):
        self._heading_stagnation_ref = None
        self._heading_stagnation_cycles = 0

    def _heading_unchanged(self, current, reference):
        if current is None or reference is None:
            return False
        return abs(shortest_angle_diff_signed(current, reference)) <= STUCK_HEADING_EPS_DEG

    def _update_heading_stagnation(self, heading):
        if heading is None:
            self._reset_heading_stagnation()
            return 0
        if self._heading_stagnation_ref is None:
            self._heading_stagnation_ref = heading
            self._heading_stagnation_cycles = 1
        elif self._heading_unchanged(heading, self._heading_stagnation_ref):
            self._heading_stagnation_cycles += 1
        else:
            self._heading_stagnation_ref = heading
            self._heading_stagnation_cycles = 1
        return self._heading_stagnation_cycles

    def _run_input_wake_recovery(self):
        self.logger.warning('[AUTOSTEER] Heading unchanged despite steer commands - input wake recovery (focus Roblox, release keys, tap W)')
        try:
            self.notifier.send_warning(
                getattr(self, 'notification_display_mode', 'AutoSteer'),
                'Steering keys may not be reaching the game; refocusing Roblox and nudging input.',
                ping=False,
            )
        except Exception:
            pass
        if bring_roblox_to_front():
            time.sleep(0.2)
        self.mouse.click_center(smooth=True)
        time.sleep(0.1)
        self.keyboard.release_all()
        time.sleep(0.05)
        self.keyboard.tap('w')
        time.sleep(0.1)
        self._reset_heading_stagnation()

    def _turn_model_hold_seconds(self, theta_deg):
        wmax = TURN_WMAX_DEG_PER_S
        tramp = TURN_T_RAMP_S
        crossover = wmax * tramp
        if theta_deg <= crossover:
            return math.sqrt(theta_deg * tramp / wmax)
        return theta_deg / wmax

    def _throttle_turn_hold_scale(self, throttle_pct):
        if throttle_pct is None or throttle_pct <= 0:
            return 1.0
        return 100.0 / float(throttle_pct)

    def _calculate_steering(self, heading, target_bearing, throttle_pct=None):
        if heading is None or target_bearing is None:
            return (None, None, None, None)
        angle = shortest_angle_diff_signed(target_bearing, heading)
        diff = abs(angle)
        if diff == 0:
            return (None, None, None, None)
        if diff < 1:
            return (None, None, None, None)
        base_h = self._turn_model_hold_seconds(diff)
        raw_tscale = self._throttle_turn_hold_scale(throttle_pct)
        tscale = 1.0 + (raw_tscale - 1.0) * THROTTLE_HOLD_STRENGTH
        scaled_h = base_h * tscale
        duration = scaled_h * self.multiplier - TURN_HOLD_TRIM_S
        duration = max(TURN_HOLD_MIN_S, duration)
        duration *= self.undocking_steering_multiplier
        direction = 'd' if angle > 0 else 'a'
        return (direction, duration, base_h, tscale)

    def _detect_oscillation(self, direction):
        self.steering_history.append(direction)
        if len(self.steering_history) > 6:
            self.steering_history.pop(0)
        if len(self.steering_history) >= 6:
            last_six = self.steering_history[-6:]
            alternations = 0
            for i in range(len(last_six) - 1):
                if last_six[i] != last_six[i + 1]:
                    alternations += 1
            if alternations >= 3:
                return True
        return False

    def execute_cycle(self):
        if not self.running:
            return None
        cycle_start = time.perf_counter()
        screenshot_path = None
        try:
            try:
                screenshot_path = capture_primary_screen()
            except Exception as capture_error:
                self.logger.warning(f'Primary screenshot capture failed, trying PIL fallback: {capture_error}')
                try:
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
            if hasattr(self, '_filter_icao_for_autopilot') and callable(getattr(self, '_filter_icao_for_autopilot')):
                override = self._filter_icao_for_autopilot(data)
                if override is not None:
                    data.icao_code, data.target_bearing = (override[0], override[1])
            log_data = data.to_dict()
            if self.override_target_bearing is not None:
                log_data['target_bearing'] = self.override_target_bearing
            if self.override_icao_code is not None:
                log_data['icao_code'] = self.override_icao_code
            self.logger.log_parsed(log_data)
            if not data.valid:
                self.logger.warning('Invalid data detected - distance (nm/km) or speed (knots/km/h) not found')
                return {'action': 'pause', 'reason': 'Invalid game state'}
            if self.requires_dest and self.override_icao_code is None and (data.icao_code is not None) and (data.icao_code.upper() != 'DEST'):
                self.logger.warning(f'Waypoint detected (ICAO: {data.icao_code}) - AutoPilot requires DEST')
                return {'action': 'pause', 'reason': f'Waypoint detected: {data.icao_code}'}
            if getattr(self, 'notification_display_mode', '') != 'AutoPilot' and data.distance is not None and (data.distance < STOP_DISTANCE_NM):
                self.logger.info(f'[AUTOSTEER] Distance < {STOP_DISTANCE_NM}nm - stopping')
                self.keyboard.press_z()
                return {'action': 'pause', 'reason': 'Distance threshold reached'}
            self.mouse.click_center(smooth=True)
            self.keyboard.tap('5')
            self.keyboard.shift_f10_sequence()
            self._click_chat_close(screenshot_path)
            urgent = self._is_urgent(data)
            autosteer_enabled = True
            mode = getattr(self, 'notification_display_mode', 'AutoSteer')
            if self.override_icao_code == 'UNDOCK':
                if not self._undocking_status_sent:
                    self.logger.debug('[AUTOSTEER] Undocking mode: sending one-time status update')
                    self.notifier.send_undocking_status(data)
                    self._undocking_status_sent = True
                else:
                    self.logger.debug('[AUTOSTEER] Undocking mode: webhook already sent for this sequence')
            elif self.notification_mode.lower() in ('urgent-only', 'urgent'):
                self._undocking_status_sent = False
                if urgent:
                    self.logger.debug('[AUTOSTEER] Urgent-only mode: sending urgent alert')
                    self.notifier.send_urgent_alert(data, self.previous_distance, autosteer_enabled, mode=mode, override_target_bearing=self.override_target_bearing, override_icao_code=self.override_icao_code)
                else:
                    self.logger.debug('[AUTOSTEER] Skipping notification (Urgent-only mode, no urgent condition)')
            else:
                self._undocking_status_sent = False
                self.logger.debug('[AUTOSTEER] All mode: sending status update')
                cycle_duration = time.perf_counter() - cycle_start
                scr = screenshot_path if self.include_screenshots else None
                self.notifier.send_status_update(data, self.previous_distance, screenshot_path=scr, cycle_duration_sec=cycle_duration, mode=mode, override_target_bearing=self.override_target_bearing, override_icao_code=self.override_icao_code, phase=getattr(self, 'autopilot_phase', None), autopilot_multiplier=getattr(self, 'multiplier', None))
                if urgent:
                    self.logger.debug('[AUTOSTEER] All mode: sending urgent alert')
                    self.notifier.send_urgent_alert(data, self.previous_distance, autosteer_enabled, mode=mode, override_target_bearing=self.override_target_bearing, override_icao_code=self.override_icao_code)
            self.previous_distance = data.distance
            target_bearing = self.override_target_bearing if self.override_target_bearing is not None else data.target_bearing
            if data.heading is not None:
                heading_for_steer = data.heading
            else:
                heading_for_steer = self.override_heading
            direction, duration, model_h0, tscale = self._calculate_steering(heading_for_steer, target_bearing, data.throttle)
            if direction and duration is not None:
                diff = abs(shortest_angle_diff_signed(target_bearing, heading_for_steer)) if heading_for_steer is not None else 0.0
                stagnation_cycles = self._update_heading_stagnation(heading_for_steer)
                if diff >= STUCK_HEADING_MIN_DIFF_DEG and stagnation_cycles >= STUCK_HEADING_CYCLES:
                    self._run_input_wake_recovery()
                self._record_ship_status(data, target_bearing, heading_for_steer, direction=direction, duration=duration, diff=diff, model_h0=model_h0)
                tp = data.throttle if data.throttle is not None else 'n/a'
                self.logger.info(f'[AUTOSTEER] Steering correction: {direction.upper()} for {duration:.2f}s (HDG={data.heading}°, steer_HDG={heading_for_steer}°, Target={target_bearing}°, Diff={diff:.1f}°, model H₀={model_h0:.2f}s, throttle={tp}%, hold_scale={tscale:.3f}, ω_max={TURN_WMAX_DEG_PER_S}, T_ramp={TURN_T_RAMP_S}, multiplier={self.multiplier}, trim={TURN_HOLD_TRIM_S}s)')
                if self._detect_oscillation(direction):
                    if not self.oscillation_alert_sent:
                        self.logger.warning('[AUTOSTEER] Oscillation detected! Vehicle is alternating left/right')
                        self.notifier.send_oscillation_alert(data, self.multiplier)
                        self.oscillation_alert_sent = True
                else:
                    self.oscillation_alert_sent = False
                if self.override_icao_code != 'UNDOCK':
                    self.notifier.send_steering_correction(data, direction, duration, diff, override_target_bearing=self.override_target_bearing, override_icao_code=self.override_icao_code, mode=mode)
                stop_check = lambda: not self.running
                self.keyboard.release_all()
                if direction == 'd':
                    self.keyboard.hold_d(duration, stop_check)
                else:
                    self.keyboard.hold_a(duration, stop_check)
            else:
                self._reset_heading_stagnation()
                self.steering_history.clear()
                self.oscillation_alert_sent = False
                if heading_for_steer is not None and target_bearing is not None:
                    diff = abs(shortest_angle_diff_signed(target_bearing, heading_for_steer))
                    self._record_ship_status(data, target_bearing, heading_for_steer, diff=diff)
                    if diff == 0:
                        self.logger.debug(f'[AUTOSTEER] No steering needed (HDG={heading_for_steer}° matches target={target_bearing}°)')
                    elif diff < 1:
                        self.logger.debug(f'[AUTOSTEER] No steering needed (diff={diff}° < 1°, too small)')
                else:
                    self._record_ship_status(data, target_bearing, heading_for_steer)
            cycle_duration = time.perf_counter() - cycle_start
            self.logger.debug(f'[AUTOSTEER] Cycle completed in {cycle_duration:.2f}s')
            return {'action': 'continue', 'data': data}
        except Exception as e:
            import traceback
            error_msg = f'Error in automation cycle: {str(e)}'
            self.logger.error_detailed(error_msg, f'Full traceback:\n{traceback.format_exc()}')
            return {'action': 'error', 'error': str(e)}
        finally:
            if screenshot_path:
                try:
                    delete_screenshot(screenshot_path)
                except Exception as cleanup_error:
                    self.logger.warning(f'Failed to delete screenshot {screenshot_path}: {cleanup_error}')
