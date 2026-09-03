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
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QFontMetrics
from AeroHelper.state import AutomationState
from AeroHelper.ui.app_icon import load_app_icon
from AeroHelper.utils.platform import get_app_font_family
APP_FONT_FAMILY = get_app_font_family()
OVERLAY_TEXT = '#F4F7FB'
OVERLAY_TEXT_MUTED = 'rgba(244, 247, 251, 0.78)'
OVERLAY_PANEL = QColor(8, 13, 27, 208)
OVERLAY_GLOW = QColor(125, 211, 252, 38)
OVERLAY_BORDER_IDLE = QColor(255, 255, 255, 82)
OVERLAY_BORDER_RUNNING = QColor(103, 232, 249, 218)
OVERLAY_BORDER_PAUSED = QColor(255, 230, 168, 210)
OVERLAY_BORDER_RECONNECTING = QColor(167, 139, 250, 214)
OVERLAY_BORDER_ERROR = QColor(255, 161, 176, 226)
OVERLAY_RADIUS = 20
OVERLAY_MIN_WIDTH = 300
OVERLAY_MIN_HEIGHT = 92
OVERLAY_MAX_HEIGHT = 220
_PHASE_SHORT = {
    'Phase 1 - route setup': 'Route setup',
    'Undocking': 'Undocking',
    'AutoSteering': 'Steering',
    'Docking alignment': 'Dock align',
    'Final dock': 'Final dock',
}
_METRIC_KEYS = ('Speed', 'Distance', 'Heading', 'Target')
_HIDE_METRICS_STATES = frozenset({
    AutomationState.RECONNECTING,
    AutomationState.STARTING,
    AutomationState.STOPPED,
})

