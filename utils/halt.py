'''
      .o.                                    ooooo   ooooo           oooo
     .888.                                   888'   888'           888
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b
   .8' 888.    d88' 88b 888""8P d88' 88b  888ooooo888  d88' 88b  888   888' 88b 888""8P
  .88ooo8888.   888ooo888  888     888   888  888     888  888ooo888  888   888   888 888ooo888  888
 .8'     888.  888    .o  888     888   888  888     888  888    .o  888   888   888 888    .o  888
o.oooooo..o88.oooooo..oPoooo88b    Yo8od8P' o888o   o888o Y8bod8P' o888o  888bod8P' Y8bod8P' d888b
d8P'    Y8 d8P'    Y8 888         "'                                    888
    10|Y88bo.      Y88bo.       888  oooo  oooo  oo.ooooo.  oooo d8b              o888o
 "Y8888o.   "Y8888o.   888 .8P'   888   888' 88b 888""8P
     "Y88b      "Y88b  888888.     888   888   888  888
oo     .d8P oo     .d8P  888 `88b.   888   888   888  888
8""88888P'  8""88888P'  o888o o888o o888o  888bod8P' d888b
                                           888
                                          o888o

https://aeronautica-helper.vercel.app
https://github.com/SSkipr/AeronauticaHelper
Version 4.1.4
'''

import threading
import time as _time

_halt = threading.Event()
_scope = threading.local()
_original_sleep = _time.sleep
_patched = False


class HaltRequested(BaseException):
    pass


def request_halt():
    _halt.set()


def clear_halt():
    _halt.clear()


def is_halted():
    return _halt.is_set()


def in_halt_scope():
    return bool(getattr(_scope, 'active', False))


def wait_for_halt(timeout):
    return _halt.wait(timeout=timeout)


def raise_if_halted():
    if is_halted() and in_halt_scope():
        raise HaltRequested()


def interruptible_sleep(seconds):

    if in_halt_scope():
        raise_if_halted()
    elif is_halted():
        return False
    seconds = float(seconds)
    if seconds <= 0:
        if in_halt_scope():
            raise_if_halted()
        return not is_halted()
    if _halt.wait(timeout=seconds):
        if in_halt_scope():
            raise HaltRequested()
        return False
    if in_halt_scope():
        raise_if_halted()
    return not is_halted()


def _halt_aware_sleep(seconds):
    interruptible_sleep(seconds)


def install_interruptible_sleep():
    global _patched
    if _patched:
        return
    _time.sleep = _halt_aware_sleep
    _patched = True


class halt_scope:


    def __enter__(self):
        _scope.active = True
        raise_if_halted()
        return self

    def __exit__(self, exc_type, exc, tb):
        _scope.active = False
        return exc_type is HaltRequested


install_interruptible_sleep()
