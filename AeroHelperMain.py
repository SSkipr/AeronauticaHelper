'''                      _    _      _                 
     /\                 | |  | |    | |                
    /  \   ___ _ __ ___ | |__| | ___| |_ __   ___ _ __ 
   / /\ \ / _ \ '__/ _ \|  __  |/ _ \ | '_ \ / _ \ '__|
  / ____ \  __/ | | (_) | |  | |  __/ | |_) |  __/ |   
 /_/    \_\_______ _____|_|  |_|\___|_| .__/ \___|_|   
https://aeronautica-helper.vercel.app
https://github.com/SSkipr/AeronauticaHelper
Version 2.4

Alert Ranking:
[!] Urgent
[$] Logging Info / 'Non-Urgent Notifications' in the UI, can be disabled
'''

# --------------------------------------------------
# 0. Library setup
# --------------------------------------------------
import importlib
import os
import webbrowser
import subprocess
import sys
import time
import re
import logging
import io
import json
import threading
import requests
import datetime
import platform

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel, QCheckBox, QMessageBox
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer

import pyautogui
import numpy
import easyocr
import pynput


required_downloads = ['PyQt5', 'pyautogui', 'numpy', 'easyocr', 'pynput']
missing_imports = []
for library_name in required_downloads:
    try:
        importlib.import_module(library_name)
    except ImportError:
        missing_imports.append(library_name)
if len(missing_imports) != 0:
    for library in missing_imports:
        subprocess.check_call([sys.executable, "-m", "pip", "install", library])

# --------------------------------------------------
# 1. Configuration and Logging Setup
# --------------------------------------------------
VERSION = "2.4"
DATA_FILE = "data.txt"
LOG_FILE = "log_data.txt"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s')

from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
keyboard = KeyboardController()
mouse = MouseController()


consecutive_alerts = 0
SHARE_DATA = False

# --------------------------------------------------
# Autosave Configuration Functions
# --------------------------------------------------
def save_config(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        logging.info("[$] Configuration data saved.")
    except Exception as e:
        logging.error("[$] Failed to save config: " + str(e))

def load_config():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error("[$] Failed to load config: " + str(e))
    return {}

# --------------------------------------------------
# Version Check on Startup
# --------------------------------------------------
def check_version():
    try:
        headers = {'User-Agent': 'AeroHelper Application'}
        response = requests.get("https://aeronautica-helper.vercel.app/api/version", headers=headers)
        response.raise_for_status()
        latest_version = response.text.strip()
        logging.info(f"[$] AeroHelper Version Check: Installed={VERSION}, Latest={latest_version}")
        if latest_version != VERSION:
            QMessageBox.warning(None, "AeroHelper Update Required",
                f"A new version ({latest_version}) of AeroHelper is available. You are running {VERSION}.\n"
                "You will be directed to the update page. The application will now attempt to delete its data files and main file.")
            webbrowser.open("https://github.com/SSkipr/AeronauticaHelper/releases/latest")
            logging.shutdown()
            try:
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
            except Exception:
                pass
            try:
                if os.path.exists(LOG_FILE):
                    os.remove(LOG_FILE)
            except Exception:
                pass
            try:
                main_file = os.path.abspath(__file__)
                if platform.system() == "Windows":
                    subprocess.call(["del", main_file], shell=True)
                else:
                    subprocess.call(["rm", "-f", main_file])
            except Exception:
                pass
            sys.exit()
    except Exception as e:
        logging.error("[$] Version check failed: " + str(e))

# --------------------------------------------------
# 2. Initialize EasyOCR Reader
# --------------------------------------------------
reader = easyocr.Reader(['en'], gpu=True)

# --------------------------------------------------
# Combined Alert Function
# --------------------------------------------------
def alert(message, include_screenshot=False):
    global consecutive_alerts, SHARE_DATA
    if message.startswith("[!]"):
        message = "@everyone " + message
        if SHARE_DATA:
            try:
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, "r") as f:
                        log_content = f.read()[-50000:]
                    data_payload = {"Data": log_content}
                    r = requests.post("https://aeronautica-helper.vercel.app/api/data",
                                      headers={'Content-Type': 'application/json'},
                                      json=data_payload)
                    r.raise_for_status()
                    logging.info("[!] Anonymous log data sent.")
                else:
                    logging.warning("[!] Log file not found for anonymous data sharing.")
            except Exception as e:
                logging.error("[!] Failed to send anonymous data: " + str(e))
    payload = {"content": message}
    try:
        if include_screenshot:
            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            buffer.seek(0)
            files = {"file": ("screenshot.png", buffer, "image/png")}
            response = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload)}, files=files)
        else:
            response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        logging.info("[!] Alert sent: " + message)
    except Exception as e:
        logging.error("[!] Failed to send alert: " + str(e))
    consecutive_alerts += 1
    return True

