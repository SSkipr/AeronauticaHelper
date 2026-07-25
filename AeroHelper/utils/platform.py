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

import sys
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'

def is_windows_elevated_admin():
    if not IS_WINDOWS:
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def get_app_font_family() -> str:
    if IS_MACOS:
        return '.AppleSystemUIFont'
    if IS_WINDOWS:
        return 'Segoe UI'
    return 'Sans Serif'

def _windows_product_name():
    if not IS_WINDOWS:
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion') as key:
            product_name = str(winreg.QueryValueEx(key, 'ProductName')[0]).strip()
            build = 0
            for build_key in ('CurrentBuildNumber', 'CurrentBuild'):
                try:
                    build = int(winreg.QueryValueEx(key, build_key)[0])
                    break
                except OSError:
                    continue
            if build >= 22000 and product_name.startswith('Windows 10'):
                product_name = 'Windows 11' + product_name[len('Windows 10'):]
            return product_name
    except OSError:
        return None

def _windows_display_fallback():
    import platform
    _release, version, _csd = platform.win32_ver()
    build = 0
    if version:
        parts = version.split('.')
        if len(parts) >= 3:
            try:
                build = int(parts[2])
            except ValueError:
                pass
    if build >= 22000:
        return 'Windows 11'
    release = platform.release()
    return f'Windows {release}'.strip() if release else 'Windows'

def get_os_display_name():
    if IS_WINDOWS:
        return _windows_product_name() or _windows_display_fallback()
    import platform
    system = platform.system()
    if IS_MACOS:
        ver = platform.mac_ver()[0]
        return f'macOS {ver}'.strip() if ver else 'macOS'
    release = platform.release()
    return f'{system} {release}'.strip() if release else system

def get_primary_screen_size():
    if IS_WINDOWS:
        try:
            import win32api
            import win32con
            width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            if width > 0 and height > 0:
                return (width, height)
        except Exception:
            pass
    if IS_MACOS:
        try:
            from AppKit import NSScreen
            frame = NSScreen.mainScreen().frame()
            return (int(frame.size.width), int(frame.size.height))
        except Exception:
            pass
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        w, h = img.size
        img.close()
        return (int(w), int(h))
    except Exception:
        return (1920, 1080)

def get_primary_screen_center():
    w, h = get_primary_screen_size()
    return (w // 2, h // 2)

def get_image_pixel_size(image_path):
    if not image_path:
        return None
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            w, h = img.size
            if w > 0 and h > 0:
                return (int(w), int(h))
    except Exception:
        pass
    return None

def map_screenshot_coords_to_screen(screenshot_x, screenshot_y, screenshot_path, window_rect=None):
    img_size = get_image_pixel_size(screenshot_path)
    if img_size:
        img_w, img_h = img_size
    else:
        img_w, img_h = get_primary_screen_size()
    screen_w, screen_h = get_primary_screen_size()
    sx, sy = (float(screenshot_x), float(screenshot_y))
    if window_rect:
        left, top, right, bottom = window_rect
        win_w = right - left
        win_h = bottom - top
        if abs(win_w - screen_w) < 10 and abs(win_h - screen_h) < 10:
            return (int(sx * screen_w / img_w), int(sy * screen_h / img_h))
        return (left + int(sx * win_w / img_w), top + int(sy * win_h / img_h))
    return (int(sx * screen_w / img_w), int(sy * screen_h / img_h))

def macos_accessibility_trusted(*, prompt=False):
    if not IS_MACOS:
        return True
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        from Foundation import NSDictionary
        options = None
        if prompt:
            options = NSDictionary.dictionaryWithObject_forKey_(True, 'AXTrustedCheckOptionPrompt')
        return bool(AXIsProcessTrustedWithOptions(options))
    except Exception:
        return False

def macos_listen_events_trusted(*, prompt=False):
    if not IS_MACOS:
        return True
    try:
        from Quartz import CGPreflightListenEventAccess, CGRequestListenEventAccess
        if prompt:
            CGRequestListenEventAccess()
        return bool(CGPreflightListenEventAccess())
    except Exception:
        return False

def macos_screen_capture_ready(logger=None):
    if not IS_MACOS:
        return (True, '')
    import os
    import subprocess
    import tempfile
    png_path = os.path.join(tempfile.gettempdir(), f'aerohelper_perm_probe_{os.getpid()}.png')
    try:
        result = subprocess.run(['/usr/sbin/screencapture', '-x', '-t', 'png', png_path], capture_output=True, check=False, timeout=8)
        if result.returncode != 0 or not os.path.exists(png_path) or os.path.getsize(png_path) < 64:
            message = 'macOS Screen Recording permission may be missing. Open System Settings → Privacy & Security → Screen Recording and enable AeroHelper (or Terminal/Python if running from source). OCR and screenshots may fail without it.'
            if logger:
                logger.warning(f'[MACOS] {message}')
            return (False, message)
        return (True, '')
    except Exception as exc:
        message = f'macOS screen capture probe failed ({exc}). Grant Screen Recording permission if OCR fails.'
        if logger:
            logger.warning(f'[MACOS] {message}')
        return (False, message)
    finally:
        try:
            if os.path.exists(png_path):
                os.remove(png_path)
        except OSError:
            pass

def get_macos_permission_summary():
    if not IS_MACOS:
        return []
    lines = []
    if not macos_accessibility_trusted():
        lines.append('Accessibility: not granted - keyboard/mouse automation disabled until enabled in System Settings → Privacy & Security → Accessibility.')
    return lines

def macos_input_monitoring_ready(logger=None):
    if not IS_MACOS:
        return (True, '')
    missing = get_macos_permission_summary()
    if not missing:
        return (True, '')
    message = ' '.join(missing)
    if logger:
        logger.warning(f'[MACOS] {message}')
    return (False, message)
