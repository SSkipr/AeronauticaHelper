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

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from AeroHelper.config import API_BASE, Config

_api_opener: urllib.request.OpenerDirector | None = None

class ApiRequestError(Exception):

    def __init__(self, message: str, *, status: int | None=None, reason: str | None=None):
        super().__init__(message)
        self.status = status
        self.reason = reason

def _api_urlopen(req: urllib.request.Request, timeout: int):
    global _api_opener
    if _api_opener is None:

        class _PostRedirectHandler(urllib.request.HTTPRedirectHandler):

            def redirect_request(self, req, fp, code, msg, headers, newurl):
                if code not in (301, 302, 303, 307, 308):
                    return None
                method = req.get_method()
                data = req.data
                if code in (301, 302, 303) and method == 'POST':
                    method = 'GET'
                    data = None
                return urllib.request.Request(newurl, data=data, headers=req.headers, origin_req_host=req.origin_req_host, unverifiable=True, method=method)
        _api_opener = urllib.request.build_opener(_PostRedirectHandler())
    return _api_opener.open(req, timeout=timeout)

def _parse_http_error(exc: urllib.error.HTTPError) -> tuple[str, str | None]:
    try:
        raw = exc.read().decode('utf-8', errors='replace')
        if raw:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                detail = str(parsed.get('error') or parsed.get('message') or raw)
                reason = parsed.get('reason')
                return (detail, reason if isinstance(reason, str) else None)
            return (raw, None)
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return (exc.reason or f'HTTP {exc.code}', None)

def _http_failure_message(code: int, endpoint: str, detail: str) -> str:
    if code == 429:
        return f'[API] {endpoint} blocked: rate limit exceeded (429). {detail}'
    if code == 401:
        return f'[API] {endpoint} blocked: unauthorized (401). {detail}'
    if code == 403:
        return f'[API] {endpoint} blocked: forbidden (403). {detail}'
    if code == 410:
        return f'[API] {endpoint} blocked: endpoint removed (410). {detail}'
    return f'[API] {endpoint} failed: HTTP {code}. {detail}'

def format_api_error(exc: BaseException, endpoint: str) -> str:
    if isinstance(exc, ApiRequestError):
        return str(exc)
    if isinstance(exc, urllib.error.HTTPError):
        detail, _reason = _parse_http_error(exc)
        return _http_failure_message(exc.code, endpoint, detail)
    if isinstance(exc, urllib.error.URLError):
        return f'[API] {endpoint} failed: network error. {exc.reason}'
    return f'[API] {endpoint} failed: {exc}'

_ENDPOINT_LABELS = {
    '/api/ran': 'Run notification',
    '/api/datashare': 'Share data with developer',
}

def user_api_notice(exc: BaseException, endpoint: str) -> tuple[str, str, str]:
    label = _ENDPOINT_LABELS.get(endpoint, endpoint)
    if isinstance(exc, ApiRequestError):
        reason = exc.reason or ''
        status = exc.status
        if reason == 'network_blocked' or (status == 403 and reason != 'unknown_client_ip'):
            return (
                'error',
                f'{label} blocked',
                'This network was blocked on the AeroHelper server.\n\n'
                'API features (run notifications, diagnostic sharing) are disabled from '
                'your current connection. Re-registering is not available.\n\n'
                'Contact the developer if you believe this is a mistake.',
            )
        if reason == 'rate_limited' or status == 429:
            return (
                'warning',
                f'{label} failed',
                'The AeroHelper server rate-limited this request.\n\n'
                'Wait about a minute and try again. Core automation is unaffected.',
            )
        if reason == 'unknown_client_ip' or status == 403:
            return (
                'warning',
                f'{label} failed',
                'The server could not verify your connection (client IP unknown).\n\n'
                'Try again later or from a normal home network.',
            )
        if status and status >= 500:
            return (
                'warning',
                f'{label} failed',
                'The AeroHelper server returned an error.\n\n'
                'This is usually temporary. Core automation still works; API features may be unavailable.',
            )
    if isinstance(exc, urllib.error.URLError):
        return (
            'warning',
            f'{label} failed',
            f'Could not reach the AeroHelper server ({API_BASE}).\n\n'
            f'Network error: {exc.reason}\n\n'
            'Check your internet connection. Core automation is unaffected.',
        )
    detail = format_api_error(exc, endpoint)
    return (
        'warning',
        f'{label} failed',
        detail.replace('[API] ', '', 1),
    )

def _notify_api_failure_webhook(endpoint: str, exc: BaseException, *, webhook_url: str | None=None, logger=None) -> None:
    url = (webhook_url or '').strip()
    if not url:
        try:
            url = (Config().get_webhook_url() or '').strip()
        except Exception:
            return
    if not url:
        return
    severity, title, message = user_api_notice(exc, endpoint)
    detail = format_api_error(exc, endpoint)
    webhook_body = f'**{title}**\n{detail}\n\n{message}'
    if len(webhook_body) > 3900:
        webhook_body = webhook_body[:3900] + '…'

    def _send():
        try:
            from AeroHelper.notifications.discord import DiscordNotifier
            notifier = DiscordNotifier(url, logger=logger)
            if severity == 'error':
                notifier.send_error(webhook_body, ping=False)
            else:
                notifier.send_warning(title, webhook_body, ping=False)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

def log_api_failure(endpoint: str, exc: BaseException, logger=None, *, notify_webhook: bool=True, webhook_url: str | None=None) -> str:
    message = format_api_error(exc, endpoint)
    if logger is not None:
        logger.warning(message)
    else:
        try:
            from AeroHelper.logger import Logger
            Logger().warning(message)
        except Exception:
            print(message)
    if notify_webhook:
        _notify_api_failure_webhook(endpoint, exc, webhook_url=webhook_url, logger=logger)
    return message

def _api_headers() -> dict[str, str]:
    return {'Content-Type': 'application/json'}

def post_api(path: str, payload: dict, *, config: Config | None=None, app_version: str | None=None, timeout: int=8, logger=None) -> None:
    endpoint = path if path.startswith('/') else f'/{path}'
    cfg = config or Config()
    webhook_url = cfg.get_webhook_url()
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f'{API_BASE}{endpoint}', data=data, headers=_api_headers(), method='POST')
    try:
        with _api_urlopen(req, timeout=timeout) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        detail, reason = _parse_http_error(exc)
        message = _http_failure_message(exc.code, endpoint, detail)
        log_api_failure(endpoint, ApiRequestError(message, status=exc.code, reason=reason), logger=logger, webhook_url=webhook_url)
        raise ApiRequestError(message, status=exc.code, reason=reason) from exc
    except urllib.error.URLError as exc:
        log_api_failure(endpoint, exc, logger=logger, webhook_url=webhook_url)
        raise ApiRequestError(format_api_error(exc, endpoint)) from exc
