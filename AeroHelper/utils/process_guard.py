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

import os
import subprocess
import psutil
from AeroHelper.utils.platform import IS_WINDOWS, IS_MACOS

_CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if IS_WINDOWS else 0

def _run_silent(cmd, timeout=None):
    kwargs = {
        'capture_output': True,
        'text': True,
        'check': False,
    }
    if timeout is not None:
        kwargs['timeout'] = timeout
    if IS_WINDOWS:
        kwargs['creationflags'] = _CREATE_NO_WINDOW
    return subprocess.run(cmd, **kwargs)

def _safe_process_name(name):
    cleaned = os.path.basename(str(name or '').strip().strip('"').strip("'"))
    if not cleaned or cleaned in ('.', '..'):
        return None
    if IS_WINDOWS and '.' not in cleaned:
        cleaned = f'{cleaned}.exe'
    return cleaned

def _normalize_service_name(name):
    n = (name or '').strip()
    if not n:
        return ''
    if any((c in n for c in '/\\:*?"<>|\n\r\t')):
        return ''
    return n

def _windows_process_running(name):
    name_l = name.lower()
    try:
        for proc in psutil.process_iter(['name']):
            try:
                if (proc.info.get('name') or '').lower() == name_l:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        result = _run_silent(['tasklist', '/FI', f'IMAGENAME eq {name}', '/NH'])
        return name_l in (result.stdout or '').lower()
    return False

def _terminate_windows(name):
    if not _windows_process_running(name):
        return 'not_running'
    killed = False
    access_denied = False
    name_l = name.lower()
    try:
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if (proc.info.get('name') or '').lower() != name_l:
                    continue
                proc.kill()
                killed = True
            except psutil.AccessDenied:
                access_denied = True
            except (psutil.NoSuchProcess, psutil.Error):
                continue
    except Exception:
        pass
    if killed:
        return 'terminated'
    result = _run_silent(['taskkill', '/F', '/T', '/IM', name])
    if result.returncode == 0:
        return 'terminated'
    output = f'{result.stdout} {result.stderr}'.lower()
    if access_denied or 'access is denied' in output or 'permission' in output:
        return 'access_denied'
    return 'failed'

def _terminate_posix(name):
    cmd = ['pkill', '-9', '-x', name]
    if IS_MACOS:
        cmd = ['pkill', '-9', '-x', name]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return 'terminated'
    return 'not_running' if result.returncode == 1 else 'failed'

def stop_blocked_services(names, logger=None):
    results = []
    if not IS_WINDOWS or not names:
        return results
    seen = set()
    for raw in names:
        svc = _normalize_service_name(raw)
        if not svc:
            continue
        key = svc.lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            listed = _run_silent(['sc', 'query', svc], timeout=15)
            out = (listed.stdout or '') + (listed.stderr or '')
            if listed.returncode != 0 and '1060' in out:
                results.append({'name': svc, 'status': 'not_found'})
                continue
            if 'RUNNING' not in out:
                results.append({'name': svc, 'status': 'not_running'})
                continue
            stopped = _run_silent(['sc', 'stop', svc], timeout=120)
            tail = ((stopped.stdout or '') + (stopped.stderr or '')).lower()
            if stopped.returncode == 0:
                results.append({'name': svc, 'status': 'stopped'})
                if logger:
                    logger.warning(f'[PROCESS GUARD] Stopped blocked service: {svc}')
            elif 'access is denied' in tail:
                results.append({'name': svc, 'status': 'access_denied'})
                if logger:
                    logger.warning(f'[PROCESS GUARD] Access denied stopping service {svc}. Run AeroHelper as administrator if this service is protected.')
            else:
                results.append({'name': svc, 'status': 'failed'})
                if logger:
                    logger.warning(f"[PROCESS GUARD] Could not stop service {svc}: {(stopped.stdout or stopped.stderr or '')}")
        except (OSError, subprocess.SubprocessError) as exc:
            results.append({'name': svc, 'status': 'failed'})
            if logger:
                logger.warning(f'[PROCESS GUARD] sc query/stop {svc} failed: {exc}')
    return results

def terminate_blocked_processes(names, logger=None):
    results = []
    seen = set()
    for raw_name in names:
        name = _safe_process_name(raw_name)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        try:
            status = _terminate_windows(name) if IS_WINDOWS else _terminate_posix(name)
        except Exception as exc:
            status = 'failed'
            if logger:
                logger.warning(f'[PROCESS GUARD] Failed checking {name}: {exc}')
        if status == 'terminated' and logger:
            logger.warning(f'[PROCESS GUARD] Terminated blocked executable: {name}')
        elif status == 'access_denied' and logger:
            logger.warning(f'[PROCESS GUARD] Access denied terminating {name}. Run AeroHelper as administrator to close elevated or protected processes.')
        results.append({'name': name, 'status': status})
    return results
