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

import re
from AeroHelper.utils.icao import extract_icao_and_bearing

_KM_TO_NM = 1.0 / 1.852
_MI_TO_NM = 1609.344 / 1852.0
_KMH_TO_KNOTS = 1.0 / 1.852
_MPH_TO_KNOTS = 1609.344 / 1852.0
_MS_TO_KNOTS = 3600.0 / 1852.0

class FlightData:

    def __init__(self):
        self.speed = None
        self.throttle = None
        self.fuel = None
        self.distance = None
        self.heading = None
        self.target_bearing = None
        self.icao_code = None
        self.valid = False

    def to_dict(self):
        return {'speed': self.speed, 'throttle': self.throttle, 'fuel': self.fuel, 'distance': self.distance, 'heading': self.heading, 'target_bearing': self.target_bearing, 'icao_code': self.icao_code, 'valid': self.valid}

class OCRParser:
    _LABEL_SEP = '[.:\\s]+'
    _KNOTS = 'knot[5s]?'
    # Preferred: knots / nm. Also accepts km/h, mph, m/s and km, miles.
    _SPEED_UNIT = '(?:knot[5s]?|km/?f?h|mph|m/?s|mps)'
    _DISTANCE_UNIT = '(?:nm|NM|\\bn\\b|km|miles?|\\bmi\\b)'

    def __init__(self):
        sep = self._LABEL_SEP
        speed_unit = self._SPEED_UNIT
        dist = self._DISTANCE_UNIT
        self.patterns = {
            'speed': re.compile(rf'Speed{sep}(\d+(?:\.\d+)?)\s*({speed_unit})', re.IGNORECASE),
            'throttle': re.compile(rf'Thrott?le{sep}(\d+(?:\.\d+)?)\s*%', re.IGNORECASE),
            # % is optional: EasyOCR often emits "Fuel: 83.29 Abandon" with no percent sign
            'fuel': re.compile(rf'Fuel{sep}(\d+(?:\.\d+)?)\s*%?', re.IGNORECASE),
            'distance': re.compile(rf'Distance{sep}(\d+(?:\.\d+)?)\s*({dist})', re.IGNORECASE),
            'heading': re.compile(r'(?:HDG|HOG)[:.\s]*(\d{1,3})', re.IGNORECASE),
        }

    def _normalize_ocr_text(self, text):
        normalized = text.replace(',', '.')
        # OCR often produces 155.,4 or 155..4 instead of 155.4
        normalized = re.sub(r'(\d+)\.+(\d+)', r'\1.\2', normalized)
        normalized = re.sub(r'\bKnot5\b', 'Knots', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'(\d+(?:\.\d+)?)\s+n(?!\w)', r'\1 nm', normalized, flags=re.IGNORECASE)
        return normalized

    def _distance_to_nm(self, value, unit):
        if not unit:
            return value
        u = unit.lower()
        if u == 'km':
            return value * _KM_TO_NM
        if u in ('mile', 'miles', 'mi'):
            return value * _MI_TO_NM
        return value

    def _speed_to_knots(self, value, unit):
        if not unit:
            return value
        u = unit.lower().replace(' ', '')
        if 'km' in u:
            return value * _KMH_TO_KNOTS
        if u in ('mph', 'mp/h'):
            return value * _MPH_TO_KNOTS
        if u in ('m/s', 'ms', 'mps'):
            return value * _MS_TO_KNOTS
        return value

    def _normalize_fuel(self, fuel_value):
        if 0 <= fuel_value <= 100:
            return fuel_value
        # WinRT often drops the decimal: 84.3% -> 843%
        if 100 < fuel_value < 1000:
            fixed = fuel_value / 10.0
            if 0 <= fixed <= 100:
                return fixed
        return None

    def parse(self, text, preferred_code=None, prefer_custom=False):
        normalized_text = self._normalize_ocr_text(text)
        data = FlightData()
        speed_matches = list(self.patterns['speed'].finditer(normalized_text))
        if speed_matches:
            try:
                best_match = speed_matches[-1]
                data.speed = self._speed_to_knots(float(best_match.group(1)), best_match.group(2))
            except (ValueError, IndexError):
                pass
        throttle_matches = list(self.patterns['throttle'].finditer(normalized_text))
        if throttle_matches:
            try:
                vals = [float(m.group(1)) for m in throttle_matches]
                nonzero = [v for v in vals if v > 0]
                if nonzero and any(v == 0 for v in vals):
                    data.throttle = nonzero[-1]
                else:
                    data.throttle = vals[-1]
            except (ValueError, IndexError):
                pass
        fuel_matches = list(self.patterns['fuel'].finditer(normalized_text))
        if fuel_matches:
            valid_matches = []
            for match in fuel_matches:
                try:
                    fuel_value = self._normalize_fuel(float(match.group(1)))
                    match_text = match.group(0)
                    if fuel_value is not None and 'DEST' not in match_text.upper():
                        valid_matches.append((match, fuel_value))
                except (ValueError, IndexError):
                    continue
            if valid_matches:
                best_match, fuel_value = valid_matches[-1]
                data.fuel = fuel_value
            elif fuel_matches:
                try:
                    fuel_value = self._normalize_fuel(float(fuel_matches[-1].group(1)))
                    if fuel_value is not None:
                        data.fuel = fuel_value
                except (ValueError, IndexError):
                    pass
        distance_matches = list(self.patterns['distance'].finditer(normalized_text))
        if distance_matches:
            try:
                vals = [self._distance_to_nm(float(m.group(1)), m.group(2)) for m in distance_matches]
                if len(vals) >= 2:
                    lo, hi = (min(vals), max(vals))
                    if hi - lo <= 2.0:
                        data.distance = lo
                    else:
                        data.distance = vals[-1]
                else:
                    data.distance = vals[0]
            except (ValueError, IndexError, TypeError):
                pass
        heading_match = self.patterns['heading'].search(normalized_text)
        if heading_match:
            try:
                data.heading = int(heading_match.group(1))
            except ValueError:
                pass
        icao_code, bearing = extract_icao_and_bearing(
            normalized_text,
            preferred_code=preferred_code,
            prefer_custom=prefer_custom,
        )
        if icao_code and bearing is not None:
            data.icao_code = icao_code
            data.target_bearing = bearing
        data.valid = self._validate(data)
        return data

    def _validate(self, data):
        has_distance = data.distance is not None
        has_speed = data.speed is not None
        if not (has_distance or has_speed):
            return False
        return True
