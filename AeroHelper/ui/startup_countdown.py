'''
      .o.                                    ooooo   ooooo           oooo
     .888.                                   888'   888'           888
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b
   .8' 888.    d88' 88b 888""8P d88' 88b  888ooooo888  d88' 88b  888   888' 88b d88' 88b 888""8P
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
Version 4.1.0
'''

import math
import time
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QRadialGradient, QLinearGradient, QPainterPath
from AeroHelper.ui.app_icon import load_app_icon
from AeroHelper.utils.platform import get_app_font_family

APP_FONT_FAMILY = get_app_font_family()
BG_TOP = QColor(5, 7, 19, 248)
BG_BOTTOM = QColor(8, 16, 36, 250)
ACCENT = QColor(125, 211, 252)
ACCENT_SOFT = QColor(103, 232, 249)
TEXT_PRIMARY = QColor(248, 251, 255)

class StartupCountdownOverlay(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._remaining = 10
        self._total = 10.0
        self._started_at = 0.0
        self._phase = 0.0
        self._tick_pulse = 0.0
        self._active = False
        self._last_shown = -1
        self._init_ui()
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_anim)

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        icon = load_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self.setAttribute(Qt.WA_TranslucentBackground)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addStretch(9)
        self.headline = QLabel()
        self.headline.setAlignment(Qt.AlignCenter)
        self.headline.setWordWrap(True)
        self.headline.setStyleSheet('color: #F8FBFF; background: transparent;')
        root.addWidget(self.headline)
        root.addSpacing(14)
        tip = QLabel('Hands off! Intervene only after an error, if applicable.')
        tip.setAlignment(Qt.AlignCenter)
        tip.setWordWrap(True)
        tip.setStyleSheet('color: rgba(168, 183, 216, 0.92); background: transparent;')
        root.addWidget(tip)
        root.addSpacing(22)
        self.cook = QLabel('LET IT COOK')
        self.cook.setAlignment(Qt.AlignCenter)
        self.cook.setStyleSheet('color: #67E8F9; background: transparent; letter-spacing: 4px;')
        root.addWidget(self.cook)
        root.addStretch(2)
        self._tip = tip
        self.hide()

    def _apply_responsive_fonts(self):
        short = min(self.width(), self.height())
        head = max(18, int(short * 0.028))
        tip = max(12, int(short * 0.018))
        cook = max(28, int(short * 0.045))
        self.headline.setFont(QFont(APP_FONT_FAMILY, head, QFont.Bold))
        self._tip.setFont(QFont(APP_FONT_FAMILY, tip))
        self.cook.setFont(QFont(APP_FONT_FAMILY, cook, QFont.Bold))
        side = max(36, int(short * 0.06))
        self.layout().setContentsMargins(side, side, side, side)

    def _cover_primary_screen(self):
        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())
        else:
            self.setGeometry(0, 0, 1280, 720)

    def _elapsed(self):
        if not self._started_at:
            return 0.0
        return max(0.0, time.monotonic() - self._started_at)

    def _remaining_seconds(self):
        return max(0.0, self._total - self._elapsed())

    def _remaining_ratio(self):
        if self._total <= 0:
            return 0.0
        return max(0.0, min(1.0, self._remaining_seconds() / self._total))

    def _refresh_headline(self):
        shown = max(0, int(math.ceil(self._remaining_seconds() - 1e-6))) if self._remaining_seconds() > 0 else 0
        if shown == self._last_shown and self._remaining > 0:
            return
        if shown != self._last_shown and self._last_shown >= 0:
            self._tick_pulse = 1.0
        self._last_shown = shown
        self._remaining = shown
        unit = 'second' if shown == 1 else 'seconds'
        self.headline.setText(f'AeroHelper starting in {shown} {unit}')

    @pyqtSlot(int)
    def begin(self, seconds=10):
        seconds = max(1, int(seconds))
        self._total = float(seconds)
        self._remaining = seconds
        self._last_shown = -1
        self._started_at = time.monotonic()
        self._phase = 0.0
        self._tick_pulse = 1.0
        self._active = True
        self._cover_primary_screen()
        self._apply_responsive_fonts()
        self._refresh_headline()
        self.show()
        self.raise_()
        self.activateWindow()
        self._anim_timer.start(16)
        self.update()

    @pyqtSlot()
    def cancel(self):
        was_active = self._active
        self._stop_timers()
        self._active = False
        self.hide()
        if was_active:
            self.finished.emit()

    def _stop_timers(self):
        self._anim_timer.stop()

    def _on_anim(self):
        if not self._active:
            return
        self._phase = (self._phase + 0.04) % (math.pi * 2)
        if self._tick_pulse > 0:
            self._tick_pulse = max(0.0, self._tick_pulse - 0.04)
        remaining = self._remaining_seconds()
        self._refresh_headline()
        if remaining <= 0:
            self._remaining = 0
            self._complete()
            return
        self.update()

    def _complete(self):
        self._stop_timers()
        self._active = False
        self.hide()
        self.finished.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._active:
            self._apply_responsive_fonts()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0.0, BG_TOP)
        gradient.setColorAt(0.55, QColor(6, 12, 28, 248))
        gradient.setColorAt(1.0, BG_BOTTOM)
        painter.fillRect(self.rect(), gradient)
        cx, cy = w * 0.5, h * 0.30
        remaining_ratio = self._remaining_ratio() if self._active else 1.0
        pulse = 0.55 + 0.45 * math.sin(self._phase)
        tick = self._tick_pulse
        short = min(w, h)
        glow = QRadialGradient(cx, cy, short * 0.38)
        glow.setColorAt(0.0, QColor(125, 211, 252, int(48 + 30 * pulse + 36 * tick)))
        glow.setColorAt(0.5, QColor(103, 232, 249, int(14 + 12 * pulse)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(int(cx - short * 0.38), int(cy - short * 0.38), int(short * 0.76), int(short * 0.76))
        base_r = short * 0.14
        track_r = int(base_r + 44)
        track_pen = QPen(QColor(255, 255, 255, 28), 5)
        track_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(int(cx - track_r), int(cy - track_r), track_r * 2, track_r * 2)
        for i in range(2):
            expand = i * 40 + 12 * math.sin(self._phase + i)
            radius = base_r + expand + tick * 12
            alpha = max(20, int(90 - i * 28))
            painter.setPen(QPen(QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), alpha), 2))
            painter.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))
        arc_pen = QPen(QColor(ACCENT_SOFT.red(), ACCENT_SOFT.green(), ACCENT_SOFT.blue(), 230), 5)
        arc_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(arc_pen)
        span = int(-360 * 16 * remaining_ratio)
        if remaining_ratio > 0.001:
            painter.drawArc(int(cx - track_r), int(cy - track_r), track_r * 2, track_r * 2, int(90 * 16), span)
        number = str(max(0, self._remaining))
        scale = 1.0 + 0.05 * tick
        font_size = int(short * 0.16 * scale)
        font = QFont(APP_FONT_FAMILY, max(64, font_size), QFont.Bold)
        painter.setFont(font)
        path = QPainterPath()
        metrics_rect = painter.fontMetrics().boundingRect(number)
        tx = cx - metrics_rect.width() / 2
        ty = cy + metrics_rect.height() / 3
        path.addText(tx, ty, font, number)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(125, 211, 252, int(28 + 36 * tick)))
        painter.drawPath(path.translated(0, 3))
        painter.setBrush(TEXT_PRIMARY)
        painter.drawPath(path)
