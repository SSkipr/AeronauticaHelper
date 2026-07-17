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

from __future__ import annotations

import re

def sanitize_remote_version(raw: str | None) -> str | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s or len(s) > 32:
        return None
    upper = s.upper()
    if '<' in s or '>' in s or 'DOCTYPE' in upper or 'HTML' in upper:
        return None
    if _numeric_parts(s) is None:
        return None
    return s

def _numeric_parts(version_str: str) -> tuple[int, ...] | None:
    if not version_str or not isinstance(version_str, str):
        return None
    s = version_str.strip()
    if not s:
        return None
    if s[0] in 'vV':
        s = s[1:].strip()
    main = s.split('-', 1)[0].strip()
    nums: list[int] = []
    for part in main.split('.'):
        part = part.strip()
        if not part:
            continue
        match = re.match(r'^(\d+)', part)
        if not match:
            break
        nums.append(int(match.group(1)))
    return tuple(nums) if nums else None

def _padded(parts: tuple[int, ...] | None, length: int) -> tuple[int, ...]:
    if not parts:
        return (0,) * length
    if len(parts) >= length:
        return parts[:length]
    return parts + (0,) * (length - len(parts))

def compare_versions(local: str | None, remote: str | None) -> int:
    local_parts = _numeric_parts(local)
    remote_parts = _numeric_parts(remote)
    if local_parts is None and remote_parts is None:
        return 0
    if local_parts is None:
        return -1
    if remote_parts is None:
        return 1
    length = max(len(local_parts), len(remote_parts))
    local_padded = _padded(local_parts, length)
    remote_padded = _padded(remote_parts, length)
    if local_padded < remote_padded:
        return -1
    if local_padded > remote_padded:
        return 1
    return 0

def is_version_outdated(local: str | None, remote: str | None) -> bool:
    return compare_versions(local, remote) < 0
