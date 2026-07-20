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

import time
import threading
from datetime import datetime, timezone
from PyQt5.QtCore import QMetaObject, QObject, Qt, Q_ARG, pyqtSignal
from pynput.keyboard import Key
from AeroHelper.state import AutomationState
from AeroHelper.config import Config
from AeroHelper.logger import Logger
from AeroHelper.automation.monitoring import MonitoringMode
from AeroHelper.automation.autosteer import AutoSteerMode
from AeroHelper.automation.autopilot import AutoPilotMode
from AeroHelper.automation.reconnect import ReconnectHandler
from AeroHelper.input.detector import HumanInterventionDetector
from AeroHelper.input.keyboard import Keyboard
from AeroHelper.utils.display import validate_display_mode
from AeroHelper.utils.platform import IS_MACOS, get_macos_permission_summary, macos_input_monitoring_ready, macos_screen_capture_ready
from AeroHelper.utils.roblox_check import is_roblox_running
from AeroHelper.utils.window import bring_roblox_to_front, is_roblox_f11_fullscreen
from AeroHelper.utils.screenshot import capture_primary_screen, delete_screenshot
from AeroHelper.notifications.discord import DiscordNotifier
from AeroHelper.utils.process_guard import stop_blocked_services, terminate_blocked_processes
from AeroHelper.startup_log import log_startup_banner
from AeroHelper.version import APP_VERSION

LOG_TAIL_BYTES = 25 * 1024

def _condense_ocr_snapshot(text, max_len=350):
    compact = ' '.join((text or '').split())
    if len(compact) <= max_len:
        return compact
    cut = compact[:max_len].rsplit(' ', 1)[0]
    return f'{cut}…'

def _sanitize_log_tail_for_datashare(log_tail):
    if not log_tail:
        return log_tail
    lines = log_tail.splitlines()
    out = []
    last_ocr = None
    for line in lines:
        marker = 'OCR Raw Text:'
        if marker in line:
            idx = line.find(marker)
            last_ocr = line[idx + len(marker):].strip()
            continue
        out.append(line)
    if last_ocr:
        out.append(f'OCR snapshot: {_condense_ocr_snapshot(last_ocr)}')
    return '\n'.join(out)

class _MainThreadBridge(QObject):
    invoke_blocking = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.invoke_blocking.connect(self._run_callable, Qt.BlockingQueuedConnection)

    def _run_callable(self, fn):
        fn()

