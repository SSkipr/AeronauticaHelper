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
from AeroHelper.utils.platform import IS_WINDOWS, IS_MACOS
ROBLOX_PLACE_ID = 6647962258
_CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if IS_WINDOWS else 0

def _run_silent(cmd):
    kwargs = {'capture_output': True, 'check': False}
    if IS_WINDOWS:
        kwargs['creationflags'] = _CREATE_NO_WINDOW
    return subprocess.run(cmd, **kwargs)

def close_roblox():
    try:
        if IS_WINDOWS:
            _run_silent(['taskkill', '/F', '/IM', 'RobloxPlayerBeta.exe'])
            _run_silent(['taskkill', '/F', '/IM', 'Roblox.exe'])
            return
        if IS_MACOS:
            for name in ('RobloxPlayer', 'Roblox'):
                subprocess.run(['pkill', '-9', '-x', name], capture_output=True, check=False)
            subprocess.run(['osascript', '-e', 'tell application "Roblox" to quit'], capture_output=True, check=False)
            return
        subprocess.run(['pkill', '-9', '-f', 'Roblox'], capture_output=True, check=False)
    except Exception:
        pass

def launch_roblox_place(place_id):
    roblox_url = f'roblox://placeId={place_id}'
    try:
        if IS_WINDOWS:
            try:
                subprocess.Popen(
                    ['cmd', '/c', 'start', '', roblox_url],
                    shell=False,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception:
                return False
        if IS_MACOS:
            try:
                subprocess.run(['open', roblox_url], check=False)
                return True
            except Exception:
                return False
        try:
            subprocess.run(['xdg-open', roblox_url], check=False)
            return True
        except Exception:
            return False
    except Exception:
        return False

def launch_aeronautica():
    return launch_roblox_place(ROBLOX_PLACE_ID)
