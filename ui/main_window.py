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

import html
import webbrowser
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLineEdit, QLabel, QFrame, QMessageBox, QCheckBox, QButtonGroup, QTextEdit, QStyleFactory, QApplication, QDialog, QScrollArea, QToolButton, QProgressBar, QGraphicsDropShadowEffect, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QPalette, QColor
from AeroHelper.config import Config, API_BASE
from AeroHelper.logger import default_log_path
from AeroHelper.ui.app_icon import load_app_icon, load_app_pixmap
from AeroHelper.utils.platform import IS_MACOS, IS_WINDOWS, get_app_font_family, get_macos_permission_summary, get_os_display_name, is_windows_elevated_admin
from AeroHelper.utils.update_cleanup import schedule_frozen_update_cleanup
from AeroHelper.utils.version import is_version_outdated, sanitize_remote_version
APP_FONT_FAMILY = get_app_font_family()
WEBHOOK_PREFIX = 'https://discord.com/api/webhooks/'
MASK_CHARS = 24
UI_SCALE = 0.9

def scale_px(value):
    return max(1, int(round(value * UI_SCALE)))

def scale_font(value):
    return max(7, int(round(value * UI_SCALE)))
WINDOW_MARGIN = scale_px(14)
SECTION_SPACING = scale_px(10)
TEXT_PRIMARY = '#F8FBFF'
TEXT_MUTED = '#A8B7D8'
TEXT_SUBTLE = '#7786A5'
TEXT_DARK = '#07111F'
BG_WINDOW = '#050713'
BG_PANEL = '#0B1020'
BG_PANEL_SOFT = 'rgba(11, 18, 36, 0.68)'
BG_INPUT = 'rgba(8, 13, 27, 0.74)'
BG_CARD = 'rgba(255, 255, 255, 0.075)'
BG_CARD_HOVER = 'rgba(255, 255, 255, 0.12)'
BORDER_SOFT = 'rgba(255, 255, 255, 0.14)'
BORDER_STRONG = 'rgba(159, 210, 255, 0.46)'
BORDER_GLOW = 'rgba(120, 211, 255, 0.22)'
ACCENT = '#7DD3FC'
ACCENT_2 = '#A78BFA'
ACCENT_3 = '#67E8F9'
ACCENT_SOFT = 'rgba(125, 211, 252, 0.18)'
ACCENT_WARM = '#F8FBFF'
SUCCESS_TEXT = '#B7F7D2'
SUCCESS_BG = 'rgba(23, 73, 53, 0.66)'
SUCCESS_BORDER = 'rgba(74, 222, 128, 0.32)'
WARNING_TEXT = '#FFE6A8'
WARNING_BG = 'rgba(107, 74, 18, 0.62)'
WARNING_BORDER = 'rgba(251, 191, 36, 0.34)'
ERROR_TEXT = '#FFC1C8'
ERROR_BG = 'rgba(104, 36, 52, 0.64)'
ERROR_BORDER = 'rgba(248, 113, 113, 0.36)'
GLASS_PANEL_STYLE = f'\n    QFrame#glassPanel {{\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 rgba(255, 255, 255, 0.105),\n            stop:0.46 rgba(125, 211, 252, 0.052),\n            stop:1 rgba(167, 139, 250, 0.068));\n        border: 1px solid {BORDER_SOFT};\n        border-radius: 18px;\n    }}\n'
HERO_PANEL_STYLE = f'\n    QFrame#heroPanel {{\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 rgba(125, 211, 252, 0.18),\n            stop:0.42 rgba(255, 255, 255, 0.095),\n            stop:1 rgba(167, 139, 250, 0.16));\n        border: 1px solid {BORDER_STRONG};\n        border-radius: 20px;\n    }}\n'
BUTTON_STYLE = f'\n    QPushButton {{\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 #FFFFFF,\n            stop:0.38 #D8F8FF,\n            stop:1 #B9B6FF);\n        color: {TEXT_DARK};\n        border: 1px solid rgba(255, 255, 255, 0.62);\n        border-radius: 13px;\n        padding: 8px 14px;\n        font-weight: 800;\n    }}\n    QPushButton:hover {{\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 #FFFFFF,\n            stop:0.34 #E9FBFF,\n            stop:1 #CAC7FF);\n        border-color: rgba(255, 255, 255, 0.84);\n    }}\n    QPushButton:pressed {{\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 #BFEFFF,\n            stop:1 #9DA4FF);\n    }}\n    QPushButton:disabled {{\n        background: rgba(255, 255, 255, 0.08);\n        color: {TEXT_SUBTLE};\n        border-color: rgba(255, 255, 255, 0.08);\n    }}\n'
SECONDARY_BUTTON_STYLE = f'\n    QPushButton {{\n        background: rgba(255, 255, 255, 0.065);\n        color: {TEXT_PRIMARY};\n        border: 1px solid {BORDER_SOFT};\n        border-radius: 12px;\n        padding: 8px 13px;\n        font-weight: 650;\n    }}\n    QPushButton:hover {{\n        background: {BG_CARD_HOVER};\n        color: #FFFFFF;\n        border-color: {BORDER_STRONG};\n    }}\n    QPushButton:pressed {{\n        background: rgba(255, 255, 255, 0.045);\n    }}\n    QPushButton:disabled {{\n        background: rgba(255, 255, 255, 0.04);\n        color: rgba(119, 134, 165, 0.58);\n        border-color: rgba(255, 255, 255, 0.06);\n    }}\n'
SHARE_DATA_OVERRIDE_SUCCESS_BUTTON_STYLE = f'\n    QPushButton {{\n        background: {SUCCESS_BG};\n        color: {SUCCESS_TEXT};\n        border: 1px solid {SUCCESS_BORDER};\n        border-radius: 12px;\n        padding: 8px 13px;\n        font-weight: 650;\n    }}\n    QPushButton:disabled {{\n        background: {SUCCESS_BG};\n        color: {SUCCESS_TEXT};\n        border: 1px solid {SUCCESS_BORDER};\n    }}\n'
MODE_BUTTON_STYLE = f'\n    QPushButton {{\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 rgba(255, 255, 255, 0.10),\n            stop:1 rgba(255, 255, 255, 0.045));\n        color: {TEXT_PRIMARY};\n        border: 1px solid {BORDER_SOFT};\n        border-radius: 14px;\n        padding: 8px 6px;\n        font-weight: 750;\n    }}\n    QPushButton:hover {{\n        border-color: {BORDER_STRONG};\n        background: {BG_CARD_HOVER};\n    }}\n    QPushButton:checked {{\n        color: #FFFFFF;\n        border-color: {ACCENT};\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 rgba(125, 211, 252, 0.30),\n            stop:1 rgba(167, 139, 250, 0.28));\n    }}\n'
STOP_BUTTON_STYLE = f'\n    QPushButton {{\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 rgba(255, 148, 148, 0.94),\n            stop:1 rgba(248, 113, 113, 0.72));\n        color: #28070B;\n        border: 1px solid rgba(255, 215, 215, 0.42);\n    }}\n    QPushButton:hover {{\n        background: rgba(255, 170, 170, 0.96);\n    }}\n    QPushButton:pressed {{\n        background: rgba(226, 88, 98, 0.94);\n    }}\n'
HELPER_ICON_STYLE = f'color: {TEXT_SUBTLE}; background: transparent; padding: 0px;'
TOOLTIP_STYLE = f'''
    QToolTip {{
        color: {TEXT_PRIMARY};
        background-color: {BG_PANEL};
        border: 1px solid {BORDER_STRONG};
        padding: 8px 12px;
        font-family: "{APP_FONT_FAMILY}";
        font-size: 9pt;
    }}
'''
KNOWN_ISSUES_TOOLTIP = 'Live list of current AeroHelper problems pulled from the website.\nPriority badges and the progress bar show how serious each issue is and how far along a fix is.\nIf nothing is listed, there are no active reported issues right now.'
DISCLOSURE_TOOLBUTTON_STYLE = f'\n    QToolButton {{\n        color: {TEXT_PRIMARY};\n        background: transparent;\n        border: none;\n        border-radius: 8px;\n        padding: 6px 10px;\n        font-weight: bold;\n    }}\n    QToolButton:hover {{\n        background: {ACCENT_SOFT};\n    }}\n    QToolButton:pressed {{\n        background: rgba(143, 183, 255, 0.28);\n    }}\n    QToolButton:disabled {{\n        color: {TEXT_SUBTLE};\n        background: transparent;\n    }}\n'
WEBHOOK_REVEAL_BUTTON_STYLE = f'\n    QPushButton {{\n        color: {ACCENT};\n        background: transparent;\n        border: 1px solid {BORDER_SOFT};\n        border-radius: 8px;\n        padding: 6px 12px;\n        font-weight: 600;\n        min-width: 72px;\n    }}\n    QPushButton:hover {{\n        background: {ACCENT_SOFT};\n        border-color: {BORDER_STRONG};\n    }}\n    QPushButton:pressed {{\n        background: rgba(143, 183, 255, 0.28);\n    }}\n    QPushButton:disabled {{\n        color: {TEXT_SUBTLE};\n        border-color: rgba(255, 255, 255, 0.06);\n    }}\n'
CLEAR_LOG_BUTTON_STYLE = f'\n    QPushButton {{\n        color: {TEXT_SUBTLE};\n        background: transparent;\n        border: 1px solid rgba(255, 255, 255, 0.08);\n        border-radius: 7px;\n        padding: 3px 8px;\n        font-weight: 500;\n    }}\n    QPushButton:hover {{\n        color: {WARNING_TEXT};\n        background: rgba(255, 255, 255, 0.04);\n        border-color: {WARNING_BORDER};\n    }}\n    QPushButton:pressed {{\n        background: rgba(107, 74, 18, 0.35);\n    }}\n'
SEPARATOR_STYLE = f'background-color: {BORDER_SOFT}; max-height: 1px;'
MODE_OPTIONS = ('Monitoring', 'AutoSteer', 'AutoPilot')
START_PREREQUISITE_HINT = 'Start Roblox and load into Aeronautica before clicking Start.'
MACOS_START_HINT = 'On macOS: grant Accessibility and Screen Recording for AeroHelper (or Terminal/Python) in System Settings → Privacy & Security. Click Roblox after Start if the window does not come to the front. Human-intervention pause is not available on macOS - use Stop to end automation.'
CUSTOM_WAYPOINT_TOOLTIP = 'When checked: Monitoring keeps running if the HUD shows a waypoint code (for example ZEPHR) instead of DEST. Moving away from the destination warns instead of stopping. Use this when following a custom waypoint that may route around land masses.'
SKIP_CURRENT_BEARING_TOOLTIP = 'When checked: Monitoring will not press 5 each cycle and will not use current heading (HDG).\n\nWarning: off-course heading alerts and HDG in Discord updates will be unavailable. Destination bearing (DEST) can still be read if it is already on screen.'
THROTTLE_UP_TOOLTIP = 'When checked: if OCR reads throttle below 100%, hold W for 10 seconds to restore full throttle.\n\nApplies in Monitoring and AutoSteer.\n\nAutoPilot always throttles up during cruise. Skipped during AutoPilot docking/undocking where lower throttle is intentional.\n\nWhen off: no throttle-up action is taken.'
QUIT_AFTER_5_ERRORS_TOOLTIP = 'Highly recommended.'
INTELLIGENT_STEERING_TOOLTIP = 'Beta feature: hones the steering multiplier to match how your vehicle actually turns, starting from the current Multiplier value.\n\nIf the ship understeers, the multiplier goes up. If it oversteers, it goes down. The learned value is saved to Multiplier so the next start continues from there.\n\nStill in beta - results vary by vehicle.'
OCR_DEBUG_TOOLTIP = 'When checked: writes full OCR output to AeroHelper.log.\nWhen off: OCR text is not logged, except a short window around errors.'
CONSENT_TEXT = 'AeroHelper is an independent helper tool for Aeronautica. It is not endorsed by the Aeronautica staff team.\n\nAeroHelper can read your screen with OCR, send Discord webhook updates, and control keyboard/mouse input for supported automation modes.\n\nAeronautica staff said development may continue, but it may not be advertised as official or endorsed, and autopilot features must be restricted to vehicles with an intended AFK gameplay loop. Use those features only with boat and airship licenses.\n\nThis is allowed under that guidance, but there may still be rare theoretical Roblox account or platform concerns.'
TOS_URL = f'{API_BASE.rstrip("/")}/tos'
INFO_PANEL_STYLE = '\n    color: %s;\n    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(125, 211, 252, 0.12), stop:1 rgba(255, 255, 255, 0.05));\n    padding: 10px;\n    border-radius: 13px;\n    border: 1px solid %s;\n' % (TEXT_PRIMARY, BORDER_SOFT)
STATUS_VIEW_STYLES = {'info': '\n        QTextEdit {\n            color: %s;\n            background-color: rgba(38, 57, 87, 0.72);\n            padding: 10px;\n            border-radius: 12px;\n            border: 1px solid rgba(143, 183, 255, 0.38);\n        }\n    ' % ACCENT, 'ok': '\n        QTextEdit {\n            color: %s;\n            background-color: %s;\n            padding: 10px;\n            border-radius: 12px;\n            border: 1px solid %s;\n        }\n    ' % (SUCCESS_TEXT, SUCCESS_BG, SUCCESS_BORDER), 'warning': '\n        QTextEdit {\n            color: %s;\n            background-color: %s;\n            padding: 10px;\n            border-radius: 12px;\n            border: 1px solid %s;\n        }\n    ' % (WARNING_TEXT, WARNING_BG, WARNING_BORDER), 'error': '\n        QTextEdit {\n            color: %s;\n            background-color: %s;\n            padding: 10px;\n            border-radius: 12px;\n            border: 1px solid %s;\n        }\n    ' % (ERROR_TEXT, ERROR_BG, ERROR_BORDER)}
ISSUES_SCROLL_STYLE = f'\n    QScrollArea#issuesScroll {{\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n            stop:0 rgba(255, 255, 255, 0.055),\n            stop:1 rgba(125, 211, 252, 0.04));\n        border: 1px solid {BORDER_SOFT};\n        border-radius: 13px;\n    }}\n    QWidget#issuesScrollInner {{\n        background: transparent;\n    }}\n'
ISSUES_EMPTY_STYLE = f'color: {TEXT_MUTED}; background: transparent; padding: 10px 4px;'
ISSUE_PRIORITY_THEME = {'high': {'text': ERROR_TEXT, 'bg': ERROR_BG, 'border': ERROR_BORDER, 'label': 'HIGH'}, 'medium': {'text': '#F9B84B', 'bg': WARNING_BG, 'border': WARNING_BORDER, 'label': 'MED'}, 'low': {'text': WARNING_TEXT, 'bg': 'rgba(255, 255, 255, 0.05)', 'border': BORDER_SOFT, 'label': 'LOW'}}
_STATUS_VIEW_SCROLLBAR_QSS = '\n    QScrollBar:vertical {\n        border: none;\n        background: transparent;\n        width: 6px;\n        margin: 7px 2px 7px 0;\n        border-radius: 3px;\n    }\n    QScrollBar::handle:vertical {\n        border: none;\n        background: rgba(208, 228, 255, 0.13);\n        min-height: 26px;\n        border-radius: 3px;\n    }\n    QScrollBar::handle:vertical:hover {\n        background: rgba(208, 228, 255, 0.26);\n    }\n    QScrollBar::handle:vertical:pressed {\n        background: rgba(208, 228, 255, 0.34);\n    }\n    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n        border: none;\n        background: transparent;\n        height: 0px;\n        width: 0px;\n    }\n    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n        background: transparent;\n    }\n    QScrollBar:horizontal, QScrollBar::handle:horizontal, QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {\n        height: 0px;\n        background: transparent;\n        border: none;\n    }\n'

