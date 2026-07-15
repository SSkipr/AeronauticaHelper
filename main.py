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

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from AeroHelper.version import APP_VERSION as AEROHELPER_VERSION_DEV
from AeroHelper.ocr.torch_bootstrap import import_torch_early
import_torch_early()

if not getattr(sys, 'frozen', False):
    import importlib
    import subprocess
    _REQUIRED = [('PyQt5', 'PyQt5'), ('PIL', 'Pillow'), ('pynput', 'pynput'), ('requests', 'requests'), ('dotenv', 'python-dotenv'), ('numpy', 'numpy'), ('psutil', 'psutil')]

    def _check_dependencies():
        missing = []
        for import_name, pip_name in _REQUIRED:
            try:
                importlib.import_module(import_name)
            except ImportError:
                missing.append(pip_name)
        return missing
    _missing = _check_dependencies()
    if _missing:
        print('\n[AeroHelper] Missing required packages:', ', '.join(_missing))
        req_path = _REPO_ROOT / 'requirements.txt'
        print(f'Command: {sys.executable} -m pip install -r "{req_path}"')
        try:
            answer = input('\nInstall missing packages now? [y/N]: ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = 'n'
        if answer != 'y':
            print('[AeroHelper] Aborted. Install packages manually and re-run.')
            sys.exit(1)
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(req_path)], check=False)
        if result.returncode != 0:
            print('[AeroHelper] Installation failed. Please install manually.')
            sys.exit(1)
        print('\n[AeroHelper] Installation complete. Please restart AeroHelper.')
        sys.exit(0)
import faulthandler
import threading
import traceback
if sys.stderr is not None:
    faulthandler.enable()

def _thread_excepthook(args):
    tb = ''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    msg = f'[AeroHelper] Uncaught exception in thread {args.thread.name}:\n{tb}'
    stream = sys.stderr or sys.stdout
    if stream is not None:
        print(msg, file=stream)
threading.excepthook = _thread_excepthook
if sys.platform.startswith('win'):
    try:
        import ctypes
        _app_id = f"AeroHelper.Desktop.{AEROHELPER_VERSION_DEV.replace('-', '.')}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_app_id)
    except Exception:
        pass
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    try:
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    except AttributeError:
        Image.ANTIALIAS = getattr(Image, 'LANCZOS', 1)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication
from AeroHelper.ui.main_window import MainWindow
from AeroHelper.ui.app_icon import load_app_icon, apply_windows_taskbar_icons
from AeroHelper.ui.status_overlay import StatusOverlay
from AeroHelper.controller import Controller

def _fetch_startup_data(main_window, webhook_url, app_version):
    import json
    import platform
    from urllib.request import urlopen
    from AeroHelper.config import API_BASE
    from AeroHelper.notifications.discord import DiscordNotifier

    def _fetch():
        try:
            from AeroHelper.utils.version import sanitize_remote_version
            global_version = None
            for url in (f'{API_BASE}/version.txt', f'{API_BASE}/api/version'):
                try:
                    with urlopen(url, timeout=6) as r:
                        global_version = sanitize_remote_version(r.read().decode().strip())
                    if global_version:
                        break
                except Exception:
                    continue
            if global_version:
                main_window.set_global_version_signal.emit(global_version)
        except Exception:
            pass
        try:
            with urlopen(f'{API_BASE}/api/issues', timeout=10) as r:
                raw = r.read().decode('utf-8', errors='replace')
                issues = json.loads(raw)
            if isinstance(issues, list):
                main_window.set_issues_signal.emit(issues)
            else:
                main_window.set_issues_signal.emit([])
        except Exception:
            main_window.set_issues_signal.emit([])
        if webhook_url:
            try:
                DiscordNotifier(webhook_url).set_webhook_branding()
            except Exception:
                pass
        try:
            from AeroHelper.config import Config
            from AeroHelper.device_client import log_api_failure, post_api, user_api_notice
            from AeroHelper.utils.platform import get_os_display_name
            post_api('/api/ran', {'os': platform.system(), 'os_release': get_os_display_name(), 'machine': platform.machine(), 'app_version': app_version, 'frozen': getattr(sys, 'frozen', False)}, config=Config(), app_version=app_version)
        except Exception as exc:
            try:
                from AeroHelper.device_client import ApiRequestError, log_api_failure, user_api_notice
                if not isinstance(exc, ApiRequestError):
                    log_api_failure('/api/ran', exc)
                severity, title, message = user_api_notice(exc, '/api/ran')
                main_window.api_notice_signal.emit(severity, title, message, True)
            except Exception:
                pass
    t = threading.Thread(target=_fetch, daemon=True)
    t.start()

def main():
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app_icon = load_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    main_window = MainWindow(version=AEROHELPER_VERSION_DEV)
    status_overlay = StatusOverlay()
    controller = Controller(main_window, status_overlay, app_version=AEROHELPER_VERSION_DEV)
    main_window.show()
    status_overlay.show()

    def _apply_win_taskbar_icons():
        if not app_icon.isNull():
            apply_windows_taskbar_icons([main_window, status_overlay], app_icon)
    QTimer.singleShot(0, _apply_win_taskbar_icons)
    from AeroHelper.config import Config
    _cfg = Config()
    QTimer.singleShot(500, lambda: _fetch_startup_data(main_window, _cfg.get_webhook_url(), AEROHELPER_VERSION_DEV))
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
