'''

   simple                _    _      _                 
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
Version: 1.1 (simple)
ChatGPT Was used for the regex stuff here, sorry if it isn't great - Person 12
'''


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

CYCLE_INTERVAL = 60       # Cycle interval in seconds (must be lower than WEBHOOK_INTERVAL)
WEBHOOK_INTERVAL = 30 * 60 # Webhook interval in seconds
STEERING_MULTIPLIER = 1.6 # Steering multiplier, make bigger for larger ships. Keep relatively low as the ship will correct over time. Ensure it doesn't auscultate (go back and forth)
WEBHOOK_URL = "YOUR_WEBHOOK_URL" # your webhook URL for screenshots

if CYCLE_INTERVAL > 1140: # If the cycle time is more than 19m, set it to 19m (roblox anti-AFK will kick you if there is no input for 20m)
    CYCLE_INTERVAL = 1440

import time
import re   
import logging
import io
import json
import threading
import platform
import importlib
import subprocess
import sys


logging.basicConfig(filename='log_data.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

OS = platform.system()
logging.info("OS detected as {OS}") # Logging


# --------------------------------------------------
# 2. Downloading and importing required packages
# --------------------------------------------------
required_downloads = ['PyQt5', 'pyautogui', 'numpy', 'easyocr', 'requests']
missing_imports = []

if OS == "Windows": # if on windows you need pydirecinput
    required_downloads.append('pydirectinput')
else: #otherwise you need pynput
    required_downloads.append('pynput')


for library_name in required_downloads:
    try:
        importlib.import_module(library_name)
    except ImportError:
        missing_imports.append(library_name)
if missing_imports:
    for library in missing_imports:
        subprocess.check_call([sys.executable, "-m", "pip", "install", library])


if OS == "Windows": # if on windows you need pydirecinput
    import pydirectinput
else: #otherwise you need pynput
    import pynput
    
    from pynput.keyboard import Key, Controller as KeyboardController
    from pynput.mouse import Button, Controller as MouseController
    pynputkeyboard = KeyboardController()
    pynputmouse = MouseController()



import PyQt5
import pyautogui
import numpy
import easyocr
import pydirectinput
import requests

# --------------------------------------------------
# 3. Initialize EasyOCR Reader and Input Setup
# --------------------------------------------------
reader = easyocr.Reader(['en'], gpu=False) # Change to true if needed, only compatible with some GPUs


def MouseLeft(x,y):
    if OS == "Windows":
        pydirectinput.click(x,y)
    else:
        pynputmouse.click(Button.left)

def Keyboard(button, duration):
    if OS == "Windows":
        pydirectinput.keyDown(button)
        time.sleep(duration)
        pydirectinput.keyUp(button)
    else:
        pynputkeyboard.press(button)
        time.sleep(duration)
        pynputkeyboard.release(button)
# --------------------------------------------------
# 3. Webhook Alert Function (with screenshot on error)
# --------------------------------------------------
def send_webhook_alert(message):
    payload = {"content": message}
    try: # In a try/except as webhook may return a error
        screenshot = pyautogui.screenshot() # Take a screenshot
        buffer = io.BytesIO() # Create a buffer
        screenshot.save(buffer, format="PNG") # Save image to buffer
        buffer.seek(0)

        files = {"file": ("screenshot.png", buffer, "image/png")}
        response = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload)}, files=files) # Send the webhook
        response.raise_for_status()
        logging.info("Alert sent with screenshot: " + message) # Logs
    except Exception as e: # If we run into a error, capture the error as e
        logging.error("Failed to send alert with screenshot: " + str(e)) # Log error

# --------------------------------------------------
# 4. Screenshot Capture and OCR Processing
# --------------------------------------------------
def capture_and_process_screenshot(regions):

    screenshots = [pyautogui.screenshot(region=region) for region in regions] # take screenshots in the regions specified when starting the program

    text = [] # define the text variable

    for screenshot in screenshots: # for every screenshot:
        image = numpy.array(screenshot)
        results = reader.readtext(image) # read the text in screenshot
        text.append(" ".join([res[1] for res in results])) # add the text to the text variable
    return str(text) # return the text variable (list) as a string

# --------------------------------------------------
# 5. Extract Bearing Values for AutoSteer
# --------------------------------------------------
def extract_target_bearing(ocr_text):

    text = ocr_text

    match = re.search(r"\b\d+\b", text)  # Find the first number

    if match:
        first_number = int(match.group())  # Convert to an integer if needed
        return first_number  # Returns the first number (Dest Heading)
        

def extract_current_bearing(ocr_text):
    
    text = ocr_text

    match = re.search(r"\b(\d+)\b(?!.*\b\d+\b)", text)  # Find the last number

    if match:
        last_number = int(match.group(1))  # Extract the last number
        return last_number # Returns the third number (TRK)

