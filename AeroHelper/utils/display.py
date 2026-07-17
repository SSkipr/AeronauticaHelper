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
Version 4.0.3
'''

from AeroHelper.utils.platform import IS_WINDOWS, IS_MACOS
if IS_WINDOWS:
    try:
        import win32api
        import win32con
    except Exception:
        win32api = None
        win32con = None
else:
    win32api = None
    win32con = None

def is_display_duplicated():
    if IS_WINDOWS and win32api is not None and (win32con is not None):
        try:
            monitors = win32api.EnumDisplayMonitors()
            monitor_count = len(monitors)
            if monitor_count < 2:
                return (True, f'Single monitor detected (count: {monitor_count})')
            primary_monitor = None
            primary_info = None
            for monitor in monitors:
                monitor_info = win32api.GetMonitorInfo(monitor[0])
                if monitor_info['Flags'] == win32con.MONITORINFOF_PRIMARY:
                    primary_monitor = monitor
                    primary_info = monitor_info
                    break
            if primary_monitor is None:
                return (False, 'No primary monitor detected')
            primary_rect = primary_info['Monitor']
            monitor_details = []
            for i, monitor in enumerate(monitors):
                monitor_info = win32api.GetMonitorInfo(monitor[0])
                monitor_rect = monitor_info['Monitor']
                is_primary = monitor == primary_monitor
                monitor_details.append(f'Monitor {i + 1}: Primary={is_primary}, Rect=({monitor_rect[0]}, {monitor_rect[1]}, {monitor_rect[2]}, {monitor_rect[3]})')
                if monitor != primary_monitor:
                    if monitor_rect[0] == primary_rect[0] and monitor_rect[1] == primary_rect[1] and (monitor_rect[2] == primary_rect[2]) and (monitor_rect[3] == primary_rect[3]):
                        return (True, f"DUPLICATE mode confirmed. {', '.join(monitor_details)}")
            return (False, f"EXTEND mode detected. Monitors are not duplicated. Details: {', '.join(monitor_details)}")
        except Exception as e:
            return (False, f'Error checking display mode: {str(e)}')
    if IS_MACOS:
        try:
            import Quartz
            max_displays = 16
            err, active_displays, count = Quartz.CGGetActiveDisplayList(max_displays, None, None)
            if err != 0 or count == 0:
                return (True, 'macOS: unable to enumerate displays, assuming OK')
            if count == 1:
                return (True, 'macOS: single display detected')
            main_id = Quartz.CGMainDisplayID()
            mirrored_count = 0
            for i in range(count):
                did = active_displays[i]
                if did == main_id:
                    continue
                if Quartz.CGDisplayIsInMirrorSet(did) and Quartz.CGDisplayMirrorsDisplay(did) == main_id:
                    mirrored_count += 1
            if mirrored_count > 0:
                return (True, f'macOS: {mirrored_count} display(s) mirror the primary')
            return (True, 'macOS: extend mode (skipping strict duplicate check)')
        except Exception as e:
            return (True, f'macOS: display-mode check skipped ({e})')
    return (True, 'Non-Windows/macOS platform - display mode check skipped')

def validate_display_mode():
    if not IS_WINDOWS:
        return
    is_dup, details = is_display_duplicated()
    if not is_dup:
        raise ValueError(f'Display mode validation failed: {details}')
