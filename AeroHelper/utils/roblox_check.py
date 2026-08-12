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
Version 4.1.2
'''

import psutil

from AeroHelper.utils.platform import IS_MACOS

_ROBLOX_NAME_HINTS = (
    'roblox',
    'robloxplayer',
    'robloxplayerbeta',
)


def _looks_like_roblox(value):
    text = (value or '').strip().lower()
    if not text:
        return False
    return any(hint in text for hint in _ROBLOX_NAME_HINTS)


def _process_name_or_exe_is_roblox(proc):
    """Check one process without letting AccessDenied on exe skip a name match."""
    try:
        if _looks_like_roblox(proc.name()):
            return True, proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

    try:
        exe = proc.exe()
        if _looks_like_roblox(exe):
            return True, exe
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

    return False, None


def _macos_roblox_via_appkit():
    try:
        from AppKit import NSWorkspace
    except Exception:
        return None
    try:
        for app in NSWorkspace.sharedWorkspace().runningApplications():
            name = app.localizedName() or ''
            bundle = app.bundleIdentifier() or ''
            if _looks_like_roblox(name) or _looks_like_roblox(bundle):
                return name or bundle
    except Exception:
        return None
    return None


def _macos_roblox_via_window():
    try:
        from AeroHelper.utils.window import find_roblox_window
        info = find_roblox_window()
    except Exception:
        return None
    if not info:
        return None
    return info.get('owner') or info.get('title') or 'Roblox'


def is_roblox_running():
    try:
        # Only request name here. Asking for exe in process_iter causes AccessDenied
        # on many macOS processes (including Roblox), which previously skipped them.
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info.get('name')
                if _looks_like_roblox(name):
                    return (True, name)
                found, label = _process_name_or_exe_is_roblox(proc)
                if found:
                    return (True, label or 'Roblox')
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if IS_MACOS:
            for detector in (_macos_roblox_via_appkit, _macos_roblox_via_window):
                found = detector()
                if found:
                    return (True, found)

        return (False, None)
    except Exception as e:
        return (False, f'Error checking Roblox: {str(e)}')
