from __future__ import annotations

import os
import sys

def _torch_lib_candidates():
    candidates = []
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', '') or ''
        if meipass:
            candidates.append(os.path.join(meipass, 'torch', 'lib'))
    try:
        from importlib.util import find_spec
        spec = find_spec('torch')
        if spec and spec.origin:
            candidates.append(os.path.join(os.path.dirname(spec.origin), 'lib'))
    except Exception:
        pass
    return candidates

def bootstrap_torch_dlls():
    if not sys.platform.startswith('win'):
        return
    os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
    for torch_lib in _torch_lib_candidates():
        if not os.path.isdir(torch_lib):
            continue
        os.environ['PATH'] = torch_lib + os.pathsep + os.environ.get('PATH', '')
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(torch_lib)
            except Exception:
                pass
        c10 = os.path.join(torch_lib, 'c10.dll')
        if os.path.isfile(c10):
            try:
                import ctypes
                ctypes.CDLL(os.path.normpath(c10))
            except Exception:
                pass
        return

def import_torch_early():
    bootstrap_torch_dlls()
    try:
        import torch
        return True
    except Exception:
        return False
