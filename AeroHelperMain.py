'''
                         _    _      _                 
     /\                 | |  | |    | |                
    /  \   ___ _ __ ___ | |__| | ___| |_ __   ___ _ __ 
   / /\ \ / _ \ '__/ _ \|  __  |/ _ \ | '_ \ / _ \ '__|
  / ____ \  __/ | | (_) | |  | |  __/ | |_) |  __/ |   
 /_/    \_\_______ _____|_|  |_|\___|_| .__/ \___|_|   
https://github.com/SSkipr/AeronauticaHelper

'''

# --------------------------------------------------
# 0. Library setup
# -------------------------------------------------

# We import this library first as we need to use it to check for the libraries installed by the user.
import importlib 

# List of non-vanilla libraries (libraries that do not come with Python's base install) that need to be imported.
# Make sure you put all of these libraries just before section 1 as well so that they can be called later in the program as well.

# (I have included pynput on this list for futureproofing. When macOS update is complete please remove pydirectinput from this list.)
required_downloads = ['PyQT5', 'pyautogui', 'numpy', 'easyocr', 'pydirectinput', 'pynput']

# Create a dictionary in order to catch any failed imports.
missing_imports = []
for library_name in required_downloads:
    try:
        importlib.import_module(library_name)
    except ImportError:
        missing_imports.append(library_name)

# Check to see if there are any failed imports - if there are any, prompt the user to install them.
if len(missing_imports) != 0:
    print("It looks like you don't have the following Python libraries installed:")
    print(*missing_imports)
    installMessage = input("These libraries are necessary for running the program. Would you like to install them? (y/n): ")
    if installMessage.lower() != "y":
        print("As these libraries are necessary for running the program, the program is unable to continue, and will now exit.")
        print("If you wish to re-download the libraries, please re-run this program and you will be brought back to the previous dialog.")
        exit()
    else:
        print("Installation in progress - please wait.")
        for library in missing_imports:
            subprocess.check_call([sys.executable, "-m", "pip", "install", library])

# Everything is installed, we are ready to go.

# Stock imports
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

# Third-party imports
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer

import pyautogui
import numpy
import easyocr
import pydirectinput