# --------------------------------------------------
# 4. Screenshot Capture and OCR Processing
# --------------------------------------------------
def capture_and_process_screenshot():
    screenshot = pyautogui.screenshot()
    image = numpy.array(screenshot)
    results = reader.readtext(image)
    text = " ".join([res[1] for res in results])
    return text

# --------------------------------------------------
# 5. Extracting the Distance Value
# --------------------------------------------------
def extract_distance(ocr_text):
    ocr_text = ocr_text.lower()
    pattern = r"distance\s*[\:\;\,\'\-]+\s*(\d+)(?:[.,]+(\d+))?\s*nm"
    match = re.search(pattern, ocr_text, re.IGNORECASE)
    if match:
        try:
            integer_part = match.group(1)
            fractional_part = match.group(2) if match.group(2) is not None else ""
            value_str = integer_part + ("." + fractional_part if fractional_part else "")
            return abs(float(value_str))
        except ValueError:
            return None
    return None

# --------------------------------------------------
# 6. Extract Bearing Values for AutoSteer
# --------------------------------------------------
def extract_target_bearing(ocr_text):
    ocr_text_lower = ocr_text.lower()
    match = re.search(r"dest(?:ination)?\D+(\d{3})", ocr_text_lower)
    if match:
        try:
            target = int(match.group(1))
            return "dest", target
        except ValueError:
            pass

    pattern = r"(?!clear|trk|hdg)(?!\b\d{1,2}nm\b)(?!\d{3,6}(?=\s?mb\b))(\b[a-z]{4,5}\b)\s+(\d{3})"
    match = re.search(pattern, ocr_text_lower)
    if match:
        try:
            dest = match.group(1)
            target = int(match.group(2))
            return dest, target
        except ValueError:
            return None
    return None