class MainWindow(QMainWindow):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    test_webhook_requested = pyqtSignal()
    share_data_override_requested = pyqtSignal()
    share_data_override_done_signal = pyqtSignal(bool)
    ocr_debug_changed = pyqtSignal(bool)
    update_multiplier_signal = pyqtSignal(float)
    show_error_signal = pyqtSignal(str, str, str)
    api_notice_signal = pyqtSignal(str, str, str, bool)
    set_paused_state_signal = pyqtSignal(bool)
    lock_fields_signal = pyqtSignal()
    unlock_fields_signal = pyqtSignal()
    update_status_signal = pyqtSignal(str, str, object)
    set_global_version_signal = pyqtSignal(str)
    set_issues_signal = pyqtSignal(list)

    def __init__(self, version=None, global_version=None):
        super().__init__()
        self.version = version
        self.global_version = global_version
        self.config = Config()
        self.is_running = False
        self._current_error = False
        self._webhook_value = ''
        self._webhook_redacted = True
        self._share_data_override_succeeded = False
        self.init_ui()
        self.load_config()
        self.show_error_signal.connect(self.show_error)
        self.update_multiplier_signal.connect(self.apply_learned_multiplier)
        self.api_notice_signal.connect(self.show_api_notice)
        self.set_paused_state_signal.connect(self.set_paused_state)
        self.lock_fields_signal.connect(self.lock_fields)
        self.unlock_fields_signal.connect(self.unlock_fields)
        self.update_status_signal.connect(self.update_status_panel)
        self.share_data_override_done_signal.connect(self.on_share_data_override_done)
        self.set_global_version_signal.connect(self.set_global_version)
        self.set_issues_signal.connect(self.update_issues)
        if not self.config.get_consent_accepted():
            self._set_controls_enabled(False)
            self.start_button.setEnabled(False)
            QTimer.singleShot(0, self._show_consent_dialog)

    def _webhook_display_text(self):
        val = self._webhook_value.strip()
        if not val:
            return ''
        if val.startswith(WEBHOOK_PREFIX):
            return WEBHOOK_PREFIX + '•' * MASK_CHARS
        return '•' * MASK_CHARS

    def _update_webhook_display(self):
        if self._webhook_redacted:
            self.webhook_input.setReadOnly(True)
            self.webhook_input.setText(self._webhook_display_text())
            self.webhook_reveal_btn.setText('Show')
            self.webhook_reveal_btn.setToolTip('Show the full webhook URL in the field')
        else:
            self.webhook_input.setReadOnly(False)
            self.webhook_input.setText(self._webhook_value)
            self.webhook_reveal_btn.setText('Hide')
            self.webhook_reveal_btn.setToolTip('Mask the webhook URL again')

    def _on_webhook_reveal_clicked(self):
        if self._webhook_redacted:
            self._webhook_redacted = False
        else:
            self._webhook_value = self.webhook_input.text().strip()
            self.config.set_webhook_url(self._webhook_value)
            self._webhook_redacted = True
        self._update_webhook_display()
        self._update_warnings()

    def _create_mode_button(self, mode_name):
        btn = QPushButton(mode_name)
        btn.setCheckable(True)
        btn.setMinimumHeight(scale_px(64))
        btn.setMinimumWidth(0)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setFont(QFont(APP_FONT_FAMILY, scale_font(10)))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(MODE_BUTTON_STYLE)
        btn.clicked.connect(lambda checked, m=mode_name: self.on_mode_changed(m))
        return btn

    def _badge_stylesheet(self, color=None, background=None, border=None):
        text_color = color or TEXT_PRIMARY
        bg = background or 'rgba(255, 255, 255, 0.09)'
        bd = border or BORDER_SOFT
        return (
            f'color: {text_color};'
            f'background: {bg};'
            f'border: 1px solid {bd};'
            f'border-radius: 8px;'
            f'padding: 2px 6px;'
        )

    def _style_badge(self, badge, color=None, background=None, border=None):
        badge.setAlignment(Qt.AlignCenter)
        badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        badge.setStyleSheet(self._badge_stylesheet(color, background, border))

    def _create_badge(self, text, font_size=8, bold=True, color=None, background=None, border=None, tooltip=None):
        badge = QLabel(text)
        weight = QFont.Bold if bold else QFont.Normal
        badge.setFont(QFont(APP_FONT_FAMILY, scale_font(font_size), weight))
        if tooltip:
            badge.setToolTip(tooltip)
        self._style_badge(badge, color=color, background=background, border=border)
        return badge

    def _create_info_label(self, text):
        label = QLabel(text)
        label.setFont(QFont(APP_FONT_FAMILY, 9))
        label.setStyleSheet(INFO_PANEL_STYLE)
        label.setWordWrap(True)
        label.hide()
        return label

    def _add_separator(self, layout):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(SEPARATOR_STYLE)
        layout.addWidget(separator)

    def _apply_shadow(self, widget, blur=26, y=8, alpha=72):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y)
        shadow.setColor(QColor(0, 0, 0, alpha))
        widget.setGraphicsEffect(shadow)

    def _create_glass_panel(self, object_name='glassPanel', style=None, margins=(14, 14, 14, 14), spacing=10, shadow=True):
        panel = QFrame()
        panel.setObjectName(object_name)
        panel.setStyleSheet(style or GLASS_PANEL_STYLE)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(*margins)
        panel_layout.setSpacing(spacing)
        if shadow:
            self._apply_shadow(panel)
        return panel, panel_layout

    def _format_tooltip(self, tooltip):
        text = (tooltip or '').strip()
        if not text:
            return ''
        body = html.escape(text).replace('\n', '<br/>')
        return f'<div style="color:{TEXT_PRIMARY};max-width:280px;">{body}</div>'

    def _build_primary_buttons(self, layout):
        self.start_button = QPushButton('Start Automation')
        self.start_button.setMinimumHeight(scale_px(50))
        self.start_button.setFont(QFont(APP_FONT_FAMILY, scale_font(12), QFont.Bold))
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setStyleSheet(BUTTON_STYLE)
        self.start_button.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.start_button)
        self.start_prerequisite_label = QLabel(START_PREREQUISITE_HINT)
        self.start_prerequisite_label.setFont(QFont(APP_FONT_FAMILY, scale_font(9)))
        self.start_prerequisite_label.setWordWrap(True)
        self.start_prerequisite_label.setStyleSheet(INFO_PANEL_STYLE)
        layout.addWidget(self.start_prerequisite_label)
        if IS_MACOS:
            self.macos_start_hint_label = QLabel(MACOS_START_HINT)
            self.macos_start_hint_label.setFont(QFont(APP_FONT_FAMILY, scale_font(9)))
            self.macos_start_hint_label.setWordWrap(True)
            self.macos_start_hint_label.setStyleSheet(INFO_PANEL_STYLE)
            layout.addWidget(self.macos_start_hint_label)
        self.stop_button = QPushButton('Stop Automation')
        self.stop_button.setMinimumHeight(scale_px(50))
        self.stop_button.setFont(QFont(APP_FONT_FAMILY, scale_font(12), QFont.Bold))
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setStyleSheet(BUTTON_STYLE + STOP_BUTTON_STYLE)
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.hide()
        layout.addWidget(self.stop_button)
        self.history_button = QPushButton('Session History')
        self.history_button.setMinimumHeight(scale_px(38))
        self.history_button.setFont(QFont(APP_FONT_FAMILY, scale_font(10), QFont.Bold))
        self.history_button.setCursor(Qt.PointingHandCursor)
        self.history_button.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.history_button.clicked.connect(self.show_history_dialog)
        layout.addWidget(self.history_button)

    def _build_brand_header(self, layout):
        header_layout = QHBoxLayout()
        header_layout.setSpacing(scale_px(11))
        logo = QLabel()
        pixmap = load_app_pixmap(scale_px(47))
        if not pixmap.isNull():
            logo.setPixmap(pixmap)
            logo.setFixedSize(scale_px(53), scale_px(53))
            logo.setAlignment(Qt.AlignCenter)
            logo.setStyleSheet(f'background: rgba(255, 255, 255, 0.08); border: 1px solid {BORDER_SOFT}; border-radius: 15px; padding: 3px;')
            header_layout.addWidget(logo)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        title = QLabel('AeroHelper')
        title.setFont(QFont(APP_FONT_FAMILY, scale_font(19), QFont.Bold))
        title.setStyleSheet(f'color: {TEXT_PRIMARY}; letter-spacing: 0.4px;')
        subtitle = QLabel('Your ultimate companion for AFK automation in Aeronautica')
        subtitle.setFont(QFont(APP_FONT_FAMILY, scale_font(9)))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f'color: {TEXT_MUTED};')
        version_row = QHBoxLayout()
        version_row.setSpacing(6)
        local_ver_text = f'v{self.version}' if self.version else 'dev'
        self.local_version_label = self._create_badge(local_ver_text, font_size=9, bold=False)
        version_row.addWidget(self.local_version_label)
        self.version_check_label = self._create_badge('', font_size=9, bold=True)
        version_row.addWidget(self.version_check_label)
        version_row.addStretch()
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        text_layout.addLayout(version_row)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

    def _build_mode_section(self, layout):
        mode_label = QLabel('Mode')
        mode_label.setFont(QFont(APP_FONT_FAMILY, 9, QFont.Bold))
        layout.addWidget(mode_label)
        mode_boxes_layout = QHBoxLayout()
        mode_boxes_layout.setSpacing(scale_px(6))
        self.mode_buttons = {}
        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.setExclusive(True)
        for mode_name in MODE_OPTIONS:
            btn = self._create_mode_button(mode_name)
            self.mode_buttons[mode_name] = btn
            self.mode_btn_group.addButton(btn)
            mode_boxes_layout.addWidget(btn, 1)
        layout.addLayout(mode_boxes_layout)

    def _build_notification_mode_row(self, layout):
        from AeroHelper.notifications.policy import NOTIFICATION_MODE_LABELS, NOTIFICATION_MODE_TOOLTIPS
        self.notification_mode_layout = QHBoxLayout()
        self.notification_mode_label = QLabel('Notification Mode:')
        self.notification_mode_label.setFont(QFont(APP_FONT_FAMILY, 9))
        self.notification_mode_layout.addWidget(self.notification_mode_label)
        self.notification_mode_combo = QComboBox()
        self.notification_mode_combo.addItems(list(NOTIFICATION_MODE_LABELS))
        for i, tip in enumerate(NOTIFICATION_MODE_TOOLTIPS):
            self.notification_mode_combo.setItemData(i, self._format_tooltip(tip), Qt.ToolTipRole)
        self.notification_mode_combo.setToolTip(self._format_tooltip(NOTIFICATION_MODE_TOOLTIPS[0]))
        self.notification_mode_combo.currentTextChanged.connect(self.on_notification_mode_changed)
        self.notification_mode_combo.activated.connect(self._on_notification_mode_activated)
        self.notification_mode_layout.addWidget(self.notification_mode_combo)
        layout.addLayout(self.notification_mode_layout)

    def _build_option_checkboxes(self, layout):
        self.mid_mission_checkbox = QCheckBox('Start Mid-Mission')
        self.mid_mission_checkbox.setFont(QFont(APP_FONT_FAMILY, 9))
        self.mid_mission_checkbox.stateChanged.connect(self._on_checkbox_state_changed)
        self.mid_mission_checkbox.stateChanged.connect(self.on_mid_mission_changed)
        self.mid_mission_checkbox.hide()
        layout.addWidget(self.mid_mission_checkbox)
        self.custom_waypoint_checkbox = QCheckBox('Custom waypoint')
        self.custom_waypoint_checkbox.setFont(QFont(APP_FONT_FAMILY, 9))
        self.custom_waypoint_checkbox.stateChanged.connect(self._on_checkbox_state_changed)
        self.custom_waypoint_checkbox.stateChanged.connect(self.on_custom_waypoint_changed)
        self.custom_waypoint_checkbox.setToolTip(self._format_tooltip(CUSTOM_WAYPOINT_TOOLTIP))
        self.custom_waypoint_checkbox.hide()
        layout.addWidget(self.custom_waypoint_checkbox)
        self.skip_bearing_checkbox = QCheckBox('Unlock 5 view')
        self.skip_bearing_checkbox.setFont(QFont(APP_FONT_FAMILY, 9))
        self.skip_bearing_checkbox.stateChanged.connect(self._on_checkbox_state_changed)
        self.skip_bearing_checkbox.stateChanged.connect(self.on_skip_bearing_changed)
        self.skip_bearing_checkbox.setToolTip(self._format_tooltip(SKIP_CURRENT_BEARING_TOOLTIP))
        self.skip_bearing_checkbox.hide()
        layout.addWidget(self.skip_bearing_checkbox)
        self.throttle_up_checkbox = QCheckBox('Throttle up if not 100%')
        self.throttle_up_checkbox.setFont(QFont(APP_FONT_FAMILY, 9))
        self.throttle_up_checkbox.stateChanged.connect(self._on_checkbox_state_changed)
        self.throttle_up_checkbox.stateChanged.connect(self.on_throttle_up_changed)
        self.throttle_up_checkbox.setToolTip(self._format_tooltip(THROTTLE_UP_TOOLTIP))
        self.throttle_up_checkbox.hide()
        layout.addWidget(self.throttle_up_checkbox)
        self.intelligent_steering_row = QWidget()
        intelligent_row = QHBoxLayout(self.intelligent_steering_row)
        intelligent_row.setContentsMargins(0, 0, 0, 0)
        intelligent_row.setSpacing(8)
        self.intelligent_steering_checkbox = QCheckBox('Intelligent Steering')
        self.intelligent_steering_checkbox.setFont(QFont(APP_FONT_FAMILY, 9))
        self.intelligent_steering_checkbox.stateChanged.connect(self._on_checkbox_state_changed)
        self.intelligent_steering_checkbox.stateChanged.connect(self.on_intelligent_steering_changed)
        self.intelligent_steering_checkbox.setToolTip(self._format_tooltip(INTELLIGENT_STEERING_TOOLTIP))
        intelligent_row.addWidget(self.intelligent_steering_checkbox)
        intelligent_beta = self._create_badge(
            'β',
            color=WARNING_TEXT,
            background=WARNING_BG,
            border=WARNING_BORDER,
            tooltip=self._format_tooltip(INTELLIGENT_STEERING_TOOLTIP),
        )
        intelligent_row.addWidget(intelligent_beta)
        intelligent_row.addStretch()
        self.intelligent_steering_row.hide()
        layout.addWidget(self.intelligent_steering_row)
        self.quit_after_5_errors_checkbox = QCheckBox('Quit after 5 consecutive errors')
        self.quit_after_5_errors_checkbox.setFont(QFont(APP_FONT_FAMILY, 9))
        self.quit_after_5_errors_checkbox.stateChanged.connect(self._on_checkbox_state_changed)
        self.quit_after_5_errors_checkbox.stateChanged.connect(self.on_quit_after_5_errors_changed)
        self.quit_after_5_errors_checkbox.setToolTip(self._format_tooltip(QUIT_AFTER_5_ERRORS_TOOLTIP))
        layout.addWidget(self.quit_after_5_errors_checkbox)
        self.include_screenshots_checkbox = QCheckBox('Include screenshots in Mission Status')
        self.include_screenshots_checkbox.setFont(QFont(APP_FONT_FAMILY, 9))
        self.include_screenshots_checkbox.stateChanged.connect(self._on_checkbox_state_changed)
        self.include_screenshots_checkbox.stateChanged.connect(self.on_include_screenshots_changed)
        self.include_screenshots_checkbox.setToolTip(self._format_tooltip('When checked: attaches a screenshot to each mission status webhook update'))
        layout.addWidget(self.include_screenshots_checkbox)
        share_wrap = QFrame()
        share_wrap.setObjectName('shareDataWrap')
        share_wrap.setMinimumHeight(58)
        share_wrap.setStyleSheet(f'\n            #shareDataWrap {{\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(125, 211, 252, 0.12), stop:1 rgba(255, 255, 255, 0.055));\n                border: 1px solid {BORDER_SOFT};\n                border-radius: 16px;\n                padding: 8px 10px;\n            }}\n        ')
        share_outer = QVBoxLayout(share_wrap)
        share_outer.setContentsMargins(4, 2, 4, 2)
        share_outer.setSpacing(8)
        self.share_data_checkbox = QCheckBox('Share data with developer')
        self.share_data_checkbox.setFont(QFont(APP_FONT_FAMILY, 9))
        self.share_data_checkbox.setMinimumHeight(26)
        self.share_data_checkbox.setChecked(False)
        self.share_data_checkbox.stateChanged.connect(self._on_checkbox_state_changed)
        self.share_data_checkbox.stateChanged.connect(self.on_share_data_changed)
        self.share_data_checkbox.setToolTip(self._format_tooltip('Sends diagnostic logs on errors so the developer can help you.\nOnly your webhook URL and the last 25 KB of AeroHelper.log are shared.'))
        share_outer.addWidget(self.share_data_checkbox)
        share_btn_row = QHBoxLayout()
        share_btn_row.setSpacing(8)
        learn_more_btn = QPushButton('Learn More')
        learn_more_btn.setFont(QFont(APP_FONT_FAMILY, 9))
        learn_more_btn.setCursor(Qt.PointingHandCursor)
        learn_more_btn.setMinimumHeight(28)
        learn_more_btn.setStyleSheet(f'\n            QPushButton {{\n                color: {ACCENT};\n                background: transparent;\n                border: 1px solid {BORDER_SOFT};\n                border-radius: 6px;\n                padding: 4px 12px;\n                font-weight: 500;\n            }}\n            QPushButton:hover {{ background: {ACCENT_SOFT}; border-color: {BORDER_STRONG}; }}\n        ')
        learn_more_btn.clicked.connect(self._on_share_data_learn_more)
        share_btn_row.addWidget(learn_more_btn)
        self.share_data_override_btn = QPushButton('Share Data Override')
        self.share_data_override_btn.setFont(QFont(APP_FONT_FAMILY, 9))
        self.share_data_override_btn.setCursor(Qt.PointingHandCursor)
        self.share_data_override_btn.setMinimumHeight(28)
        self.share_data_override_btn.setToolTip(self._format_tooltip('Send your webhook URL and the last 25 KB of AeroHelper.log to the developer once, right now.\nDoes not require automatic sharing to be on.'))
        self.share_data_override_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.share_data_override_btn.clicked.connect(self.on_share_data_override_clicked)
        share_btn_row.addWidget(self.share_data_override_btn)
        share_btn_row.addStretch()
        share_outer.addLayout(share_btn_row)
        layout.addWidget(share_wrap)

    def _build_info_panels(self, layout):
        self.monitoring_info = self._create_info_label('Start in: mission\n\nWatches the HUD and sends Discord updates for speed, fuel, distance, and alerts.')
        layout.addWidget(self.monitoring_info)
        self.autosteer_info = self._create_info_label('Start in: mission\n\nYou start the mission; AeroHelper keeps you on course toward DEST.')
        layout.addWidget(self.autosteer_info)
        self.autopilot_info = self._create_info_label('Start in: server lobby\n\nFull AFK loop: jobs, routes, steer, dock, repeat. Supported boats and airships only.')
        layout.addWidget(self.autopilot_info)

    def _build_cycle_controls(self, layout):
        timing_label = QLabel('Timing')
        timing_label.setFont(QFont(APP_FONT_FAMILY, 9, QFont.Bold))
        layout.addWidget(timing_label)
        interval_tip = self._format_tooltip('How often AeroHelper reads the screen and runs its checks.\nLower = more responsive but heavier on your PC.\nHigher = lighter but slower to react.\nAutoPilot always uses 15 seconds.')
        interval_layout = QHBoxLayout()
        interval_label = QLabel('Cycle Delay (10–30s):')
        interval_label.setFont(QFont(APP_FONT_FAMILY, 9))
        interval_label.setToolTip(interval_tip)
        interval_layout.addWidget(interval_label)
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText('15')
        self.interval_input.setToolTip(interval_tip)
        self.interval_input.editingFinished.connect(self.on_interval_changed)
        interval_layout.addWidget(self.interval_input)
        layout.addLayout(interval_layout)
        multiplier_tip = self._format_tooltip('Steering duration multiplier. 1.0 is tuned as a good Seawise baseline.\nVehicles that turn slower than Seawise may need multiplier > 1.\nVehicles that turn faster may need multiplier < 1.\nIntelligent Steering starts from this value and saves what it learns back here.')
        multiplier_layout = QHBoxLayout()
        multiplier_label = QLabel('Multiplier (0–2):')
        multiplier_label.setFont(QFont(APP_FONT_FAMILY, 9))
        multiplier_label.setToolTip(multiplier_tip)
        multiplier_layout.addWidget(multiplier_label)
        self.multiplier_input = QLineEdit()
        self.multiplier_input.setPlaceholderText('1.0')
        self.multiplier_input.setToolTip(multiplier_tip)
        self.multiplier_input.editingFinished.connect(self.on_multiplier_changed)
        multiplier_layout.addWidget(self.multiplier_input)
        layout.addLayout(multiplier_layout)

    def _build_process_guard_section(self, layout):
        fold_row = QHBoxLayout()
        self.guard_fold_btn = QToolButton()
        self.guard_fold_btn.setText('Auto App Shutdown')
        self.guard_fold_btn.setFont(QFont(APP_FONT_FAMILY, 9, QFont.Bold))
        self.guard_fold_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.guard_fold_btn.setArrowType(Qt.RightArrow)
        self.guard_fold_btn.setAutoRaise(True)
        self.guard_fold_btn.setCursor(Qt.PointingHandCursor)
        self.guard_fold_btn.setStyleSheet(DISCLOSURE_TOOLBUTTON_STYLE)
        self.guard_fold_btn.setToolTip(self._format_tooltip('Closes or stops apps and services you list every cycle.\nUseful for parental controls, blocking apps that auto-launch, or stopping software that interferes with AFK gameplay.'))
        self.guard_fold_btn.clicked.connect(self._toggle_guard_panel)
        fold_row.addWidget(self.guard_fold_btn, alignment=Qt.AlignLeft)
        fold_row.addStretch(1)
        layout.addLayout(fold_row)
        self.process_guard_panel = QWidget()
        guard_inner = QVBoxLayout(self.process_guard_panel)
        guard_inner.setContentsMargins(0, 4, 0, 0)
        guard_inner.setSpacing(8)
        services_label = QLabel('Blocked Windows services:')
        services_label.setFont(QFont(APP_FONT_FAMILY, 9))
        services_label.setToolTip(self._format_tooltip('Optional comma-separated service short names (SCM names) to stop each cycle when running - e.g. WpcMonSvc. Not the Task Manager display name.'))
        guard_inner.addWidget(services_label)
        self.blocked_services_input = QLineEdit()
        self.blocked_services_input.setPlaceholderText('e.g. WpcMonSvc, AnotherSvc')
        self.blocked_services_input.setToolTip(services_label.toolTip())
        self.blocked_services_input.editingFinished.connect(self.on_blocked_services_changed)
        guard_inner.addWidget(self.blocked_services_input)
        process_label = QLabel('Blocked executables:')
        process_label.setFont(QFont(APP_FONT_FAMILY, 9))
        process_label.setToolTip(self._format_tooltip('Optional comma-separated image names to close each cycle - e.g. WpcMon.exe, msedge.exe (same idea as AeroMulti process field).'))
        guard_inner.addWidget(process_label)
        self.blocked_process_input = QLineEdit()
        self.blocked_process_input.setPlaceholderText('e.g. WpcMon.exe, Another.exe')
        self.blocked_process_input.setToolTip(process_label.toolTip())
        self.blocked_process_input.editingFinished.connect(self.on_blocked_processes_changed)
        guard_inner.addWidget(self.blocked_process_input)
        layout.addWidget(self.process_guard_panel)
        self.process_guard_panel.hide()

    def _toggle_guard_panel(self):
        expanded = not self.process_guard_panel.isVisible()
        self.process_guard_panel.setVisible(expanded)
        self.guard_fold_btn.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)

    def _build_webhook_section(self, layout):
        webhook_label = QLabel('Discord Webhook:')
        webhook_label.setFont(QFont(APP_FONT_FAMILY, 9))
        layout.addWidget(webhook_label)
        webhook_row = QHBoxLayout()
        self.webhook_input = QLineEdit()
        self.webhook_input.setPlaceholderText('https://discord.com/api/webhooks/...')
        self.webhook_input.editingFinished.connect(self.on_webhook_changed)
        webhook_row.addWidget(self.webhook_input)
        self.webhook_reveal_btn = QPushButton('Show')
        self.webhook_reveal_btn.setFont(QFont(APP_FONT_FAMILY, 9))
        self.webhook_reveal_btn.setCursor(Qt.PointingHandCursor)
        self.webhook_reveal_btn.setStyleSheet(WEBHOOK_REVEAL_BUTTON_STYLE)
        self.webhook_reveal_btn.setToolTip('Show the full webhook URL in the field')
        self.webhook_reveal_btn.clicked.connect(self._on_webhook_reveal_clicked)
        webhook_row.addWidget(self.webhook_reveal_btn, alignment=Qt.AlignCenter)
        layout.addLayout(webhook_row)
        self.test_webhook_button = QPushButton('Test Webhook')
        self.test_webhook_button.setMinimumHeight(34)
        self.test_webhook_button.setFont(QFont(APP_FONT_FAMILY, 9))
        self.test_webhook_button.setCursor(Qt.PointingHandCursor)
        self.test_webhook_button.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.test_webhook_button.clicked.connect(self.on_test_webhook_clicked)
        layout.addWidget(self.test_webhook_button)

    def _build_status_section(self, layout):
        status_label_title = QLabel('Status')
        status_label_title.setFont(QFont(APP_FONT_FAMILY, 9, QFont.Bold))
        layout.addWidget(status_label_title)
        self.status_view = QTextEdit()
        fusion = QStyleFactory.create('Fusion')
        if fusion:
            self.status_view.setStyle(fusion)
        self.status_view.setReadOnly(True)
        self.status_view.setFrameShape(QFrame.NoFrame)
        self.status_view.setLineWrapMode(QTextEdit.WidgetWidth)
        self.status_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.status_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.status_view.setFont(QFont(APP_FONT_FAMILY, 9))
        self.status_view.setMinimumHeight(74)
        self.status_view.setMaximumHeight(170)
        self.status_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.status_view.document().setDocumentMargin(8)
        self.status_view.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.status_view, 1)

    def _build_issues_section(self, layout):
        self._add_separator(layout)
        header = QHBoxLayout()
        header.setSpacing(8)
        issues_label = QLabel('Known Issues')
        issues_label.setFont(QFont(APP_FONT_FAMILY, 9, QFont.Bold))
        issues_label.setToolTip(self._format_tooltip(KNOWN_ISSUES_TOOLTIP))
        header.addWidget(issues_label)
        header.addStretch(1)
        self.issues_count_label = self._create_badge('...', font_size=8, bold=True, color=TEXT_MUTED)
        header.addWidget(self.issues_count_label)
        layout.addLayout(header)
        self.issues_view = QScrollArea()
        self.issues_view.setObjectName('issuesScroll')
        self.issues_view.setWidgetResizable(True)
        self.issues_view.setFrameShape(QFrame.NoFrame)
        self.issues_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.issues_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.issues_view.setMinimumHeight(160)
        self.issues_view.setMaximumHeight(240)
        self.issues_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.issues_view.setFocusPolicy(Qt.NoFocus)
        self.issues_view.setStyleSheet(ISSUES_SCROLL_STYLE)
        self.issues_view.viewport().setStyleSheet('background: transparent;')
        self.issues_view.verticalScrollBar().setStyleSheet(_STATUS_VIEW_SCROLLBAR_QSS)
        self._issues_inner = QWidget()
        self._issues_inner.setObjectName('issuesScrollInner')
        self._issues_layout = QVBoxLayout(self._issues_inner)
        self._issues_layout.setContentsMargins(8, 8, 8, 8)
        self._issues_layout.setSpacing(8)
        self.issues_view.setWidget(self._issues_inner)
        layout.addWidget(self.issues_view, 1)
        self._set_issues_empty('Loading issues...')

    def _build_contributors_footer(self, layout):
        self._add_separator(layout)
        footer_row = QHBoxLayout()
        footer_row.setSpacing(8)
        self.discord_btn = QPushButton('Join Discord')
        self.discord_btn.setMinimumHeight(34)
        self.discord_btn.setFont(QFont(APP_FONT_FAMILY, 9, QFont.Bold))
        self.discord_btn.setCursor(Qt.PointingHandCursor)
        self.discord_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.discord_btn.clicked.connect(self._on_discord_clicked)
        footer_row.addWidget(self.discord_btn)
        self.contributors_btn = QPushButton('View Contributors')
        self.contributors_btn.setMinimumHeight(34)
        self.contributors_btn.setFont(QFont(APP_FONT_FAMILY, 9))
        self.contributors_btn.setCursor(Qt.PointingHandCursor)
        self.contributors_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.contributors_btn.clicked.connect(self._on_contributors_clicked)
        footer_row.addWidget(self.contributors_btn)
        layout.addLayout(footer_row)
        clear_row = QHBoxLayout()
        clear_row.setContentsMargins(0, 2, 0, 0)
        clear_row.addStretch()
        self.clear_log_btn = QPushButton('Clear log')
        self.clear_log_btn.setFont(QFont(APP_FONT_FAMILY, scale_font(8)))
        self.clear_log_btn.setCursor(Qt.PointingHandCursor)
        self.clear_log_btn.setStyleSheet(CLEAR_LOG_BUTTON_STYLE)
        self.clear_log_btn.setToolTip('Deletes AeroHelper.log. Only use this if you are sure.')
        self.clear_log_btn.clicked.connect(self._on_clear_log_clicked)
        clear_row.addWidget(self.clear_log_btn)
        self.ocr_debug_checkbox = QCheckBox('Debug')
        self.ocr_debug_checkbox.setFont(QFont(APP_FONT_FAMILY, scale_font(8)))
        self.ocr_debug_checkbox.setCursor(Qt.PointingHandCursor)
        self.ocr_debug_checkbox.setStyleSheet(f'color: {TEXT_SUBTLE}; background: transparent;')
        self.ocr_debug_checkbox.setToolTip(self._format_tooltip(OCR_DEBUG_TOOLTIP))
        self.ocr_debug_checkbox.stateChanged.connect(self.on_ocr_debug_changed)
        clear_row.addWidget(self.ocr_debug_checkbox)
        layout.addLayout(clear_row)

    def _on_discord_clicked(self):
        webbrowser.open('https://discord.gg/acdQ6BFrFs')

    def _on_contributors_clicked(self):
        url = f"{API_BASE.rstrip('/')}/#contributors"
        webbrowser.open(url)

    def _on_clear_log_clicked(self):
        if not self._confirm_clear_log():
            return
        log_path = default_log_path()
        try:
            if log_path.exists():
                log_path.unlink()
            self.update_status_panel('ok', f'Deleted log file:\n{log_path.name}')
        except OSError as exc:
            self._show_message_dialog(QMessageBox.Critical, 'Could Not Clear Log', f'Failed to delete {log_path.name}.\n\n{exc}')

    def _confirm_clear_log(self):
        dialog = QDialog(self)
        self._apply_no_context_help(dialog)
        dialog.setWindowTitle('Clear Log File?')
        dialog.setModal(True)
        icon_obj = load_app_icon()
        if not icon_obj.isNull():
            dialog.setWindowIcon(icon_obj)
        dialog.setMinimumSize(420, 200)
        dialog.resize(max(int(self.width() * 0.92), 420), 220)
        dialog.setStyleSheet(f'\n            QDialog {{\n                background-color: {BG_WINDOW};\n            }}\n            QLabel {{\n                color: {TEXT_PRIMARY};\n                background-color: transparent;\n            }}\n            QPushButton {{\n                background-color: {ACCENT_WARM};\n                color: {BG_WINDOW};\n                border: 1px solid rgba(255, 255, 255, 0.05);\n                border-radius: 10px;\n                padding: 8px 18px;\n                min-width: 90px;\n                font-weight: 600;\n            }}\n            QPushButton:hover {{\n                background-color: #E3D3B7;\n            }}\n            QPushButton:pressed {{\n                background-color: #C9B18D;\n            }}\n            QPushButton#cancelClearLog {{\n                background: rgba(255, 255, 255, 0.065);\n                color: {TEXT_PRIMARY};\n                border: 1px solid {BORDER_SOFT};\n            }}\n            QPushButton#cancelClearLog:hover {{\n                background: {BG_CARD_HOVER};\n                border-color: {BORDER_STRONG};\n            }}\n            QPushButton#confirmClearLog {{\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 rgba(255, 148, 148, 0.94),\n                    stop:1 rgba(248, 113, 113, 0.72));\n                color: #28070B;\n                border: 1px solid rgba(255, 215, 215, 0.42);\n            }}\n            QPushButton#confirmClearLog:hover {{\n                background: rgba(255, 170, 170, 0.96);\n            }}\n            ')
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        title_lbl = QLabel('Only do this if you are sure')
        title_lbl.setFont(QFont(APP_FONT_FAMILY, 13, QFont.Bold))
        title_lbl.setStyleSheet(f'color: {WARNING_TEXT};')
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)
        body = QLabel('This permanently deletes AeroHelper.log. Support and diagnostics may be harder without it.\n\nOnly continue if you are sure you want to clear the log (because of large file size, for example)')
        body.setFont(QFont(APP_FONT_FAMILY, 10))
        body.setWordWrap(True)
        layout.addWidget(body)
        layout.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setObjectName('cancelClearLog')
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(dialog.reject)
        confirm_btn = QPushButton('Delete Log')
        confirm_btn.setObjectName('confirmClearLog')
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.clicked.connect(dialog.accept)
        row.addWidget(cancel_btn)
        row.addWidget(confirm_btn)
        layout.addLayout(row)
        return dialog.exec_() == QDialog.Accepted

    def _clear_issues_layout(self):
        while self._issues_layout.count():
            item = self._issues_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _set_issues_empty(self, message):
        self._clear_issues_layout()
        empty = QLabel(message)
        empty.setFont(QFont(APP_FONT_FAMILY, 9))
        empty.setWordWrap(True)
        empty.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        empty.setStyleSheet(ISSUES_EMPTY_STYLE)
        self._issues_layout.addWidget(empty)
        self._issues_layout.addStretch(1)

    def _issue_theme(self, priority):
        return ISSUE_PRIORITY_THEME.get(priority, ISSUE_PRIORITY_THEME['low'])

    def _create_issue_card(self, issue):
        priority = (issue.get('priority') or 'low').lower()
        theme = self._issue_theme(priority)
        progress = max(0, min(100, int(issue.get('progress') or 0)))
        title = (issue.get('title') or '').strip() or 'Untitled issue'
        desc = (issue.get('description') or '').strip()
        card = QFrame()
        card.setObjectName('issueCard')
        card.setStyleSheet(f'\n            QFrame#issueCard {{\n                background: {theme["bg"]};\n                border: 1px solid {theme["border"]};\n                border-radius: 12px;\n            }}\n        ')
        outer = QHBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        accent = QFrame()
        accent.setFixedWidth(3)
        accent.setStyleSheet(f'background: {theme["text"]}; border: none; border-top-left-radius: 11px; border-bottom-left-radius: 11px;')
        outer.addWidget(accent)
        body = QWidget()
        body.setStyleSheet('background: transparent;')
        card_layout = QVBoxLayout(body)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(5)
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(self._create_badge(theme['label'], color=theme['text'], background='rgba(255, 255, 255, 0.08)', border=theme['border']), alignment=Qt.AlignTop)
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(APP_FONT_FAMILY, 9, QFont.Bold))
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(f'color: {TEXT_PRIMARY}; background: transparent;')
        title_row.addWidget(title_lbl, 1)
        card_layout.addLayout(title_row)
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont(APP_FONT_FAMILY, 9))
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f'color: {TEXT_MUTED}; background: transparent;')
            card_layout.addWidget(desc_lbl)
        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(progress)
        bar.setTextVisible(False)
        bar.setFixedHeight(7)
        bar.setStyleSheet(f'\n            QProgressBar {{\n                background: rgba(255, 255, 255, 0.10);\n                border: none;\n                border-radius: 4px;\n            }}\n            QProgressBar::chunk {{\n                background: {theme["text"]};\n                border-radius: 4px;\n            }}\n        ')
        progress_row.addWidget(bar, 1)
        pct = QLabel(f'{progress}%')
        pct.setFont(QFont(APP_FONT_FAMILY, scale_font(8), QFont.Bold))
        pct.setStyleSheet(f'color: {TEXT_SUBTLE}; background: transparent; min-width: 28px;')
        pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_row.addWidget(pct)
        card_layout.addLayout(progress_row)
        outer.addWidget(body, 1)
        return card

    @pyqtSlot(list)
    def update_issues(self, issues):
        issues = issues if isinstance(issues, list) else []
        if not issues:
            self.issues_count_label.setText('Clear')
            self._style_badge(self.issues_count_label, color=SUCCESS_TEXT)
            self._set_issues_empty('No active issues.')
            return
        self._clear_issues_layout()
        highest = 'low'
        for issue in issues:
            priority = (issue.get('priority') or 'low').lower()
            if priority == 'high':
                highest = 'high'
            elif priority == 'medium' and highest != 'high':
                highest = 'medium'
            self._issues_layout.addWidget(self._create_issue_card(issue))
        self._issues_layout.addStretch(1)
        count = len(issues)
        self.issues_count_label.setText(f'{count} open' if count != 1 else '1 open')
        theme = self._issue_theme(highest)
        self._style_badge(self.issues_count_label, color=theme['text'])
        self.issues_view.verticalScrollBar().setValue(0)

    @pyqtSlot(str)
    def set_global_version(self, global_version):
        global_version = sanitize_remote_version(global_version)
        self.global_version = global_version
        if not global_version or not (self.version or '').strip():
            return
        if is_version_outdated(self.version, global_version):
            self.version_check_label.setText('Outdated')
            self._style_badge(self.version_check_label, color=ERROR_TEXT)
            QTimer.singleShot(200, lambda: self._show_version_mismatch_dialog(global_version))
        else:
            self.version_check_label.setText(f'v{global_version}')
            self._style_badge(self.version_check_label, color=SUCCESS_TEXT)

    def _show_version_mismatch_dialog(self, global_version):
        dialog = QDialog(self)
        self._apply_no_context_help(dialog)
        dialog.setWindowTitle('AeroHelper - Update Required')
        icon = load_app_icon()
        if not icon.isNull():
            dialog.setWindowIcon(icon)
        dialog.setModal(True)
        dialog.resize(500, 280)
        dialog.setStyleSheet(f'\n            QDialog {{ background-color: {BG_WINDOW}; }}\n            QLabel {{ color: {TEXT_PRIMARY}; background: transparent; }}\n            QPushButton {{\n                background-color: {ACCENT_WARM};\n                color: {BG_WINDOW};\n                border: none;\n                border-radius: 10px;\n                padding: 10px 22px;\n                font-weight: 700;\n                font-size: 13px;\n            }}\n            QPushButton:hover {{ background-color: #E3D3B7; }}\n            QPushButton:pressed {{ background-color: #C9B18D; }}\n        ')
        v_layout = QVBoxLayout(dialog)
        v_layout.setContentsMargins(28, 24, 28, 20)
        v_layout.setSpacing(12)
        warn_lbl = QLabel('This version of AeroHelper is out of date')
        warn_lbl.setFont(QFont(APP_FONT_FAMILY, 14, QFont.Bold))
        warn_lbl.setStyleSheet(f'color: {ERROR_TEXT};')
        warn_lbl.setWordWrap(True)
        v_layout.addWidget(warn_lbl)
        local_ver = self.version or 'unknown'
        detail = QLabel(f'Your version: {local_ver}\nLatest version: {global_version}\n\nPlease download the latest release to get bug fixes, new features,\nand important updates. Click below to go to the releases page.')
        detail.setFont(QFont(APP_FONT_FAMILY, 10))
        detail.setStyleSheet(f'color: {TEXT_PRIMARY};')
        detail.setWordWrap(True)
        v_layout.addWidget(detail)
        v_layout.addStretch()
        btn = QPushButton("Okay, I'll Update")
        btn.setMinimumHeight(44)
        btn.setCursor(Qt.PointingHandCursor)

        def _on_update():
            webbrowser.open('https://github.com/SSkipr/AeronauticaHelper/releases')
            dialog.accept()
            schedule_frozen_update_cleanup()
            app = QApplication.instance()
            if app:
                app.quit()
        btn.clicked.connect(_on_update)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn)
        v_layout.addLayout(btn_row)
        dialog.exec_()

    def on_share_data_changed(self, state):
        self.config.set_share_data_with_developer(state == Qt.Checked)

    def _on_share_data_learn_more(self):
        url = f"{API_BASE.rstrip('/')}/data-sharing"
        webbrowser.open(url)

    def on_share_data_override_clicked(self):
        if self._share_data_override_succeeded:
            return
        self.share_data_override_btn.setEnabled(False)
        self.share_data_override_btn.setText('Sending...')
        self.share_data_override_btn.setCursor(Qt.ArrowCursor)
        self.share_data_override_requested.emit()

    @pyqtSlot(bool)
    def on_share_data_override_done(self, success):
        if success:
            self._share_data_override_succeeded = True
            self.share_data_override_btn.setText('Success!')
            self.share_data_override_btn.setStyleSheet(SHARE_DATA_OVERRIDE_SUCCESS_BUTTON_STYLE)
            self.share_data_override_btn.setEnabled(False)
            self.share_data_override_btn.setCursor(Qt.ArrowCursor)
            self.share_data_override_btn.setToolTip('Diagnostic data was sent to the developer.')
            return
        self.share_data_override_btn.setText('Share Data Override')
        self.share_data_override_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.share_data_override_btn.setCursor(Qt.PointingHandCursor)
        self.share_data_override_btn.setEnabled(True)

    def _set_checkbox_from_config(self, checkbox, checked):
        checkbox.blockSignals(True)
        checkbox.setChecked(checked)
        self._on_checkbox_state_changed(Qt.Checked if checked else Qt.Unchecked, checkbox)
        checkbox.blockSignals(False)

    def _custom_waypoint_enabled_for_mode(self, mode=None):
        selected_mode = mode or self.config.get_mode()
        if selected_mode == 'AutoSteer':
            return self.config.get_autosteer_custom_waypoint()
        return self.config.get_monitoring_custom_waypoint()

    def _set_custom_waypoint_for_mode(self, enabled, mode=None):
        selected_mode = mode or self.config.get_mode()
        if selected_mode == 'AutoSteer':
            self.config.set_autosteer_custom_waypoint(enabled)
        else:
            self.config.set_monitoring_custom_waypoint(enabled)

    def _checkbox_definitions(self):
        return ((self.mid_mission_checkbox, self.config.get_start_mid_mission()), (self.custom_waypoint_checkbox, self._custom_waypoint_enabled_for_mode()), (self.skip_bearing_checkbox, self.config.get_monitoring_skip_current_bearing()), (self.throttle_up_checkbox, self.config.get_throttle_up_if_not_100()), (self.intelligent_steering_checkbox, self.config.get_intelligent_steering()), (self.quit_after_5_errors_checkbox, self.config.get_quit_after_5_errors()), (self.include_screenshots_checkbox, self.config.get_include_screenshots()), (self.share_data_checkbox, self.config.get_share_data_with_developer()))

    def _checkbox_label(self, checkbox):
        for widget, label in ((self.mid_mission_checkbox, 'Start Mid-Mission'), (self.custom_waypoint_checkbox, 'Custom waypoint'), (self.skip_bearing_checkbox, 'Unlock 5 view'), (self.throttle_up_checkbox, 'Throttle up if not 100%'), (self.intelligent_steering_checkbox, 'Intelligent Steering'), (self.quit_after_5_errors_checkbox, 'Quit after 5 consecutive errors'), (self.include_screenshots_checkbox, 'Include screenshots in Mission Status'), (self.share_data_checkbox, 'Share data with developer')):
            if checkbox == widget:
                return label
        return None

    def _sync_multiplier_input_enabled(self):
        if getattr(self, 'is_running', False):
            self.multiplier_input.setEnabled(False)
            self._sync_locked_field_styles()
            return
        learn_on = (
            self.config.get_mode() in ('AutoSteer', 'AutoPilot')
            and getattr(self, 'intelligent_steering_checkbox', None) is not None
            and self.intelligent_steering_checkbox.isChecked()
        )
        self.multiplier_input.setEnabled(not learn_on)
        self._sync_locked_field_styles()

    def _sync_multiplier_display(self):
        self.multiplier_input.setText(str(self.config.get_multiplier()))

    def _intelligent_steering_on(self):
        return (
            self.config.get_mode() in ('AutoSteer', 'AutoPilot')
            and getattr(self, 'intelligent_steering_checkbox', None) is not None
            and self.intelligent_steering_checkbox.isChecked()
        )

    def _set_input_locked(self, widget, locked):
        widget.setProperty('locked', 'true' if locked else 'false')
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    def _sync_locked_field_styles(self):
        self._set_input_locked(self.interval_input, self.config.get_mode() == 'AutoPilot')
        self._set_input_locked(self.multiplier_input, self._intelligent_steering_on())

    def apply_learned_multiplier(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        self.config.set_multiplier(value)
        self.multiplier_input.blockSignals(True)
        self.multiplier_input.setText(str(value))
        self.multiplier_input.blockSignals(False)

    def _set_controls_enabled(self, enabled):
        for btn in self.mode_buttons.values():
            btn.setEnabled(enabled)
        self.notification_mode_combo.setEnabled(enabled)
        self.guard_fold_btn.setEnabled(enabled)
        self.blocked_services_input.setEnabled(enabled)
        self.blocked_process_input.setEnabled(enabled)
        self.webhook_input.setEnabled(enabled)
        self.webhook_reveal_btn.setEnabled(enabled)
        self.test_webhook_button.setEnabled(enabled)
        self.mid_mission_checkbox.setEnabled(enabled)
        self.custom_waypoint_checkbox.setEnabled(enabled)
        self.skip_bearing_checkbox.setEnabled(enabled)
        self.throttle_up_checkbox.setEnabled(enabled)
        self.intelligent_steering_checkbox.setEnabled(enabled)
        self.quit_after_5_errors_checkbox.setEnabled(enabled)
        self.include_screenshots_checkbox.setEnabled(enabled)
        self.share_data_checkbox.setEnabled(enabled)
        self.share_data_override_btn.setEnabled(enabled and not self._share_data_override_succeeded)
        self._sync_multiplier_input_enabled()

    def init_ui(self):
        title = f'AeroHelper {self.version}' if self.version else 'AeroHelper'
        self.setWindowTitle(title)
        icon = load_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self._set_initial_window_size()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        central_widget = QWidget()
        central_widget.setObjectName('mainCard')
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(SECTION_SPACING)
        layout.setContentsMargins(WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN)
        self._apply_theme()
        hero_panel, hero_layout = self._create_glass_panel('heroPanel', HERO_PANEL_STYLE, margins=(scale_px(14), scale_px(14), scale_px(14), scale_px(14)), spacing=scale_px(9))
        self._build_brand_header(hero_layout)
        layout.addWidget(hero_panel)
        controls_panel, controls_layout = self._create_glass_panel(margins=(scale_px(13), scale_px(13), scale_px(13), scale_px(13)), spacing=scale_px(9))
        self._build_primary_buttons(controls_layout)
        self._build_mode_section(controls_layout)
        self._build_info_panels(controls_layout)
        self._add_separator(controls_layout)
        self._build_notification_mode_row(controls_layout)
        self._build_option_checkboxes(controls_layout)
        layout.addWidget(controls_panel)
        tuning_panel, tuning_layout = self._create_glass_panel(margins=(scale_px(13), scale_px(13), scale_px(13), scale_px(13)), spacing=scale_px(9))
        self._build_cycle_controls(tuning_layout)
        self._build_process_guard_section(tuning_layout)
        layout.addWidget(tuning_panel)
        comms_panel, comms_layout = self._create_glass_panel(margins=(scale_px(13), scale_px(9), scale_px(13), scale_px(13)), spacing=scale_px(9))
        self._build_webhook_section(comms_layout)
        layout.addWidget(comms_panel)
        status_panel, status_layout = self._create_glass_panel(margins=(scale_px(13), scale_px(9), scale_px(13), scale_px(13)), spacing=scale_px(9))
        self._status_panel = status_panel
        self._build_status_section(status_layout)
        self._build_issues_section(status_layout)
        self._build_contributors_footer(status_layout)
        status_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(status_panel, 1)
        self._main_layout = layout
        self.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self._apply_no_context_help(self)
        self._update_layout_for_window_size()

    def _set_initial_window_size(self):
        screen = QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            width = min(max(int(available.width() * 0.22), 460), 560)
            height = min(max(int(available.height() * 0.78), 540), 820, available.height() - 80)
            x = available.x() + max(20, int(available.width() * 0.04))
            y = available.y() + max(20, int(available.height() * 0.04))
            self.setGeometry(x, y, width, height)
            self.setMinimumSize(440, 520)
        else:
            self.resize(480, 780)
            self.setMinimumSize(440, 520)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_layout_for_window_size()

    def _update_layout_for_window_size(self):
        if not hasattr(self, 'status_view') or not hasattr(self, 'issues_view'):
            return
        h = max(1, self.height())
        w = max(1, self.width())
        maximized = bool(self.windowState() & (Qt.WindowMaximized | Qt.WindowFullScreen))
        if maximized or h >= 900:
            self.status_view.setMaximumHeight(16777215)
            self.issues_view.setMaximumHeight(16777215)
            self.status_view.setMinimumHeight(max(120, int(h * 0.16)))
            self.issues_view.setMinimumHeight(max(180, int(h * 0.22)))
        elif h >= 720:
            self.status_view.setMaximumHeight(max(170, int(h * 0.22)))
            self.issues_view.setMaximumHeight(max(240, int(h * 0.28)))
            self.status_view.setMinimumHeight(90)
            self.issues_view.setMinimumHeight(160)
        else:
            self.status_view.setMaximumHeight(170)
            self.issues_view.setMaximumHeight(240)
            self.status_view.setMinimumHeight(74)
            self.issues_view.setMinimumHeight(160)
        if hasattr(self, '_main_layout') and self._main_layout is not None:
            side = max(WINDOW_MARGIN, min(48, int(w * 0.04))) if (maximized or w >= 700) else WINDOW_MARGIN
            self._main_layout.setContentsMargins(side, side, side, side)

    def _apply_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(BG_WINDOW))
        palette.setColor(QPalette.WindowText, QColor(TEXT_PRIMARY))
        palette.setColor(QPalette.Base, QColor(BG_PANEL))
        palette.setColor(QPalette.AlternateBase, QColor('#111A2E'))
        palette.setColor(QPalette.Button, QColor(ACCENT_WARM))
        palette.setColor(QPalette.ButtonText, QColor(BG_WINDOW))
        palette.setColor(QPalette.Highlight, QColor(ACCENT))
        palette.setColor(QPalette.HighlightedText, QColor(BG_WINDOW))
        palette.setColor(QPalette.ToolTipBase, QColor(BG_PANEL))
        palette.setColor(QPalette.ToolTipText, QColor(TEXT_PRIMARY))
        self.setPalette(palette)
        app = QApplication.instance()
        if app is not None:
            app.setPalette(palette)
            existing = app.styleSheet() or ''
            start = existing.find('QToolTip {')
            if start >= 0:
                end = existing.find('}', start)
                if end >= 0:
                    existing = (existing[:start] + existing[end + 1:]).strip()
            app.setStyleSheet((existing + '\n' + TOOLTIP_STYLE).strip())
        self.setStyleSheet('\n            QMainWindow {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #040612,\n                    stop:0.44 #071528,\n                    stop:1 #130A25);\n            }\n            QScrollArea {\n                background: transparent;\n                border: none;\n            }\n            QWidget#mainCard {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n                    stop:0 rgba(10, 17, 34, 0.86),\n                    stop:0.55 rgba(6, 12, 25, 0.90),\n                    stop:1 rgba(20, 11, 39, 0.88));\n                border: 1px solid rgba(255, 255, 255, 0.08);\n                border-radius: 0px;\n            }\n            %s\n            QLineEdit {\n                background: %s;\n                color: %s;\n                border: 1px solid %s;\n                border-radius: 14px;\n                padding: 10px 12px;\n                selection-background-color: %s;\n            }\n            QLineEdit:hover {\n                border: 1px solid %s;\n                background: rgba(255, 255, 255, 0.075);\n            }\n            QLineEdit:focus {\n                border: 1px solid %s;\n                background: rgba(255, 255, 255, 0.095);\n            }\n            QLineEdit:read-only {\n                color: %s;\n            }\n            QComboBox {\n                background: %s;\n                color: %s;\n                border: 1px solid %s;\n                border-radius: 14px;\n                padding: 8px 12px;\n                min-height: 22px;\n            }\n            QComboBox:hover, QComboBox:focus {\n                border: 1px solid %s;\n                background: rgba(255, 255, 255, 0.085);\n            }\n            QComboBox::drop-down {\n                border: none;\n                width: 22px;\n            }\n            QComboBox QAbstractItemView {\n                background-color: %s;\n                color: %s;\n                selection-background-color: %s;\n                selection-color: %s;\n                border: 1px solid %s;\n                outline: none;\n            }\n            QCheckBox {\n                color: %s;\n                spacing: 9px;\n                background: transparent;\n            }\n            QCheckBox::indicator {\n                width: 21px;\n                height: 21px;\n                border-radius: 8px;\n                border: 1px solid %s;\n                background: rgba(255, 255, 255, 0.06);\n            }\n            QCheckBox::indicator:hover {\n                border-color: %s;\n                background: rgba(125, 211, 252, 0.12);\n            }\n            QCheckBox::indicator:checked {\n                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 %s, stop:1 %s);\n                border-color: %s;\n            }\n            QLabel {\n                color: %s;\n                background: transparent;\n            }\n            QScrollBar:vertical {\n                border: none;\n                background: rgba(255, 255, 255, 0.035);\n                width: 10px;\n                margin: 8px 3px 8px 0;\n                border-radius: 4px;\n            }\n            QScrollBar::handle:vertical {\n                border: none;\n                background: rgba(173, 216, 255, 0.24);\n                min-height: 32px;\n                border-radius: 4px;\n            }\n            QScrollBar::handle:vertical:hover {\n                background: rgba(173, 216, 255, 0.36);\n            }\n            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {\n                height: 0px;\n                background: transparent;\n            }\n            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n                background: transparent;\n            }\n        ' % (BUTTON_STYLE, BG_INPUT, TEXT_PRIMARY, BORDER_SOFT, ACCENT, BORDER_GLOW, BORDER_STRONG, TEXT_MUTED, BG_INPUT, TEXT_PRIMARY, BORDER_SOFT, BORDER_STRONG, BG_PANEL, TEXT_PRIMARY, ACCENT_SOFT, TEXT_PRIMARY, BORDER_SOFT, TEXT_PRIMARY, BORDER_SOFT, BORDER_STRONG, ACCENT, ACCENT_2, ACCENT, TEXT_PRIMARY))

        self.setStyleSheet(self.styleSheet() + '''
            QLineEdit {
                border-radius: 12px;
                padding: 7px 10px;
            }
            QLineEdit[locked="true"],
            QLineEdit[locked="true"]:hover,
            QLineEdit[locked="true"]:focus,
            QLineEdit[locked="true"]:disabled {
                border: 1px solid rgba(248, 113, 113, 0.92);
            }
            QComboBox {
                border-radius: 12px;
                padding: 6px 10px;
                min-height: 18px;
            }
            QCheckBox::indicator {
                width: 17px;
                height: 17px;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 9px 2px 9px 0;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                border: none;
                background: rgba(208, 228, 255, 0.12);
                min-height: 28px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(208, 228, 255, 0.24);
            }
            QScrollBar:horizontal,
            QScrollBar::handle:horizontal,
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                height: 0px;
                background: transparent;
                border: none;
            }
        ''')

    def load_config(self):
        mode = self.config.get_mode()
        if mode in ['Monitoring', 'AutoSteer', 'AutoPilot']:
            btn = self.mode_buttons.get(mode)
            if btn:
                btn.setChecked(True)
                self.on_mode_changed(mode)
        from AeroHelper.notifications.policy import NOTIFICATION_MODE_KEYS, tooltip_for_mode
        notification_mode = self.config.get_notification_mode()
        try:
            idx = NOTIFICATION_MODE_KEYS.index(notification_mode)
        except ValueError:
            idx = 0
        self.notification_mode_combo.blockSignals(True)
        self.notification_mode_combo.setCurrentIndex(idx)
        self.notification_mode_combo.blockSignals(False)
        self.notification_mode_combo.setToolTip(self._format_tooltip(tooltip_for_mode(notification_mode)))
        for checkbox, checked in self._checkbox_definitions():
            self._set_checkbox_from_config(checkbox, checked)
        self.ocr_debug_checkbox.blockSignals(True)
        self.ocr_debug_checkbox.setChecked(self.config.get_ocr_debug())
        self.ocr_debug_checkbox.blockSignals(False)
        interval = self.config.get_cycle_interval()
        self.interval_input.setText(str(interval))
        multiplier = self.config.get_multiplier()
        self.multiplier_input.setText(str(multiplier))
        self._sync_multiplier_display()
        self._sync_multiplier_input_enabled()
        self.blocked_services_input.setText(self.config.get_blocked_services_text())
        self.blocked_process_input.setText(self.config.get_blocked_executables_text())
        self._webhook_value = self.config.get_webhook_url()
        self._update_webhook_display()
        self._update_warnings()

    def _update_warnings(self):
        if not self._webhook_value.strip():
            self._update_status('warning', 'Webhook URL is empty - no Discord notifications')
        elif not self._current_error:
            self._update_status('ok', 'Ready')

    def _update_status(self, status_type, message):
        self.update_status_panel(status_type, message, None)

    def _build_status_message_html(self, status_type, message):
        text = message or ''
        if status_type == 'error':
            if '\n' in text:
                head, body = text.split('\n', 1)
                return f"<div style='font-size:14px;font-weight:700;color:{ERROR_TEXT};line-height:1.35;margin-bottom:8px;'>{html.escape(head)}</div><div style='font-size:12px;font-weight:500;color:{TEXT_PRIMARY};line-height:1.55;white-space:pre-wrap;word-wrap:break-word;'>{html.escape(body)}</div>"
            return f"<div style='font-size:13px;font-weight:700;color:{ERROR_TEXT};line-height:1.45;white-space:pre-wrap;'>{html.escape(text)}</div>"
        if status_type == 'warning':
            return f"<div style='font-size:13px;font-weight:600;color:{WARNING_TEXT};line-height:1.45;white-space:pre-wrap;'>{html.escape(text)}</div>"
        return f"<div style='font-size:13px;font-weight:700;color:{TEXT_PRIMARY};line-height:1.45;white-space:pre-wrap;'>{html.escape(text)}</div>"

    def _os_info_html(self):
        import platform
        os_str = get_os_display_name()
        os_line = f"<div style='font-size:11px;margin-top:8px;line-height:1.45;color:{TEXT_MUTED};'><b>OS:</b> {html.escape(os_str)}</div>"
        if platform.system() == 'Darwin':
            mac_lines = ['macOS: grant Accessibility and Screen Recording in System Settings → Privacy & Security.', 'Human-intervention pause (auto-pause when you type) is not available on macOS - use Stop.', 'Auto App Shutdown (services/process kill) is Windows-only.', 'If Roblox does not focus automatically, click it after Start.']
            missing = get_macos_permission_summary()
            for item in missing:
                mac_lines.append(item)
            mac_body = '<br>'.join(html.escape(line) for line in mac_lines)
            mac_warn = f"<div style='font-size:11px;margin-top:4px;line-height:1.45;color:{WARNING_TEXT};background:rgba(98,72,20,0.45);border-radius:6px;padding:4px 8px;'>{mac_body}</div>"
            return os_line + mac_warn
        return os_line

    def _admin_privilege_html(self):
        os_html = self._os_info_html()
        if not IS_WINDOWS:
            return os_html
        if is_windows_elevated_admin():
            return os_html + f"<div style='font-size:11px;margin-top:6px;line-height:1.45;color:{SUCCESS_TEXT};'><b>Administrator:</b> true - Auto App Shutdown can stop services and end tasks as configured.</div>"
        return os_html + f"<div style='font-size:11px;margin-top:6px;line-height:1.45;color:{WARNING_TEXT};'><b>Administrator:</b> false - some settings (such as <b>Auto App Shutdown</b>) may be limited. Right-click AeroHelper and choose <b>Run as administrator</b> if stopping services or ending protected tasks fails.</div>"

    @pyqtSlot(str, str, object)
    def update_status_panel(self, status_type, message, diagnostics=None):
        self._current_error = status_type == 'error'
        lines = [self._build_status_message_html(status_type, message)]
        if diagnostics:
            diag_lines = []
            for key, value in diagnostics.items():
                diag_lines.append(f"<div><span style='color:{TEXT_MUTED};'>{html.escape(str(key))}:</span> {html.escape(str(value))}</div>")
            lines.append(f"<div style='font-size:10px;margin-top:8px;'>{''.join(diag_lines)}</div>")
        lines.append(self._admin_privilege_html())
        self.status_view.setHtml(''.join(lines))
        self.status_view.setStyleSheet(STATUS_VIEW_STYLES.get(status_type, STATUS_VIEW_STYLES['info']))
        self.status_view.verticalScrollBar().setStyleSheet(_STATUS_VIEW_SCROLLBAR_QSS)
        self.status_view.verticalScrollBar().setValue(0)

    def _apply_no_context_help(self, window):
        window.setWindowFlags(window.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    def _show_message_dialog(self, icon, title, message):
        dialog = QDialog(self)
        self._apply_no_context_help(dialog)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        icon_obj = load_app_icon()
        if not icon_obj.isNull():
            dialog.setWindowIcon(icon_obj)
        accent = ERROR_TEXT if icon == QMessageBox.Critical else WARNING_TEXT
        dialog.setMinimumSize(480, 220)
        dialog.resize(max(int(self.width() * 0.92), 480), max(int(self.height() * 0.42), 260))
        dialog.setStyleSheet(f'\n            QDialog {{\n                background-color: {BG_WINDOW};\n            }}\n            QLabel {{\n                color: {TEXT_PRIMARY};\n                background-color: transparent;\n            }}\n            QTextEdit {{\n                color: {TEXT_PRIMARY};\n                background-color: {BG_CARD};\n                border: 1px solid {BORDER_SOFT};\n                border-radius: 12px;\n                padding: 12px;\n            }}\n            QPushButton {{\n                background-color: {ACCENT_WARM};\n                color: {BG_WINDOW};\n                border: 1px solid rgba(255, 255, 255, 0.05);\n                border-radius: 10px;\n                padding: 8px 18px;\n                min-width: 90px;\n                font-weight: 600;\n            }}\n            QPushButton:hover {{\n                background-color: #E3D3B7;\n            }}\n            QPushButton:pressed {{\n                background-color: #C9B18D;\n            }}\n            ')
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        header = QHBoxLayout()
        logo = QLabel()
        pixmap = load_app_pixmap(36)
        if not pixmap.isNull():
            logo.setPixmap(pixmap)
            header.addWidget(logo)
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(APP_FONT_FAMILY, 13, QFont.Bold))
        title_lbl.setStyleSheet(f'color: {accent};')
        title_lbl.setWordWrap(True)
        header.addWidget(title_lbl, 1)
        layout.addLayout(header)
        body = QTextEdit()
        body.setReadOnly(True)
        body.setLineWrapMode(QTextEdit.WidgetWidth)
        body.setPlainText(message or '')
        body.setMinimumHeight(max(int(dialog.height() * 0.38), 140))
        layout.addWidget(body, 1)
        row = QHBoxLayout()
        row.addStretch()
        ok_btn = QPushButton('OK')
        ok_btn.clicked.connect(dialog.accept)
        row.addWidget(ok_btn)
        layout.addLayout(row)
        dialog.exec_()

    def _format_history_entry(self, entry, index):
        if not isinstance(entry, dict):
            return f'{index}. Unreadable history entry'
        lines = [f"{index}. {entry.get('event', 'Session')} - {entry.get('result', 'Unknown')}", f"Mode: {entry.get('mode', 'Unknown')}"]
        for key in ('timestamp', 'started_at', 'ended_at', 'duration_sec', 'cycles', 'reason'):
            value = entry.get(key)
            if value not in (None, ''):
                label = key.replace('_', ' ').title()
                lines.append(f'{label}: {value}')
        details = entry.get('details')
        if isinstance(details, dict):
            for key, value in details.items():
                if value not in (None, ''):
                    label = str(key).replace('_', ' ').title()
                    lines.append(f'{label}: {value}')
        return '\n'.join(lines)

    def show_history_dialog(self):
        self.config.get_history()
        entries = self.config.get_history()
        dialog = QDialog(self)
        self._apply_no_context_help(dialog)
        dialog.setWindowTitle('AeroHelper History')
        icon = load_app_icon()
        if not icon.isNull():
            dialog.setWindowIcon(icon)
        dialog.setMinimumSize(620, 460)
        dialog.setStyleSheet(f'\n            QDialog {{\n                background-color: {BG_WINDOW};\n            }}\n            QTextEdit {{\n                color: {TEXT_PRIMARY};\n                background-color: {BG_CARD};\n                border: 1px solid {BORDER_SOFT};\n                border-radius: 12px;\n                padding: 12px;\n            }}\n            QLabel {{\n                color: {TEXT_PRIMARY};\n            }}\n            {BUTTON_STYLE}\n            ')
        layout = QVBoxLayout(dialog)
        title = QLabel('Recent History')
        title.setFont(QFont(APP_FONT_FAMILY, 13, QFont.Bold))
        layout.addWidget(title)
        history_text = QTextEdit()
        history_text.setReadOnly(True)
        history_text.setFont(QFont(APP_FONT_FAMILY, 10))
        if entries:
            history_text.setPlainText('\n\n'.join((self._format_history_entry(entry, i + 1) for i, entry in enumerate(entries))))
        else:
            history_text.setPlainText('No history yet. Recent sessions and completed AutoPilot missions will appear here.')
        layout.addWidget(history_text)
        close_button = QPushButton('Close')
        close_button.setMinimumHeight(40)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        dialog.exec_()

    def _show_consent_dialog(self):
        dialog = QDialog(self)
        self._apply_no_context_help(dialog)
        dialog.setWindowTitle('AeroHelper Consent Required')
        icon = load_app_icon()
        if not icon.isNull():
            dialog.setWindowIcon(icon)
        dialog.setModal(True)
        dialog.resize(max(int(self.width() * 1.05), 520), max(int(self.height() * 0.48), 360))
        dialog.setStyleSheet(f'\n            QDialog {{\n                background-color: {BG_WINDOW};\n            }}\n            QLabel {{\n                color: {TEXT_PRIMARY};\n                background-color: transparent;\n            }}\n            QTextEdit {{\n                color: {TEXT_PRIMARY};\n                background-color: {BG_CARD};\n                border: 1px solid {BORDER_SOFT};\n                border-radius: 12px;\n                padding: 12px;\n            }}\n            QPushButton {{\n                background-color: {ACCENT_WARM};\n                color: {BG_WINDOW};\n                border: 1px solid rgba(255, 255, 255, 0.05);\n                border-radius: 10px;\n                padding: 8px 18px;\n                min-width: 90px;\n                font-weight: 600;\n            }}\n            QPushButton:hover {{\n                background-color: #E3D3B7;\n            }}\n            QPushButton:pressed {{\n                background-color: #C9B18D;\n            }}\n            ')
        layout = QVBoxLayout(dialog)
        header = QHBoxLayout()
        logo = QLabel()
        pixmap = load_app_pixmap(40)
        if not pixmap.isNull():
            logo.setPixmap(pixmap)
            header.addWidget(logo)
        title = QLabel('AeroHelper Consent Required')
        title.setFont(QFont(APP_FONT_FAMILY, 13, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setLineWrapMode(QTextEdit.WidgetWidth)
        text.setPlainText(CONSENT_TEXT)
        text.setMinimumHeight(max(int(dialog.height() * 0.45), 180))
        layout.addWidget(text)
        tos_label = QLabel(
            f'Review AeroHelper\'s <a href="{html.escape(TOS_URL)}" style="color: {ACCENT};">Terms of Service</a> on the website before continuing.'
        )
        tos_label.setOpenExternalLinks(True)
        tos_label.setWordWrap(True)
        tos_label.setTextFormat(Qt.RichText)
        tos_label.setFont(QFont(APP_FONT_FAMILY, 10))
        layout.addWidget(tos_label)
        button_row = QHBoxLayout()
        button_row.addStretch()
        agree_button = QPushButton('I Agree')
        exit_button = QPushButton('Exit')
        agree_button.clicked.connect(dialog.accept)
        exit_button.clicked.connect(dialog.reject)
        button_row.addWidget(agree_button)
        button_row.addWidget(exit_button)
        layout.addLayout(button_row)
        dialog.exec_()
        if dialog.result() == QDialog.Accepted:
            self.config.set_consent_accepted(True)
            self._set_controls_enabled(True)
            self.start_button.setEnabled(True)
            self.on_mode_changed(self.config.get_mode())
            self._update_warnings()
            return
        app = QApplication.instance()
        if app:
            app.quit()
        else:
            self.close()

    def show_api_notice(self, severity, title, message, show_dialog=False):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.show()
        status_type = 'error' if severity == 'error' else 'warning'
        self._update_status(status_type, f'{title}\n{message}')
        if show_dialog:
            icon = QMessageBox.Critical if severity == 'error' else QMessageBox.Warning
            self._show_message_dialog(icon, title, message)

    def show_error(self, title, message, details=None):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.show()
        self.raise_()
        self.activateWindow()
        full_message = message
        status_message = f'{title}\n{full_message}'
        self._update_status('error', status_message)
        self._show_message_dialog(QMessageBox.Critical, title, full_message)

    def clear_error(self):
        self._current_error = False
        self._update_warnings()

    def lock_fields(self):
        self._set_controls_enabled(False)
        self.interval_input.setEnabled(False)
        self._sync_locked_field_styles()

    def unlock_fields(self):
        self._set_controls_enabled(True)
        is_autopilot = self.config.get_mode() == 'AutoPilot'
        self.interval_input.setEnabled(not is_autopilot)
        self._sync_locked_field_styles()

    def _get_webhook_url(self):
        if not self._webhook_redacted:
            return self.webhook_input.text().strip()
        return self._webhook_value

    def on_start_clicked(self):
        self.clear_error()
        if not self.config.get_consent_accepted():
            self._show_consent_dialog()
            if not self.config.get_consent_accepted():
                return
        if not self._webhook_redacted:
            self._webhook_value = self.webhook_input.text().strip()
            self.config.set_webhook_url(self._webhook_value)
        self.config.set_blocked_services_text(self.blocked_services_input.text().strip())
        self.config.set_blocked_executables_text(self.blocked_process_input.text().strip())
        try:
            interval = int(self.interval_input.text() or '15')
            if interval < 10 or interval > 30:
                self._show_message_dialog(QMessageBox.Warning, 'Invalid Input', 'Cycle interval must be between 10 and 30 seconds')
                return
        except ValueError:
            self._show_message_dialog(QMessageBox.Warning, 'Invalid Input', 'Cycle interval must be a number')
            return
        try:
            multiplier = float(self.multiplier_input.text() or '1.0')
            if multiplier < 0 or multiplier > 2:
                self._show_message_dialog(QMessageBox.Warning, 'Invalid Input', 'Multiplier must be between 0 and 2')
                return
        except ValueError:
            self._show_message_dialog(QMessageBox.Warning, 'Invalid Input', 'Multiplier must be a number')
            return
        self.config.set_multiplier(multiplier)
        self.is_running = True
        self.start_button.hide()
        self.stop_button.show()
        self.lock_fields()
        self.setWindowState(Qt.WindowMinimized)
        self.start_requested.emit()

    @pyqtSlot(bool)
    def show_start_button(self, clear_error=True):
        self.start_button.show()
        self.stop_button.hide()
        self.unlock_fields()
        if clear_error:
            self.clear_error()

    def on_stop_clicked(self):
        self.is_running = False
        self.show_start_button()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.stop_requested.emit()

    def on_test_webhook_clicked(self):
        if not self._webhook_redacted:
            self._webhook_value = self.webhook_input.text().strip()
            self.config.set_webhook_url(self._webhook_value)
        if not self._webhook_value.strip():
            self._show_message_dialog(QMessageBox.Warning, 'Webhook Required', 'Enter a Discord webhook URL before testing.')
            self._update_warnings()
            return
        self._update_status('info', 'Sending test webhook...')
        self.test_webhook_requested.emit()

    def on_mode_changed(self, text):
        self.config.set_mode(text)
        is_monitoring = text == 'Monitoring'
        is_autosteer = text == 'AutoSteer'
        is_autopilot = text == 'AutoPilot'
        self.monitoring_info.setVisible(is_monitoring)
        self.autosteer_info.setVisible(is_autosteer)
        self.autopilot_info.setVisible(is_autopilot)
        self.custom_waypoint_checkbox.setVisible(is_monitoring or is_autosteer)
        self.skip_bearing_checkbox.setVisible(is_monitoring)
        self.throttle_up_checkbox.setVisible(is_monitoring or is_autosteer)
        self.intelligent_steering_row.setVisible(is_autosteer or is_autopilot)
        self.mid_mission_checkbox.setVisible(is_autopilot)
        self.interval_input.setEnabled(not is_autopilot)
        if is_monitoring or is_autosteer:
            self._set_checkbox_from_config(self.custom_waypoint_checkbox, self._custom_waypoint_enabled_for_mode(text))
        if is_monitoring or is_autosteer:
            self._set_checkbox_from_config(self.throttle_up_checkbox, self.config.get_throttle_up_if_not_100())
        if is_autosteer or is_autopilot:
            self._set_checkbox_from_config(self.intelligent_steering_checkbox, self.config.get_intelligent_steering())
        if is_monitoring:
            self._set_checkbox_from_config(self.skip_bearing_checkbox, self.config.get_monitoring_skip_current_bearing())
        if is_autopilot:
            self.interval_input.setText('15')
            self.config.set_cycle_interval(15)
        self._sync_multiplier_display()
        self._sync_multiplier_input_enabled()

    def on_notification_mode_changed(self, text):
        from AeroHelper.notifications.policy import NOTIFICATION_MODE_KEYS, NOTIFICATION_MODE_LABELS, tooltip_for_mode
        try:
            mode = NOTIFICATION_MODE_KEYS[NOTIFICATION_MODE_LABELS.index(text)]
        except ValueError:
            mode = 'minimal'
        self.config.set_notification_mode(mode)
        self.notification_mode_combo.setToolTip(self._format_tooltip(tooltip_for_mode(mode)))

    def _on_notification_mode_activated(self, _index=None):
        if self.notification_mode_combo.currentIndex() == 2:
            self._show_custom_notification_dialog()

    def _show_custom_notification_dialog(self):
        from AeroHelper.notifications.policy import NOTIFICATION_CATEGORIES, normalize_custom_pings
        pings = dict(self.config.get_notification_custom_pings())
        dialog = QDialog(self)
        dialog.setWindowTitle('Custom @everyone pings')
        dialog.setModal(True)
        self._apply_no_context_help(dialog)
        dialog.setMinimumWidth(scale_px(380))
        dialog.setStyleSheet(f'''
            QDialog {{ background-color: {BG_WINDOW}; }}
            QLabel {{ color: {TEXT_PRIMARY}; background: transparent; }}
            QPushButton#pingOn {{
                background: {SUCCESS_BG};
                color: {SUCCESS_TEXT};
                border: 1px solid {SUCCESS_BORDER};
                border-radius: 10px;
                min-width: 44px;
                min-height: 32px;
                font-weight: 800;
            }}
            QPushButton#pingOff {{
                background: {ERROR_BG};
                color: {ERROR_TEXT};
                border: 1px solid {ERROR_BORDER};
                border-radius: 10px;
                min-width: 44px;
                min-height: 32px;
                font-weight: 800;
            }}
            QPushButton#savePings {{
                background-color: {ACCENT_WARM};
                color: {BG_WINDOW};
                border-radius: 10px;
                padding: 8px 18px;
                font-weight: 600;
            }}
        ''')
        layout = QVBoxLayout(dialog)
        buttons = {}

        def refresh_button(key):
            btn = buttons[key]
            on = bool(pings.get(key))
            btn.setText('✓' if on else '✕')
            btn.setObjectName('pingOn' if on else 'pingOff')
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        def toggle(key):
            pings[key] = not bool(pings.get(key))
            refresh_button(key)

        for key, label, description in NOTIFICATION_CATEGORIES:
            row = QHBoxLayout()
            text_col = QVBoxLayout()
            title = QLabel(label)
            title.setFont(QFont(APP_FONT_FAMILY, 10, QFont.Bold))
            desc = QLabel(description)
            desc.setWordWrap(True)
            desc.setFont(QFont(APP_FONT_FAMILY, 8))
            desc.setStyleSheet(f'color: {TEXT_MUTED};')
            text_col.addWidget(title)
            text_col.addWidget(desc)
            row.addLayout(text_col, 1)
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, k=key: toggle(k))
            buttons[key] = btn
            refresh_button(key)
            row.addWidget(btn, 0, Qt.AlignRight | Qt.AlignVCenter)
            layout.addLayout(row)
        save = QPushButton('Save')
        save.setObjectName('savePings')
        save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(dialog.accept)
        layout.addWidget(save, 0, Qt.AlignRight)
        if dialog.exec_() == QDialog.Accepted:
            self.config.set_notification_custom_pings(normalize_custom_pings(pings))

    def _on_checkbox_state_changed(self, state, checkbox=None):
        cb = checkbox or self.sender()
        if cb is None:
            return
        base = self._checkbox_label(cb)
        if base is None:
            return
        cb.setText(base)

    def on_mid_mission_changed(self, state):
        self.config.set_start_mid_mission(state == Qt.Checked)

    def on_custom_waypoint_changed(self, state):
        self._set_custom_waypoint_for_mode(state == Qt.Checked)

    def on_skip_bearing_changed(self, state):
        self.config.set_monitoring_skip_current_bearing(state == Qt.Checked)

    def on_throttle_up_changed(self, state):
        self.config.set_throttle_up_if_not_100(state == Qt.Checked)

    def on_intelligent_steering_changed(self, state):
        if state == Qt.Checked:
            try:
                self.config.set_multiplier(float(self.multiplier_input.text() or '1.0'))
            except ValueError:
                pass
        self.config.set_intelligent_steering(state == Qt.Checked)
        self._sync_multiplier_display()
        self._sync_multiplier_input_enabled()
        self._sync_locked_field_styles()

    def on_quit_after_5_errors_changed(self, state):
        self.config.set_quit_after_5_errors(state == Qt.Checked)

    def on_include_screenshots_changed(self, state):
        self.config.set_include_screenshots(state == Qt.Checked)

    def on_ocr_debug_changed(self, state):
        enabled = state == Qt.Checked
        self.config.set_ocr_debug(enabled)
        self.ocr_debug_changed.emit(enabled)

    def on_interval_changed(self):
        try:
            interval = int(self.interval_input.text() or '15')
            self.config.set_cycle_interval(interval)
        except ValueError:
            pass

    def on_multiplier_changed(self):
        try:
            multiplier = float(self.multiplier_input.text() or '1.0')
            self.config.set_multiplier(multiplier)
        except ValueError:
            pass

    def on_blocked_services_changed(self):
        self.config.set_blocked_services_text(self.blocked_services_input.text().strip())

    def on_blocked_processes_changed(self):
        self.config.set_blocked_executables_text(self.blocked_process_input.text().strip())

    def on_webhook_changed(self):
        if not self._webhook_redacted:
            self._webhook_value = self.webhook_input.text().strip()
            self.config.set_webhook_url(self._webhook_value)
        self._update_warnings()

    def set_paused_state(self, paused):
        pass
