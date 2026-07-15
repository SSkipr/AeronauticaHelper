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
Version 4.0.0
'''

import math

def shortest_angle_diff_signed(target, current):
    a = (target - current) % 360
    if a > 180:
        a -= 360
    return a

def shortest_angle_diff_abs(target, current):
    return abs(shortest_angle_diff_signed(target, current))

class HeadingEWMA:

    def __init__(self, alpha=0.35):
        self.alpha = alpha
        self.x = None
        self.y = None
        self.value = None

    def update(self, heading_deg):
        if heading_deg is None:
            return self.value
        rad = math.radians(heading_deg)
        nx, ny = (math.cos(rad), math.sin(rad))
        if self.x is None:
            self.x, self.y = (nx, ny)
        else:
            self.x = (1 - self.alpha) * self.x + self.alpha * nx
            self.y = (1 - self.alpha) * self.y + self.alpha * ny
        self.value = math.degrees(math.atan2(self.y, self.x)) % 360
        return self.value

    def reset(self):
        self.x = None
        self.y = None
        self.value = None

class DistanceEWMA:

    def __init__(self, alpha=0.35):
        self.alpha = alpha
        self.value = None

    def update(self, x):
        if x is None:
            return self.value
        if self.value is None:
            self.value = x
        else:
            self.value = (1 - self.alpha) * self.value + self.alpha * x
        return self.value

    def reset(self):
        self.value = None

def blended_target_bearing(distance, entry_bearing, dock_bearing):
    t = max(0, min(1, (5 - distance) / (5 - 0.2)))
    signed = shortest_angle_diff_signed(dock_bearing, entry_bearing)
    return (entry_bearing + t * signed) % 360

def compute_push_time_seconds(delta_nm, speed_knots, multiplier=1.0):
    if speed_knots is None or speed_knots <= 0.5:
        return 3 * multiplier
    time_seconds = delta_nm / speed_knots * 3600.0
    return max(1.0, min(20.0, time_seconds))