def extract_current_bearing(ocr_text):
    ocr_text = ocr_text.lower()
    match = re.search(r"trk\s*(\d{3})\s+\d{3}\s+hdg", ocr_text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

# --------------------------------------------------
# 7. AutoSteer Function
# --------------------------------------------------
def run_autosteer(ocr_text):
    result = extract_target_bearing(ocr_text)
    current_bearing = extract_current_bearing(ocr_text)
    if result is not None and current_bearing is not None:
        dest, target = result
        logging.info(f"[$] AutoSteer - Target Bearing: {target}, Current Bearing: {current_bearing}")
        diff = abs(current_bearing - target)
        if target < current_bearing:
            key_to_press = 'a'
        elif target > current_bearing:
            key_to_press = 'd'
        else:
            logging.info("[$] AutoSteer - No difference in bearing, no steering required.")
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
            logging.info("[$] AutoSteer - Difference too small, no steering adjustment needed.")
            return

        logging.info(f"[$] AeroHelper AutoSteer - Pressing {key_to_press} for {hold_duration} sec (difference: {diff})")
        keyboard.press(key_to_press)
        time.sleep(hold_duration)
        keyboard.release(key_to_press)
    else:
        if result is None and current_bearing is None:
            alert("[!] AutoSteer - Target and current bearing not found in OCR text.", include_screenshot=False)
        elif result is None:
            alert("[!] AutoSteer - Target not found in OCR text.", include_screenshot=False)
        elif current_bearing is None:
            alert("[!] AutoSteer - Current bearing not found in OCR text.", include_screenshot=False)
        else:
            alert("[!] AutoSteer - Outstanding OCR error.", include_screenshot=False)
        logging.warning("[!] AutoSteer - Target or current bearing not found in OCR text.")

# --------------------------------------------------
# 8. Main Application Logic (for each cycle)
# --------------------------------------------------
def run_main_logic(prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter,
                   cycle_count, start_time, auto_steer_enabled, webhook_logging_enabled,
                   stop_distance, ship_top_speed):
    cycle_count += 1
    mouse.click(Button.left)
    keyboard.type('5')
    formatted_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    current_time = time.time()
    ocr_text = capture_and_process_screenshot()
    logging.info("[$] OCR text: " + ocr_text)
    if "disconnected" in ocr_text.lower():
        alert("[!] Disconnect detected!", include_screenshot=True)
    
    movement = None
    threshold = None

    current_distance = extract_distance(ocr_text)
    if current_distance is not None:
        logging.info(f"[$] Extracted Distance: {current_distance} nm")
        if prev_distance is not None and prev_time is not None:
            elapsed = current_time - prev_time
            expected_distance = ship_top_speed * (elapsed / 3600)
            threshold = expected_distance - LEEWAY
            movement = prev_distance - current_distance
            logging.info(f"[$] Elapsed: {elapsed:.2f} sec, Expected: {expected_distance:.2f} nm, Threshold: {threshold:.2f} nm")
            logging.info(f"[$] Movement this cycle: {movement:.2f} nm")
            if webhook_logging_enabled:
                if cycle_count % 5 == 0 and movement != 0:
                    eta_hours = (current_distance / movement) / 60
                    completion = (((start_distance - current_distance) / start_distance) * 100) if start_distance and start_distance > 0 else 0
                    alert(f"[?] ETA: {eta_hours:.2f} Hours, {completion:.2f}% Completed.", include_screenshot=True)
                alert(f"[$] Elapsed: {elapsed:.2f} sec, Movement: {movement:.2f} nm, Distance: {current_distance} nm", include_screenshot=False)
            if movement < threshold or movement == 0:
                alert(f"[!] Movement below threshold. Moved {movement:.2f} nm. Possible island collision!", include_screenshot=True)
                alert_counter += 1
        else:
            alert("[$] System Start", include_screenshot=False)
            alert(f"[$] AeroHelper System Start time: {formatted_time}", include_screenshot=False)
            start_distance = current_distance

        prev_distance = current_distance
        prev_time = current_time

        if current_distance < stop_distance:
            keyboard.press("z")
            time.sleep(0.1)
            keyboard.release("z")
            alert("[!] Boat needs manual docking. Boat is currently stopping.", include_screenshot=True)
            false_arrival_counter += 1
            alert_counter += 1
            if false_arrival_counter >= 3:
                alert("[!] Boat has stopped, closing System.", include_screenshot=True)
                alert(f"[!] Total elapsed time: {current_time - start_time:.2f} seconds.", include_screenshot=False)
                sys.exit()
        else:
            if false_arrival_counter >= 1:
                alert("[!] False Arrival detected, Boat is resuming trip.", include_screenshot=False)
                false_arrival_counter = 0
                keyboard.press('w')
                time.sleep(3)
                keyboard.release('w')
    else:
        logging.warning("[!] Distance not found in OCR text.")
        alert("[!] ROBLOX possibly crashed.", include_screenshot=True)
        alert_counter += 1
        prev_time = current_time

    if auto_steer_enabled:
        threading.Thread(target=run_autosteer, args=(ocr_text,)).start()
        if webhook_logging_enabled:
            try:
                res = extract_target_bearing(ocr_text)
                if res is not None:
                    dest2, target2 = res
                    current_bearing2 = extract_current_bearing(ocr_text)
                    alert(f"[$] AeroHelper AutoSteer - Destination is {dest2.upper()} with bearing {target2}", include_screenshot=False)
                    alert(f"[$] AeroHelper AutoSteer - Target Bearing: {target2}, Current Bearing: {current_bearing2}", include_screenshot=False)
                else:
                    alert("[!] AutoSteer - Unable to extract target bearing.", include_screenshot=False)
            except Exception as e:
                logging.error("[!] AutoSteer Webhook error: " + str(e))

    if alert_counter >= 5:
        alert("[!] Too many consecutive alerts triggered. Closing System.", include_screenshot=True)
        sys.exit()
    else:
        if movement is not None and alert_counter > 0 and movement >= threshold:
            alert_counter = 0

    return prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter, cycle_count

# --------------------------------------------------
# 9. PyQt5 GUI with Toggle Buttons and Options
# --------------------------------------------------
class AeroHelperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.config = load_config()
        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_AeroHelper_Logic)
        self.is_running = False

        self.previous_distance = None
        self.previous_time = None
        self.start_distance = None
        self.false_arrival_counter = 0
        self.alert_counter = 0
        self.cycle_count = 0
        self.start_time = time.time()

        self.auto_steer_enabled = False
        self.webhook_logging_enabled = False

    def init_ui(self):
        self.setWindowTitle('AeroHelper')
        
        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.toggle_logic)
        self.autosteer_button = QPushButton('AutoSteer', self)
        self.autosteer_button.clicked.connect(self.toggle_AutoSteer)
        self.webhooknotif_button = QPushButton('Non-Urgent Notifications', self)
        self.webhooknotif_button.clicked.connect(self.toggle_WebhookNotif)
        self.share_checkbox = QCheckBox("Share anonymous data with developer", self)
        self.share_checkbox.stateChanged.connect(self.toggle_share_data)

        self.ship_speed_input = QLineEdit(self)
        self.ship_speed_input.setPlaceholderText("Enter vehicle's top speed")
        self.ship_speed_label = QLabel("Vehicle's Top Speed (Knots)", self)

        self.stop_distance_input = QLineEdit(self)
        self.stop_distance_input.setPlaceholderText("1-5 Recommended")
        self.stop_distance_label = QLabel("Stop Distance from Destination (nm)", self)

        self.cycle_interval_input = QLineEdit(self)
        self.cycle_interval_input.setPlaceholderText("1-3 Recommended")
        self.cycle_interval_label = QLabel("System Cycle Interval (Minutes)", self)

        self.leeway_label = QLabel("Leeway (nm)", self)
        self.leeway_input = QLineEdit(self)
        self.leeway_input.setPlaceholderText("0.3 Recommended")
        
        self.multiplier_label = QLabel("Turning Multiplier", self)
        self.multiplier_input = QLineEdit(self)
        self.multiplier_input.setPlaceholderText("Keep between .5-2. Ensure no auscultation")
        
        self.webhook_url_label = QLabel("Webhook URL", self)
        self.webhook_url_input = QLineEdit(self)
        self.webhook_url_input.setPlaceholderText("Enter Webhook URL")
        
        if self.config:
            self.webhook_url_input.setText(self.config.get("webhook_url", "YOUR_WEBHOOK_URL"))
            self.ship_speed_input.setText(str(self.config.get("ship_top_speed", 20)))
            self.stop_distance_input.setText(str(self.config.get("stop_distance", 3)))
            self.cycle_interval_input.setText(str(self.config.get("cycle_interval", 1)))
            self.leeway_input.setText(str(self.config.get("leeway", 0.3)))
            self.multiplier_input.setText(str(self.config.get("multiplier", 1.9)))
            if self.config.get("share_anonymous_data", False):
                self.share_checkbox.setChecked(True)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.start_button)
        layout.addWidget(self.autosteer_button)
        layout.addWidget(self.webhooknotif_button)
        layout.addWidget(self.share_checkbox)
        layout.addWidget(self.ship_speed_label)
        layout.addWidget(self.ship_speed_input)
        layout.addWidget(self.stop_distance_label)
        layout.addWidget(self.stop_distance_input)
        layout.addWidget(self.cycle_interval_label)
        layout.addWidget(self.cycle_interval_input)
        layout.addWidget(self.leeway_label)
        layout.addWidget(self.leeway_input)
        layout.addWidget(self.multiplier_label)
        layout.addWidget(self.multiplier_input)
        layout.addWidget(self.webhook_url_label)
        layout.addWidget(self.webhook_url_input)
        self.setLayout(layout)
        self.setGeometry(300, 300, 300, 450)
        
    def toggle_share_data(self, state):
        global SHARE_DATA
        SHARE_DATA = (state == 2)

    def toggle_AutoSteer(self):
        if not self.auto_steer_enabled:
            self.auto_steer_enabled = True
            self.autosteer_button.setText('✓')
        else:
            self.auto_steer_enabled = False
            self.autosteer_button.setText('AutoSteer')

    def toggle_WebhookNotif(self):
        if not self.webhook_logging_enabled:
            self.webhook_logging_enabled = True
            self.webhooknotif_button.setText('✓')
        else:
            self.webhook_logging_enabled = False
            self.webhooknotif_button.setText('Notifications')
    
    def toggle_logic(self):
        global LEEWAY, MULTIPLIER, WEBHOOK_URL
        self.stop_distance = int(self.stop_distance_input.text())
        if not self.is_running:
            try:
                self.cycle_interval = int(self.cycle_interval_input.text()) * 60
                self.ship_top_speed = int(self.ship_speed_input.text())
                self.stop_distance = int(self.stop_distance_input.text())
                LEEWAY = float(self.leeway_input.text())
                MULTIPLIER = float(self.multiplier_input.text())
                WEBHOOK_URL = self.webhook_url_input.text()

                config_data = {
                    "webhook_url": WEBHOOK_URL,
                    "ship_top_speed": self.ship_top_speed,
                    "stop_distance": self.stop_distance,
                    "cycle_interval": self.cycle_interval // 60,
                    "leeway": LEEWAY,
                    "multiplier": MULTIPLIER,
                    "share_anonymous_data": SHARE_DATA
                }
                save_config(config_data)
                
                self.is_running = True
                self.start_button.setText('Stop')
                self.timer.start(self.cycle_interval * 1000)
                logging.info("[!] AeroHelper started.")
                self.cycle_interval_input.setDisabled(True)
                self.ship_speed_input.setDisabled(True)
                self.stop_distance_input.setDisabled(True)
                self.leeway_input.setDisabled(True)
                self.multiplier_input.setDisabled(True)
                self.webhook_url_input.setDisabled(True)
                time.sleep(1)
            except Exception as e:
                logging.error("Error starting AeroHelper: " + str(e))
                self.is_running = False
        else:
            self.is_running = False
            self.start_button.setText('Start')
            self.timer.stop()
            logging.info("[!] AeroHelper stopped.")
            self.cycle_interval_input.setDisabled(False)
            self.ship_speed_input.setDisabled(False)
            self.stop_distance_input.setDisabled(False)
            self.leeway_input.setDisabled(False)
            self.multiplier_input.setDisabled(False)
            self.webhook_url_input.setDisabled(False)

    def run_AeroHelper_Logic(self):
        if self.is_running:
            (self.previous_distance, self.previous_time, self.start_distance, 
             self.false_arrival_counter, self.alert_counter, self.cycle_count) = run_main_logic(
                self.previous_distance, self.previous_time, self.start_distance, self.false_arrival_counter,
                self.alert_counter, self.cycle_count, self.start_time, self.auto_steer_enabled,
                self.webhook_logging_enabled, self.stop_distance, self.ship_top_speed
            )

# --------------------------------------------------
# 10. Application Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    check_version()
    window = AeroHelperApp()
    window.show()
    sys.exit(app.exec_())
