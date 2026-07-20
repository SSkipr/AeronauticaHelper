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

import os
import tempfile
from PIL import ImageGrab, Image
from AeroHelper.utils.platform import IS_WINDOWS, IS_MACOS
if IS_WINDOWS:
    try:
        import win32gui
        import win32ui
        import win32con
    except Exception:
        win32gui = None
        win32ui = None
        win32con = None
else:
    win32gui = None
    win32ui = None
    win32con = None

def _temp_png_path():
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, f'aerohelper_screenshot_{os.getpid()}_{os.urandom(4).hex()}.png')

def _capture_windows():
    if win32gui is None:
        raise IOError('win32 libraries unavailable')
    hwnd = win32gui.GetDesktopWindow()
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        raise ValueError(f'Invalid screen dimensions: {width}x{height}')
    hwndDC = win32gui.GetWindowDC(hwnd)
    if not hwndDC:
        raise ValueError('Failed to get window DC')
    try:
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        temp_dir = tempfile.gettempdir()
        base = os.path.join(temp_dir, f'aerohelper_screenshot_{os.getpid()}_{os.urandom(4).hex()}')
        bmp_path = base + '.bmp'
        png_path = base + '.png'
        saveBitMap.SaveBitmapFile(saveDC, bmp_path)
        if not os.path.exists(bmp_path):
            raise IOError(f'Failed to save bitmap file: {bmp_path}')
        Image.open(bmp_path).save(png_path, 'PNG')
        try:
            os.remove(bmp_path)
        except OSError:
            pass
        if not os.path.exists(png_path):
            raise IOError(f'Failed to save PNG screenshot: {png_path}')
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        return png_path
    finally:
        win32gui.ReleaseDC(hwnd, hwndDC)

def _capture_macos_native():
    import subprocess
    png_path = _temp_png_path()
    try:
        subprocess.run(['/usr/sbin/screencapture', '-x', '-t', 'png', png_path], check=True, capture_output=True)
    except Exception as e:
        raise IOError(f'screencapture failed: {e}')
    if not os.path.exists(png_path):
        raise IOError(f'screencapture produced no file at {png_path}')
    return png_path

def _capture_pil():
    screenshot = ImageGrab.grab()
    png_path = _temp_png_path()
    screenshot.save(png_path, 'PNG')
    screenshot.close()
    if not os.path.exists(png_path):
        raise IOError(f'Failed to save PIL screenshot: {png_path}')
    return png_path

def capture_primary_screen():
    errors = []
    if IS_WINDOWS and win32gui is not None:
        try:
            return _capture_windows()
        except Exception as e:
            import traceback
            errors.append(f'win32 failed: {e}\n{traceback.format_exc()}')
    if IS_MACOS:
        try:
            return _capture_macos_native()
        except Exception as e:
            import traceback
            errors.append(f'screencapture failed: {e}\n{traceback.format_exc()}')
    try:
        return _capture_pil()
    except Exception as e:
        import traceback
        errors.append(f'PIL failed: {e}\n{traceback.format_exc()}')
    raise IOError('Screenshot capture failed. ' + ' | '.join(errors))

def capture_screen_pil():
    try:
        return _capture_pil()
    except Exception as e:
        import traceback
        raise IOError(f'PIL screenshot failed: {e}\n{traceback.format_exc()}')

def delete_screenshot(filepath):
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
