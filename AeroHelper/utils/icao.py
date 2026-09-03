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

import re

ICAO_CODES = {'TTLG', 'KPIS', 'EGNA', 'ATFA', 'KGA', 'EDHB', 'ATDA', 'EKKJ', 'LSTA', 'EGEC', 'VNHO', 'KMEA', 'NAHS', 'KHF', 'UHNF', 'KAA', 'MUWI', 'NTAA', 'RJKP', 'NTCA', 'KPPA', 'EGCA', 'ANBA', 'NTBA', 'RJTS', 'AFTA', 'RJKS', 'EGBK', 'EGSB', 'WSPA', 'KFFA', 'UEWA', 'EGMO', 'EKKP', 'LICR', 'ESNW', 'AAHA', 'EBAB', 'AEMB', 'AHBN', 'AMGH', 'AMRG', 'APET', 'ARHA', 'ATRQ', 'ATRK', 'ARTN', 'AVYS', 'KKRA', 'SDRA', 'KLMA', 'KOIA', 'SKPD', 'EGBH', 'KGZI', 'SYKT', 'ATRI', 'VDSA', 'KNET', 'CTCA', 'CUTH', 'BIEN', 'SLFG', 'LGHE', 'PMEA', 'SKGF', 'LGPL', 'EGAN', 'URRA', 'ECAF', 'WSTN', 'ATOM', 'EKNO', 'LIEA', 'NTRI', 'LPPM', 'EHGA', 'AVLF', 'EFYV', 'UNFB', 'VNBA', 'ENNS', 'WSPB', 'BIKY', 'VMTM', 'SPOD', 'CEMA', 'EGAB', 'BIAK', 'ASRF', 'KCLA', 'KLAB', 'CVFA', 'LPAA', 'SCSM', 'CNAB', 'LDUA', 'RCMH', 'VTRD', 'VVSL', 'EGOP', 'RKBO', 'LESD', 'BIJF', 'BIOA', 'SYHP', 'RKJP', 'VHAL', 'EICB', 'CTIK', 'LESA', 'EGLH', 'KHIA', 'KKBI', 'ULIA', 'CRIZ', 'SCTL', 'LBYA', 'EDSA', 'UHFI', 'LFVI', 'ZBHM', 'RJUB', 'ZBYN', 'EGAI', 'WSML', 'KNIA', 'OSSL', 'VHTC', 'EGBH', 'KBRS', 'KCGH', 'KDCH', 'BINH', 'CNGH', 'EKUH', 'KNGH', 'UHFU', 'BIHA', 'EKHA', 'KHMC', 'SYHC', 'SBHG', 'CIRO', 'KKUH', 'ULGH', 'BILF', 'UMCH', 'KNHH', 'UNSU', 'KOCH', 'KODS', 'OBS1', 'BIOG', 'PRYM', 'PR1', 'PR2', 'PR3', 'PR4', 'PR5', 'PR6', 'PR7', 'PR8', 'PR9', 'PR10', 'PR11', 'PR12', 'PR13', 'URCH', 'EGHH', 'EGOH', 'SCSC', 'EKSH', 'EKSA', 'ESNO', 'EKGA', 'TDH', 'CTGH', 'UASA', 'RJUH', 'LIUK', 'EDUS', 'CVOY', 'WR1', 'WR2', 'WR3', 'WR4', 'WR5', 'WR6', 'WR7', 'WR8', 'WR9', 'WR10', 'WR11', 'WR12', 'WR13', 'ADMS', 'ESRB', 'CMJA', 'CHIC', 'ENGF', 'BIGB', 'CHVD', 'ENIH', 'ESID', 'CFFL', 'BING', 'KODF', 'VVPL', 'BIVS', 'CSRO', 'ENSV', 'ENFR', 'BGSB', 'CNJO', 'TTLA', 'DEST'}

def _compile_airport_patterns():
    compiled = []
    for code in ICAO_CODES:
        if code == 'DEST':
            continue
        compiled.append((code, (
            re.compile(f'\\b{re.escape(code)}\\s+(\\d{{2,3}})\\b'),
            re.compile(f'{re.escape(code)}\\s+(\\d{{2,3}})(?:[\'°]|(?!\\.\\d)(?!\\d))'),
            re.compile(f'\\b{re.escape(code)}(\\d{{2,3}})(?!\\d)'),
        )))
    return compiled

_AIRPORT_PATTERNS = _compile_airport_patterns()

