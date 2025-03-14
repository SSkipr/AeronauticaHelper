'''

                         _    _      _                 
     /\                 | |  | |    | |                
    /  \   ___ _ __ ___ | |__| | ___| |_ __   ___ _ __ 
   / /\ \ / _ \ '__/ _ \|  __  |/ _ \ | '_ \ / _ \ '__|
  / ____ \  __/ | | (_) | |  | |  __/ | |_) |  __/ |   
 /_/    \_\_______ _____|_|  |_|\___|_| .__/ \___|_|   
            / ____/ ____| |  (_)      | |              
           | (___| (___ | | ___ _ __  ____             
            \___ \\___ \| |/ / | '_ \| '__|            
            ____) |___) |   <| | |_) | |               
           |_____/_____/|_|\_\_| .__/|_|               
                               | |                     
                               |_|                     
Version: 2
'''




import time
import re
import logging
import pyautogui
import requests
import numpy as np
import easyocr
import io
import json
import pynput
import threading

# --------------------------------------------------
# 1. Configuration and Logging Setup
# --------------------------------------------------
logging.basicConfig(filename='log_data.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
keyboard = KeyboardController()
mouse = MouseController()

#Defining variables for later
alert_sent = False
destination_reached = False

# Constants:
SHIP_TOP_SPEED = 20           # Ship's top speed in knots
CYCLE_INTERVAL = 1 * 60       # Cycle interval in seconds (must be within 1m-19m and factor of 60, 1m is recomended)
LEEWAY = 0.3                  # Leeway in nautical miles for crash detection (keep relatively low)
WEBHOOK_URL = "your_webhook_url"

# --------------------------------------------------
# 2. Initialize EasyOCR Reader
# --------------------------------------------------
reader = easyocr.Reader(['en'], gpu=False) # Change to true if needed, only compatible with some GPUs

# --------------------------------------------------
# 3. Webhook Alert Function (with screenshot on error)
# --------------------------------------------------
def send_webhook_alert(message, include_screenshot=False):
    payload = {"content": message}
    if alert_sent == False and destination_reached == False:
        alert_sent = True
        if include_screenshot:
            try:
                screenshot = pyautogui.screenshot()
                buffer = io.BytesIO()
                screenshot.save(buffer, format="PNG")
                buffer.seek(0)
                files = {"file": ("screenshot.png", buffer, "image/png")}
                response = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload)}, files=files)
                response.raise_for_status()
                logging.info("[$] Alert sent with screenshot: " + message)
            except Exception as e:
                logging.error("[$] Failed to send alert with screenshot: " + str(e))
        else:
            try:
                response = requests.post(WEBHOOK_URL, json=payload)
                response.raise_for_status()
                logging.info("[$] Alert sent: " + message)
            except Exception as e:
                logging.error("[$] Failed to send alert: " + str(e))

# --------------------------------------------------
# 4. Screenshot Capture and OCR Processing
# --------------------------------------------------
def capture_and_process_screenshot():
    screenshot = pyautogui.screenshot()
    image = np.array(screenshot)
    results = reader.readtext(image)
    text = " ".join([res[1] for res in results])
    return text

# --------------------------------------------------
# 5. Extracting the Distance Value
# --------------------------------------------------
def extract_distance(ocr_text):
    ocr_text = ocr_text.lower()
    pattern = r"distance\s*[\:\;\,\'\-]+\s*(\d+)(?:[.,]+(\d+))?\s*nm"
    match = re.search(pattern, ocr_text)
    if match:
        try:
            integer_part = match.group(1)
            fractional_part = match.group(2) if match.group(2) is not None else ""
            value_str = integer_part
            if fractional_part:
                value_str += "." + fractional_part
            return abs(float(value_str))
        except ValueError:
            return None
    return None

# --------------------------------------------------
# 6. Extract Bearing Values for AutoSteer
# --------------------------------------------------
def extract_target_bearing(ocr_text):
    match = re.search(r"dest\s+(\d{3})", ocr_text.lower())
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

