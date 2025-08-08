'''

      .o.                                    ooooo   ooooo           oooo                                
     .888.                                   `888'   `888'           `888                                
    .8"888.      .ooooo.  oooo d8b  .ooooo.   888     888   .ooooo.   888  oo.ooooo.   .ooooo.  oooo d8b 
   .8' `888.    d88' `88b `888""8P d88' `88b  888ooooo888  d88' `88b  888   888' `88b d88' `88b `888""8P 
  .88ooo8888.   888ooo888  888     888   888  888     888  888ooo888  888   888   888 888ooo888  888     
 .8'     `888.  888    .o  888     888   888  888     888  888    .o  888   888   888 888    .o  888     
o.oooooo..o88.oooooo..oPoooo88b    `Yo8od8P' o888o   o888o `Y8bod8P' o888o  888bod8P' `Y8bod8P' d888b    
d8P'    `Y8 d8P'    `Y8 `888         `"'                                    888                          
Y88bo.      Y88bo.       888  oooo  oooo  oo.ooooo.  oooo d8b              o888o                         
 `"Y8888o.   `"Y8888o.   888 .8P'   `888   888' `88b `888""8P                                            
     `"Y88b      `"Y88b  888888.     888   888   888  888                                                
oo     .d8P oo     .d8P  888 `88b.   888   888   888  888                                                
8""88888P'  8""88888P'  o888o o888o o888o  888bod8P' d888b                                               
                                           888                                                           
                                          o888o                                                          
                                                                                                                      
https://aeronautica-helper.vercel.app
https://github.com/SSkipr/AeronauticaHelper
Version 3.6
'''

# Main File

import sys
import time
import logging
import re
import threading
import datetime
import pyautogui
import webbrowser
import requests
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QLineEdit, QLabel, QCheckBox, QMessageBox, QFrame,
                             QHBoxLayout, QDialog, QComboBox, QTextEdit, QDialogButtonBox,
                             QScrollArea, QProgressBar, QGridLayout)
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QByteArray

import core
from core import (
    check_version, alert,
    capture_and_process_screenshot, extract_distance,
    extract_target_bearing, extract_current_bearing,
    extract_land_clearance_altitude, extract_sea_level_altitude, 
    extract_fuel_level, restart_all_engines,
    save_config, load_config, VERSION, AIRPORT_ROUTES, AIRSHIP_ROUTES,
    keyboard, cross_mouse, click_center, close_roblox_client, launch_roblox_client,
    focus_roblox_window, _run_doctr_ocr_on_top_right_quadrant, _run_doctr_ocr_on_top_half,
    extract_military_time, is_night_time
)
from pynput.keyboard import Key
from autopilot import AutoPilotThread, check_for_end_sail

STEERING_HISTORY = []
OSCILLATION_ALERT_SENT = False
JUST_RECONNECTED = False

