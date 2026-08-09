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

import base64
from pathlib import Path
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QBuffer, QByteArray

def _icon_data():
    icon_path = Path(__file__).resolve().parent.parent / 'icon.txt'
    try:
        raw = icon_path.read_text(encoding='utf-8').strip()
    except OSError:
        return None
    if ',' in raw and raw.startswith('data:image/'):
        raw = raw.split(',', 1)[1]
    try:
        return base64.b64decode(raw)
    except ValueError:
        return None

def load_app_pixmap(size=None):
    data = _icon_data()
    if not data:
        return QPixmap()
    pixmap = QPixmap()
    if not pixmap.loadFromData(data):
        return QPixmap()
    if size:
        return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pixmap

def load_app_icon():
    pixmap = load_app_pixmap()
    if pixmap.isNull():
        return QIcon()
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return icon

def apply_windows_taskbar_icons(widgets, qicon):
    import io
    import os
    import sys
    import tempfile
    if sys.platform != 'win32' or qicon is None or qicon.isNull():
        return
    try:
        import win32con
        import win32gui
    except ImportError:
        return
    try:
        from PIL import Image
    except ImportError:
        return
    pm = qicon.pixmap(256, 256)
    if pm.isNull():
        return
    arr = QByteArray()
    qbuf = QBuffer(arr)
    qbuf.open(QBuffer.WriteOnly)
    if not pm.save(qbuf, 'PNG'):
        qbuf.close()
        return
    qbuf.close()
    try:
        png_bytes = arr.data()
        if isinstance(png_bytes, memoryview):
            png_bytes = png_bytes.tobytes()
        im = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
    except OSError:
        return
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix='.ico')
        os.close(fd)
        im.save(tmp_path, format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    except OSError:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return
    WM_SETICON = 128
    ICON_SMALL = 0
    ICON_BIG = 1
    hicon_sm = win32gui.LoadImage(0, tmp_path, win32con.IMAGE_ICON, 16, 16, win32con.LR_LOADFROMFILE)
    hicon_lg = win32gui.LoadImage(0, tmp_path, win32con.IMAGE_ICON, 256, 256, win32con.LR_LOADFROMFILE)
    if not hicon_lg:
        hicon_lg = win32gui.LoadImage(0, tmp_path, win32con.IMAGE_ICON, 48, 48, win32con.LR_LOADFROMFILE)
    try:
        for widget in widgets:
            if widget is None:
                continue
            try:
                hwnd = int(widget.winId())
            except (TypeError, ValueError, OverflowError):
                continue
            if not hwnd:
                continue
            if hicon_lg:
                win32gui.SendMessage(hwnd, WM_SETICON, ICON_BIG, hicon_lg)
            if hicon_sm:
                win32gui.SendMessage(hwnd, WM_SETICON, ICON_SMALL, hicon_sm)
    finally:
        try:
            if tmp_path:
                os.unlink(tmp_path)
        except OSError:
            pass