_NON_AIRPORT_TOKEN_BLACKLIST = {
    'AUTO', 'CHAT', 'CLEAR', 'CTRLS', 'FUEL', 'HIDE', 'HOG', 'HOLD', 'HSI', 'KNOT', 'KNOTS',
    'MEMORY', 'MINUTE', 'MINUTES', 'ND', 'OPEN', 'OCR', 'PAUSE', 'PRESS', 'RUN', 'SAIL', 'SHOW',
    'SPEED', 'STEER', 'SYS', 'THROT', 'THROTTLE', 'TRACK', 'TRK', 'HDG', 'HIDDEN', 'UNITED',
    'UPTIME', 'VERSION', 'SERVER', 'ALTITUDE', 'CONTROLS', 'SYSTEM', 'AVAILABLE', 'END',
    'ILS', 'CDI', 'OBS',
    'TRE', 'HOURS', 'HOUR', 'DEY', 'CMR', 'OMB', 'ESTOK', 'ESOK', 'EST', 'TOK', 'LTE9T',
    'SOUZZ', 'PLS', 'YCLED', 'OOO', 'LUKAT', 'ESVK', 'ELDIS', 'LDIS', 'OKPLS',
    'RUNNING', 'STEERING', 'TARGET', 'PHASE',
}


_DEST_WORD = r'(?:[DBPO]EST|DES[TDZY\].,]?)'
_DEST_AFTER_NUMBER = r'(?!\.\d)(?!\d)(?![\s°\']*(?:NM|NMI|MI)\b)'
_DEST_STRICT_PATTERN = re.compile(_DEST_WORD + r'\]?\s*(\d{1,3})' + _DEST_AFTER_NUMBER)
_DEST_FUZZY_PATTERN = re.compile(_DEST_WORD + r'[^\d]{0,3}(\d{2,3})' + _DEST_AFTER_NUMBER)
_DEST_GLUED_PATTERN = re.compile(_DEST_WORD + r'[^\d]{0,2}(\d{2,3})' + _DEST_AFTER_NUMBER)
_OVERLAY_CODE_SPAN = re.compile(
    r'\d{1,4}\s*°?\s*[–\-•]\s*\d{1,4}\s*°?\s*\(\s*[A-Z][A-Z0-9]{2,7}\s*\)|'
    r'\d{1,4}\s*°\s*\(\s*[A-Z][A-Z0-9]{2,7}\s*\)|'
    r'\(\s*[A-Z][A-Z0-9]{2,7}\s*\)'
)
_DEST_ALIAS_TOKENS = frozenset({'DEST', 'DES', 'PEST', 'BEST', 'OEST', 'DESD', 'DEZT', 'DESZ', 'DESY'})
_NON_AIRPORT_ALPHA_PATTERN = re.compile(
    r"\b([A-Z][A-Z0-9]{2,4})\s+(?:B['°O0]?\s*)?(\d{2,4})(?:['°]|(?!\.\d)(?!\d))",
)
_NON_AIRPORT_DECIMAL_CODE_PATTERN = re.compile(
    r"\b([A-Z]\d{1,2}\.\d+)\s+(?:B['°O0]?\s*)?(\d{2,4})(?:['°]|(?!\.\d)(?!\d))",
)

def is_valid_icao(code):
    return code.upper() in ICAO_CODES

def is_junk_icao_token(code):
    return bool(code) and code.upper() in _NON_AIRPORT_TOKEN_BLACKLIST

def _strip_overlay_artifacts(text_upper):
    return _OVERLAY_CODE_SPAN.sub(' ', text_upper)

def _normalize_text(text):
    return _strip_overlay_artifacts(text.replace(',', '.').upper())

def _sanitize_bearing(bearing):
    if bearing is None:
        return None
    try:
        value = int(bearing)
    except (TypeError, ValueError):
        return None
    if 0 <= value <= 360:
        return value
    if value < 1000:
        truncated = int(str(value)[:2])
        if 0 <= truncated <= 360:
            return truncated
    return None

def _bearing_valid(bearing):
    return bearing is not None and 0 <= bearing <= 360

def _is_non_airport_code(token):
    code = token.upper()
    if code in ICAO_CODES or code in _NON_AIRPORT_TOKEN_BLACKLIST or code in _DEST_ALIAS_TOKENS:
        return False
    if code.startswith(('TRK', 'HDG', 'HOG', 'H0G')):
        return False
    if re.fullmatch(r'[A-Z]\d{1,2}\.\d+', code):
        return True
    if re.fullmatch(r'[A-Z][A-Z0-9]{2,4}', code) and any(ch.isalpha() for ch in code):
        return True
    return False