DARK_STYLE = """
    QWidget {
        background-color: #2E3440;
        color: #D8DEE9;
        font-family: "Segoe UI";
        font-size: 10pt;
    }
    QFrame {
        border: none;
    }
    QLabel {
        background-color: transparent;
    }
    QPushButton {
        background-color: #4C566A;
        color: #ECEFF4;
        border: 1px solid #4C566A;
        border-radius: 4px;
        padding: 6px;
    }
    QPushButton:hover {
        background-color: #5E81AC;
        border: 1px solid #5E81AC;
    }
    QPushButton:pressed {
        background-color: #81A1C1;
    }
    QPushButton:disabled {
        background-color: #3B4252;
        color: #4C566A;
        border-color: #3B4252;
    }
    QLineEdit {
        background-color: #3B4252;
        border: 1px solid #4C566A;
        border-radius: 4px;
        padding: 5px;
        color: #ECEFF4;
    }
    QLineEdit:disabled {
        background-color: #2E3440;
        color: #4C566A;
        border-color: #3B4252;
    }
    QCheckBox {
        spacing: 5px;
    }
    QCheckBox::indicator {
        width: 13px;
        height: 13px;
    }
    QCheckBox:disabled {
        color: #4C566A;
    }
    QLabel:disabled {
        color: #4C566A;
    }
    QMessageBox {
        background-color: #3B4252;
    }
    QDialog {
        background-color: #3B4252;
    }
    QProgressBar {
        border: 1px solid #4C566A;
        border-radius: 4px;
        text-align: center;
        color: #ECEFF4;
    }
    QProgressBar::chunk {
        background-color: #88C0D0;
        border-radius: 3px;
    }
    QScrollArea {
        border: 1px solid #4C566A;
        border-radius: 4px;
    }
    QScrollBar:vertical {
        border: none;
        background: #3B4252;
        width: 10px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #5E81AC;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

class IssueCard(QFrame):
    def __init__(self, issue_data, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(100)
        
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        
        self.priority_label = QLabel()
        priority = issue_data.get("priority", "low").lower()
        color_map = {"high": "#FF4C4C", "medium": "#FFB84C", "low": "#4CAF50"}
        color = color_map.get(priority, "gray")
        self.priority_label.setStyleSheet(f"""
            background-color: {color};
            border: 1px solid #555;
            border-radius: 7px;
            min-width: 14px;
            max-width: 14px;
            min-height: 14px;
            max-height: 14px;
        """)
        
        self.title_label = QLabel(f"<b>{issue_data.get('title', 'No Title')}</b>")
        self.title_label.setWordWrap(True)
        
        top_layout.addWidget(self.priority_label)
        top_layout.addWidget(self.title_label)
        
        self.description_label = QLabel(issue_data.get('description', 'No description available.'))
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("padding-left: 5px; color: #B0B8C4;")

        bottom_layout = QHBoxLayout()
        self.progress_label = QLabel("Progress:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(issue_data.get('status', 0))
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"%p%")
        
        bottom_layout.addWidget(self.progress_label)
        bottom_layout.addWidget(self.progress_bar)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.description_label)
        main_layout.addLayout(bottom_layout)

class FeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Submit Feedback")
        self.setMinimumWidth(350)
        self.error_message = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.priority_combo.setCurrentText("Medium")
        layout.addWidget(self.priority_combo)

        layout.addWidget(QLabel("Feedback:"))
        self.feedback_text = QTextEdit()
        self.feedback_text.setPlaceholderText("")
        layout.addWidget(self.feedback_text)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("Submit")
        self.button_box.accepted.connect(self.submit_feedback)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def submit_feedback(self):
        priority = self.priority_combo.currentText()
        feedback = self.feedback_text.toPlainText().strip()

        if not feedback:
            QMessageBox.warning(self, "Empty Feedback", "Please enter your feedback before submitting.")
            return

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.Cancel).setEnabled(False)
        
        threading.Thread(target=self._send_request, args=(priority, feedback), daemon=True).start()

    def _send_request(self, priority, feedback):
        endpoint = "https://aeronautica-helper.vercel.app/api/feedback"
        payload = {"priority": priority, "feedback": feedback}
        try:
            response = requests.post(endpoint, json=payload, timeout=15)
            response.raise_for_status()
            self.accept()
        except requests.exceptions.RequestException as e:
            self.error_message = str(e)
            self.reject()

class AeroHelperApp(QWidget):
    issues_fetched = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.issues_fetched.connect(self.populate_issues_ui)
        
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.config = load_config()
        core.SHARE_DATA = self.config.get("share_anonymous_data", True)
        self.quit_on_errors_enabled = self.config.get("quit_on_errors", True)
        core.QUIT_ON_ERRORS = self.quit_on_errors_enabled

        self.boat_autopilot_mode = False
        self.airship_autopilot_mode = False
        self.autopilot_ready = False
        self.autopilot_thread = None
        self.autopilot_final_phase = False
        self.start_mid_mission = False
        self.airship_flight_phase = None
        
        self.set_app_icon()
        
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_AeroHelper_Logic)
        self.is_running = False

        threading.Thread(target=self.fetch_issues, daemon=True).start()

        self.previous_distance = None
        self.previous_time = None
        self.start_distance = None
        self.false_arrival_counter = 0
        self.alert_counter = 0
        self.ocr_error_counter = 0
        self.cycle_count = 0
        self.start_time = time.time()
        self.last_fuel_alert_level = -1

        self.auto_steer_enabled = False
        self.webhook_logging_enabled = False
        self.throttle_alert_sent = False
        self.time_of_last_ocr_refresh = time.time()
        self.last_seen_target_info = None
        self.target_bearing_confirmed = False
        
        self.night_vision_cycle_counter = 0
        self.current_night_mode = None
        self.last_time_check = None

        self.altitude_control_running = False
        self.airship_throttle_set = False

    def closeEvent(self, event):
        try:
            logging.info("Application closing, saving configuration data")
            
            def safe_get_input(input_field, field_type, default_value):
                try:
                    if hasattr(self, input_field) and getattr(self, input_field) is not None:
                        field = getattr(self, input_field)
                        text = field.text().strip()
                        if text:
                            return field_type(text)
                    return self.config.get(field_name_map.get(input_field, ""), default_value)
                except (ValueError, AttributeError):
                    return default_value
            
            def safe_get_checkbox(checkbox_field, default_value):
                try:
                    if hasattr(self, checkbox_field) and getattr(self, checkbox_field) is not None:
                        return getattr(self, checkbox_field).isChecked()
                    return self.config.get(field_name_map.get(checkbox_field, ""), default_value)
                except AttributeError:
                    return default_value
            
            field_name_map = {
                'webhook_url_input': 'webhook_url',
                'ship_speed_input': 'ship_top_speed',
                'stop_distance_input': 'stop_distance',
                'cycle_interval_input': 'cycle_interval',
                'leeway_input': 'leeway',
                'multiplier_input': 'multiplier',
                'airship_altitude_input': 'airship_cruising_altitude',
                'airship_throttle_input': 'airship_throttle_level',
                'share_checkbox': 'share_anonymous_data',
                'quit_on_errors_checkbox': 'quit_on_errors',
                'mid_mission_checkbox': 'start_mid_mission'
            }
            
            config_data = {
                "webhook_url": safe_get_input('webhook_url_input', str, "").strip(),
                "ship_top_speed": safe_get_input('ship_speed_input', float, 20),
                "stop_distance": safe_get_input('stop_distance_input', float, 1),
                "cycle_interval": safe_get_input('cycle_interval_input', float, 0.5),
                "leeway": safe_get_input('leeway_input', float, 0.3),
                "multiplier": safe_get_input('multiplier_input', float, 1.9),
                "airship_cruising_altitude": safe_get_input('airship_altitude_input', float, 1500),
                "airship_throttle_level": safe_get_input('airship_throttle_input', int, 30),
                "share_anonymous_data": safe_get_checkbox('share_checkbox', True),
                "quit_on_errors": safe_get_checkbox('quit_on_errors_checkbox', True),
                "start_mid_mission": safe_get_checkbox('mid_mission_checkbox', False)
            }
            
            save_config(config_data)
            logging.info(f"Configuration data saved successfully with {len(config_data)} settings on application close")
            
        except Exception as e:
            logging.error(f"[!] Failed to save configuration on application close: {str(e)}")
        
        event.accept()
        super().closeEvent(event)

    def set_app_icon(self):
        try:
            icon_data = "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"
            if icon_data:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray.fromBase64(icon_data.encode()))
                icon = QIcon(pixmap)
                self.setWindowIcon(icon)
        except Exception as e:
            logging.error(f"[!] Failed to set application icon: {str(e)}")

    def init_ui(self):
        self.setWindowTitle('AeroHelper v' + VERSION)
        
        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.toggle_logic)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        mode_layout = QHBoxLayout()
        self.boat_autopilot_button = QPushButton('Boat AutoPilot', self)
        self.boat_autopilot_button.clicked.connect(self.toggle_BoatAutoPilot)
        mode_layout.addWidget(self.boat_autopilot_button)

        self.airship_autopilot_button = QPushButton('Airship AutoPilot', self)
        self.airship_autopilot_button.clicked.connect(self.toggle_AirshipAutoPilot)
        mode_layout.addWidget(self.airship_autopilot_button)
        
        self.autosteer_button = QPushButton('AutoSteer', self)
        self.autosteer_button.clicked.connect(self.toggle_AutoSteer)
        self.mid_mission_checkbox = QCheckBox("Start AutoPilot mid-mission", self)
        self.mid_mission_checkbox.stateChanged.connect(self.toggle_mid_mission)
        self.mid_mission_checkbox.setEnabled(False)
        self.webhooknotif_button = QPushButton('Verbose Notifications', self)
        self.webhooknotif_button.clicked.connect(self.toggle_WebhookNotif)
        self.share_checkbox = QCheckBox("Share anonymous data with developer", self)
        self.share_checkbox.stateChanged.connect(self.toggle_share_data)
        
        self.quit_on_errors_checkbox = QCheckBox("Quit after 5 Consecutive Errors", self)
        self.quit_on_errors_checkbox.stateChanged.connect(self.toggle_quit_on_errors)
        self.quit_on_errors_checkbox.setChecked(self.quit_on_errors_enabled)
        
        self.ship_speed_input = QLineEdit(self)
        self.ship_speed_input.setPlaceholderText("Enter Vehicle's Top Speed")
        self.ship_speed_label = QLabel("Vehicle's Top Speed (Knots)", self)

        self.stop_distance_input = QLineEdit(self)
        self.stop_distance_input.setPlaceholderText("0.5-1 Recommended")
        self.stop_distance_label = QLabel("Stop Distance from Destination (nm)", self)

        self.cycle_interval_input = QLineEdit(self)
        self.cycle_interval_input.setPlaceholderText("0.25-0.5 Recommended")
        self.cycle_interval_label = QLabel("System Cycle Interval (Minutes)", self)

        self.airship_altitude_label = QLabel("Airship Cruising Altitude (ft)", self)
        self.airship_altitude_input = QLineEdit(self)
        self.airship_altitude_input.setPlaceholderText(">3000 Recommended")
        self.airship_altitude_input.setEnabled(False)

        self.airship_throttle_label = QLabel("Airship Throttle (1-100)", self)
        self.airship_throttle_input = QLineEdit(self)
        self.airship_throttle_input.setPlaceholderText("% Throttle of Vehicle")
        self.airship_throttle_input.setEnabled(False)

        self.leeway_label = QLabel("Leeway (nm)", self)
        self.leeway_input = QLineEdit(self)
        self.leeway_input.setPlaceholderText("0.3 Recommended")
        
        self.multiplier_label = QLabel("Multiplier", self)
        self.multiplier_input = QLineEdit(self)
        self.multiplier_input.setPlaceholderText("Keep between 0.5-2")
        
        self.webhook_url_label = QLabel("Webhook URL", self)
        self.webhook_url_input = QLineEdit(self)
        self.webhook_url_input.setPlaceholderText("Enter Webhook URL")

        self.ship_speed_input.focusOutEvent = lambda event: self.cleanup_decimal_input(self.ship_speed_input, event)
        self.airship_altitude_input.focusOutEvent = lambda event: self.cleanup_decimal_input(self.airship_altitude_input, event)
        self.airship_throttle_input.focusOutEvent = lambda event: self.cleanup_decimal_input(self.airship_throttle_input, event)

        bottom_button_layout = QHBoxLayout()
        self.help_button = QPushButton("Need Help?", self)
        self.help_button.clicked.connect(self.open_help_link)
        bottom_button_layout.addWidget(self.help_button)

        self.feedback_button = QPushButton("Feedback", self)
        self.feedback_button.clicked.connect(self.open_feedback_dialog)
        bottom_button_layout.addWidget(self.feedback_button)
        
        self.all_controls = [
            self.boat_autopilot_button, self.airship_autopilot_button,
            self.autosteer_button, self.mid_mission_checkbox, 
            self.webhooknotif_button, self.share_checkbox,
            self.quit_on_errors_checkbox,
            self.ship_speed_label, self.ship_speed_input,
            self.stop_distance_label, self.stop_distance_input,
            self.cycle_interval_label, self.cycle_interval_input,
            self.airship_altitude_label, self.airship_altitude_input,
            self.airship_throttle_label, self.airship_throttle_input,
            self.leeway_label, self.leeway_input,
            self.multiplier_label, self.multiplier_input,
            self.webhook_url_label, self.webhook_url_input
        ]

        if self.config:
            self.webhook_url_input.setText(self.config.get("webhook_url", "YOUR_WEBHOOK_URL"))
            self.ship_speed_input.setText(str(self.config.get("ship_top_speed", 20)))
            self.stop_distance_input.setText(str(self.config.get("stop_distance", 1)))
            self.cycle_interval_input.setText(str(self.config.get("cycle_interval", 0.5)))
            self.leeway_input.setText(str(self.config.get("leeway", 0.3)))
            self.multiplier_input.setText(str(self.config.get("multiplier", 1.9)))
            self.airship_altitude_input.setText(str(self.config.get("airship_cruising_altitude", 1500)))
            self.airship_throttle_input.setText(str(self.config.get("airship_throttle_level", 30)))
            self.share_checkbox.setChecked(core.SHARE_DATA)
            self.quit_on_errors_checkbox.setChecked(self.config.get("quit_on_errors", True))
            self.mid_mission_checkbox.setChecked(self.config.get("start_mid_mission", False))
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.start_button)
        layout.addWidget(separator)
        layout.addLayout(mode_layout)
        layout.addWidget(self.mid_mission_checkbox)
        layout.addWidget(self.autosteer_button)
        layout.addWidget(self.webhooknotif_button)
        layout.addWidget(self.share_checkbox)
        layout.addWidget(self.quit_on_errors_checkbox)

        settings_layout = QGridLayout()
        settings_layout.addWidget(self.ship_speed_label, 0, 0)
        settings_layout.addWidget(self.ship_speed_input, 0, 1)
        settings_layout.addWidget(self.stop_distance_label, 1, 0)
        settings_layout.addWidget(self.stop_distance_input, 1, 1)
        settings_layout.addWidget(self.cycle_interval_label, 2, 0)
        settings_layout.addWidget(self.cycle_interval_input, 2, 1)
        settings_layout.addWidget(self.airship_altitude_label, 3, 0)
        settings_layout.addWidget(self.airship_altitude_input, 3, 1)
        settings_layout.addWidget(self.airship_throttle_label, 4, 0)
        settings_layout.addWidget(self.airship_throttle_input, 4, 1)
        settings_layout.addWidget(self.leeway_label, 5, 0)
        settings_layout.addWidget(self.leeway_input, 5, 1)
        settings_layout.addWidget(self.multiplier_label, 6, 0)
        settings_layout.addWidget(self.multiplier_input, 6, 1)
        settings_layout.addWidget(self.webhook_url_label, 7, 0)
        settings_layout.addWidget(self.webhook_url_input, 7, 1)
        layout.addLayout(settings_layout)

        layout.addLayout(bottom_button_layout)
        
        news_separator = QFrame()
        news_separator.setFrameShape(QFrame.HLine)
        news_separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(news_separator)
        
        news_header = QLabel("<b>Live Issues & News</b>")
        news_header.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(news_header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(250)

        self.issues_container = QWidget()
        self.issues_layout = QVBoxLayout(self.issues_container)
        self.issues_layout.setContentsMargins(5, 5, 5, 5)
        self.issues_layout.setSpacing(10)

        scroll_area.setWidget(self.issues_container)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
        self.setGeometry(300, 300, 420, 700)

    def set_controls_enabled(self, enabled):
        for control in self.all_controls:
            control.setEnabled(enabled)
        
        if enabled:
            if not self.airship_autopilot_mode:
                self.airship_altitude_input.setEnabled(False)
                self.airship_throttle_input.setEnabled(False)
            
            if self.boat_autopilot_mode:
                self.stop_distance_input.setDisabled(True)
                self.cycle_interval_input.setDisabled(True)
                self.autosteer_button.setDisabled(True)

            if self.airship_autopilot_mode:
                 self.autosteer_button.setDisabled(True)

            self.mid_mission_checkbox.setEnabled(self.airship_autopilot_mode or self.boat_autopilot_mode)

            #if not self.webhook_logging_enabled:
                #self.webhook_url_input.setDisabled(True)
        else:
            self.mid_mission_checkbox.setEnabled(False)

    def check_night_vision(self):
        try:
            ocr_text, _ = _run_doctr_ocr_on_top_right_quadrant()
            military_time = extract_military_time(ocr_text)
            
            if military_time:
                self.last_time_check = military_time
                is_night = is_night_time(military_time)
                
                if is_night is not None:
                    should_press_n = False
                    
                    if is_night and self.current_night_mode != 'night':
                        self.current_night_mode = 'night'
                        should_press_n = True
                        logging.info(f"Night time detected ({military_time}), enabling night vision mode")
                        alert(f"Night time detected ({military_time}). Enabling night vision.", include_screenshot=False, verbose_mode=self.webhook_logging_enabled)
                    
                    elif not is_night and self.current_night_mode != 'day':
                        if self.current_night_mode is None:
                            logging.info(f"First detection is day time ({military_time}), setting day mode without pressing 'n'")
                            alert(f"First detection is day time ({military_time}). Setting day mode without toggling.", include_screenshot=False, verbose_mode=self.webhook_logging_enabled)
                            should_press_n = False
                        else:
                            should_press_n = True
                            logging.info(f"Day time detected ({military_time}), disabling night vision mode")
                            alert(f"Day time detected ({military_time}). Disabling night vision.", include_screenshot=False, verbose_mode=self.webhook_logging_enabled)
                        
                        self.current_night_mode = 'day'
                    
                    if should_press_n:
                        keyboard.press('n')
                        time.sleep(0.1)
                        keyboard.release('n')
                        logging.info("Pressed 'n' to toggle night vision")
            else:
                logging.debug("[!] No military time found in top right quadrant")
                
        except Exception as e:
            logging.error(f"[!] Error in night vision detection: {str(e)}")

    def run_altitude_control_safe(self, target_altitude, altitude_type, multiplier, ocr_text):
        try:
            run_altitude_control_logic(target_altitude, altitude_type, multiplier, ocr_text)
        finally:
            self.altitude_control_running = False

    def cleanup_decimal_input(self, line_edit, event):
        from PyQt5.QtWidgets import QLineEdit
        
        QLineEdit.focusOutEvent(line_edit, event)
        
        text = line_edit.text().strip()
        if text and '.' in text:
            try:
                value = float(text)

                if value == int(value):
                    line_edit.setText(str(int(value)))
                else:
                    integer_part = int(value)
                    line_edit.setText(str(integer_part))
                    
            except ValueError:
                pass

    def toggle_share_data(self, state):
        core.SHARE_DATA = (state == 2)

    def toggle_AutoSteer(self):
        if not self.auto_steer_enabled:
            self.auto_steer_enabled = True
            self.autosteer_button.setText('AutoSteer ✓')
        else:
            self.auto_steer_enabled = False
            self.autosteer_button.setText('AutoSteer')

    def toggle_BoatAutoPilot(self):
        if self.boat_autopilot_mode:
            self.boat_autopilot_mode = False
            self.boat_autopilot_button.setText('Boat AutoPilot')
            self.autopilot_ready = False
            self.autopilot_final_phase = False
            self.mid_mission_checkbox.setEnabled(self.airship_autopilot_mode)
            self.mid_mission_checkbox.setChecked(False)
            self.start_mid_mission = False
            
            self.auto_steer_enabled = False
            self.autosteer_button.setText('AutoSteer')
            
            if not self.is_running:
                self.stop_distance_input.setDisabled(False)
                self.cycle_interval_input.setDisabled(False)
                self.autosteer_button.setDisabled(False)
                self.stop_distance_input.setText("1")
                self.cycle_interval_input.setText("0.5")
        else:
            self.boat_autopilot_mode = True
            self.boat_autopilot_button.setText('Boat AutoPilot ✓')
            self.mid_mission_checkbox.setEnabled(True)
            
            if self.airship_autopilot_mode:
                self.airship_autopilot_mode = False
                self.airship_autopilot_button.setText('Airship AutoPilot')

            self.auto_steer_enabled = True
            self.autosteer_button.setText('AutoSteer ✓')
            self.autosteer_button.setDisabled(True)

            self.stop_distance_input.setText("0.20")
            self.cycle_interval_input.setText("0.25")
            self.stop_distance_input.setDisabled(True)
            self.cycle_interval_input.setDisabled(True)

    def toggle_AirshipAutoPilot(self):
        self.airship_autopilot_mode = not self.airship_autopilot_mode

        if self.airship_autopilot_mode:
            self.airship_autopilot_button.setText('Airship AutoPilot ✓')
            self.airship_altitude_input.setEnabled(True)
            self.airship_throttle_input.setEnabled(True)
            self.mid_mission_checkbox.setEnabled(True)

            if self.boat_autopilot_mode:
                self.boat_autopilot_mode = False
                self.boat_autopilot_button.setText('Boat AutoPilot')
            
            self.auto_steer_enabled = True
            self.autosteer_button.setText('AutoSteer ✓')
            self.autosteer_button.setDisabled(True)

            self.stop_distance_input.setText("0.20")
            self.cycle_interval_input.setText("0.25")
            self.stop_distance_input.setDisabled(True)
            self.cycle_interval_input.setDisabled(True)
        else:
            self.airship_autopilot_button.setText('Airship AutoPilot')
            self.airship_altitude_input.setEnabled(False)
            self.airship_throttle_input.setEnabled(False)
            self.mid_mission_checkbox.setEnabled(self.boat_autopilot_mode)
            
            self.airship_flight_phase = None
            self.airship_throttle_set = False
            
            if not self.boat_autopilot_mode:
                self.autosteer_button.setDisabled(False)
                self.autosteer_button.setText('AutoSteer')
                self.auto_steer_enabled = False

                self.stop_distance_input.setDisabled(False)
                self.cycle_interval_input.setDisabled(False)
                self.stop_distance_input.setText("1")
                self.cycle_interval_input.setText("0.5")

    def start_autopilot_thread(self, is_final_phase=False, autopilot_mode_type="boat"):
        if self.autopilot_thread and self.autopilot_thread.isRunning():
            self.autopilot_thread.terminate()
            self.autopilot_thread.wait()
            
        try:
            self.autopilot_final_phase = is_final_phase
            leeway = float(self.leeway_input.text())
            multiplier = float(self.multiplier_input.text())
            self.autopilot_thread = AutoPilotThread(is_final_phase=is_final_phase, leeway=leeway, multiplier=multiplier, autopilot_mode_type=autopilot_mode_type)
            self.autopilot_thread.finished.connect(self.on_autopilot_finished)
            self.autopilot_thread.start()
            logging.info(f"[$$] AutoPilot {'final' if is_final_phase else 'initial'} phase started for {autopilot_mode_type}")
        except Exception as e:
            logging.error(f"[!] AutoPilot Error: {str(e)}")
            alert(f"[!] Failed to start AutoPilot: {str(e)}", include_screenshot=False)
            QMessageBox.critical(self, "Error", f"AutoPilot failed to start: {str(e)}")

    def on_autopilot_finished(self, success=False):
        if self.autopilot_final_phase:
            if success:
                self.autopilot_final_phase = False
                self.previous_distance = None
                self.previous_time = None
                self.start_distance = None
                self.false_arrival_counter = 0
                alert("New job started successfully. AutoPilot cycle complete", include_screenshot=False, verbose_mode=self.webhook_logging_enabled)
            else:
                alert("[!] Failed to complete AutoPilot final phase. Manual intervention required", include_screenshot=True)
                QMessageBox.warning(self, "AutoPilot Warning", "Failed to complete final phase. Manual intervention required")
        else:
            if success:
                self.autopilot_ready = True
                alert("AutoPilot initial phase complete. Using AutoSteer for navigation", include_screenshot=False, verbose_mode=self.webhook_logging_enabled)
                self.timer.start(self.cycle_interval)
            else:
                if self.boat_autopilot_mode:
                    self.boat_autopilot_mode = False
                    self.boat_autopilot_button.setText('Boat AutoPilot')
                if self.airship_autopilot_mode:
                    self.airship_autopilot_mode = False
                    self.airship_autopilot_button.setText('Airship AutoPilot')

                self.autopilot_ready = False
                self.is_running = False
                self.start_button.setText('Start')
                
                self.set_controls_enabled(True)
                
                QMessageBox.critical(self, "AutoPilot Error", "Failed to initialize AutoPilot. Check the logs for details")

    def toggle_WebhookNotif(self):
        if not self.webhook_logging_enabled:
            self.webhook_logging_enabled = True
            self.webhooknotif_button.setText('Verbose Notifications ✓')
        else:
            self.webhook_logging_enabled = False
            self.webhooknotif_button.setText('Verbose Notifications')
    
    def toggle_logic(self):
        global LEEWAY, MULTIPLIER, WEBHOOK_URL
        if self.is_running:
            self.is_running = False
            self.start_button.setText('Resume')
            self.timer.stop()
            
            if self.boat_autopilot_mode and self.autopilot_thread and self.autopilot_thread.isRunning():
                self.start_button.setEnabled(False)
                self.start_button.setText('Stopping...')
                
                def terminate_thread():
                    try:
                        self.autopilot_thread.terminate()
                        if not self.autopilot_thread.wait(5000):
                            logging.warning("[!] Autopilot thread termination timed out, forcing quit")
                            self.autopilot_thread.quit()
                        
                        QtCore.QMetaObject.invokeMethod(self, "finalize_pause", 
                                                       QtCore.Qt.QueuedConnection)
                    except Exception as e:
                        logging.error(f"[!] Error terminating autopilot thread: {str(e)}")
                        QtCore.QMetaObject.invokeMethod(self, "finalize_pause", 
                                                       QtCore.Qt.QueuedConnection)
                
                threading.Thread(target=terminate_thread, daemon=True).start()
                return

            self.finalize_pause()
            return
        
        try:
            if not self.ship_speed_input.text().strip():
                error_msg = "Vehicle's Top Speed is required"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=False)
                QMessageBox.critical(self, "Error", error_msg)
                return
                
            if not self.stop_distance_input.text().strip():
                error_msg = "Stop Distance is required"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=False)
                QMessageBox.critical(self, "Error", error_msg)
                return
                
            if not self.cycle_interval_input.text().strip():
                error_msg = "Cycle Interval is required"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=False)
                QMessageBox.critical(self, "Error", error_msg)
                return
                
            if not self.leeway_input.text().strip():
                error_msg = "Leeway is required"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=False)
                QMessageBox.critical(self, "Error", error_msg)
                return
                
            if not self.multiplier_input.text().strip():
                error_msg = "Turning Multiplier is required"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=False)
                QMessageBox.critical(self, "Error", error_msg)
                return
                
            if self.airship_autopilot_mode and not self.airship_altitude_input.text().strip():
                error_msg = "Airship Cruising Altitude is required"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=False)
                QMessageBox.critical(self, "Error", error_msg)
                return

            if self.airship_autopilot_mode:
                throttle_text = self.airship_throttle_input.text().strip()
                if not throttle_text:
                    error_msg = "Airship Throttle is required"
                    logging.error(f"[!] {error_msg}")
                    alert(f"[!] {error_msg}", include_screenshot=False)
                    QMessageBox.critical(self, "Error", error_msg)
                    return
                try:
                    throttle_level = int(throttle_text)
                    if not 1 <= throttle_level <= 100:
                        raise ValueError("Throttle must be between 1 and 100")
                except ValueError:
                    error_msg = "Airship Throttle must be a whole number between 1 and 100"
                    logging.error(f"[!] {error_msg}")
                    alert(f"[!] {error_msg}", include_screenshot=False)
                    QMessageBox.critical(self, "Error", error_msg)
                    return

            webhook_url = self.webhook_url_input.text().strip()
            if webhook_url:
                if not webhook_url.startswith('https://'):
                    error_msg = "Webhook URL must start with 'https://'"
                    logging.error(f"[!] {error_msg}")
                    alert(f"[!] {error_msg}", include_screenshot=False)
                    QMessageBox.critical(self, "Error", error_msg)
                    return
            '''
            else:
                error_msg = "Webhook URL is required"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=False)
                QMessageBox.critical(self, "Error", error_msg)
                return
            '''

            if not focus_roblox_window():
                QMessageBox.critical(self, "Roblox Not Found", "Please start Roblox before running the helper.")
                self.is_running = False
                self.start_button.setText('Start')
                self.set_controls_enabled(True)
                return

            if self.boat_autopilot_mode or self.airship_autopilot_mode:
                logging.info("Checking if user is in the main game lobby...")
                ocr_text, _ = capture_and_process_screenshot()
                if "invite a friend" in ocr_text.lower():
                    error_msg = "Autopilot cannot start from the main menu. Please join a server first."
                    logging.error(f"[!] {error_msg}")
                    alert(f"[!] {error_msg}", include_screenshot=True)
                    QMessageBox.critical(self, "Server Not Detected", error_msg)
                    
                    self.is_running = False
                    self.start_button.setText('Start')
                    self.set_controls_enabled(True)
                    return

            self.showMinimized()
            time.sleep(0.5)
            screen_width, screen_height = pyautogui.size()
            x, y = screen_width // 2, screen_height // 2
            cross_mouse.left_click_xy_natural(x, y, delay=0.1)
            time.sleep(0.5)

            self.stop_distance = float(self.stop_distance_input.text())

            if self.previous_distance is None:
                try:
                    cycle_interval_minutes = float(self.cycle_interval_input.text())
                    if cycle_interval_minutes < 0.25:
                        cycle_interval_minutes = 0.25
                        logging.warning(f"[!] Cycle interval too low, adjusted to 0.25 minutes (15 seconds) for performance")
                    
                    self.cycle_interval = int(cycle_interval_minutes * 60 * 1000)
                    vehicle_top_speed = float(self.ship_speed_input.text())
                    LEEWAY = float(self.leeway_input.text())
                    MULTIPLIER = float(self.multiplier_input.text())
                    WEBHOOK_URL = webhook_url
                    airship_cruising_altitude = self.airship_altitude_input.text()

                    config_data = {
                        "webhook_url": WEBHOOK_URL,
                        "ship_top_speed": vehicle_top_speed,
                        "stop_distance": self.stop_distance,
                        "cycle_interval": float(self.cycle_interval) / (60 * 1000),
                        "leeway": LEEWAY,
                        "multiplier": MULTIPLIER,
                        "airship_cruising_altitude": airship_cruising_altitude,
                        "share_anonymous_data": core.SHARE_DATA,
                        "quit_on_errors": self.quit_on_errors_enabled
                    }
                    save_config(config_data)
                    
                    self.cycle_interval_input.setDisabled(True)
                    self.ship_speed_input.setDisabled(True)
                    self.stop_distance_input.setDisabled(True)
                    self.leeway_input.setDisabled(True)
                    self.multiplier_input.setDisabled(True)
                    self.webhook_url_input.setDisabled(True)
                except Exception as e:
                    error_msg = f"Invalid input values: {str(e)}"
                    logging.error(f"Error starting AeroHelper: {error_msg}")
                    alert(f"[!] {error_msg}", include_screenshot=False)
                    QMessageBox.critical(self, "Error", error_msg)
                    return

            self.set_controls_enabled(False)

            if self.boat_autopilot_mode:
                if self.start_mid_mission:
                    is_valid_mission = self.check_mid_mission_destination()
                    if not is_valid_mission:
                        return
                    
                    ensure_engine_and_throttle()
                    
                    self.autopilot_ready = True
                    self.is_running = True
                    self.start_button.setText('Pause')
                    self.timer.start(self.cycle_interval)
                    logging.info("[!] AeroHelper started in mid-mission AutoPilot mode.")
                    alert("AeroHelper started in mid-mission AutoPilot mode.", include_screenshot=False, verbose_mode=self.webhook_logging_enabled)
                    return
                elif not self.autopilot_ready and not self.autopilot_final_phase:
                    self.start_autopilot_thread(is_final_phase=False, autopilot_mode_type="boat")
                    self.is_running = True
                    self.start_button.setText('Pause')
                    logging.info("AeroHelper started in AutoPilot mode.")
                    alert("AeroHelper started in AutoPilot mode.", include_screenshot=False)
                    return
            
            if self.airship_autopilot_mode:
                if self.start_mid_mission:
                    is_valid_mission = self.check_mid_mission_destination()
                    if not is_valid_mission:
                        return
                    
                    logging.info("Airship mid-mission: Starting engine only.")
                    keyboard.press('e')
                    keyboard.release('e')
                    time.sleep(1)
                    alert("Mid-mission start", include_screenshot=False)

                    self.autopilot_ready = True
                    self.is_running = True
                    self.start_button.setText('Pause')
                    self.timer.start(self.cycle_interval)
                    logging.info("AeroHelper started in mid-mission Airship AutoPilot mode.")
                    alert("AeroHelper started in mid-mission Airship AutoPilot mode.", include_screenshot=False)
                    return
                elif not self.autopilot_ready and not self.autopilot_final_phase:
                    self.start_autopilot_thread(is_final_phase=False, autopilot_mode_type="airship")
                    self.is_running = True
                    self.start_button.setText('Pause')
                    logging.info("AeroHelper started in Airship AutoPilot mode.")
                    alert("AeroHelper started in Airship AutoPilot mode.", include_screenshot=False)
                    return
            
            self.is_running = True
            self.start_button.setText('Pause')
            self.timer.start(self.cycle_interval)
            logging.info("AeroHelper " + ("started" if self.previous_distance is None else "resumed") + ".")
            alert("AeroHelper " + ("started" if self.previous_distance is None else "resumed") + ".", include_screenshot=False)

        except ValueError as e:
            error_msg = "Invalid number format. Please check your inputs."
            logging.error(f"Error parsing inputs: {error_msg}")
            alert(f"[!] {error_msg}", include_screenshot=False)
            QMessageBox.critical(self, "Error", error_msg)

    @pyqtSlot()
    def finalize_pause(self):
        """Finalize the pause operation - called after thread termination completes"""
        try:
            self.autopilot_ready = False
            self.autopilot_final_phase = False
            
            self.start_button.setEnabled(True)
            self.start_button.setText('Resume')
            self.set_controls_enabled(True)
            
            logging.info("[*] AeroHelper paused")
            alert("AeroHelper paused", include_screenshot=False, verbose_mode=self.webhook_logging_enabled)
            
        except Exception as e:
            logging.error(f"[!] Error in finalize_pause: {str(e)}")
            self.start_button.setEnabled(True)
            self.start_button.setText('Resume')

    def run_AeroHelper_Logic(self):
        global JUST_RECONNECTED
        if JUST_RECONNECTED:
            logging.info("[/] Post-reconnect validation...")
            alert("[/] Reconnected to server. Re-validating mission state...", include_screenshot=False)
            JUST_RECONNECTED = False
            
            time.sleep(5) 
            
            is_valid_mission = self.check_mid_mission_destination()
            
            if is_valid_mission:
                logging.info("[/] Mission re-validated successfully after reconnect.")
                alert("[/] Mission re-validated. Resuming autopilot.", include_screenshot=False)
                ensure_engine_and_throttle()
            else:
                logging.error("[!] Failed to re-validate mission after reconnect. Stopping autopilot.")
                alert("[!] Could not re-validate mission after reconnect. Autopilot paused.", include_screenshot=True)
                if self.is_running:
                    self.toggle_logic() 
                return

        if not self.is_running:
            return
            
        if (self.boat_autopilot_mode or self.airship_autopilot_mode) and not self.autopilot_ready:
            return
            
        if self.autopilot_final_phase:
            return
            
        try:
            start_time = time.time()
            
            ocr_text, ocr_results = capture_and_process_screenshot()
            
            ocr_duration = time.time() - start_time
            if ocr_duration > 10:
                logging.warning(f"[!] OCR operation took {ocr_duration:.1f} seconds - performance degradation detected")

            if self.ocr_error_counter >= 3 and time.time() - self.time_of_last_ocr_refresh > 1000:
                logging.info("[!] OCR degradation detected. Attempting to refresh OCR engine...")
                alert("OCR degradation detected. Attempting to refresh OCR engine...", include_screenshot=False)
                threading.Thread(target=restart_all_engines, daemon=True).start()
                self.ocr_error_counter = 0
                self.time_of_last_ocr_refresh = time.time()
                logging.info("OCR engine refresh initiated in background.")
                return

            throttle_level = extract_throttle_level(ocr_text)
            if throttle_level == 0:
                if not self.throttle_alert_sent:
                    alert("Throttle is at 0%. Vehicle may be stopped.", include_screenshot=True)
                    logging.warning("Throttle is at 0%.")
                    self.throttle_alert_sent = True
            elif throttle_level is not None and throttle_level > 0:
                self.throttle_alert_sent = False

            self.night_vision_cycle_counter += 1
            if self.night_vision_cycle_counter >= 5:
                self.night_vision_cycle_counter = 0
                threading.Thread(target=self.check_night_vision, daemon=True).start()


            new_target_info = extract_target_bearing(ocr_text)
            if new_target_info and self.last_seen_target_info and new_target_info[1] == self.last_seen_target_info[1]:
                if not self.target_bearing_confirmed:
                    logging.info(f"Target bearing {new_target_info[1]} confirmed.")
                    alert(f"Target bearing {new_target_info[1]} confirmed.", include_screenshot=False)
                    self.target_bearing_confirmed = True
            else:
                if self.target_bearing_confirmed:
                    logging.info("Target bearing lost or changed. Re-confirming.")
                self.target_bearing_confirmed = False
            
            self.last_seen_target_info = new_target_info
            
            if self.is_running and (self.boat_autopilot_mode or self.airship_autopilot_mode):
                bearing_ocr_text, _ = _run_doctr_ocr_on_top_half()
                current_bearing = extract_current_bearing(bearing_ocr_text)

            vehicle_speed = float(self.ship_speed_input.text())
            
            (self.previous_distance, self.previous_time, self.start_distance, 
             self.false_arrival_counter, self.alert_counter, self.cycle_count, self.ocr_error_counter,
             target_info, current_bearing_val) = run_main_logic(
                ocr_text, ocr_results,
                self.previous_distance, self.previous_time, self.start_distance, self.false_arrival_counter,
                self.alert_counter, self.cycle_count, self.start_time, self.auto_steer_enabled,
                self.webhook_logging_enabled, self.stop_distance, vehicle_speed, self.ocr_error_counter,
                autopilot_mode=(self.boat_autopilot_mode or self.airship_autopilot_mode), 
                autopilot_callback=self.start_final_phase if self.boat_autopilot_mode else None,
                throttle_level=throttle_level,
                airship_mode=self.airship_autopilot_mode,
                airship_flight_phase=getattr(self, 'airship_flight_phase', None)
            )

            if self.auto_steer_enabled and self.target_bearing_confirmed:
                threading.Thread(target=run_autosteer, args=(ocr_text, target_info, current_bearing_val)).start()
                if self.webhook_logging_enabled:
                    try:
                        res = extract_target_bearing(ocr_text)
                        if res is not None:
                            dest2, target2 = res
                            bearing_ocr_text2, _ = _run_doctr_ocr_on_top_half()
                            current_bearing2 = extract_current_bearing(bearing_ocr_text2)
                            alert(f"AeroHelper AutoSteer - Destination is {dest2.upper()} with bearing {target2}", include_screenshot=False)
                            alert(f"AeroHelper AutoSteer - Target Bearing: {target2}, Current Bearing: {current_bearing2}", include_screenshot=False)
                        else:
                            alert("AutoSteer - Unable to extract target bearing", include_screenshot=False)
                    except Exception as e:
                        logging.error("AutoSteer Webhook error: " + str(e))

            if self.airship_autopilot_mode:
                try:
                    altitude_text = self.airship_altitude_input.text().strip()
                    multiplier_text = self.multiplier_input.text().strip() 
                    
                    if not altitude_text:
                        raise ValueError("Airship altitude field is empty")
                    if not multiplier_text:
                        raise ValueError("Multiplier field is empty")
                    
                    target_cruising_altitude = int(altitude_text)
                    multiplier = float(multiplier_text)

                    if self.airship_flight_phase is None:
                        self.airship_flight_phase = 'climb'
                        self.airship_throttle_set = False

                    if self.airship_flight_phase == 'climb':
                        logging.info("Airship Phase: Climb. Targeting 500ft clearance.")
                        alert("Airship Phase: Climb. Targeting 500ft clearance.", include_screenshot=False)

                        current_land_clearance = extract_land_clearance_altitude(ocr_text)
                        logging.info(f"Current land clearance: {current_land_clearance} ft")

                        if current_land_clearance is not None and current_land_clearance >= 500:
                            self.airship_flight_phase = 'cruise_climb'
                            logging.info("Achieved 500ft clearance. Switching to cruise climb.")
                            alert("Achieved 500ft clearance. Switching to cruise climb.", include_screenshot=False)
                        else:
                            if not self.altitude_control_running:
                                self.altitude_control_running = True
                                threading.Thread(target=self.run_altitude_control_safe, args=(500, "land_clearance", multiplier, ocr_text)).start()

                    elif self.airship_flight_phase == 'cruise_climb':
                        logging.info(f"Airship Phase: Cruise Climb. Targeting {target_cruising_altitude}ft sea level.")
                        alert(f"Airship Phase: Cruise Climb. Targeting {target_cruising_altitude}ft sea level.", include_screenshot=False)

                        if not self.airship_throttle_set:
                            throttle_level = int(self.airship_throttle_input.text())
                            threading.Thread(target=set_airship_throttle, args=(throttle_level,), daemon=True).start()
                            self.airship_throttle_set = True
                            logging.info(f"Airship throttle set to {throttle_level}% for cruise climb phase")
                        
                        current_sea_level_alt = extract_sea_level_altitude(ocr_text)
                        logging.info(f"Current sea level altitude: {current_sea_level_alt} ft")
                        
                        if current_sea_level_alt is not None and abs(current_sea_level_alt - target_cruising_altitude) <= 100:
                            self.airship_flight_phase = 'cruise'
                            logging.info("Reached cruising altitude. Switching to cruise.")
                            alert("Reached cruising altitude. Switching to cruise.", include_screenshot=False)
                        else:
                            if not self.altitude_control_running:
                                self.altitude_control_running = True
                                threading.Thread(target=self.run_altitude_control_safe, args=(target_cruising_altitude, "sea_level", multiplier, ocr_text)).start()
                    
                    elif self.airship_flight_phase == 'cruise':
                        if self.previous_distance is not None and self.previous_distance < 1:
                            self.airship_flight_phase = 'final_approach'
                            logging.info("[Distance < 1 nm. Switching to final approach phase.")
                            alert("Distance < 1 nm. Switching to final approach phase.", include_screenshot=False)
                        else:
                            logging.info(f"Airship Phase: Cruise. Maintaining {target_cruising_altitude}ft sea level.")
                            if not self.altitude_control_running:
                                self.altitude_control_running = True
                                threading.Thread(target=self.run_altitude_control_safe, args=(target_cruising_altitude, "sea_level", multiplier, ocr_text)).start()

                    elif self.airship_flight_phase == 'final_approach':
                        logging.info("Airship Phase: Final Approach. Stopping forward movement.")
                        alert("Airship Phase: Final Approach. Stopping forward movement.", include_screenshot=False)
                        keyboard.press("z")
                        time.sleep(3)
                        keyboard.release("z")
                        self.airship_flight_phase = 'descent'
                        logging.info("Forward movement stopped. Switching to descent phase.")
                        alert("Forward movement stopped. Switching to descent phase.", include_screenshot=False)

                    elif self.airship_flight_phase == 'descent':
                        logging.info("Airship Phase: Descent. Targeting 100ft clearance.")
                        alert("Airship Phase: Descent. Targeting 100ft clearance.", include_screenshot=False)
                        if not self.altitude_control_running:
                            self.altitude_control_running = True
                            threading.Thread(target=self.run_altitude_control_safe, args=(100, "land_clearance", multiplier, ocr_text)).start()

                except ValueError as e:
                    error_msg = f"[!] Invalid Airship input: {str(e)}"
                    logging.error(error_msg)
                    alert(error_msg, include_screenshot=False)
            
            self.last_fuel_alert_level = run_fuel_check(self.last_fuel_alert_level, ocr_text)

        except ValueError as e:
            logging.error("Error in run_AeroHelper_Logic: " + str(e))
            QMessageBox.critical(self, "Error", "Invalid number format in vehicle speed.")
            self.toggle_logic()
        except Exception as e:
            error_msg = f"Unexpected error in main logic: {str(e)}"
            logging.error(f"[!] {error_msg}")
            
            if not hasattr(self, 'last_error_time') or time.time() - self.last_error_time > 60:
                alert(f"[!] {error_msg}", include_screenshot=False)
                self.last_error_time = time.time()
            
            return

    def toggle_quit_on_errors(self, state):
        self.quit_on_errors_enabled = (state == 2)
        core.QUIT_ON_ERRORS = self.quit_on_errors_enabled

    def toggle_mid_mission(self, state):
        self.start_mid_mission = (state == 2)

    def check_mid_mission_destination(self):
        try:
            ocr_text, ocr_results = capture_and_process_screenshot()
            
            transport_pattern = r"transport (?:your vehicle )?to\s*(.+?)\s*safely"
            mission_match = re.search(transport_pattern, ocr_text.lower())
            distance_present = extract_distance(ocr_text) is not None
            
            if mission_match and distance_present:
                destination = mission_match.group(1).strip()
                logging.info(f"Mid-mission destination detected: {destination}")

                if self.airship_autopilot_mode:
                    routes = AIRSHIP_ROUTES
                    logging.info("Checking against Airship routes.")
                else:
                    routes = AIRPORT_ROUTES
                    logging.info("Checking against Boat routes.")

                supported_airports = set()
                for airports in routes.values():
                    for airport in airports:
                        supported_airports.add(airport)
                
                supported_airports.update(routes.keys())
                
                destination_no_spaces = destination.replace(" ", "").lower()
                for airport in supported_airports:
                    airport_no_spaces = airport.replace(" ", "").lower()
                    if destination_no_spaces in airport_no_spaces or airport_no_spaces in destination_no_spaces:
                        logging.info(f"Destination '{destination}' matches supported airport '{airport}'")
                        alert(f"Starting mid-mission to '{airport}'", include_screenshot=False)
                        return True
                
                error_msg = f"Destination '{destination}' is not in the list of supported airports"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=True)
                QMessageBox.critical(self, "Error", error_msg)
                return False
            else:
                error_msg = "No transport mission detected. Please ensure you're in a mission"
                logging.error(f"[!] {error_msg}")
                alert(f"[!] {error_msg}", include_screenshot=True)
                QMessageBox.critical(self, "Error", error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error checking mid-mission destination: {str(e)}"
            logging.error(f"[!] {error_msg}")
            alert(f"[!] {error_msg}", include_screenshot=True)
            QMessageBox.critical(self, "Error", error_msg)
            return False

    def start_final_phase(self):
        self.start_autopilot_thread(is_final_phase=True)

    def open_help_link(self):
        webbrowser.open("https://aeronautica-helper.vercel.app/help")

    def open_feedback_dialog(self):
        dialog = FeedbackDialog(self)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            QMessageBox.information(self, "Feedback Sent", "Thank you! Your feedback has been submitted.")
        elif dialog.error_message:
            QMessageBox.critical(self, "Submission Error", f"Failed to send feedback:\n\n{dialog.error_message}")

    def fetch_issues(self):
        try:
            response = requests.get("https://aeronautica-helper.vercel.app/api/issues", timeout=10)
            response.raise_for_status()
            
            issues_data = response.json()

            if not isinstance(issues_data, list):
                raise ValueError(f"API returned unexpected data type: {type(issues_data).__name__}")

            if not issues_data:
                issues_data = [{"title": "No current issues or news", "description": "Check back later for updates.", "priority": "low", "status": 100}]

            self.issues_fetched.emit(issues_data)
        except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError) as e:
            logging.error(f"[!] Could not fetch issues: {e}")

    @pyqtSlot(list)
    def populate_issues_ui(self, issues):
        while self.issues_layout.count():
            child = self.issues_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for issue in issues:
            card = IssueCard(issue)
            self.issues_layout.addWidget(card)
        
        self.issues_layout.addStretch(1)

def extract_throttle_level(ocr_text):
    match = re.search(r"Throttle:\s*(\d+)\s*%", ocr_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def run_main_logic(ocr_text, ocr_results, prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter,
                   cycle_count, start_time, auto_steer_enabled, webhook_logging_enabled,
                   stop_distance, vehicle_top_speed, ocr_error_counter, autopilot_mode=False, autopilot_callback=None,
                   throttle_level=None, airship_mode=False, airship_flight_phase=None):
    cycle_count += 1

    screen_width, screen_height = pyautogui.size()
    x, y = screen_width // 2, screen_height // 2
    
    cross_mouse.left_click_xy_natural(x, y, delay=0.3, min_variation=-3, max_variation=3,
                                use_every=4, sleeptime=(0.005, 0.009), print_coords=False, percent=90)

    keyboard.type('5')
    formatted_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    current_time = time.time()

    logging.info("OCR text: " + ocr_text)

    if "disconnected" in ocr_text.lower():
        alert("[!] 'Disconnected' detected on screen. Initiating reconnect sequence.", include_screenshot=True)
        logging.error("[!] 'Disconnected' detected. Initiating reconnect.")
        reconnect_sequence()
        return prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter, cycle_count, ocr_error_counter, None, None

    hide_results = [res for res in ocr_results if res[1] in ("Hide", "> Hide")]
    for res in hide_results:
        click_center(res[0])
        alert("Chat/Player UI was expanded. Successfully closed all", include_screenshot=False)

    current_distance = extract_distance(ocr_text)
    target_info = extract_target_bearing(ocr_text)
    bearing_ocr_text_main, _ = _run_doctr_ocr_on_top_half()
    current_bearing_val = extract_current_bearing(bearing_ocr_text_main)

    if current_distance is None or (auto_steer_enabled and (target_info is None or current_bearing_val is None)):
        logging.warning("[!] OCR Error: Failed to extract critical data (distance, bearing, etc.).")
        ocr_error_counter += 1
    else:
        ocr_error_counter = 0

    if current_distance is None:
        if autopilot_mode:
            if target_info is None and current_bearing_val is None and "join game" not in ocr_text.lower():
                alert("[!] ROBLOX crashed (UI elements missing). Initiating reconnect sequence.", include_screenshot=True)
                logging.error("[!] ROBLOX crashed (UI elements missing).")
                reconnect_sequence()

        alert_counter += 1
        prev_time = current_time
        return prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter, cycle_count, ocr_error_counter, target_info, current_bearing_val

    logging.info(f"Extracted Distance: {current_distance} nm")
    if prev_distance is not None and prev_time is not None:
        elapsed = current_time - prev_time
        expected_distance = vehicle_top_speed * (elapsed / 3600)
        threshold = expected_distance - LEEWAY
        movement = prev_distance - current_distance

        if abs(movement) > 20:
            logging.warning(f"OCR Error: Movement value too high: {movement:.2f} nm")
            movement = 0.01
            return prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter, cycle_count, ocr_error_counter, target_info, current_bearing_val

        logging.info(f"Elapsed: {elapsed:.2f} sec, Expected: {expected_distance:.2f} nm, Threshold: {threshold:.2f} nm")
        logging.info(f"Movement this cycle: {movement:.2f} nm")
        if webhook_logging_enabled:
            if cycle_count % 5 == 0 and movement != 0:
                eta_hours = (current_distance / movement) / 60
                completion = (((start_distance - current_distance) / start_distance) * 100) if start_distance and start_distance > 0 else 0
                alert(f"{completion:.2f}% Completed", include_screenshot=True, verbose_mode=webhook_logging_enabled)
            
            throttle_str = f", Throttle: {throttle_level}%" if throttle_level is not None else ""
            alert(f"Elapsed: {elapsed:.2f}s | Move: {movement:.2f}nm | Dist: {current_distance}nm{throttle_str}", include_screenshot=False, verbose_mode=webhook_logging_enabled)

        if movement == 0:
            if airship_mode and airship_flight_phase in ['climb', 'cruise_climb']:
                logging.info("Airship climbing phase detected, skipping collision and stall detection as movement is expected to be zero during climb")
                alert("Airship climbing - movement expected to be zero", include_screenshot=False, verbose_mode=webhook_logging_enabled)
            else:
                alert(f"[!] Possible island collision or stalled vehicle.", include_screenshot=True)
                logging.error(f"[!] Possible island collision or stalled vehicle detected - no movement registered this cycle")
                alert_counter += 1
                
                if alert_counter >= 3:
                    logging.warning("[!] Vehicle stalled for 3 cycles. Attempting to re-apply throttle.")
                    alert("[!] Vehicle stalled. Re-engaging throttle.", include_screenshot=False)
                    ensure_engine_and_throttle()
                    alert_counter = 0

                if autopilot_mode and false_arrival_counter >= 2:
                    if autopilot_callback:
                        alert("Vehicle has stopped. Initiating AutoPilot final phase", include_screenshot=False)
                        logging.error("Vehicle has stopped. Initiating AutoPilot final phase")
                        autopilot_callback()
    else:
        alert("System Start", include_screenshot=False)
        alert(f"AeroHelper System Start time: {formatted_time}", include_screenshot=False)
        start_distance = current_distance
        movement = 0

    prev_distance = current_distance
    prev_time = current_time

    if current_distance < stop_distance:
        if not autopilot_mode:
            keyboard.press("z")
            time.sleep(0.1)
            keyboard.release("z")
            alert("[!] Boat needs manual docking. Vehicle is currently stopping", include_screenshot=True)
            logging.info("[!] Boat needs manual docking. Vehicle is currently stopping")
            false_arrival_counter += 1
            alert_counter += 1
            
            if false_arrival_counter >= 3:
                alert("[Vehicle has stopped, closing System", include_screenshot=True)
                alert(f"Total elapsed time: {current_time - start_time:.2f} seconds", include_screenshot=False)
                logging.info("Total elapsed time: {current_time - start_time:.2f} seconds. Closing System")
                sys.exit()
        
        elif autopilot_mode and autopilot_callback:
            keyboard.press("z")
            time.sleep(0.3)
            keyboard.release("z")
            
            alert("[*] Destination reached. Starting AutoPilot Phase 2", include_screenshot=False)
            logging.info("[*] Destination reached. Starting AutoPilot Phase 2")
            if autopilot_callback:
                autopilot_callback()
                return prev_distance, prev_time, start_distance, 0, alert_counter, cycle_count, ocr_error_counter, target_info, current_bearing_val
    else:
        if false_arrival_counter >= 1:
            alert("False Arrival detected, Vehicle is resuming trip", include_screenshot=False)
            logging.error("False Arrival detected, Vehicle is resuming trip")
            false_arrival_counter = 0
            keyboard.press('w')
            time.sleep(5)
            keyboard.release('w')

    if movement is not None and movement > 0 and alert_counter > 0:
        alert_counter = 0

    return prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter, cycle_count, ocr_error_counter, target_info, current_bearing_val

def run_autosteer(ocr_text, target_info, current_bearing):
    global STEERING_HISTORY, OSCILLATION_ALERT_SENT
    result = target_info
    if result is not None and current_bearing is not None:
        dest, target = result
        logging.info(f"AutoSteer - Target Bearing: {target}, Current Bearing: {current_bearing}")
        diff = abs(current_bearing - target)
        if target < current_bearing:
            key_to_press = 'a'
        elif target > current_bearing:
            key_to_press = 'd'
        else:
            clear_steering_history()
            logging.info("AutoSteer - No difference in bearing, no steering required")
            return

        if diff > 35:
            hold_duration = 7 * MULTIPLIER
        elif 15 <= diff <= 34:
            hold_duration = 5 * MULTIPLIER
        elif 11 <= diff <= 15:
            hold_duration = 3 * MULTIPLIER
        elif 6 <= diff <= 10:
            hold_duration = 2 * MULTIPLIER
        elif 3 <= diff <= 5:
            hold_duration = 1 * MULTIPLIER
        elif 1 <= diff < 3:
            hold_duration = 0.75 * MULTIPLIER
        else:
            clear_steering_history()
            logging.info("AutoSteer - Difference too small, no steering adjustment needed")
            return

        STEERING_HISTORY.append(key_to_press)
        if len(STEERING_HISTORY) > 8:
            STEERING_HISTORY = STEERING_HISTORY[-8:]

        if len(STEERING_HISTORY) == 8 and not OSCILLATION_ALERT_SENT:
            first_turn = STEERING_HISTORY[0]
            second_turn = STEERING_HISTORY[1]
            if first_turn != second_turn:
                expected_pattern = [first_turn, second_turn] * 4
                if STEERING_HISTORY == expected_pattern:
                    alert("[!] Auscultation Detected: The vehicle is turning back and forth rapidly. Please lower the 'Turning Multiplier' to improve stability. If you are using an airship, the wind may be affecting stability.", include_screenshot=False)
                    OSCILLATION_ALERT_SENT = True

        logging.info(f"AeroHelper AutoSteer - Pressing {key_to_press} for {hold_duration} sec (difference: {diff})")
        keyboard.press(key_to_press)
        time.sleep(hold_duration)
        keyboard.release(key_to_press)

        logging.info("AeroHelper AutoSteer - Pressing '=' for 3 seconds after steering to level out vehicle")
        keyboard.press('=')
        time.sleep(3)
        keyboard.release('=')
    else:
        if result is None and current_bearing is None:
            alert("[AutoSteer - Target and current bearing not found in OCR text", include_screenshot=False)
        elif result is None:
            alert("[AutoSteer - Target not found in OCR text", include_screenshot=False)
        elif current_bearing is None:
            alert("[AutoSteer - Current bearing not found in OCR text", include_screenshot=False)
        else:
            alert("[!] AutoSteer - Outstanding OCR error", include_screenshot=False)
        logging.warning("AutoSteer - Target or current bearing not found in OCR text")

def set_airship_throttle(throttle_level):
    logging.info(f"Setting airship throttle to level: {throttle_level}")
    alert(f"Setting airship throttle to level: {throttle_level}", include_screenshot=False)

    time.sleep(0.2)
    
    keyboard.press(Key.shift)
    time.sleep(0.1)
    
    for i in range(throttle_level):
        keyboard.press('w')
        time.sleep(0.05)
        keyboard.release('w')
        time.sleep(0.05)
    
    time.sleep(0.1)
    keyboard.release(Key.shift)

    logging.info("Airship throttle sequence complete.")

def ensure_engine_and_throttle():
    logging.info("Ensuring engine is on and throttle is max for mid-mission start...")
    keyboard.press('e')
    keyboard.release('e')
    time.sleep(10)
    keyboard.press('w')
    time.sleep(5)
    keyboard.release('w')
    alert("Mid-mission start: Engine and Throttle sequence initiated.", include_screenshot=False)
    logging.info("Mid-mission start: Engine and Throttle sequence complete.")

def clear_steering_history():
    global STEERING_HISTORY, OSCILLATION_ALERT_SENT
    if STEERING_HISTORY:
        logging.info("Steering is stable, resetting oscillation check.")
        STEERING_HISTORY.clear()
        OSCILLATION_ALERT_SENT = False

def reconnect_sequence():
    alert("[/] Roblox disconnected/crashed. Starting full reconnect.", include_screenshot=False)

    logging.info("Closing Roblox process...")
    close_roblox_client()
    time.sleep(5)

    logging.info("Launching Roblox...")
    if not launch_roblox_client():
        alert("[!] Failed to launch Roblox. Aborting reconnect.", include_screenshot=True)
        return False

    logging.info("Waiting 45 seconds for game to load...")
    time.sleep(45)

    def find_and_click_button(text_to_find, max_attempts=5, is_optional=False):
        for attempt in range(max_attempts):
            logging.info(f"Attempt {attempt + 1}/{max_attempts} to find and click '{text_to_find}'")
            ocr_text, ocr_results = capture_and_process_screenshot()
            for res in ocr_results:
                if len(res) > 1 and isinstance(res[1], str) and text_to_find.lower() in res[1].lower():
                    click_center(res[0])
                    alert(f"Found and clicked '{text_to_find}'.", include_screenshot=False)
                    return True
            time.sleep(5)
        
        if not is_optional:
            alert(f"[!] Failed to find and click '{text_to_find}' after {max_attempts} attempts.", include_screenshot=True)
        else:
            logging.warning(f"Optional button '{text_to_find}' not found, continuing.")
        return False

    if not find_and_click_button("Join Game"):
        return False
    
    time.sleep(15)

    find_and_click_button("Close", max_attempts=2, is_optional=True)
    time.sleep(2)

    find_and_click_button("Continue Flight", max_attempts=2, is_optional=False)

    time.sleep(10)
    keyboard.press('e')
    keyboard.release('e')
    alert("Engine Started", include_screenshot=False)
    logging.info("Engine Started")

    time.sleep(15)
    keyboard.press('w')
    time.sleep(5)
    keyboard.release('w')
    alert("Throttle has been turned to max", include_screenshot=True)
    logging.info("Throttle has been turned to max")

    alert("Reconnect sequence complete.", include_screenshot=True)
    logging.info("Reconnect sequence complete.")

    global JUST_RECONNECTED
    JUST_RECONNECTED = True
    
    return True

def run_altitude_control_logic(target_altitude, altitude_type, multiplier, ocr_text):
    current_altitude = None
    if altitude_type == "land_clearance":
        current_altitude = extract_land_clearance_altitude(ocr_text)
    elif altitude_type == "sea_level":
        current_altitude = extract_sea_level_altitude(ocr_text)

    if current_altitude is not None:
        logging.info(f"[$] Altitude Control - Type: {altitude_type}, Target: {target_altitude}, Current: {current_altitude}")
        diff = abs(current_altitude - target_altitude)
        
        tolerance = 0 if altitude_type == "land_clearance" and target_altitude == 500 else 25
        logging.info(f"Altitude control analysis - Current: {current_altitude}ft, Target: {target_altitude}ft, Difference: {diff}ft, Tolerance: {tolerance}ft, Within range: {diff <= tolerance}")
        
        if diff <= tolerance:
            logging.info(f"Altitude within target range ({tolerance}ft tolerance), no adjustment needed.")
            return

        if target_altitude < current_altitude:
            key_to_press = 'f'
            action = "descending"
        else:
            key_to_press = 'r'
            action = "ascending"

        if diff > 500:
            hold_duration = min(7 * multiplier, 10)
        elif 250 <= diff <= 500:
            hold_duration = min(5 * multiplier, 7)
        elif 100 <= diff < 250:
            hold_duration = min(3 * multiplier, 5)
        elif 50 <= diff < 100:
            hold_duration = min(2.5 * multiplier, 3)
        elif 25 <= diff < 50:
            hold_duration = min(2 * multiplier, 2)
        elif 10 <= diff < 25:
            hold_duration = min(1.5 * multiplier, 1.5)
        else:
            hold_duration = min(1 * multiplier, 0.8)

        logging.info(f"AeroHelper Altitude Control - {action} - Pressing {key_to_press} for {hold_duration:.1f} sec (difference: {diff})")
        alert(f"Altitude Control: {action} {diff}ft to reach {target_altitude}ft", include_screenshot=False)

        keyboard.press(key_to_press)
        time.sleep(hold_duration)
        keyboard.release(key_to_press)
        logging.info(f"AeroHelper Altitude Control - held {key_to_press} for {hold_duration:.1f} sec COMPLETE.")
    else:
        logging.warning(f"[!] Altitude Control - Could not determine current altitude for type '{altitude_type}' from OCR.")
        alert(f"[!] Altitude Control - OCR failed for {altitude_type} altitude", include_screenshot=False)

def run_fuel_check(last_alert_level, ocr_text):
    fuel_level = extract_fuel_level(ocr_text)
    if fuel_level is not None:
        logging.info(f"Fuel Check - Current Level: {fuel_level}%")
        if fuel_level < 10:
            current_fuel_tens = int(fuel_level)
            if current_fuel_tens < last_alert_level or last_alert_level == -1:
                alert(f"Low Fuel Warning: {fuel_level:.1f}% remaining!", include_screenshot=True)
                return current_fuel_tens
    return last_alert_level

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    check_version()
    logging.info("Clearing caches and initializing engines...")
    restart_all_engines()
    logging.info("Engines initialized.")
    window = AeroHelperApp()
    window.show()
    sys.exit(app.exec_()) 