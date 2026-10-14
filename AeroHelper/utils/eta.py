import math
from datetime import datetime, timedelta

STOP_DISTANCE_NM = 1.0
DOCK_THROTTLE_3NM = 3.0
DOCK_THROTTLE_15NM = 1.5
FINAL_APPROACH_NM_PER_MULT = 0.4
UNDOCK_THROTTLE_FRACTION = 0.40
POST_3NM_THROTTLE_FRACTION = 0.50
POST_15NM_THROTTLE_FRACTION = 0.30
MIN_SPEED_KT = 1.0

def heading_closure_factor(heading, target_bearing):
    if heading is None or target_bearing is None:
        return 1.0
    diff = abs(float(heading) - float(target_bearing))
    if diff > 180:
        diff = 360 - diff
    return max(math.cos(math.radians(diff)), 0.12)

def effective_speed_knots(speed, heading=None, target_bearing=None, throttle_pct=None):
    if speed is None or speed <= 0:
        return None
    if throttle_pct is not None and throttle_pct <= 0:
        return None
    closure = heading_closure_factor(heading, target_bearing)
    eff = float(speed) * closure
    if throttle_pct is not None:
        eff *= float(throttle_pct) / 100.0
    return max(eff, MIN_SPEED_KT)

def segment_speed_knots(base_speed, throttle_fraction, ocr_throttle_pct=None, is_current=False):
    if base_speed is None or base_speed <= 0:
        return None
    if is_current and ocr_throttle_pct is not None and ocr_throttle_pct > 0:
        factor = float(ocr_throttle_pct) / 100.0
    else:
        factor = throttle_fraction
    return max(float(base_speed) * factor, MIN_SPEED_KT)

def _base_speed_knots(speed, heading, target_bearing):
    if speed is None or speed <= 0:
        return None
    return max(float(speed) * heading_closure_factor(heading, target_bearing), MIN_SPEED_KT)

def _final_approach_nm(autopilot_multiplier):
    mult = autopilot_multiplier if autopilot_multiplier else 1.0
    return FINAL_APPROACH_NM_PER_MULT * float(mult)

def eta_hours_monitoring(distance, speed, heading=None, target_bearing=None, throttle_pct=None):
    if distance is None or distance <= 0:
        return 0.0 if distance is not None and distance <= 0 else None
    eff = effective_speed_knots(speed, heading, target_bearing, throttle_pct)
    if eff is None:
        return None
    return float(distance) / eff

def eta_hours_autosteer(distance, speed, heading=None, target_bearing=None, throttle_pct=None):
    if distance is None:
        return None
    remaining = max(float(distance) - STOP_DISTANCE_NM, 0.0)
    if remaining <= 0:
        return 0.0
    eff = effective_speed_knots(speed, heading, target_bearing, throttle_pct)
    if eff is None:
        return None
    return remaining / eff

def eta_hours_autopilot(
    distance,
    speed,
    heading=None,
    target_bearing=None,
    throttle_pct=None,
    phase=None,
    override_icao_code=None,
    autopilot_multiplier=None,
):
    if distance is None or distance <= 0:
        return 0.0 if distance is not None and distance <= 0 else None
    base_speed = _base_speed_knots(speed, heading, target_bearing)
    if base_speed is None:
        return None

    phase_key = str(phase or '').lower()
    if phase_key == 'undocking' or override_icao_code == 'UNDOCK':
        seg_speed = segment_speed_knots(
            base_speed,
            UNDOCK_THROTTLE_FRACTION,
            None,
            is_current=False,
        )
        if seg_speed is None:
            return None
        return float(distance) / seg_speed

    if phase_key == 'phase_2':
        eff = effective_speed_knots(speed, heading, target_bearing, throttle_pct)
        if eff is None:
            return None
        return float(distance) / eff

    final_nm = _final_approach_nm(autopilot_multiplier)
    dist = float(distance)
    segments = (
        (DOCK_THROTTLE_3NM, float('inf'), 1.0),
        (DOCK_THROTTLE_15NM, DOCK_THROTTLE_3NM, POST_3NM_THROTTLE_FRACTION),
        (final_nm, DOCK_THROTTLE_15NM, POST_15NM_THROTTLE_FRACTION),
        (0.0, final_nm, POST_15NM_THROTTLE_FRACTION),
    )

    total_hours = 0.0
    for lower, upper, throttle_fraction in segments:
        if dist <= lower:
            continue
        top = dist if upper == float('inf') else min(dist, upper)
        seg_nm = top - lower
        if seg_nm <= 0:
            continue
        is_current = dist > lower and (upper == float('inf') or dist <= upper)
        seg_speed = segment_speed_knots(
            base_speed,
            throttle_fraction,
            throttle_pct,
            is_current=is_current,
        )
        if seg_speed is None:
            return None
        total_hours += seg_nm / seg_speed

    return total_hours

def calculate_arrival_time(
    distance,
    speed,
    mode=None,
    phase=None,
    override_icao_code=None,
    autopilot_multiplier=None,
    heading=None,
    target_bearing=None,
    throttle=None,
    **_ignored,
):
    if not distance or not speed or speed == 0:
        return (None, None)

    mode_key = str(mode or '').lower()
    kwargs = {
        'distance': distance,
        'speed': speed,
        'heading': heading,
        'target_bearing': target_bearing,
        'throttle_pct': throttle,
    }
    if mode_key == 'autopilot':
        hours = eta_hours_autopilot(
            **kwargs,
            phase=phase,
            override_icao_code=override_icao_code,
            autopilot_multiplier=autopilot_multiplier,
        )
    elif mode_key == 'autosteer':
        hours = eta_hours_autosteer(**kwargs)
    else:
        hours = eta_hours_monitoring(**kwargs)

    if hours is None:
        return (None, None)
    return (datetime.now() + timedelta(hours=max(hours, 0.0)), hours)
