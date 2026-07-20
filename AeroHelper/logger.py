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

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
EST = timezone(timedelta(hours=-4), name='EST')

def default_log_path(log_file='AeroHelper.log') -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent / log_file
    return Path(__file__).parent.parent / log_file

class RotatingFileHandler:

    def __init__(self, filename, max_bytes=250 * 1024 * 1024):
        self.filename = Path(filename)
        self.max_bytes = max_bytes
        self.file = None
        self._ensure_file()

    def _ensure_file(self):
        if not self.filename.exists():
            self.filename.touch()

    def _check_size(self):
        if self.filename.exists() and self.filename.stat().st_size > self.max_bytes:
            self._rotate_log()

    def _rotate_log(self):
        if not self.filename.exists():
            return
        with open(self.filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        target_size = self.max_bytes // 2
        current_size = 0
        start_index = 0
        for i in range(len(lines) - 1, -1, -1):
            line_size = len(lines[i].encode('utf-8'))
            if current_size + line_size > target_size:
                start_index = i + 1
                break
            current_size += line_size
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.writelines(lines[start_index:])

    def write(self, message):
        self._check_size()
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(message + '\n')

class Logger:

    def __init__(self, log_file='AeroHelper.log'):
        self.log_file = default_log_path(log_file)
        self.handler = RotatingFileHandler(self.log_file)
        self.logger = logging.getLogger('AeroHelper')
        self.logger.setLevel(logging.DEBUG)

    def _format_message(self, level, message):
        timestamp = datetime.now(EST).strftime('%Y-%m-%d %I:%M:%S %p EST')
        return f'[{timestamp}] [{level}] {message}'

    def _write(self, level, message):
        formatted = self._format_message(level, message)
        self.handler.write(formatted)
        print(formatted)
        return formatted

    def debug(self, message):
        self._write('DEBUG', message)

    def info(self, message):
        self._write('INFO', message)

    def warning(self, message):
        self._write('WARNING', message)

    def error(self, message, exc_info=None):
        self._write('ERROR', message)
        if exc_info:
            import sys
            import traceback
            exc_tuple = sys.exc_info() if exc_info is True else exc_info
            if exc_tuple and exc_tuple[0] is not None:
                tb_str = ''.join(traceback.format_exception(*exc_tuple))
                self.handler.write(f'Exception details:\n{tb_str}')

    def error_detailed(self, message, context=None):
        detailed_msg = f'{message}'
        if context:
            detailed_msg += f' | Context: {context}'
        self._write('ERROR', detailed_msg)

    def log_ocr(self, raw_text):
        self.debug(f'OCR Raw Text: {raw_text}')

    def log_parsed(self, data):
        self.debug(f'Parsed Data: {data}')

    def log_action(self, action):
        self.info(f'Action: {action}')