# --------------------------------------------------
# 6. AutoSteer Function (runs in a separate thread)
# --------------------------------------------------
def run_autosteer(ocr_text):
    target = extract_target_bearing(ocr_text) # get target bearing
    current_bearing = extract_current_bearing(ocr_text) # get current bearing
    if target is not None and current_bearing is not None: # if we get numbers for both bearings
        logging.info(f"AutoSteer - Target Bearing: {target}, Current Bearing: {current_bearing}") #logs current and target bearings
        diff = abs(current_bearing - target)
        if target < current_bearing: # find direction needed to turn and set that to key_to_press
            key_to_press = 'a'
        elif target > current_bearing:
            key_to_press = 'd'
        else:
            logging.info("AutoSteer - No difference in bearing, no steering required.") # logging
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
            logging.info("AutoSteer - Difference too small, no steering adjustment needed.") # logging
            return
        
        hold_duration = hold_duration * STEERING_MULTIPLIER # multiply the hold duration by the steering multiplier

        logging.info(f"AutoSteer - Pressing {key_to_press} for {hold_duration} sec (difference: {diff})") #log what direction + how long autosteer is being used for
        Keyboard(key_to_press, hold_duration) #hold a/d for the set amount of time
        time.sleep(3)
    else:
        logging.warning("AutoSteer - Target or current bearing not found in OCR text.") # if one of the bearings is none, then we log the error

# --------------------------------------------------
# 7. Main Application Logic
# --------------------------------------------------
def main():

    screen_width, screen_height = pyautogui.size() # Find the screen width and height for region finding below

    # Region finding, used to capture screenshots later:

    if screen_height == 2160: # If 4k:
        regions = [
            (int(0.105 * screen_width), int(0.72 * screen_height), int(0.04 * screen_width), int(0.04 * screen_height)), # Dest Bearing + Dest distance Capture
            (int(0.475 * screen_width), int(0.055 * screen_height), int(0.02 * screen_width), int(0.03 * screen_height))  # Current Bearing (TRK) Capture
        ] 
    elif screen_height == 900: # if 16:10 (macbook display)
       regions = [
        (int(0.117 * screen_width), int(0.73 * screen_height), int(0.06 * screen_width), int(0.04 * screen_height)), # Dest Bearing + Dest distance Capture
        (int(0.45 * screen_width), int(0.13 * screen_height), int(0.04 * screen_width), int(0.03 * screen_height))  # Current Bearing Capture     
        ]   
    elif screen_height == 1440: # If 1440p:
        regions = [
            (int(0.105 * screen_width), int(0.73 * screen_height), int(0.04 * screen_width), int(0.04 * screen_height)), # Dest Bearing + Dest distance Capture
            (int(0.47 * screen_width), int(0.08 * screen_height), int(0.02 * screen_width), int(0.03 * screen_height))  # Current Bearing (TRK) Capture
        ]  
    elif screen_height == 1080: # If 1080p:
        regions = [
            (int(0.105 * screen_width), int(0.73 * screen_height), int(0.04 * screen_width), int(0.04 * screen_height)), # Dest Bearing + Dest distance Capture
            (int(0.455 * screen_width), int(0.1 * screen_height), int(0.035 * screen_width), int(0.03 * screen_height))  # Current Bearing (TRK) Capture
        ] 
    elif screen_height == 720: # If 720p:
        regions = [
            (int(0.105 * screen_width), int(0.74 * screen_height), int(0.04 * screen_width), int(0.04 * screen_height)), # Dest Bearing + Dest distance Capture
            (int(0.425 * screen_width), int(0.17 * screen_height), int(0.045 * screen_width), int(0.03 * screen_height))  # Current Bearing (TRK) Capture
        ]
    else: # If not on any of the supported resolutions:
        print("You're not on a supported resolution, the supported resolutions are: 4k, 1440p, 1080p 1440x900 (macbook screens) and 720p. Please rerun this program when you have one of those resolutions selected") 
        exit() # Close the program

    centerX = int(round(screen_width/2)) # Get screen centers for later so we don't have to keep doing the operation
    centerY = int(round(screen_height/2))
    
    print("Aeronautica Helper v2")
    time.sleep(1)
    print("Navigate to the ROBLOX tab, you have 10 seconds before the program starts")
    time.sleep(10)
    
    start_time = time.time() #get start time

    send_webhook_alert("Aerohelper has started successfully") # Webhook to confirm that it works

    while True:

        MouseLeft(centerX, centerY)

        ocr_text = capture_and_process_screenshot(regions) # capture screenshot with regions found earlier

        logging.info("OCR text: " + ocr_text)
            
        threading.Thread(target=run_autosteer, args=(ocr_text,)).start()

        elapsed_time = time.time() - start_time #find elapsed time
        if elapsed_time >= WEBHOOK_INTERVAL: # if it has been more than specified time for webhook interval
            start_time = time.time() #reset start
            send_webhook_alert("Boat is currently sailing") #send webhook

        
        time.sleep(CYCLE_INTERVAL)
        logging.info("Cycle complete.")

# --------------------------------------------------
# 8. Application Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    main()