class StatusOverlay(QWidget):
    update_state_signal = pyqtSignal(object)
    update_details_signal = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.current_state = AutomationState.STOPPED
        self.current_mode = 'Monitoring'
        self.diagnostics = {}
        self.animation_phase = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.init_ui()
        self.animation_timer.start(250)

    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        icon = load_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(50, 50, OVERLAY_MIN_WIDTH, OVERLAY_MIN_HEIGHT)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(3)
        label_style = f'background: transparent; color: {OVERLAY_TEXT}; margin: 0px; padding: 0px;'
        self.mode_label = QLabel()
        self.mode_label.setFont(QFont(APP_FONT_FAMILY, 12, QFont.Bold))
        self.mode_label.setStyleSheet(label_style)
        self.mode_label.setWordWrap(False)
        layout.addWidget(self.mode_label)
        self.status_label = QLabel()
        self.status_label.setFont(QFont(APP_FONT_FAMILY, 10))
        self.status_label.setStyleSheet(label_style)
        self.status_label.setWordWrap(False)
        layout.addWidget(self.status_label)
        self.detail_label = QLabel()
        self.detail_label.setFont(QFont(APP_FONT_FAMILY, 9))
        self.detail_label.setStyleSheet(f'background: transparent; color: {OVERLAY_TEXT_MUTED}; margin: 0px; padding: 0px;')
        self.detail_label.setWordWrap(False)
        layout.addWidget(self.detail_label)
        self.metrics_label = QLabel()
        self.metrics_label.setFont(QFont(APP_FONT_FAMILY, 9))
        self.metrics_label.setStyleSheet(f'background: transparent; color: {OVERLAY_TEXT_MUTED}; margin: 0px; padding: 0px;')
        self.metrics_label.setWordWrap(False)
        layout.addWidget(self.metrics_label)
        self.update_state(self.current_state)
        self.update_state_signal.connect(self.update_state)
        self.update_details_signal.connect(self.update_details)
        self.drag_position = None

    def update_state(self, state):
        self.current_state = state
        animating = state in (AutomationState.RUNNING, AutomationState.RECONNECTING)
        if animating:
            if not self.animation_timer.isActive():
                self.animation_timer.start(250)
        elif self.animation_timer.isActive():
            self.animation_timer.stop()
            self.update()
        self._refresh_text()

    def update_details(self, mode, diagnostics=None):
        self.current_mode = mode or self.current_mode
        self.diagnostics = diagnostics or {}
        self._refresh_text()

    @staticmethod
    def _short_phase(value):
        return _PHASE_SHORT.get(value, value)

    @staticmethod
    def _short_ocr(value):
        if value in (None, ''):
            return ''
        match = re.search(r'([\d.]+)%', str(value))
        if match:
            return f'OCR {match.group(1)}%'
        return f'OCR {value}'

    def _format_metrics_line(self):
        if self.current_state in _HIDE_METRICS_STATES:
            return ''
        parts = []
        for key in _METRIC_KEYS:
            value = self.diagnostics.get(key)
            if value not in (None, '', 'N/A'):
                parts.append(str(value))
        if not parts:
            return ''
        line = ' · '.join(parts)
        metrics = QFontMetrics(self.metrics_label.font())
        return metrics.elidedText(line, Qt.ElideRight, OVERLAY_MIN_WIDTH - 32)

    def _refresh_text(self):
        state_text = self.current_state.value if isinstance(self.current_state, AutomationState) else str(self.current_state)
        self.mode_label.setText(self.current_mode)
        self.status_label.setText(state_text)
        detail_parts = []
        phase = self.diagnostics.get('Phase')
        if phase not in (None, ''):
            detail_parts.append(self._short_phase(phase))
        ocr = self._short_ocr(self.diagnostics.get('OCR confidence'))
        if ocr:
            detail_parts.append(ocr)
        detail_text = ' · '.join(detail_parts)
        self.detail_label.setText(detail_text)
        self.detail_label.setVisible(bool(detail_text))
        metrics_text = self._format_metrics_line()
        self.metrics_label.setText(metrics_text)
        self.metrics_label.setVisible(bool(metrics_text))
        self._resize_to_content()

    def _resize_to_content(self):
        self.adjustSize()
        width = max(OVERLAY_MIN_WIDTH, self.sizeHint().width() + 12)
        height = max(OVERLAY_MIN_HEIGHT, min(self.sizeHint().height() + 12, OVERLAY_MAX_HEIGHT))
        self.setFixedSize(width, height)

    def _state_border_color(self):
        if self.current_state == AutomationState.RUNNING:
            alpha = 190 + int(35 * (self.animation_phase / 100))
            return QColor(OVERLAY_BORDER_RUNNING.red(), OVERLAY_BORDER_RUNNING.green(), OVERLAY_BORDER_RUNNING.blue(), alpha)
        if self.current_state in (AutomationState.PAUSED, AutomationState.PAUSED_HUMAN):
            return OVERLAY_BORDER_PAUSED
        if self.current_state == AutomationState.RECONNECTING:
            alpha = 190 + int(35 * (self.animation_phase / 100))
            return QColor(OVERLAY_BORDER_RECONNECTING.red(), OVERLAY_BORDER_RECONNECTING.green(), OVERLAY_BORDER_RECONNECTING.blue(), alpha)
        if self.current_state == AutomationState.ERROR:
            return OVERLAY_BORDER_ERROR
        return OVERLAY_BORDER_IDLE

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.animation_phase += 1
        if self.animation_phase > 100:
            self.animation_phase = 0
        glow_alpha = 26 + int(18 * (self.animation_phase / 100))
        glow = QColor(OVERLAY_GLOW.red(), OVERLAY_GLOW.green(), OVERLAY_GLOW.blue(), glow_alpha)
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), OVERLAY_RADIUS + 4, OVERLAY_RADIUS + 4)
        painter.setBrush(OVERLAY_PANEL)
        painter.drawRoundedRect(4, 4, self.width() - 8, self.height() - 8, OVERLAY_RADIUS, OVERLAY_RADIUS)
        pen = QPen(self._state_border_color(), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(4, 4, self.width() - 8, self.height() - 8, OVERLAY_RADIUS, OVERLAY_RADIUS)