# --------------------------------------------------
# 1. Configuration and Logging Setup
# --------------------------------------------------
logging.basicConfig(filename='log_data.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# // Constants: //
LEEWAY = 0.3                  # Leeway in nautical miles
MULTIPLIER = 1.9              # Customize to your ship's needs, just make sure it doesnt auscultate
WEBHOOK_URL = "YOUR_WEBHOOK_URL"
# // //

consecutive_alerts = 0

# --------------------------------------------------
# 2. Initialize EasyOCR Reader
# --------------------------------------------------
reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if supported

# --------------------------------------------------
# 3. Webhook Alert Function & Trigger Helper
# --------------------------------------------------
def send_webhook_alert(message, include_screenshot=False):
    if message.startswith("[!]") or message.startswith("[&]"):
        message = "@everyone " + message
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
        logging.info("[$] Alert sent: " + message)
    except Exception as e:
        logging.error("[$] Failed to send alert: " + str(e))

def trigger_alert(message, include_screenshot=False):
    global consecutive_alerts
    send_webhook_alert(message, include_screenshot)
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
    match = re.search(r"joined this game\s+(\d{3})", ocr_text_lower)
    if match:
        try:
            target = int(match.group(1))
            return "game", target
        except ValueError:
            pass
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
# 7. AutoSteer Function (runs in a separate thread)
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

        logging.info(f"[$] AutoSteer - Pressing {key_to_press} for {hold_duration} sec (difference: {diff})")
        pydirectinput.keyDown(key_to_press)
        time.sleep(hold_duration)
        pydirectinput.keyUp(key_to_press)
    else:
        if result is None and current_bearing is None:
            send_webhook_alert("[&] AutoSteer - Target and current bearing not found in OCR text.", include_screenshot=False)
        elif result is None:
            send_webhook_alert("[&] AutoSteer - Target not found in OCR text.", include_screenshot=False)
        elif current_bearing is None:
            send_webhook_alert("[&] AutoSteer - Current bearing not found in OCR text.", include_screenshot=False)
        else:
            send_webhook_alert("[&] AutoSteer - Outstanding OCR error.", include_screenshot=False)
        logging.warning("[$] AutoSteer - Target or current bearing not found in OCR text.")

# --------------------------------------------------
# 8. Main Application Logic (for each cycle)
# --------------------------------------------------
def run_main_logic(prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter,
                   cycle_count, start_time, auto_steer_enabled, webhook_logging_enabled,
                   stop_distance, ship_top_speed):
    cycle_count += 1
    pydirectinput.click()
    pydirectinput.press('5')
    formatted_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    current_time = time.time()
    ocr_text = capture_and_process_screenshot()
    logging.info("[$] OCR text: " + ocr_text)

    if "disconnected" in ocr_text.lower():
        trigger_alert("[!] Disconnect detected!", include_screenshot=True)
    
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
                    send_webhook_alert(f"[?] ETA: {eta_hours:.2f} Hours, {completion:.2f}% Completed.", include_screenshot=True)
                send_webhook_alert(f"[$] Elapsed: {elapsed:.2f} sec, Movement: {movement:.2f} nm, Distance: {current_distance} nm", include_screenshot=False)
            if movement is not None and movement < threshold:
                trigger_alert(f"[!] Movement below threshold. Expected at least {threshold:.2f} nm, but moved {movement:.2f} nm.", include_screenshot=True)
                alert_counter += 1
        else:
            trigger_alert("[!] Script Start", include_screenshot=False)
            trigger_alert(f"[?] Script Start time: {formatted_time}", include_screenshot=False)
            start_distance = current_distance

        prev_distance = current_distance
        prev_time = current_time

        if current_distance < stop_distance:
            pydirectinput.press('z')
            trigger_alert("[!] Boat needs manual docking. Boat is currently stopping.", include_screenshot=True)
            false_arrival_counter += 1
            alert_counter += 1
            if false_arrival_counter >= 3:
                trigger_alert("[!] Boat has stopped, closing script.", include_screenshot=True)
                trigger_alert(f"[!] Total elapsed time: {current_time - start_time:.2f} seconds.", include_screenshot=False)
                sys.exit()
        else:
            if false_arrival_counter >= 1:
                trigger_alert("[<3] False Arrival detected, Boat is resuming trip.", include_screenshot=False)
                false_arrival_counter = 0
                pydirectinput.keyDown('w')
                time.sleep(1)
                pydirectinput.keyUp('w')
    else:
        logging.warning("[$] Distance not found in OCR text.")
        trigger_alert("[!] ROBLOX possibly crashed.", include_screenshot=True)
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
                    trigger_alert(f"[$] AutoSteer - Destination is {dest2.upper()} with bearing {target2}", include_screenshot=False)
                    trigger_alert(f"[$] AutoSteer - Target Bearing: {target2}, Current Bearing: {current_bearing2}", include_screenshot=False)
                else:
                    trigger_alert("[&] AutoSteer - Unable to extract target bearing.", include_screenshot=False)
            except Exception as e:
                logging.error("[&] AutoSteer Webhook error: " + str(e))

    if alert_counter >= 5:
        trigger_alert("@everyone [!] Too many consecutive alerts triggered. Closing script.", include_screenshot=True)
        sys.exit()
    else:
        if movement is not None and alert_counter > 0 and movement >= threshold:
            alert_counter = 0

    return prev_distance, prev_time, start_distance, false_arrival_counter, alert_counter, cycle_count

# --------------------------------------------------
# 9. PyQt5 GUI with Toggle Buttons
# --------------------------------------------------
class AeroHelperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
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
        self.webhooknotif_button = QPushButton('Notifications', self)
        self.webhooknotif_button.clicked.connect(self.toggle_WebhookNotif)

        self.ship_speed_input = QLineEdit(self)
        self.ship_speed_input.setText('20')
        self.ship_speed_input.setPlaceholderText("0")
        self.ship_speed_label = QLabel("Vehicle's top speed", self)

        self.stop_distance_input = QLineEdit(self)
        self.stop_distance_input.setText('3')
        self.stop_distance_input.setPlaceholderText("1-5 Recommended")
        self.stop_distance_label = QLabel("Stop distance from destination (nm)", self)

        self.cycle_interval_input = QLineEdit(self)
        self.cycle_interval_input.setText('1')
        self.cycle_interval_input.setPlaceholderText("1-10 Recommended")
        self.cycle_interval_label = QLabel("Script Cycle Interval (Minutes)")

        layout = QVBoxLayout(self)
        layout.addWidget(self.start_button)
        layout.addWidget(self.autosteer_button)
        layout.addWidget(self.webhooknotif_button)
        layout.addWidget(self.ship_speed_label)
        layout.addWidget(self.ship_speed_input)
        layout.addWidget(self.stop_distance_label)
        layout.addWidget(self.stop_distance_input)
        layout.addWidget(self.cycle_interval_label)
        layout.addWidget(self.cycle_interval_input)
        self.setLayout(layout)
        self.setGeometry(300, 300, 250, 250)
        
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
        self.stop_distance = int(self.stop_distance_input.text())
        if not self.is_running:
            try:
                self.cycle_interval = int(self.cycle_interval_input.text()) * 60
                self.ship_top_speed = int(self.ship_speed_input.text())
                self.stop_distance = int(self.stop_distance_input.text())
                self.is_running = True
                self.start_button.setText('Stop')
                self.timer.start(self.cycle_interval * 1000)
                logging.info("[!] AeroHelper started.")
                self.cycle_interval_input.setDisabled(True)
                self.ship_speed_input.setDisabled(True)
                self.stop_distance_input.setDisabled(True)
                time.sleep(1)
            except:
                self.is_running = False
        else:
            self.is_running = False
            self.start_button.setText('Start')
            self.timer.stop()
            logging.info("[!] AeroHelper stopped.")
            self.cycle_interval_input.setDisabled(False)
            self.ship_speed_input.setDisabled(False)
            self.stop_distance_input.setDisabled(False)

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
    window = AeroHelperApp()
    window.show()
    sys.exit(app.exec_())
