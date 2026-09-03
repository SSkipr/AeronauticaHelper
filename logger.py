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
Version 4.1.4
'''

import logging
import os
import sys
import threading
from collections import deque
from pathlib import Path
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    _LOG_TZ = ZoneInfo('America/New_York')
except Exception:
    _LOG_TZ = timezone(timedelta(hours=-5), name='EST')

def default_log_path(log_file='AeroHelper.log') -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent / log_file
    return Path(__file__).parent.parent / log_file

class RotatingFileHandler:

    def __init__(self, filename, max_bytes=10 * 1024 * 1024):
        self.filename = Path(filename)
        self.max_bytes = max_bytes
        self._lock = threading.Lock()
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
        keep = max(self.max_bytes // 2, 1)
        size = self.filename.stat().st_size
        if size <= keep:
            return
        with open(self.filename, 'rb') as f:
            f.seek(size - keep)
            data = f.read()
        nl = data.find(b'\n')
        if nl != -1:
            data = data[nl + 1:]
        tmp = self.filename.with_name(self.filename.name + '.tmp')
        with open(tmp, 'wb') as f:
            f.write(data)
        os.replace(tmp, self.filename)

    def write(self, message):
        with self._lock:
            self._check_size()
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(message + '\n')

class Logger:

    def __init__(self, log_file='AeroHelper.log'):
        self.log_file = default_log_path(log_file)
        self.handler = RotatingFileHandler(self.log_file)
        self.logger = logging.getLogger('AeroHelper')
        self.logger.setLevel(logging.DEBUG)
        self.ocr_debug_enabled = False
        self._ocr_lock = threading.Lock()
        self._ocr_ring = deque(maxlen=20)
        self._error_ocr_remaining = 0
        self._error_ocr_after_seen = 0

    def _format_message(self, level, message):
        now = datetime.now(_LOG_TZ)
        tz_name = now.tzname() or 'EST'
        timestamp = now.strftime(f'%Y-%m-%d %I:%M:%S %p {tz_name}')
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

    def _write_ocr_entry(self, entry, tag='OCR', label=''):
        text = entry.get('text') or ''
        source = entry.get('source') or 'extract'
        image = entry.get('image') or '?'
        sections = entry.get('sections') or {}
        header = f'[{tag}]'
        if label:
            header += f' {label}'
        header += f' source={source} image={image} chars={len(text)}'
        parts = [header]
        if sections:
            for name, body in sections.items():
                chunk = body if body is not None else ''
                parts.append(f'--- {name} ({len(chunk)} chars) ---')
                parts.append(chunk)
        else:
            parts.append(f'--- combined ({len(text)} chars) ---')
            parts.append(text)
        level = 'WARNING' if tag == 'ERROR-OCR' else 'DEBUG'
        self._write(level, '\n'.join(parts))

    def capture_ocr(self, text, source='extract', sections=None, image_path=''):
        entry = {
            'text': text or '',
            'source': source,
            'sections': sections or {},
            'image': os.path.basename(str(image_path or '')) or '?',
        }
        with self._ocr_lock:
            self._ocr_ring.append(entry)
            dump_after = self._error_ocr_remaining > 0
            after_index = 0
            if dump_after:
                self._error_ocr_after_seen += 1
                after_index = self._error_ocr_after_seen
                self._error_ocr_remaining -= 1
                finished = self._error_ocr_remaining <= 0
            else:
                finished = False
            debug_on = self.ocr_debug_enabled
        if dump_after:
            self._write_ocr_entry(entry, tag='ERROR-OCR', label=f'after (+{after_index})')
            if finished:
                self.info('[ERROR-OCR] -- context capture complete --')
        elif debug_on:
            self._write_ocr_entry(entry, tag='OCR')
        else:
            self.debug(f'OCR: {len(entry["text"])} chars')

    def activate_error_ocr_dump(self, before=3, after=2):
        with self._ocr_lock:
            prior = list(self._ocr_ring)[-before:]
            self._error_ocr_remaining = after
            self._error_ocr_after_seen = 0
        self.warning('[ERROR-OCR] -- captures before error --')
        count = len(prior)
        if not count:
            self.warning('[ERROR-OCR] (no prior OCR captures)')
            return
        for i, entry in enumerate(prior):
            offset = i - count + 1
            label = 'at error' if offset == 0 else f'before ({offset:+d})'
            self._write_ocr_entry(entry, tag='ERROR-OCR', label=label)

    def log_ocr(self, raw_text):
        return

    def log_parsed(self, data):
        self.debug(f'[PARSED] {data}')

    def log_action(self, action):
        self.info(f'[ACTION] {action}')