def _is_runway_designator(text_upper, bearing_end):

    if bearing_end is None or bearing_end >= len(text_upper):
        return False
    return text_upper[bearing_end] in ('L', 'R', 'C')

def _append_bearing_match(matches, code, raw_bearing, end_pos=None):
    bearing = _sanitize_bearing(int(raw_bearing))
    if bearing is not None and _bearing_valid(bearing):
        if end_pos is None:
            matches.append((code.upper(), bearing))
        else:
            matches.append((code.upper(), bearing, end_pos))

def _collect_dest_candidates(text_upper):
    candidates = []
    for pattern in (_DEST_STRICT_PATTERN, _DEST_FUZZY_PATTERN, _DEST_GLUED_PATTERN):
        for match in pattern.finditer(text_upper):
            if _is_runway_designator(text_upper, match.end(1)):
                continue
            try:
                bearing = _sanitize_bearing(int(match.group(1)))
                if bearing is not None:
                    candidates.append((len(match.group(1)), match.end(), bearing))
            except ValueError:
                pass
    return candidates

def _collect_airport_matches(text_upper):
    matches = []
    for code, patterns in _AIRPORT_PATTERNS:
        for pattern in patterns:
            for match in pattern.finditer(text_upper):
                try:
                    _append_bearing_match(matches, code, match.group(1), match.end())
                except ValueError:
                    pass
    return matches

def _collect_non_airport_matches(text_upper):
    matches = []
    for pattern in (_NON_AIRPORT_ALPHA_PATTERN, _NON_AIRPORT_DECIMAL_CODE_PATTERN):
        for match in pattern.finditer(text_upper):
            code = match.group(1)
            if not _is_non_airport_code(code):
                continue
            if _is_runway_designator(text_upper, match.end(2)):
                continue
            try:
                _append_bearing_match(matches, code, match.group(2), match.end())
            except ValueError:
                pass
    return matches

def _dest_fragment_visible(text_upper):
    return bool(re.search(_DEST_WORD, text_upper))

def is_icao_match_suspicious(icao, bearing, text):
    if icao is None or bearing is None:
        return True
    if not _bearing_valid(bearing):
        return True
    if is_junk_icao_token(icao):
        return True
    text_upper = _normalize_text(text)
    if icao == 'DEST' or icao in _DEST_ALIAS_TOKENS:
        return False
    if is_valid_icao(icao) and _dest_fragment_visible(text_upper):
        return True
    return False

def _last_match_for_code(matches, code):
    if not code or not matches:
        return None
    code = code.upper()
    found = None
    for item in matches:
        match_code, bearing = item[0], item[1]
        if match_code == code:
            found = (match_code, bearing)
    return found

def _pick_last_by_position(matches):
    if not matches:
        return None
    ordered = sorted(matches, key=lambda item: item[2] if len(item) > 2 else 0)
    code, bearing = ordered[-1][0], ordered[-1][1]
    return (code, bearing)

def extract_icao_and_bearing(text, preferred_code=None, prefer_custom=False):
    text_upper = _normalize_text(text)
    preferred = (preferred_code or '').upper().strip() or None
    if preferred and is_junk_icao_token(preferred):
        preferred = None
    airport_matches = _collect_airport_matches(text_upper)
    non_airport_matches = _collect_non_airport_matches(text_upper)
    searchable = airport_matches + non_airport_matches
    if preferred:
        preferred_hit = _last_match_for_code(searchable, preferred)
        if preferred_hit is not None and not is_junk_icao_token(preferred_hit[0]):
            return preferred_hit
    allow_dest = not prefer_custom or preferred is None
    if allow_dest:
        dest_candidates = _collect_dest_candidates(text_upper)
        if dest_candidates:
            dest_candidates.sort()
            bearing = dest_candidates[-1][2]
            if _bearing_valid(bearing):
                return ('DEST', bearing)
        if _dest_fragment_visible(text_upper):
            return (None, None)
    ranked = searchable if prefer_custom else airport_matches
    if ranked:
        picked = _pick_last_by_position(ranked)
        if picked and not is_junk_icao_token(picked[0]):
            return picked
    return (None, None)
