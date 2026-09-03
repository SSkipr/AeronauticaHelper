'''
      .o.                                    ooooo   ooooo           oooo
     .888.                                   888'   888'           888
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b
   .8'     888.    d88' 88b 888""8P d88' 88b  888ooooo888  d88' 88b  888   888' 88b d88' 88b 888""8P
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

NOTIFICATION_CATEGORIES = (
    ('urgent', 'Urgent alerts', 'Fuel, heading, throttle, stale distance, and oscillation.'),
    ('mission_complete', 'Mission complete', 'Mission complete and destination reached.'),
    ('stop_quit', 'Stop / quit', 'Stops, errors, 10-cycle going-away stop, and phase fails.'),
    ('disconnect', 'Disconnect', 'Reconnect / disconnect updates.'),
    ('warnings', 'Warnings', 'Non-stop warnings (routing around land, input recovery, etc.).'),
    ('status', 'Status updates', 'Per-cycle status and AutoPilot phase updates.'),
    ('steering', 'Steering corrections', 'Left/right steer posts.'),
    ('undocking', 'Undocking status', 'Harbor undocking post.'),
)

NOTIFICATION_MODE_KEYS = ('minimal', 'urgent', 'custom')
NOTIFICATION_MODE_LABELS = ('Minimal', 'Urgent Only', 'Custom')
NOTIFICATION_MODE_TOOLTIPS = (
    'Sends all notifications. Only stop/quit pings @everyone.',
    'Only urgent alerts are sent (including oscillation). Those ping @everyone.\nStop/quit still sends and pings so you know if it halted.',
    'Sends all notifications. Opens a window to choose which categories ping @everyone.',
)

_URGENT_ONLY_SEND = frozenset({'urgent', 'stop_quit', 'disconnect'})
_URGENT_ONLY_PING = frozenset({'urgent', 'stop_quit', 'disconnect'})

DEFAULT_CUSTOM_PINGS = {
    'urgent': True,
    'mission_complete': True,
    'stop_quit': True,
    'disconnect': True,
    'warnings': False,
    'status': False,
    'steering': False,
    'undocking': False,
}

_LEGACY_MODE = {
    'all': 'minimal',
    'all notifications': 'minimal',
    'urgent-only': 'urgent',
    'urgent only': 'urgent',
}


def normalize_notification_mode(raw):
    text = str(raw or 'minimal').strip().lower()
    text = _LEGACY_MODE.get(text, text)
    if text in NOTIFICATION_MODE_KEYS:
        return text
    return 'minimal'


def mode_label(mode):
    mode = normalize_notification_mode(mode)
    try:
        return NOTIFICATION_MODE_LABELS[NOTIFICATION_MODE_KEYS.index(mode)]
    except ValueError:
        return 'Minimal'


def tooltip_for_mode(mode):
    mode = normalize_notification_mode(mode)
    try:
        return NOTIFICATION_MODE_TOOLTIPS[NOTIFICATION_MODE_KEYS.index(mode)]
    except ValueError:
        return NOTIFICATION_MODE_TOOLTIPS[0]


def normalize_custom_pings(raw):
    pings = dict(DEFAULT_CUSTOM_PINGS)
    if isinstance(raw, dict):
        for key, _label, _hint in NOTIFICATION_CATEGORIES:
            if key in raw:
                pings[key] = bool(raw[key])
    return pings


class NotificationPolicy:

    def __init__(self, mode='minimal', custom_pings=None):
        self.mode = normalize_notification_mode(mode)
        self.custom_pings = normalize_custom_pings(custom_pings)

    def should_send(self, category):
        if self.mode == 'urgent':
            return category in _URGENT_ONLY_SEND
        return True

    def should_ping(self, category):
        if not self.should_send(category):
            return False
        if self.mode == 'minimal':
            return category == 'stop_quit'
        if self.mode == 'urgent':
            return category in _URGENT_ONLY_PING
        return bool(self.custom_pings.get(category, False))