class Controller:

    def __init__(self, main_window, status_overlay, app_version=None, startup_countdown=None):
        self.main_window = main_window
        self.status_overlay = status_overlay
        self.startup_countdown = startup_countdown
        self.app_version = app_version
        self.config = Config()
        self.logger = Logger()
        self.state = AutomationState.STOPPED
        self.automation_mode = None
        self.automation_thread = None
        self.running = False
        self.paused = False
        self.human_detector = HumanInterventionDetector(logger=self.logger)
        self.keyboard = Keyboard(logger=self.logger)
        self._main_thread_bridge = _MainThreadBridge()
        self.reconnect_handler = ReconnectHandler(self.config.get_webhook_url(), self.logger, self.human_detector, include_screenshots=self.config.get_include_screenshots(), keyboard=self.keyboard)
        self.retry_countdown = 10
        self.intervention_monitor_thread = None
        self.intervention_monitoring = False
        self.countdown_thread = None
        self.countdown_running = False
        self.consecutive_error_count = 0
        self._last_datashare_time = 0.0
        self._start_cancelled = False
        self._pending_startup_webhook = None
        self._startup_grace_remaining = 0
        self._roblox_focus_ok = True
        self._session_started_at = None
        self._session_started_wall = None
        self._session_mode = None
        self._session_cycle_count = 0
        self._last_cycle_data = None
        self._history_recorded = False
        self.main_window.start_requested.connect(self.start)
        self.main_window.stop_requested.connect(self.stop)
        log_startup_banner(
            self.logger,
            app_version or APP_VERSION,
            extra={
                'webhook': 'configured' if self.config.get_webhook_url() else 'missing',
                'share_data_with_developer': self.config.get_share_data_with_developer(),
            },
        )
        self.main_window.test_webhook_requested.connect(self.test_webhook)
        self.main_window.share_data_override_requested.connect(self.share_data_override)

    def _startup_cancelled(self):
        return self._start_cancelled or not self.main_window.is_running

    def _current_cycle_interval(self):
        if self.automation_mode is not None:
            return getattr(self.automation_mode, 'cycle_interval', self.config.get_cycle_interval())
        if self.config.get_mode() == 'AutoPilot':
            return 15
        return self.config.get_cycle_interval()

    def _sleep_with_running_check(self, seconds):
        remaining = seconds
        while remaining > 0 and self.running:
            sleep_time = min(1, remaining)
            time.sleep(sleep_time)
            remaining -= sleep_time

    def _run_startup_countdown(self, seconds=10):
        overlay = self.startup_countdown
        if overlay is None:
            self._sleep_with_running_check(seconds)
            return bool(self.running and not self._startup_cancelled())
        done = threading.Event()

        def _on_finished():
            done.set()

        def _begin():
            try:
                overlay.finished.disconnect(_on_finished)
            except (TypeError, RuntimeError):
                pass
            overlay.finished.connect(_on_finished)
            overlay.begin(int(seconds))

        self._run_on_main_thread(_begin)
        while not done.wait(timeout=0.2):
            if not self.running or self._startup_cancelled():
                # Queued only - never block the worker on the GUI thread (avoids deadlock with stop())
                try:
                    QMetaObject.invokeMethod(overlay, 'cancel', Qt.QueuedConnection)
                except Exception:
                    pass
                done.wait(timeout=1.5)
                return False
        return bool(self.running and not self._startup_cancelled())

    def _hide_startup_countdown(self):
        overlay = self.startup_countdown
        if overlay is None:
            return
        try:
            if threading.current_thread() is threading.main_thread():
                overlay.cancel()
            else:
                QMetaObject.invokeMethod(overlay, 'cancel', Qt.QueuedConnection)
        except Exception:
            pass

    def _update_status_overlay(self, state):
        try:
            self.status_overlay.update_state_signal.emit(state)
        except Exception:
            self.status_overlay.update_state(state)

    def _set_paused_ui_state(self, paused):
        try:
            self.main_window.set_paused_state_signal.emit(paused)
        except Exception:
            QMetaObject.invokeMethod(self.main_window, 'set_paused_state', Qt.QueuedConnection, Q_ARG(bool, paused))

    def _emit_main_status(self, status_type, message, diagnostics=None):
        diagnostics = diagnostics or {}
        try:
            self.status_overlay.update_details_signal.emit(self.config.get_mode(), diagnostics)
        except Exception:
            try:
                self.status_overlay.update_details(self.config.get_mode(), diagnostics)
            except Exception:
                pass
        try:
            self.main_window.update_status_signal.emit(status_type, message, diagnostics)
        except Exception:
            try:
                self.main_window.update_status_panel(status_type, message, diagnostics)
            except Exception:
                pass

    def _autopilot_phase_label(self):
        phase = getattr(self.automation_mode, 'autopilot_phase', None)
        labels = {'phase_1': 'Phase 1 - route setup', 'undocking': 'Undocking', 'autosteer': 'AutoSteering', 'docking_alignment': 'Docking alignment', 'phase_2': 'Final dock'}
        return labels.get(phase, phase)

    def _build_diagnostics(self, data=None):
        diagnostics = {}
        mode = self.config.get_mode()
        if mode == 'AutoPilot':
            phase = self._autopilot_phase_label()
            if phase:
                diagnostics['Phase'] = phase
        if self.automation_mode is not None:
            ocr = getattr(self.automation_mode, 'ocr', None)
            confidence = getattr(ocr, 'last_confidence', None)
            regions = getattr(ocr, 'last_region_count', 0)
            if confidence is not None:
                diagnostics['OCR confidence'] = f'{confidence * 100:.1f}% ({regions} regions)'
            elif regions:
                diagnostics['OCR confidence'] = f'Unknown ({regions} regions)'
        if data is not None:
            diagnostics['Speed'] = f'{data.speed} kt' if data.speed is not None else 'N/A'
            diagnostics['Distance'] = f'{data.distance} nm' if data.distance is not None else 'N/A'
            diagnostics['Heading'] = f'{data.heading}°' if data.heading is not None else 'N/A'
            target_bearing = getattr(self.automation_mode, 'override_target_bearing', None)
            target_code = getattr(self.automation_mode, 'override_icao_code', None)
            if target_bearing is None:
                target_bearing = data.target_bearing
            if target_code is None:
                target_code = data.icao_code
            diagnostics['Target'] = f'{int(round(target_bearing))}° ({target_code})' if target_bearing is not None else 'N/A'
        return diagnostics

    def _flight_data_details(self, data):
        if data is None:
            return {}
        target_bearing = getattr(self.automation_mode, 'override_target_bearing', None)
        target_code = getattr(self.automation_mode, 'override_icao_code', None)
        if target_bearing is None:
            target_bearing = data.target_bearing
        if target_code is None:
            target_code = data.icao_code
        return {'speed': data.speed, 'distance': data.distance, 'heading': data.heading, 'target_bearing': target_bearing, 'target': target_code, 'fuel': data.fuel, 'throttle': data.throttle}

    def _build_datashare_flight_context(self):
        ctx = self._flight_data_details(self._last_cycle_data)
        ctx['mode'] = self.config.get_mode()
        phase = self._autopilot_phase_label()
        if phase:
            ctx['phase'] = phase
        ocr = getattr(getattr(self, 'automation_mode', None), 'ocr', None)
        if ocr is not None:
            confidence = getattr(ocr, 'last_confidence', None)
            regions = getattr(ocr, 'last_region_count', 0)
            if confidence is not None:
                ctx['ocr_confidence'] = round(confidence * 100, 1)
            if regions:
                ctx['ocr_regions'] = regions
        ship = getattr(getattr(self, 'automation_mode', None), 'last_ship_status', None)
        if isinstance(ship, dict):
            for key in ('heading_diff', 'steer_direction', 'steer_duration_s', 'model_h0_s', 'multiplier'):
                value = ship.get(key)
                if value is not None:
                    ctx[key] = value
        return {key: value for key, value in ctx.items() if value is not None}

    def _format_ship_status_line(self):
        ship = getattr(getattr(self, 'automation_mode', None), 'last_ship_status', None)
        if isinstance(ship, dict):
            parts = []
            if ship.get('distance_nm') is not None:
                parts.append(f"{ship['distance_nm']} nm")
            if ship.get('speed_kt') is not None:
                parts.append(f"{ship['speed_kt']} kt")
            if ship.get('heading') is not None:
                parts.append(f"HDG {ship['heading']}°")
            if ship.get('target_bearing') is not None:
                code = ship.get('target') or 'DEST'
                parts.append(f"Target {int(round(ship['target_bearing']))}° ({code})")
            if ship.get('heading_diff') is not None:
                parts.append(f"Diff {ship['heading_diff']}°")
            if ship.get('throttle_pct') is not None:
                parts.append(f"Throttle {ship['throttle_pct']}%")
            if ship.get('fuel_pct') is not None:
                parts.append(f"Fuel {ship['fuel_pct']}%")
            if ship.get('steer_direction') and ship.get('steer_duration_s') is not None:
                steer = f"Steer {ship['steer_direction']} {ship['steer_duration_s']}s"
                if ship.get('model_h0_s') is not None:
                    steer += f" (H₀ {ship['model_h0_s']}s)"
                parts.append(steer)
            if ship.get('multiplier') is not None:
                parts.append(f"×{ship['multiplier']}")
            if parts:
                return ' · '.join(parts)
        data = self._last_cycle_data
        if data is None:
            return None
        details = self._flight_data_details(data)
        parts = []
        if details.get('distance') is not None:
            parts.append(f"{details['distance']} nm")
        if details.get('speed') is not None:
            parts.append(f"{details['speed']} kt")
        if details.get('heading') is not None:
            parts.append(f"HDG {details['heading']}°")
        if details.get('target_bearing') is not None:
            code = details.get('target') or 'DEST'
            parts.append(f"Target {int(round(details['target_bearing']))}° ({code})")
        if details.get('throttle') is not None:
            parts.append(f"Throttle {details['throttle']}%")
        return ' · '.join(parts) if parts else None

    def _system_datashare(self, reason):
        self._post_datashare(reason)

    def _start_history_session(self, mode):
        self._session_started_at = time.perf_counter()
        self._session_started_wall = datetime.now().isoformat(timespec='seconds')
        self._session_mode = mode
        self._session_cycle_count = 0
        self._last_cycle_data = None
        self._history_recorded = False

    def add_history_entry(self, entry):
        payload = dict(entry or {})
        payload.setdefault('timestamp', datetime.now().isoformat(timespec='seconds'))
        payload.setdefault('version', self.app_version or 'unknown')
        try:
            self.config.add_history_entry(payload)
        except Exception as e:
            self.logger.warning(f'[HISTORY] Failed to save history entry: {e}')

    def _record_session_history(self, result, reason=None):
        if self._history_recorded or self._session_started_at is None:
            return
        duration = time.perf_counter() - self._session_started_at
        details = self._flight_data_details(self._last_cycle_data)
        phase = self._autopilot_phase_label()
        if phase:
            details['phase'] = phase
        self.add_history_entry({'event': 'Session', 'mode': self._session_mode or self.config.get_mode(), 'result': result, 'reason': reason or '', 'started_at': self._session_started_wall, 'ended_at': datetime.now().isoformat(timespec='seconds'), 'duration_sec': round(duration, 1), 'cycles': self._session_cycle_count, 'details': details})
        self._history_recorded = True

    def _check_blocked_processes(self):
        svc_names = self.config.get_blocked_services()
        if svc_names:
            svc_results = stop_blocked_services(svc_names, logger=self.logger)
            stopped_svcs = [item['name'] for item in svc_results if item['status'] == 'stopped']
            denied_svcs = [item['name'] for item in svc_results if item['status'] == 'access_denied']
            if stopped_svcs:
                self._emit_main_status('warning', f"Stopped blocked service(s): {', '.join(stopped_svcs)}", self._build_diagnostics(self._last_cycle_data))
            if denied_svcs:
                self._emit_main_status('warning', f"Admin needed to stop service(s): {', '.join(denied_svcs)}", self._build_diagnostics(self._last_cycle_data))
        names = self.config.get_blocked_executables()
        if not names:
            return
        results = terminate_blocked_processes(names, logger=self.logger)
        terminated = [item['name'] for item in results if item['status'] == 'terminated']
        denied = [item['name'] for item in results if item['status'] == 'access_denied']
        if terminated:
            self._emit_main_status('warning', f"Closed blocked process: {', '.join(terminated)}", self._build_diagnostics(self._last_cycle_data))
        if denied:
            self._emit_main_status('warning', f"Admin needed to close: {', '.join(denied)}", self._build_diagnostics(self._last_cycle_data))

    def _automation_status_message(self):
        mode = self.config.get_mode()
        if mode == 'AutoPilot':
            phase = self._autopilot_phase_label()
            if phase:
                return phase
        if mode == 'AutoSteer':
            return 'AutoSteering'
        if mode == 'Monitoring':
            return 'Monitoring'
        return 'Running'

    def _reset_start_ui(self, state):
        self.state = state
        self._update_status_overlay(state)
        self.main_window.is_running = False
        self.main_window.start_button.show()
        self.main_window.stop_button.hide()
        self.main_window.unlock_fields()
        if state != AutomationState.ERROR:
            self._emit_main_status('info', state.value)

    def _abort_start(self, title, message):
        self.running = False
        self._hide_startup_countdown()
        self.state = AutomationState.ERROR
        self._update_status_overlay(self.state)
        self.logger.error_detailed(title, message)
        self._system_datashare(f'{title}: {message[:200]}')
        self.main_window.show_error_signal.emit(title, message, '')
        self.main_window.is_running = False
        QMetaObject.invokeMethod(self.main_window, 'show_start_button', Qt.QueuedConnection, Q_ARG(bool, True))

    def _run_on_main_thread(self, fn):
        if threading.current_thread() is threading.main_thread():
            return fn()
        self._main_thread_bridge.invoke_blocking.emit(fn)

    def _create_automation_mode(self):
        mode_str = self.config.get_mode()
        cycle_interval = 15 if mode_str == 'AutoPilot' else self.config.get_cycle_interval()
        multiplier = self.config.get_multiplier()
        webhook_url = self.config.get_webhook_url()
        notification_mode = self.config.get_notification_mode()
        include_screenshots = self.config.get_include_screenshots()
        shared_keyboard = self.keyboard
        throttle_up = self.config.get_throttle_up_if_not_100()
        if mode_str == 'Monitoring':
            custom_waypoint = self.config.get_monitoring_custom_waypoint()
            skip_current_bearing = self.config.get_monitoring_skip_current_bearing()
            return (MonitoringMode(cycle_interval, webhook_url, self.logger, self.human_detector, notification_mode, custom_waypoint=custom_waypoint, include_screenshots=include_screenshots, keyboard=shared_keyboard, skip_current_bearing=skip_current_bearing, throttle_up_if_not_100=throttle_up), mode_str, cycle_interval, multiplier, notification_mode, webhook_url, include_screenshots, custom_waypoint)
        if mode_str == 'AutoSteer':
            custom_waypoint = self.config.get_autosteer_custom_waypoint()
            return (AutoSteerMode(cycle_interval, webhook_url, multiplier, self.logger, self.human_detector, custom_waypoint=custom_waypoint, include_screenshots=include_screenshots, keyboard=shared_keyboard, throttle_up_if_not_100=throttle_up), mode_str, cycle_interval, multiplier, notification_mode, webhook_url, include_screenshots, custom_waypoint)
        if mode_str == 'AutoPilot':
            start_mid_mission = self.config.get_start_mid_mission()
            return (AutoPilotMode(cycle_interval, webhook_url, multiplier, self.logger, self.human_detector, start_mid_mission=start_mid_mission, include_screenshots=include_screenshots, history_callback=self.add_history_entry, keyboard=shared_keyboard, throttle_up_if_not_100=throttle_up), mode_str, cycle_interval, multiplier, notification_mode, webhook_url, include_screenshots, None)
        raise ValueError(f'Unknown mode: {mode_str}')

    def _log_session_start(self, mode_str, cycle_interval, multiplier, notification_mode, webhook_url, include_screenshots, custom_waypoint=None):
        wh = 'configured' if (webhook_url or '').strip() else 'not configured'
        lines = ['[SESSION] ========================================', f"[SESSION] Version: {self.app_version or 'unknown'}", f'[SESSION] Mode: {mode_str}', f'[SESSION] Cycle interval: {cycle_interval}s', f'[SESSION] Multiplier: {multiplier}', f'[SESSION] Notification mode: {notification_mode}', f'[SESSION] Include screenshots: {include_screenshots}', f'[SESSION] Quit after 5 errors: {self.config.get_quit_after_5_errors()}', f'[SESSION] Throttle up if not 100%: {self.config.get_throttle_up_if_not_100()}', f'[SESSION] Webhook: {wh}']
        if mode_str == 'AutoPilot':
            lines.insert(4, f'[SESSION] Start mid-mission: {self.config.get_start_mid_mission()}')
        if mode_str in ('Monitoring', 'AutoSteer'):
            lines.insert(4, f'[SESSION] Custom waypoint: {bool(custom_waypoint)}')
        if mode_str == 'Monitoring':
            lines.insert(5, f'[SESSION] Skip current bearing: {self.config.get_monitoring_skip_current_bearing()}')
        lines.append('[SESSION] Automation begins after focus and countdown.')
        lines.append('[SESSION] ========================================')
        for line in lines:
            self.logger.info(line)

    def test_webhook(self):

        def run_test():
            webhook_url = self.config.get_webhook_url()
            mode = self.config.get_mode()
            self.logger.info('[WEBHOOK] Manual test requested')
            ok = DiscordNotifier(webhook_url, logger=self.logger).send_test_webhook(app_version=self.app_version, mode=mode)
            if ok:
                self._emit_main_status('ok', 'Test webhook sent', self._build_diagnostics())
            else:
                self._emit_main_status('error', 'Test webhook failed', self._build_diagnostics())
        threading.Thread(target=run_test, daemon=True).start()

    def start(self):
        roblox_running, roblox_info = is_roblox_running()
        if not roblox_running:
            error_msg = 'Roblox is not running'
            full = f'{error_msg}\n\nAeroHelper requires Roblox to be running and Aeronautica to be loaded. Please start Roblox and load into a mission before starting AeroHelper.'
            self.logger.error_detailed(error_msg, f'Roblox check failed. Info: {roblox_info}')
            self._system_datashare(error_msg)
            self.main_window.show_error('Roblox Not Running', full, '')
            self._reset_start_ui(AutomationState.ERROR)
            return
        try:
            validate_display_mode()
        except ValueError as e:
            error_msg = 'Display mode validation failed'
            full = f"{error_msg}\n\n{str(e)}\n\nTo fix this:\n1. Right-click on your desktop\n2. Select 'Display settings'\n3. Under 'Multiple displays', select 'Duplicate these displays'\n4. Do NOT use 'Extend these displays'"
            self.logger.error_detailed(error_msg, f'Display validation error: {str(e)}')
            self._system_datashare(error_msg)
            self.main_window.show_error('Invalid Display Mode', full, '')
            self._reset_start_ui(AutomationState.ERROR)
            return
        self.logger.info('Starting AeroHelper')
        self._start_cancelled = False
        if IS_MACOS:
            macos_input_monitoring_ready(self.logger)
            macos_screen_capture_ready(self.logger)
            missing = get_macos_permission_summary()
            if missing:
                self._emit_main_status('warning', 'macOS permissions needed\n\n' + '\n\n'.join(missing) + '\n\nAutomation can still run after you grant permissions and restart.')
        self.state = AutomationState.STARTING
        self._update_status_overlay(self.state)
        self._emit_main_status('info', 'Starting...')
        try:
            self.logger.info('[STARTUP] Creating automation mode on main thread')
            created = self._create_automation_mode()
            self.automation_mode = created[0]
            self._start_mode_meta = created[1:]
        except ValueError as e:
            self._abort_start('Unknown Mode', f'{e}\n\nSelect Monitoring, AutoSteer, or AutoPilot and try again.')
            return
        except Exception as e:
            import traceback
            self.logger.error_detailed('Failed to create automation mode', traceback.format_exc())
            self._abort_start('Startup Failed', f'AeroHelper could not initialize automation.\n\nError: {e}\n\nOn macOS, grant Accessibility in System Settings if this keeps failing.')
            return
        threading.Thread(target=self._start_automation_worker, daemon=True, name='AeroHelper-Start').start()

    def _start_automation_worker(self):
        try:
            self._start_automation_worker_impl()
        except Exception as e:
            import traceback
            self.logger.error_detailed('Startup failed unexpectedly', traceback.format_exc())
            self._abort_start('Startup Failed', f'AeroHelper could not start automation.\n\nError: {e}\n\nCheck AeroHelper.log for details. On macOS, grant Accessibility, Input Monitoring, and Screen Recording in System Settings if startup keeps failing.')

    def _start_automation_worker_impl(self):
        mode_str, cycle_interval, multiplier, notification_mode, webhook_url, include_screenshots, custom_waypoint = self._start_mode_meta
        self.consecutive_error_count = 0
        self.reconnect_handler.include_screenshots = include_screenshots
        log_config = {'mode': mode_str, 'cycle_interval': cycle_interval, 'multiplier': multiplier, 'notification_mode': notification_mode, 'webhook_url': webhook_url + '...' if webhook_url and len(webhook_url) > 50 else webhook_url or '(empty)'}
        if mode_str == 'AutoPilot':
            log_config['start_mid_mission'] = self.config.get_start_mid_mission()
        if mode_str in ('Monitoring', 'AutoSteer'):
            log_config['custom_waypoint'] = custom_waypoint
        if mode_str == 'Monitoring':
            log_config['skip_current_bearing'] = self.config.get_monitoring_skip_current_bearing()
        self.logger.info(f'[STARTUP] Config: {log_config}')
        self._log_session_start(mode_str, cycle_interval, multiplier, notification_mode, webhook_url, include_screenshots, custom_waypoint=custom_waypoint if mode_str in ('Monitoring', 'AutoSteer') else None)
        notification_label = 'All' if str(notification_mode).lower() == 'all' else 'Urgent Only'
        webhook_config = {'Version': self.app_version or 'unknown', 'Mode': mode_str, 'Cycle Delay': f'{cycle_interval}s', 'Multiplier': str(multiplier), 'Notifications': notification_label}
        if mode_str == 'AutoPilot':
            webhook_config['Start Mid-Mission'] = 'Yes' if self.config.get_start_mid_mission() else 'No'
        if mode_str in ('Monitoring', 'AutoSteer'):
            webhook_config['Custom Waypoint'] = 'Yes' if custom_waypoint else 'No'
        if mode_str == 'Monitoring':
            webhook_config['Skip Current Bearing'] = 'Yes' if self.config.get_monitoring_skip_current_bearing() else 'No'
        webhook_config['Quit After 5 Errors'] = 'Yes' if self.config.get_quit_after_5_errors() else 'No'
        webhook_config['Throttle Up If Not 100%'] = 'Yes' if self.config.get_throttle_up_if_not_100() else 'No'
        webhook_config['Include Screenshots'] = 'Yes' if include_screenshots else 'No'
        self._pending_startup_webhook = (webhook_config, include_screenshots)
        if self._startup_cancelled():
            self.logger.info('[STARTUP] Start cancelled before session begin')
            return
        self.running = True
        self.paused = False
        self._startup_grace_remaining = 5 if IS_MACOS else 2
        self._start_history_session(mode_str)
        needs_f11 = not is_roblox_f11_fullscreen()
        focus_ok = bring_roblox_to_front()
        self._roblox_focus_ok = focus_ok
        if focus_ok:
            self.logger.info('Brought Roblox window to front')
            time.sleep(0.3)
            if needs_f11:
                self.logger.info('Roblox not F11 fullscreen, pressing F11')
                self.keyboard.press(Key.f11)
                self.keyboard.release(Key.f11)
                time.sleep(0.5)
            else:
                self.logger.info('Roblox already F11 fullscreen')
        else:
            self.logger.warning('Failed to bring Roblox window to front')
            if IS_MACOS:
                self._emit_main_status('warning', 'Could not focus Roblox automatically.\n\nClick the Roblox window now so AeroHelper can read the screen and send keystrokes.', self._build_diagnostics())
        if self._pending_startup_webhook:
            wh_conf, inc_shot = self._pending_startup_webhook
            self._pending_startup_webhook = None
            startup_path = None
            if inc_shot:
                startup_path = capture_primary_screen()
            try:
                mode_label = wh_conf.get('Mode', 'AeroHelper')
                desc = f'{mode_label} is now running. Current session settings:'
                self.automation_mode.notifier.send_startup_config(wh_conf, screenshot_path=startup_path, description=desc)
            finally:
                if startup_path:
                    delete_screenshot(startup_path)
        self.logger.info('[STARTUP] Session webhook complete - preparing automation threads')
        try:
            self.logger.info('[STARTUP] Minimizing main window')
            QMetaObject.invokeMethod(self.main_window, 'showMinimized', Qt.QueuedConnection)
        except Exception as e:
            self.logger.warning(f'[STARTUP] Could not minimize main window: {e}')
        try:
            self.logger.info('[STARTUP] Initializing human intervention detector')
            self.human_detector.start()
            if IS_MACOS:
                self._emit_main_status('warning', 'macOS: human-intervention pause is disabled.\n\nUse Stop in AeroHelper to end automation. Keyboard listening is skipped on macOS for stability.', self._build_diagnostics())
        except Exception as e:
            import traceback
            self.logger.error_detailed('[STARTUP] Human intervention detector failed', traceback.format_exc())
        self.logger.info('[STARTUP] Human intervention detector initialized')
        self.logger.info('[STARTUP] Starting intervention monitor')
        self._start_intervention_monitoring()
        self.logger.info('[STARTUP] Locking UI fields')
        self.main_window.lock_fields_signal.emit()

        def delayed_start():
            countdown_secs = 10
            if IS_MACOS and not self._roblox_focus_ok:
                self.logger.info('[STARTUP] Roblox focus failed on macOS - click Roblox during the countdown if needed')
            self.logger.info(f'[STARTUP] Startup countdown overlay ({countdown_secs}s)')
            try:
                self.human_detector.suspend()
            except Exception:
                pass
            completed = self._run_startup_countdown(countdown_secs)
            try:
                self.human_detector.unsuspend()
            except Exception:
                pass
            while self.running and self.paused:
                time.sleep(0.1)
            if not completed or not self.running or self._startup_cancelled():
                self.logger.info('[STARTUP] Start cancelled during countdown')
                self._hide_startup_countdown()
                return
            if self.running:
                self.logger.info('[STARTUP] Countdown complete - starting automation loop')
                self.state = AutomationState.RUNNING
                self._update_status_overlay(self.state)
                self._emit_main_status('ok', self._automation_status_message(), self._build_diagnostics())
                self.automation_mode.start()
                self._run_automation_loop()
        self.automation_thread = threading.Thread(target=delayed_start, daemon=True)
        self.automation_thread.start()
        grace_desc = f'{5 if IS_MACOS else 2} invalid-state grace retries'
        self.logger.info(f'[STARTUP] Automation thread scheduled ({grace_desc})')

    def _start_intervention_monitoring(self):
        self.intervention_monitoring = True

        def monitor_loop():
            last_listener_check = 0.0
            while self.intervention_monitoring and self.running:
                now = time.time()
                if now - last_listener_check >= 5.0:
                    self.human_detector.ensure_listener_running()
                    last_listener_check = now
                if self.human_detector.check_intervention():
                    self.logger.info(f'Intervention detected - current state: {self.state}, paused: {self.paused}')
                    if self.state != AutomationState.PAUSED_HUMAN:
                        self.logger.info('Calling _handle_human_intervention()')
                        self._handle_human_intervention()
                    else:
                        self.logger.info('Already in PAUSED_HUMAN state - resetting countdown')
                        self.retry_countdown = 10
                        if self.countdown_running:
                            self.logger.info('Human input detected while paused - resetting countdown to 10 seconds')
                        else:
                            self._start_retry_countdown()
                time.sleep(0.1)
        self.intervention_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.intervention_monitor_thread.start()
        self.logger.info('Started dedicated human intervention monitoring thread (checks every 0.1 seconds)')

    def stop(self, clear_error=True):
        try:
            self.logger.info('Stopping automation...')
            self._start_cancelled = True
            self.running = False
            self.paused = False
            self.intervention_monitoring = False
            self.countdown_running = False
            self.retry_countdown = 0
            self.main_window.is_running = False
            self._hide_startup_countdown()
            self.state = AutomationState.STOPPED
            try:
                self.keyboard.release_all()
            except Exception as e:
                self.logger.error(f'Error releasing keyboard keys: {e}')
            if self.automation_mode:
                try:
                    self.automation_mode.stop()
                except Exception as e:
                    self.logger.error(f'Error stopping automation mode: {e}')
            try:
                self.human_detector.unsuspend()
            except Exception:
                pass
            try:
                self.human_detector.stop()
            except Exception as e:
                self.logger.error(f'Error stopping human detector: {e}')
            self._update_status_overlay(self.state)
            if clear_error:
                self._emit_main_status('info', 'Stopped')
                self._record_session_history('Stopped', 'User stopped automation')
            try:
                self.main_window.unlock_fields_signal.emit()
                QMetaObject.invokeMethod(self.main_window, 'show_start_button', Qt.QueuedConnection, Q_ARG(bool, clear_error))
                QMetaObject.invokeMethod(self.main_window, 'showNormal', Qt.QueuedConnection)
            except Exception as e:
                self.logger.error(f'Error updating UI: {e}')
            self.logger.info('Automation stopped successfully')
        except Exception as e:
            import traceback
            self.logger.error(f'Error in stop method: {e}')
            self.logger.error_detailed('Stop method error', traceback.format_exc())

    def _run_automation_loop(self):
        while self.running:
            cycle_interval = self._current_cycle_interval()
            if self.paused:
                time.sleep(1.0)
                continue
            try:
                self._check_blocked_processes()
                result = self.automation_mode.execute_cycle()
                if not self.running:
                    return
                if result is None:
                    self._sleep_with_running_check(cycle_interval)
                    continue
                action = result.get('action')
                data = result.get('data')
                self._session_cycle_count += 1
                if data is not None:
                    self._last_cycle_data = data
                if action == 'pause':
                    reason = result.get('reason', 'Unknown reason')
                    details = result.get('details', '')
                    self.logger.warning(f'Cycle pause: {reason}')
                    if result.get('stop_automation'):
                        self._handle_pause_with_error(reason, details)
                        return
                    if reason == 'Invalid game state' and self._startup_grace_remaining > 0:
                        self._startup_grace_remaining -= 1
                        remaining = self._startup_grace_remaining
                        mode = self.config.get_mode()
                        if mode == 'AutoPilot':
                            grace_hint = 'Join Aeronautica. AutoPilot: be on the server main/lobby screen (or mid-mission if already flying). Keep Roblox visible.'
                            status_hint = 'Join Aeronautica. For AutoPilot use the server main/lobby screen (or mid-mission if already flying).'
                        else:
                            grace_hint = 'Join Aeronautica and be mid-mission with HUD visible. Keep Roblox focused (not another game / overlay).'
                            status_hint = 'Join Aeronautica and be mid-mission with the HUD visible.'
                        self.logger.warning(f'[STARTUP GRACE] Invalid game state - retrying in 5s ({remaining} retr{"y" if remaining == 1 else "ies"} left). {grace_hint}')
                        self._emit_main_status('warning', f'Waiting for game state... ({remaining} retr{"y" if remaining == 1 else "ies"} left)\n\n{status_hint}', self._build_diagnostics())
                        self._sleep_with_running_check(5)
                        continue
                    self.consecutive_error_count += 1
                    if self.config.get_quit_after_5_errors():
                        if self.consecutive_error_count >= 5:
                            self._handle_5_consecutive_errors(reason)
                            return
                        self.logger.warning(f'[AUTOMATION] Consecutive issue {self.consecutive_error_count}/5 (quit after 5 enabled) - retrying after {cycle_interval}s')
                        self._sleep_with_running_check(cycle_interval)
                        continue
                    self._handle_pause_with_error(reason, details)
                    return
                elif action == 'reconnect':
                    self._emit_main_status('warning', 'Reconnecting', self._build_diagnostics(result.get('data')))
                    self._handle_reconnect()
                elif action == 'error':
                    error = result.get('error', 'Unknown error')
                    self._emit_main_status('error', f'Error: {error}', self._build_diagnostics(result.get('data')))
                    self.logger.error(f'Error in automation: {error}')
                    self.consecutive_error_count += 1
                    if self.config.get_quit_after_5_errors():
                        if self.consecutive_error_count >= 5:
                            self._handle_5_consecutive_errors(error)
                            return
                        self.logger.warning(f'[AUTOMATION] Consecutive issue {self.consecutive_error_count}/5 (quit after 5 enabled) - retrying after {cycle_interval}s')
                        self._sleep_with_running_check(cycle_interval)
                        continue
                    self._handle_error_with_ui(error)
                    return
                elif action == 'continue':
                    self.consecutive_error_count = 0
                    self._startup_grace_remaining = 0
                    self._emit_main_status('ok', self._automation_status_message(), self._build_diagnostics(result.get('data')))
            except Exception as e:
                self.logger.error(f'Exception in automation loop: {e}')
                if self.config.get_quit_after_5_errors():
                    self.consecutive_error_count += 1
                    if self.consecutive_error_count >= 5:
                        self._handle_5_consecutive_errors(str(e))
                        return
                    self.logger.warning(f'[AUTOMATION] Consecutive issue {self.consecutive_error_count}/5 (quit after 5 enabled) - retrying after {cycle_interval}s')
                    self._sleep_with_running_check(cycle_interval)
                    continue
                self._system_datashare(str(e))
            self._sleep_with_running_check(cycle_interval)

    def _post_datashare(self, error_summary, *, manual_override=False, on_complete=None):
        if not manual_override:
            if not self.config.get_share_data_with_developer():
                return
            now = time.time()
            if now - self._last_datashare_time < 300:
                return
            self._last_datashare_time = now

        def _send():
            success = False
            try:
                import json as _json
                import platform
                import sys
                from AeroHelper.utils.platform import get_os_display_name
                log_path = self.logger.log_file
                log_tail = ''
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                        f.seek(0, 2)
                        size = f.tell()
                        start = max(0, size - LOG_TAIL_BYTES)
                        f.seek(start)
                        if start > 0:
                            f.readline()
                        log_tail = f.read()
                except Exception:
                    pass
                log_tail = _sanitize_log_tail_for_datashare(log_tail)
                flight_context = self._build_datashare_flight_context()
                ship_status = self._format_ship_status_line()
                if manual_override:
                    meta = {'manual_override': True, 'trigger': 'Share Data Override button'}
                else:
                    meta = {'error': error_summary[:256]}
                body = {'webhook_url': self.config.get_webhook_url() or '', 'log_tail': log_tail, 'flight_context': flight_context, 'client_time': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'), 'app_version': self.app_version or '', 'os': platform.system(), 'os_release': get_os_display_name(), 'machine': platform.machine(), 'frozen': getattr(sys, 'frozen', False), 'metadata': meta}
                if ship_status:
                    body['ship_status'] = ship_status
                payload = _json.dumps(body).encode()
                from AeroHelper.device_client import post_api
                post_api('/api/datashare', _json.loads(payload.decode('utf-8')), config=self.config, app_version=self.app_version, logger=self.logger)
                self.logger.info('[DATASHARE] Sent to developer API successfully')
                success = True
            except Exception as exc:
                from AeroHelper.device_client import ApiRequestError, log_api_failure, user_api_notice
                if not isinstance(exc, ApiRequestError):
                    log_api_failure('/api/datashare', exc, logger=self.logger, webhook_url=self.config.get_webhook_url())
                severity, title, message = user_api_notice(exc, '/api/datashare')
                self._emit_main_status(severity if severity == 'error' else 'warning', f'{title}\n{message}', None)
            if on_complete:
                on_complete(success)
        threading.Thread(target=_send, daemon=True).start()

    def share_data_override(self):
        if not (self.config.get_webhook_url() or '').strip():
            self._emit_main_status('warning', 'Share Data Override: set your Discord webhook URL first.', None)
            self.logger.warning('[DATASHARE] Override blocked: no WEBHOOK_URL')
            self.main_window.share_data_override_done_signal.emit(False)
            return
        self.logger.info('[DATASHARE] Manual Share Data Override send requested')

        def _on_complete(success):
            if success:
                self._emit_main_status('ok', 'Success! Diagnostic data sent to the developer.', None)
            self.main_window.share_data_override_done_signal.emit(success)

        self._post_datashare('', manual_override=True, on_complete=_on_complete)

    def _handle_human_intervention(self):
        self.logger.info('Human intervention detected - pausing automation')
        self.paused = True
        self.state = AutomationState.PAUSED_HUMAN
        self._update_status_overlay(self.state)
        self._emit_main_status('warning', 'Paused - human input', self._build_diagnostics())
        self._set_paused_ui_state(True)
        self.retry_countdown = 10
        self._start_retry_countdown()

    def _start_retry_countdown(self):
        if self.countdown_running:
            return
        self.countdown_running = True

        def countdown():
            while self.retry_countdown > 0 and self.paused and self.running and (self.state == AutomationState.PAUSED_HUMAN):
                if self.human_detector.check_intervention():
                    self.retry_countdown = 10
                    self.logger.info('Human input detected during countdown - resetting to 10 seconds')
                else:
                    self.retry_countdown -= 1
                    if self.retry_countdown > 0:
                        self.logger.info(f'Resume countdown: {self.retry_countdown} seconds')
                time.sleep(1)
            if self.retry_countdown == 0 and self.paused and self.running and (self.state == AutomationState.PAUSED_HUMAN):
                self.logger.info('Resume countdown finished - resuming automation')
                self.paused = False
                self.state = AutomationState.RUNNING
                self._update_status_overlay(self.state)
                self._emit_main_status('ok', self._automation_status_message(), self._build_diagnostics())
                self._set_paused_ui_state(False)
            self.countdown_running = False
        self.countdown_thread = threading.Thread(target=countdown, daemon=True)
        self.countdown_thread.start()

    def _handle_pause_with_error(self, reason, details=''):
        self.paused = True
        self.state = AutomationState.PAUSED
        self._update_status_overlay(self.state)
        self._emit_main_status('warning', f'Paused: {reason}', self._build_diagnostics())
        self._record_session_history('Paused', reason)
        error_title = 'Automation Stopped'
        error_message = f'Automation has been paused: {reason}'
        if reason == 'Invalid game state':
            error_title = 'Invalid Game State Detected'
            error_message = self._invalid_game_state_help_text()
        elif isinstance(reason, str) and reason.startswith('Phase 1 failed'):
            error_title = 'AutoPilot Phase 1 Failed'
            extra = (details or '').strip()
            error_message = (
                'AutoPilot could not finish spawning / job selection.\n\n'
                f'Reason: {reason}'
                + (f'\nDetails: {extra}' if extra else '')
                + '\n\nPlease:\n'
                '1. Join the Aeronautica Roblox game\n'
                '2. Be on the server main/lobby screen\n'
                '3. Close Discord overlay and any modals (Special Naming, etc.)\n'
                '4. Keep Roblox focused, then restart AutoPilot'
            )
        elif reason == 'Return to Lobby detected':
            error_title = 'Return to Lobby Detected'
            error_message = (
                "AeroHelper detected the 'Return to Lobby' button on screen.\n\n"
                'Monitoring / AutoSteer need an active mission. Please:\n'
                '1. Join the Aeronautica Roblox game\n'
                '2. Start a mission and wait until you are mid-mission\n'
                '3. Then resume AeroHelper\n\n'
                'For AutoPilot, start from the server main/lobby screen instead.'
            )
        elif reason == 'Distance threshold reached':
            error_title = 'Destination Approaching'
            error_message = (
                'AeroHelper has stopped near the destination.\n\n'
                'The remaining distance reached the safety threshold.\n'
                'Please manually dock the vehicle.\n'
                'You can resume after docking or start a new mission / AutoPilot from the lobby.'
            )
        elif reason == 'Vehicle going away - stopped after 10 cycles':
            error_title = 'Vehicle Going Away'
            error_message = (
                'AeroHelper detected the vehicle moving away from the destination for 10 consecutive cycles.\n\n'
                'The vehicle has been stopped (Z pressed).\n\n'
                'This usually means:\n'
                '• Heading is wrong or steering did not apply\n'
                '• Roblox lost focus / keys did not reach the game\n'
                '• You may be routing around land\n\n'
                'Correct heading (or return to lobby and restart AutoPilot), then resume.'
            )
        elif reason == 'Final dock failed after long-Z retry - manual intervention required' or (isinstance(reason, str) and reason.startswith('Final Dock error')):
            error_title = 'AutoPilot - Final Dock Failed'
            error_message = (
                'Docking did not complete after the full retry sequence. Manual docking is required.\n\n'
                'AeroHelper stopped after two final-dock rounds (including long Z hold).\n'
                'Dock manually, then start a new mission or restart AutoPilot from the server main/lobby screen.'
            )
        elif isinstance(reason, str) and reason.startswith('Waypoint detected:'):
            waypoint_code = reason.replace('Waypoint detected: ', '').strip()
            error_title = 'Waypoint Detected'
            error_message = (
                f"AeroHelper detected a waypoint ({waypoint_code}) instead of the final destination (DEST).\n\n"
                'AeroHelper can only steer when the ICAO code shows DEST.\n\n'
                'Wait until the waypoint is passed and DEST appears, then resume.\n'
                'Keep Roblox focused in Aeronautica with the mission HUD visible.'
            )
        else:
            extra = (details or '').strip()
            if extra:
                error_message = f'Automation has been paused: {reason}\n\n{extra}\n\nJoin Aeronautica, keep Roblox visible, then restart AeroHelper.'
            else:
                error_message = (
                    f'Automation has been paused: {reason}\n\n'
                    'Join the Aeronautica Roblox game, keep the window visible and focused, then restart AeroHelper.'
                )
        self._system_datashare(reason)
        try:
            self.automation_mode.notifier.send_quit(reason)
        except Exception as e:
            self.logger.error(f'Failed to send quit webhook: {e}')
        self.main_window.show_error_signal.emit(error_title, error_message, '')
        self.main_window.is_running = False
        QMetaObject.invokeMethod(self.main_window, 'show_start_button', Qt.QueuedConnection, Q_ARG(bool, False))
        self.stop(clear_error=False)

    def _invalid_game_state_help_text(self):
        mode = self.config.get_mode()
        if mode == 'AutoPilot':
            return (
                'AeroHelper could not read valid Aeronautica data from the screen.\n\n'
                'Please:\n'
                '1. Join the Aeronautica Roblox game (not another experience)\n'
                '2. Be on the server main/lobby screen to start AutoPilot\n'
                '   (or mid-mission with HUD visible if already flying)\n'
                '3. Keep Roblox visible and focused - close Discord overlay / other windows\n'
                '4. Use DUPLICATED display mode if on multi-monitor (not EXTEND)'
            )
        return (
            'AeroHelper could not read valid mission data (distance/speed) from the screen.\n\n'
            'Please:\n'
            '1. Join the Aeronautica Roblox game (not another experience)\n'
            '2. Be mid-mission with the HUD showing distance and speed\n'
            '3. Keep Roblox visible and focused - close Discord overlay / other windows\n'
            '4. Use DUPLICATED display mode if on multi-monitor (not EXTEND)'
        )

    def _handle_5_consecutive_errors(self, last_error):
        self.logger.error(f'5 consecutive errors - stopping and sending @everyone to Discord. Last error: {last_error}')
        self._emit_main_status('error', 'Stopped after 5 consecutive errors', self._build_diagnostics())
        self._record_session_history('Error', f'5 consecutive errors: {last_error}')
        self._system_datashare(f'5 consecutive errors: {last_error}')
        help_extra = ''
        ui_body = f'Stopped after 5 consecutive errors.\n\nLast error: {last_error}\n\n'
        if last_error == 'Invalid game state':
            help_extra = '\n\n' + self._invalid_game_state_help_text()
            ui_body += self._invalid_game_state_help_text()
        else:
            ui_body += 'Check Discord / AeroHelper.log for more context. Restart AeroHelper when ready.'
        try:
            self.automation_mode.notifier.send_error(
                f'AeroHelper stopped after 5 consecutive errors. Last error: {last_error}{help_extra}'
            )
        except Exception as e:
            self.logger.error(f'Failed to send 5-errors webhook: {e}')
        self.main_window.show_error_signal.emit('AeroHelper Stopped', ui_body, '')
        self.main_window.is_running = False
        QMetaObject.invokeMethod(self.main_window, 'show_start_button', Qt.QueuedConnection, Q_ARG(bool, False))
        self.stop(clear_error=False)

    def _handle_error_with_ui(self, error):
        self.paused = True
        self.state = AutomationState.ERROR
        self._update_status_overlay(self.state)
        self._emit_main_status('error', f'Automation error: {error}', self._build_diagnostics())
        self._record_session_history('Error', error)
        self._system_datashare(error)
        error_title = 'Automation Error'
        error_message = f'An error occurred during automation.\n\nError: {error}\n\nThis could be due to:\n• Screenshot capture failure\n• OCR processing error\n• System resource issues\n• File permission problems\n\nCheck the AeroHelper.log file for detailed error information.\nTry restarting AeroHelper if the problem persists.'
        try:
            self.automation_mode.notifier.send_quit(error)
        except Exception as e:
            self.logger.error(f'Failed to send quit webhook: {e}')
        self.main_window.show_error_signal.emit(error_title, error_message, '')
        self.main_window.is_running = False
        QMetaObject.invokeMethod(self.main_window, 'show_start_button', Qt.QueuedConnection, Q_ARG(bool, False))
        self.stop(clear_error=False)

    def _handle_reconnect(self):
        self.state = AutomationState.RECONNECTING
        self._update_status_overlay(self.state)
        self._emit_main_status('warning', 'Reconnecting', self._build_diagnostics())
        self.logger.info('Entering reconnection mode')
        success = self.reconnect_handler.execute_reconnect(stop_check=lambda: not self.running)
        if not self.running:
            self.logger.info('Reconnection aborted - automation stopped')
            return
        if success:
            self.logger.info('Reconnection successful - resuming automation')
            self.state = AutomationState.RUNNING
            self._update_status_overlay(self.state)
            self._emit_main_status('ok', self._automation_status_message(), self._build_diagnostics())
            self.paused = False
        else:
            self.logger.error('Reconnection failed - stopping')
            self.paused = True
            self.state = AutomationState.PAUSED
            self._update_status_overlay(self.state)
            self._emit_main_status('error', 'Reconnection failed', self._build_diagnostics())
            self._record_session_history('Error', 'Reconnection failed')
            self._system_datashare('Reconnection failed')
            error_title = 'Reconnection Failed'
            error_message = 'AeroHelper failed to reconnect to the game.\n\nThe reconnection process encountered an error.\n\nPlease manually:\n1. Ensure Roblox is running\n2. Load into Aeronautica\n3. Start a mission\n4. Restart AeroHelper'
            try:
                self.automation_mode.notifier.send_quit('Reconnection failed')
            except Exception as e:
                self.logger.error(f'Failed to send quit webhook: {e}')
            self.main_window.show_error_signal.emit(error_title, error_message, '')
            self.main_window.is_running = False
            QMetaObject.invokeMethod(self.main_window, 'show_start_button', Qt.QueuedConnection, Q_ARG(bool, False))
            self.stop(clear_error=False)
