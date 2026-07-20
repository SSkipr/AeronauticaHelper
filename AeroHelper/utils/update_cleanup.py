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

import subprocess
import sys
import tempfile
from pathlib import Path
from AeroHelper.config import AEROHELPER_ENV_BASENAME, aerohelper_env_path

def paths_to_remove_on_update() -> list[Path]:
    candidates: list[Path] = []
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys.executable).resolve().parent
        candidates.extend([app_dir / AEROHELPER_ENV_BASENAME, app_dir / 'AeroHelper.log', app_dir / 'AeroMulti.log'])
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidates.extend([aerohelper_env_path(), repo_root / 'AeroHelper.log', repo_root / 'AeroMulti.log'])
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique

def schedule_frozen_update_cleanup() -> bool:
    if not getattr(sys, 'frozen', False) or not sys.platform.startswith('win'):
        return False
    exe_path = Path(sys.executable).resolve()
    lines = ['@echo off', 'ping 127.0.0.1 -n 4 > nul']
    for path in paths_to_remove_on_update():
        lines.append(f'if exist "{path}" del /f /q "{path}"')
    lines.append(f'if exist "{exe_path}" del /f /q "{exe_path}"')
    lines.append('del /f /q "%~f0"')
    try:
        fd, bat = tempfile.mkstemp(suffix='.bat')
        import os
        os.close(fd)
        bat_path = Path(bat)
        bat_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        subprocess.Popen(['cmd', '/c', str(bat_path)], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 134217728))
        return True
    except OSError:
        return False
