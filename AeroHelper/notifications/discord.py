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

import base64
import io
import json
import os
import requests
from datetime import datetime, timezone
from AeroHelper.utils.eta import calculate_arrival_time
from pathlib import Path
REQUEST_EXCEPTIONS = (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException)
COLOR_INFO = 7252222
COLOR_SUCCESS = 7915420
COLOR_WARNING = 14264415
COLOR_ERROR = 15035247

class DiscordNotifier:

    def __init__(self, webhook_url=None, logger=None, app_version=None):
        self.webhook_url = webhook_url
        self.logger = logger
        if app_version is None:
            from AeroHelper.version import APP_VERSION
            app_version = APP_VERSION
        self.app_version = (app_version or '').strip() or None

    def _footer_text(self, extra=None):
        parts = []
        if extra:
            text = str(extra).strip()
            if text:
                parts.append(text)
        if self.app_version:
            parts.append(f'AeroHelper v{self.app_version}')
        return ' · '.join(parts) if parts else None

    def _has_screenshot(self, screenshot_path):
        return bool(screenshot_path) and os.path.exists(screenshot_path)

    def _post_payload(self, payload, screenshot_path=None, timeout=10, missing_screenshot_warning=None):
        has_screenshot = self._has_screenshot(screenshot_path)
        if has_screenshot:
            payload = dict(payload)
            payload['attachments'] = [{'id': 0, 'filename': 'screenshot.png'}]
            with open(screenshot_path, 'rb') as screenshot_file:
                multipart = {'payload_json': (None, json.dumps(payload), 'application/json'), 'files[0]': ('screenshot.png', screenshot_file, 'image/png')}
                return requests.post(self.webhook_url, files=multipart, timeout=timeout)
        if screenshot_path and self.logger and missing_screenshot_warning:
            self.logger.warning(missing_screenshot_warning)
        return requests.post(self.webhook_url, json=payload, timeout=timeout)

    def _log_webhook_result(self, success_message, failure_message, response):
        if response.status_code in (200, 204):
            if self.logger:
                self.logger.info(success_message)
            return True
        if self.logger:
            self.logger.error(failure_message.format(status=response.status_code, response=response.text))
        return False

    def _field(self, name, value, inline=True):
        return {'name': name, 'value': value, 'inline': inline}

    def _embed(self, title, color, description=None, fields=None, footer_text=None):
        embed = {'title': title, 'color': color, 'timestamp': datetime.now(timezone.utc).isoformat()}
        if description:
            embed['description'] = description
        if fields:
            embed['fields'] = fields
        footer = self._footer_text(footer_text)
        if footer:
            embed['footer'] = {'text': footer[:2048]}
        return embed

    def _webhook_avatar_data_uri(self, icon_path, size=128, scale=0.62):
        try:
            from PIL import Image
        except ImportError:
            return None
        try:
            raw = icon_path.read_text(encoding='utf-8').strip()
        except OSError:
            return None
        if ',' in raw and raw.startswith('data:image/'):
            raw = raw.split(',', 1)[1]
        try:
            image_bytes = base64.b64decode(raw)
        except ValueError:
            return None
        try:
            source = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
        except OSError:
            return None
        inner = max(1, int(size * scale))
        resized = source.resize((inner, inner), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        offset = (size - inner) // 2
        canvas.paste(resized, (offset, offset), resized)
        out = io.BytesIO()
        canvas.save(out, format='PNG')
        encoded = base64.b64encode(out.getvalue()).decode('ascii')
        return f'data:image/png;base64,{encoded}'

    def set_webhook_branding(self):
        if not self.webhook_url:
            return
        try:
            icon_path = Path(__file__).resolve().parent.parent / 'icon.txt'
            if not icon_path.exists():
                return
            avatar_data = self._webhook_avatar_data_uri(icon_path)
            if not avatar_data:
                avatar_data = icon_path.read_text(encoding='utf-8').strip()
            response = requests.patch(self.webhook_url, json={'name': 'AeroHelper', 'avatar': avatar_data}, timeout=10)
            if self.logger:
                if response.status_code == 200:
                    self.logger.info('[WEBHOOK] Webhook branding updated (name + avatar)')
                else:
                    self.logger.warning(f'[WEBHOOK] Webhook branding failed: {response.status_code}')
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping webhook branding: {e}')
        except Exception as e:
            if self.logger:
                self.logger.warning(f'[WEBHOOK] Webhook branding error: {e}')

    def send_startup_config(self, config_dict, screenshot_path=None, description=None):
        if not self.webhook_url:
            return
        try:
            fields = [self._field(k, str(v)) for k, v in config_dict.items()]
            desc = description or 'Session started. Current settings are below.'
            has_screenshot = self._has_screenshot(screenshot_path)
            embed = self._embed('AeroHelper Session Started', COLOR_INFO, description=desc, fields=fields)
            if has_screenshot:
                embed['image'] = {'url': 'attachment://screenshot.png'}
            payload = {'content': '', 'embeds': [embed]}
            response = self._post_payload(payload, screenshot_path=screenshot_path, timeout=15 if has_screenshot else 10, missing_screenshot_warning=f'[WEBHOOK] Startup screenshot missing: {screenshot_path}')
            self._log_webhook_result('[WEBHOOK] Session start notification sent', '[WEBHOOK] Session start failed: {status}', response)
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping session start: {str(e)}')
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Session start error: {str(e)}')

    def send_test_webhook(self, app_version=None, mode=None):
        if not self.webhook_url:
            if self.logger:
                self.logger.warning('[WEBHOOK] Test skipped: Discord webhook URL is empty')
            return False
        try:
            fields = [self._field('Version', app_version or 'unknown')]
            embed = self._embed('AeroHelper Webhook Test', COLOR_SUCCESS, description='Webhook is configured correctly. Automation was not started.', fields=fields)
            payload = {'content': '', 'embeds': [embed]}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return self._log_webhook_result('[WEBHOOK] Test webhook sent successfully', '[WEBHOOK] Test webhook failed (status: {status}, response: {response})', response)
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - test webhook failed: {str(e)}')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Test webhook error: {str(e)}')
            return False

    def _is_urgent(self, data, previous_distance=None):
        if data.heading is not None and data.target_bearing is not None:
            diff = abs(data.heading - data.target_bearing)
            if diff >= 5:
                return True
        if data.fuel is not None and data.fuel < 10:
            return True
        if data.throttle is not None and data.throttle == 0:
            return True
        if previous_distance is not None and data.distance is not None:
            if abs(data.distance - previous_distance) < 0.01:
                return True
        return False

    def send_status_update(self, data, previous_distance=None, screenshot_path=None, cycle_duration_sec=None, mode=None, override_target_bearing=None, override_icao_code=None, phase=None, autopilot_multiplier=None):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug('Discord webhook URL not configured - skipping status update')
            return
        try:
            target_bearing = override_target_bearing if override_target_bearing is not None else data.target_bearing
            arrival_time, hours = calculate_arrival_time(data.distance, data.speed, mode=mode, phase=phase, override_icao_code=override_icao_code, autopilot_multiplier=autopilot_multiplier, heading=data.heading, target_bearing=target_bearing, throttle=data.throttle)
            if arrival_time is not None:
                ts = int(arrival_time.timestamp())
                time_remaining_str = f'<t:{ts}:R>'
                arrival_str = f'<t:{ts}:t>'
            else:
                time_remaining_str = 'Unknown'
                arrival_str = 'Unknown'
            icao_code = override_icao_code if override_icao_code is not None else data.icao_code
            target_str = f'{int(round(target_bearing))}°' if target_bearing is not None else 'N/A'
            spd = f'{data.speed}kt' if data.speed is not None else 'N/A'
            log_msg = f'[WEBHOOK] Sending STATUS UPDATE: Speed={spd}, Throttle={data.throttle}%, Fuel={data.fuel}%, Distance={data.distance}nm, HDG={data.heading}°, Target={target_str} ({icao_code}), ETA={arrival_str}, TimeRemaining={time_remaining_str}'
            if screenshot_path:
                log_msg += f' (with screenshot: {screenshot_path})'
            if self.logger:
                self.logger.info(log_msg)
            title = f'AeroHelper {mode} Status' if mode else 'AeroHelper Status'
            has_screenshot = self._has_screenshot(screenshot_path)
            embed = self._embed(title, COLOR_INFO, fields=[self._field('Speed', f'{data.speed} Knots' if data.speed is not None else 'N/A'), self._field('Throttle', f'{data.throttle}%' if data.throttle is not None else 'N/A'), self._field('Fuel', f'{data.fuel}%' if data.fuel is not None else 'N/A'), self._field('Distance', f'{data.distance} nm' if data.distance is not None else 'N/A'), self._field('Heading', f'{data.heading}°' if data.heading is not None else 'N/A'), self._field('Target', f'{int(round(target_bearing))}° ({icao_code})' if target_bearing is not None else 'N/A'), self._field('ETA', arrival_str), self._field('Time Left', time_remaining_str)])
            if cycle_duration_sec is not None:
                embed['fields'].append(self._field('Cycle', f'{cycle_duration_sec:.2f}s'))
            if has_screenshot:
                embed['image'] = {'url': 'attachment://screenshot.png'}
            payload = {'content': '', 'embeds': [embed]}
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Sending STATUS UPDATE (no @everyone)')
            response = self._post_payload(payload, screenshot_path=screenshot_path, timeout=10, missing_screenshot_warning=f'[WEBHOOK] Screenshot path provided but file not found: {screenshot_path}')
            return self._log_webhook_result('[WEBHOOK] Status update sent successfully', '[WEBHOOK] Failed to send status update (status: {status}, response: {response})', response)
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping status update: {str(e)}')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending status update: {str(e)}', exc_info=True)
            return False

    def send_urgent_alert(self, data, previous_distance=None, autosteer_enabled=False, mode=None, override_target_bearing=None, override_icao_code=None, throttle_up_if_not_100=False, will_throttle_up=False):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug('Discord webhook URL not configured - skipping urgent alert')
            return
        try:
            target_bearing = override_target_bearing if override_target_bearing is not None else data.target_bearing
            icao_code = override_icao_code if override_icao_code is not None else data.icao_code
            urgent_reasons = []
            hdg_diff = None
            if data.heading is not None and target_bearing is not None:
                hdg_diff = abs(data.heading - target_bearing)
                if hdg_diff >= 5:
                    if not autosteer_enabled:
                        urgent_reasons.append(f'HDG difference ≥ 5° (diff: {hdg_diff}°)')
            if data.fuel is not None and data.fuel < 10:
                urgent_reasons.append(f'Fuel < 10% (current: {data.fuel}%)')
            if data.throttle is not None and data.throttle < 100 and (throttle_up_if_not_100 or data.throttle == 0):
                setting_state = 'ON' if throttle_up_if_not_100 else 'OFF'
                if will_throttle_up:
                    action = 'holding W for 10s to restore full throttle'
                elif throttle_up_if_not_100:
                    action = 'no hold (skipped this cycle, e.g. docking/undocking)'
                else:
                    action = 'no action'
                urgent_reasons.append(f'Throttle = {data.throttle}%. Throttle-up setting: {setting_state} - {action}')
            if previous_distance is not None and data.distance is not None:
                distance_diff = abs(data.distance - previous_distance)
                if distance_diff < 0.01:
                    urgent_reasons.append(f'Distance unchanged (prev: {previous_distance}nm, curr: {data.distance}nm). This may be a false positive, if this continues, something is wrong.')
            if not urgent_reasons:
                return
            log_msg = f"[WEBHOOK] Sending URGENT ALERT: {', '.join(urgent_reasons)}"
            if self.logger:
                self.logger.warning(log_msg)
            description_parts = ['Immediate attention recommended.\n']
            for reason in urgent_reasons:
                description_parts.append(f'• {reason}')
            title = f'AeroHelper {mode} Alert' if mode else 'AeroHelper Alert'
            embed = self._embed(title, COLOR_ERROR, description='\n'.join(description_parts), fields=[self._field('Heading', f'{data.heading}°' if data.heading is not None else 'N/A'), self._field('Target', f'{int(round(target_bearing))}° ({icao_code})' if target_bearing is not None else 'N/A'), self._field('Fuel', f'{data.fuel}%' if data.fuel is not None else 'N/A'), self._field('Throttle', f'{data.throttle}%' if data.throttle is not None else 'N/A'), self._field('Distance', f'{data.distance} nm' if data.distance is not None else 'N/A')])
            payload = {'content': '@everyone', 'embeds': [embed]}
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Sending URGENT ALERT (has @everyone: True)')
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                if self.logger:
                    self.logger.info(f'[WEBHOOK] Urgent alert sent successfully (status: {response.status_code})')
                return True
            else:
                if self.logger:
                    self.logger.error(f'[WEBHOOK] Failed to send urgent alert (status: {response.status_code}, response: {response.text})')
                return False
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping urgent alert: {str(e)}')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending urgent alert: {str(e)}', exc_info=True)
            return False

    def send_steering_correction(self, data, direction, duration, diff, override_target_bearing=None, override_icao_code=None, mode=None):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug('Discord webhook URL not configured - skipping steering correction')
            return
        try:
            direction_name = 'LEFT' if direction == 'a' else 'RIGHT'
            log_msg = f'[WEBHOOK] Sending steering correction: Turning {direction_name} for {duration:.2f}s (HDG diff: {diff}°)'
            if self.logger:
                self.logger.info(log_msg)
            target_bearing = override_target_bearing if override_target_bearing is not None else data.target_bearing
            icao_code = override_icao_code if override_icao_code is not None else data.icao_code
            title = f'AeroHelper {mode} Steering' if mode else 'AeroHelper Steering'
            embed = self._embed(title, COLOR_WARNING, description=f'Turning {direction_name} for {duration:.2f}s.\nHeading difference: {diff:.1f}°', fields=[self._field('Heading', f'{data.heading}°' if data.heading is not None else 'N/A'), self._field('Target', f'{int(round(target_bearing))}° ({icao_code})' if target_bearing is not None else 'N/A'), self._field('Direction', direction_name)])
            payload = {'content': '', 'embeds': [embed]}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                if self.logger:
                    self.logger.info(f'[WEBHOOK] Steering correction sent successfully (status: {response.status_code})')
                return True
            else:
                if self.logger:
                    self.logger.error(f'[WEBHOOK] Failed to send steering correction (status: {response.status_code}, response: {response.text})')
                return False
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping steering correction: {str(e)}')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending steering correction: {str(e)}', exc_info=True)
            return False

    def send_oscillation_alert(self, data, multiplier):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug('Discord webhook URL not configured - skipping oscillation alert')
            return
        try:
            log_msg = f'[WEBHOOK] Sending OSCILLATION ALERT: Vehicle is oscillating (multiplier: {multiplier})'
            if self.logger:
                self.logger.warning(log_msg)
            embed = self._embed('AeroHelper Oscillation Detected', COLOR_ERROR, description=f'Autosteer is oscillating left and right.\n\nIf this persists, please lower the multiplier/ask for guidance (current: {multiplier}).\n\nUsually, no action is needed.', fields=[self._field('Heading', f'{data.heading}°' if data.heading is not None else 'N/A'), self._field('Target', f'{int(round(data.target_bearing))}° ({data.icao_code})' if data.target_bearing is not None else 'N/A'), self._field('Multiplier', f'{multiplier}')])
            payload = {'content': '@everyone', 'embeds': [embed]}
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Sending OSCILLATION ALERT (has @everyone: True)')
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                if self.logger:
                    self.logger.info(f'[WEBHOOK] Oscillation alert sent successfully (status: {response.status_code})')
                return True
            else:
                if self.logger:
                    self.logger.error(f'[WEBHOOK] Failed to send oscillation alert (status: {response.status_code}, response: {response.text})')
                return False
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping oscillation alert: {str(e)}')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending oscillation alert: {str(e)}', exc_info=True)
            return False

    def send_notification(self, data, previous_distance=None, urgent=False):
        if urgent:
            return self.send_urgent_alert(data, previous_distance)
        else:
            return self.send_status_update(data, previous_distance)

    def send_reconnect_update(self, stage, message, screenshot_path=None):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Discord webhook URL not configured - skipping reconnect update (Stage: {stage})')
            return
        try:
            log_msg = f'[WEBHOOK] Sending reconnect update: Stage {stage} - {message}'
            if screenshot_path:
                log_msg += f' (with screenshot: {screenshot_path})'
            if self.logger:
                self.logger.info(log_msg)
            has_screenshot = self._has_screenshot(screenshot_path)
            embed = self._embed('AeroHelper Reconnect', COLOR_WARNING, description=f'Stage {stage}\n{message}')
            if has_screenshot:
                embed['image'] = {'url': 'attachment://screenshot.png'}
            ping_stages = {'1', '7', 'ERROR'}
            payload = {'content': '@everyone' if str(stage) in ping_stages else '', 'embeds': [embed]}
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Reconnect payload: {json.dumps(payload, indent=2)}')
            response = self._post_payload(payload, screenshot_path=screenshot_path, timeout=10, missing_screenshot_warning=f'[WEBHOOK] Reconnect screenshot path missing: {screenshot_path}')
            self._log_webhook_result('[WEBHOOK] Reconnect update sent successfully', '[WEBHOOK] Failed to send reconnect update (status: {status}, response: {response})', response)
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping reconnect update: {str(e)}')
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending reconnect update: {str(e)}', exc_info=True)

    def send_undocking_status(self, data):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug('Discord webhook URL not configured - skipping undocking status')
            return
        try:
            if self.logger:
                self.logger.info('[WEBHOOK] Sending undocking status')
            fields = [{'name': 'Phase', 'value': 'Undocking', 'inline': True}, {'name': 'Status', 'value': 'Leaving harbor', 'inline': True}, {'name': 'Speed', 'value': f'{data.speed} Knots' if data.speed is not None else 'N/A', 'inline': True}, {'name': 'Throttle', 'value': f'{data.throttle}%' if data.throttle is not None else 'N/A', 'inline': True}, {'name': 'Fuel', 'value': f'{data.fuel}%' if data.fuel is not None else 'N/A', 'inline': True}]
            embed = self._embed('AeroHelper Undocking', COLOR_INFO, fields=fields)
            payload = {'content': '', 'embeds': [embed]}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                if self.logger:
                    self.logger.info('[WEBHOOK] Undocking status sent successfully')
                return True
            else:
                if self.logger:
                    self.logger.error(f'[WEBHOOK] Failed to send undocking status (status: {response.status_code})')
                return False
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping undocking status: {str(e)}')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending undocking status: {str(e)}')
            return False

    def send_autopilot_update(self, phase, message, details=None, ping=False, screenshot_path=None, embed_color=None):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Discord webhook URL not configured - skipping autopilot update')
            return
        try:
            if self.logger:
                log_line = f'[WEBHOOK] Sending autopilot update: {phase} - {message}'
                if screenshot_path:
                    log_line += f' (with screenshot: {screenshot_path})'
                self.logger.info(log_line)
            description = f'**Phase:** {phase}\n**Status:** {message}'
            err_embed = ping or (embed_color is not None and int(embed_color) == 16711680)
            if details and (not err_embed):
                description += f'\n**Details:** {details}'
            color = COLOR_INFO if embed_color is None else int(embed_color)
            has_screenshot = self._has_screenshot(screenshot_path)
            embed = self._embed('AeroHelper AutoPilot', color, description=description)
            if has_screenshot:
                embed['image'] = {'url': 'attachment://screenshot.png'}
            payload = {'content': '@everyone' if ping else '', 'embeds': [embed]}
            response = self._post_payload(payload, screenshot_path=screenshot_path, timeout=10, missing_screenshot_warning=f'[WEBHOOK] Autopilot screenshot path missing: {screenshot_path}')
            return self._log_webhook_result('[WEBHOOK] Autopilot update sent successfully', '[WEBHOOK] Failed to send autopilot update (status: {status}, response: {response})', response)
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping autopilot update: {str(e)}')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending autopilot update: {str(e)}')
            return False

    def send_mission_complete(self, destination, wp=None, money=None, mission_number=None):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Discord webhook URL not configured - skipping mission complete')
            return
        try:
            if self.logger:
                self.logger.info(f'[WEBHOOK] Sending mission complete: dest={destination}, WP={wp}, money={money}')
            dest = destination or 'Unknown'
            headline = f'**Touchdown at {dest}!** ✈️'
            if mission_number is not None:
                headline = f'**Mission #{mission_number} complete — touchdown at {dest}!** ✈️'
            rewards = []
            if wp is not None:
                rewards.append(f'**{wp:,} WP**')
            if money is not None:
                rewards.append(f'**${money:,}**')
            reward_line = f"\n\n💰 **Payout:** {' · '.join(rewards)}" if rewards else ''
            description = (
                f'{headline}\n\n'
                f'AutoPilot nailed the landing — another run in the books! 🎉'
                f'{reward_line}\n\n'
            )
            fields = [{'name': '📍 Destination', 'value': dest, 'inline': True}]
            if wp is not None:
                fields.append({'name': '⭐ WP Earned', 'value': f'{wp:,}', 'inline': True})
            if money is not None:
                fields.append({'name': '💵 Cash Earned', 'value': f'${money:,}', 'inline': True})
            embed = self._embed('🎊 Job Complete!', COLOR_SUCCESS, description=description, fields=fields)
            payload = {'content': '@everyone **Job done!** Another mission in the bag 🎊', 'embeds': [embed]}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                if self.logger:
                    self.logger.info(f'[WEBHOOK] Mission complete sent successfully')
                return True
            else:
                if self.logger:
                    self.logger.error(f'[WEBHOOK] Failed to send mission complete (status: {response.status_code})')
                return False
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping mission complete: {str(e)}')
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending mission complete: {str(e)}')
            return False

    def send_warning(self, title, message, ping=True):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug('[WEBHOOK] Discord webhook URL not configured - skipping warning')
            return
        try:
            if self.logger:
                self.logger.warning(f'[WEBHOOK] Sending warning: {title} - {message}')
            embed = self._embed(f'AeroHelper Warning: {title}', COLOR_WARNING, description=message)
            payload = {'content': '@everyone' if ping else '', 'embeds': [embed]}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                if self.logger:
                    self.logger.info(f'[WEBHOOK] Warning sent successfully')
            elif self.logger:
                self.logger.error(f'[WEBHOOK] Failed to send warning (status: {response.status_code})')
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping warning: {str(e)}')
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending warning: {str(e)}')

    def send_quit(self, reason):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug('[WEBHOOK] Discord webhook URL not configured - skipping quit notification')
            return
        try:
            msg = f'AeroHelper has stopped. Reason: {reason}'
            if self.logger:
                self.logger.info(f'[WEBHOOK] Sending quit notification: {msg}')
            embed = self._embed('AeroHelper Stopped', COLOR_WARNING, description=msg)
            payload = {'content': '@everyone', 'embeds': [embed]}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204) and self.logger:
                self.logger.info('[WEBHOOK] Quit notification sent')
            elif response.status_code not in (200, 204) and self.logger:
                self.logger.error(f'[WEBHOOK] Quit notification failed: {response.status_code}')
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping quit: {str(e)}')
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending quit: {str(e)}')

    def send_error(self, error_message, ping=True):
        if not self.webhook_url:
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Discord webhook URL not configured - skipping error notification')
            return
        try:
            log_msg = f'[WEBHOOK] Sending error notification: {error_message}'
            if self.logger:
                self.logger.error(log_msg)
            embed = self._embed('AeroHelper Error', COLOR_ERROR, description=error_message)
            payload = {'content': '@everyone' if ping else '', 'embeds': [embed]}
            if self.logger:
                self.logger.debug(f'[WEBHOOK] Error payload: {json.dumps(payload, indent=2)}')
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                if self.logger:
                    self.logger.info(f'[WEBHOOK] Error notification sent successfully (status: {response.status_code})')
            elif self.logger:
                self.logger.error(f'[WEBHOOK] Failed to send error notification (status: {response.status_code}, response: {response.text})')
        except REQUEST_EXCEPTIONS as e:
            if self.logger:
                self.logger.info(f'[WEBHOOK] No network - skipping error notification: {str(e)}')
        except Exception as e:
            if self.logger:
                self.logger.error(f'[WEBHOOK] Exception sending error notification: {str(e)}', exc_info=True)
