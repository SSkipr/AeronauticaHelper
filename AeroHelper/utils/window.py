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
Version 4.1.3
'''

from AeroHelper.utils.platform import IS_WINDOWS, IS_MACOS, get_primary_screen_size
if IS_WINDOWS:
    try:
        import win32gui
        import win32con
        import win32api
    except Exception:
        win32gui = None
        win32con = None
        win32api = None
else:
    win32gui = None
    win32con = None
    win32api = None
if IS_MACOS:
    try:
        import Quartz
    except Exception:
        Quartz = None
else:
    Quartz = None

def _is_roblox_title(title, owner=''):
    if not title and (not owner):
        return False
    t = (title or '').lower()
    o = (owner or '').lower()
    return 'roblox' in t or 'roblox' in o

def _windows_find_roblox():
    if win32gui is None:
        return None

    def enum_handler(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            if 'Roblox' in window_title or 'Roblox' in class_name:
                windows.append(hwnd)
        return True
    windows = []
    win32gui.EnumWindows(enum_handler, windows)
    return windows[0] if windows else None

def _macos_find_roblox_window_info():
    if Quartz is None:
        return None
    try:
        opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        window_list = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID)
        for w in window_list:
            owner = w.get('kCGWindowOwnerName', '') or ''
            title = w.get('kCGWindowName', '') or ''
            if _is_roblox_title(title, owner):
                bounds = w.get('kCGWindowBounds')
                if not bounds:
                    continue
                return {'owner': owner, 'title': title, 'pid': w.get('kCGWindowOwnerPID'), 'window_id': w.get('kCGWindowNumber'), 'bounds': {'x': int(bounds.get('X', 0)), 'y': int(bounds.get('Y', 0)), 'w': int(bounds.get('Width', 0)), 'h': int(bounds.get('Height', 0))}}
    except Exception:
        return None
    return None

def find_roblox_window():
    if IS_WINDOWS:
        return _windows_find_roblox()
    if IS_MACOS:
        return _macos_find_roblox_window_info()
    return None

def get_window_rect(handle):
    if handle is None:
        return None
    if IS_WINDOWS:
        try:
            return win32gui.GetWindowRect(handle)
        except Exception:
            return None
    if IS_MACOS and isinstance(handle, dict):
        b = handle.get('bounds') or {}
        try:
            left = int(b['x'])
            top = int(b['y'])
            right = left + int(b['w'])
            bottom = top + int(b['h'])
            return (left, top, right, bottom)
        except Exception:
            return None
    return None

def get_window_center(handle):
    rect = get_window_rect(handle)
    if rect is None:
        return None
    left, top, right, bottom = rect
    return (left + (right - left) // 2, top + (bottom - top) // 2)

def get_roblox_window_center():
    handle = find_roblox_window()
    if handle is not None:
        center = get_window_center(handle)
        if center:
            return center
    w, h = get_primary_screen_size()
    return (w // 2, h // 2)

def get_roblox_window_rect():
    handle = find_roblox_window()
    if handle is None:
        return None
    return get_window_rect(handle)

def bring_roblox_to_front():
    if IS_WINDOWS:
        hwnd = _windows_find_roblox()
        if hwnd is None or win32gui is None:
            return False
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.BringWindowToTop(hwnd)
            return True
        except Exception:
            return False
    if IS_MACOS:
        info = _macos_find_roblox_window_info()
        if info is None:
            return False
        try:
            from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
            pid = info.get('pid')
            if pid is None:
                return False
            app = NSRunningApplication.runningApplicationWithProcessIdentifier_(int(pid))
            if app is None:
                return False
            return bool(app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps))
        except Exception:
            try:
                import subprocess
                subprocess.run(['osascript', '-e', 'tell application "Roblox" to activate'], capture_output=True, check=False)
                return True
            except Exception:
                return False
    return False

def is_roblox_f11_fullscreen():
    if IS_WINDOWS:
        hwnd = _windows_find_roblox()
        if hwnd is None or win32gui is None:
            return False
        try:
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            if style & win32con.WS_CAPTION:
                return False
            rect = get_window_rect(hwnd)
            if not rect:
                return False
            left, top, right, bottom = rect
            window_width = right - left
            window_height = bottom - top
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            return abs(window_width - screen_width) <= 2 and abs(window_height - screen_height) <= 2
        except Exception:
            return False
    if IS_MACOS:
        info = _macos_find_roblox_window_info()
        if info is None:
            return False
        rect = get_window_rect(info)
        if rect is None:
            return False
        left, top, right, bottom = rect
        window_width = right - left
        window_height = bottom - top
        screen_width, screen_height = get_primary_screen_size()
        return abs(window_width - screen_width) <= 4 and abs(window_height - screen_height) <= 4
    return False
