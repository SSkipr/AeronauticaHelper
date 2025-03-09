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
Version: 1
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

# --------------------------------------------------
# 1. Configuration and Logging Setup
# --------------------------------------------------
logging.basicConfig(filename='distance_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Constants:
SHIP_TOP_SPEED = 20           # Ship's top speed in knots
CYCLE_INTERVAL = 5 * 60       # Sleep time between cycles in seconds (recomended: 5 minutes)
LEEWAY = 0.2                  # Leeway in nautical miles
WEBHOOK_URL = "your_webhook_url"

# --------------------------------------------------
# 2. Initialize EasyOCR Reader
# --------------------------------------------------
reader = easyocr.Reader(['en'], gpu=False)

# --------------------------------------------------
# 3. Webhook Alert Function
# --------------------------------------------------
def send_webhook_alert(message, include_screenshot=False):
    payload = {"content": message}
    if include_screenshot:
        try:
            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            buffer.seek(0)
            files = {"file": ("screenshot.png", buffer, "image/png")}
            response = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload)}, files=files)
            response.raise_for_status()
            logging.info("Alert sent with screenshot: " + message)
        except Exception as e:
            logging.error("Failed to send alert with screenshot: " + str(e))
    else:
        try:
            response = requests.post(WEBHOOK_URL, json=payload)
            response.raise_for_status()
            logging.info("Alert sent: " + message)
        except Exception as e:
            logging.error("Failed to send alert: " + str(e))

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
    pattern = r"Distance:\s*(-?[\d\.]+)\s*nm"
    match = re.search(pattern, ocr_text)
    if match:
        return abs(float(match.group(1)))
    return None

# --------------------------------------------------
# 6. Main Application Logic
# --------------------------------------------------
def main():
    previous_distance = None
    previous_time = None

    while True:
        current_time = time.time()
        ocr_text = capture_and_process_screenshot()
        logging.info("OCR text: " + ocr_text)

        if "disconnected" in ocr_text.lower():
            send_webhook_alert("Alert: Disconnected detected!", include_screenshot=True)

        current_distance = extract_distance(ocr_text)
        if current_distance is not None:
            logging.info(f"Extracted Distance: {current_distance} nm")
            
            if previous_distance is not None and previous_time is not None:
                elapsed = current_time - previous_time
                expected_distance = SHIP_TOP_SPEED * (elapsed / 3600)
                threshold = expected_distance - LEEWAY

                movement = previous_distance - current_distance

                logging.info(f"Elapsed time: {elapsed:.2f} sec, Expected Distance: {expected_distance:.2f} nm, Threshold: {threshold:.2f} nm")
                logging.info(f"Distance moved in this cycle: {movement:.2f} nm")
                
                if movement < threshold:
                    send_webhook_alert(f"Alert: Movement below threshold. Expected at least {threshold:.2f} nm, but moved {movement:.2f} nm.", include_screenshot=True)
            
            previous_distance = current_distance
            previous_time = current_time
        else:
            logging.warning("Distance not found in OCR text.")
            send_webhook_alert("Alert: Distance not found in OCR text!", include_screenshot=True)
            previous_time = current_time

        time.sleep(CYCLE_INTERVAL)

# --------------------------------------------------
# 7. Application Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    main()