def extract_current_bearing(ocr_text):
    match = re.search(r"trk\s+\d{3}\s+(\d{3})\s+hdg", ocr_text.lower())
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
    target = extract_target_bearing(ocr_text)
    current_bearing = extract_current_bearing(ocr_text)
    if target is not None and current_bearing is not None:
        logging.info(f"[&] AutoSteer - Target Bearing: {target}, Current Bearing: {current_bearing}")
        diff = abs(current_bearing - target)
        if target < current_bearing:
            key_to_press = 'a'
        elif target > current_bearing:
            key_to_press = 'd'
        else:
            logging.info("[&] AutoSteer - No difference in bearing, no steering required.")
            return

        if diff > 11:
            hold_duration = 3
        elif 6 <= diff <= 10:
            hold_duration = 2
        elif 3 <= diff <= 5:
            hold_duration = 1
        elif 1 <= diff < 3:
            hold_duration = 0.75
        else:
            logging.info("[&] AutoSteer - Difference too small, no steering adjustment needed.")
            return

        logging.info(f"[&] AutoSteer - Pressing {key_to_press} for {hold_duration} sec (difference: {diff})")
        keyboard.press(key_to_press)
        time.sleep(hold_duration)
        keyboard.release(key_to_press)
        time.sleep(3)
    else:
        logging.warning("[&] AutoSteer - Target or current bearing not found in OCR text.")

# --------------------------------------------------
# 8. Main Application Logic
# --------------------------------------------------
def main():
    cycle = 0
    print("Aeronautica Helper v2")
    print("You will have 5 seconds to navigate to the ROBLOX tab after completing the following question.")
    
    auto_steer_input = input("Enable AutoSteer? (y/n): ")
    print("Navigate to the ROBLOX tab")
    time.sleep(5)
    auto_steer_enabled = auto_steer_input.lower().startswith('y')
    
    if auto_steer_enabled:
        logging.info("[$] AutoSteer enabled.")

    previous_distance = None
    previous_time = None

    while True:
        mouse.click(Button.left)
        current_time = time.time()
        ocr_text = capture_and_process_screenshot()
        logging.info("[$] OCR text: " + ocr_text)
        if "disconnected" in ocr_text.lower():
            send_webhook_alert("[!] Disconnect detected!", include_screenshot=True)

        current_distance = extract_distance(ocr_text)
        if current_distance is not None:
            logging.info(f"[$] Extracted Distance: {current_distance} nm")
            if previous_distance is not None and previous_time is not None:
                elapsed = current_time - previous_time
                expected_distance = SHIP_TOP_SPEED * (elapsed / 3600)
                threshold = expected_distance - LEEWAY
                movement = previous_distance - current_distance
                logging.info(f"[$] Elapsed time: {elapsed:.2f} sec, Expected Distance: {expected_distance:.2f} nm, Threshold: {threshold:.2f} nm")
                logging.info(f"[$] Distance moved in this cycle: {movement:.2f} nm")
                if movement < threshold:
                    send_webhook_alert(f"[!] Movement below threshold. Expected at least {threshold:.2f} nm, but moved {movement:.2f} nm.", include_screenshot=True)
            previous_distance = current_distance
            previous_time = current_time

            if current_distance < 3 and destination_reached == False:
                keyboard.press('z')
                time.sleep(0.1)
                keyboard.release('z')
                send_webhook_alert("[!] Boat needs manual docking. Boat is currently stopping.", include_screenshot=True)
                destination_reached = True
        else:
            logging.warning("[$] Distance not found in OCR text.")
            send_webhook_alert("[!] ROBLOX possibly crashed.", include_screenshot=True)
            previous_time = current_time
            
        if auto_steer_enabled:
            threading.Thread(target=run_autosteer, args=(ocr_text,)).start()

        if cycle * CYCLE_INTERVAL % 60 == 0 and destination_reached == False: # every 60mins without reaching the destination
            alert_sent = False
        
        cycle = cycle + 1
        time.sleep(CYCLE_INTERVAL)
        logging.info("[$] Cycle complete.")

# --------------------------------------------------
# 9. Application Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    main()
