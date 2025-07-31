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
Version 3.5
'''

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
import math
import random
import uuid
import psutil
import pygetwindow as gw
import torch
import gc

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QByteArray

import pyautogui
from PIL import Image
import numpy
import asyncio
from pathlib import Path
from winsdk.windows.media.ocr import OcrEngine, OcrResult
from winsdk.windows.globalization import Language, ApplicationLanguages
from winsdk.windows.graphics.imaging import BitmapDecoder, SoftwareBitmap
from winsdk.windows.storage import StorageFile
from winsdk.windows.storage.streams import RandomAccessStreamReference
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

VERSION = "3.5"
AIRPORT_ROUTES = {
    "leovetsk international airport": [
        "tikaranto international airport",
        "auchenburgh international airport"
    ],
    "tikaranto international airport": [
        "leovetsk international airport",
        "eisenhardt municipal airport",
    ],
    "auchenburgh international airport": [
        "leovetsk international airport",
        "eisenhardt municipal airport"
    ],
    "eisenhardt municipal airport": [
        "tikaranto international airport",
        "auchenburgh international airport"
    ],
    "nordspyd arctic airfield": [
        "norman international airport",
        "udyanapura merlani international airport"
    ],
    "norman international airport": [
        "nordspyd arctic airfield"
    ],
    "udyanapura merlani international airport": [
        "nordspyd arctic airfield"
    ],
    "kapa airportt": [
        "hipe airport"
    ],
    "umibutsu international airport": [
        "hipe airport"
    ],
    "hipe airport": [
        "kapa airportt",
        "umibutsu international airport"
    ],
}
AIRSHIP_ROUTES = {
    "nordspyd arctic airfield": ["valois international"],
    "valois international": ["nordspyd arctic airfield"]
}
DATA_FILE = "data.txt"
LOG_FILE = "log_data.txt"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s', force=True)

consecutive_alerts = 0
SHARE_DATA = False
QUIT_ON_ERRORS = True
doctr_model = None

keyboard = KeyboardController()
mouse = MouseController()

class CrossPlatformMouse:
    def __init__(self):
        try:
            from mousekey import MouseKey
            self.mouse = MouseKey()
            self.using_mousekey = True
        except ImportError:
            self.mouse = MouseController()
            self.using_mousekey = False
    
    def left_click_xy_natural(self, x, y, delay=0.3, min_variation=-3, max_variation=3, 
                             use_every=4, sleeptime=(0.005, 0.009), print_coords=False, percent=90):
        if not self.using_mousekey:
            current_x, current_y = self.mouse.position
            
            steps = 20
            for i in range(1, steps + 1):
                progress = i / steps
                path_x = current_x + (x - current_x) * progress
                path_y = current_y + (y - current_y) * progress
                
                if i != steps:
                    path_x += random.randint(min_variation, max_variation)
                    path_y += random.randint(min_variation, max_variation)
                
                self.mouse.position = (path_x, path_y)
                time.sleep(random.uniform(*sleeptime) * 2)
            
            self.mouse.position = (x, y)
            time.sleep(delay)
            self.mouse.press(Button.left)
            time.sleep(0.1)
            self.mouse.release(Button.left)
        else:
            self.mouse.left_click_xy_natural(x, y, delay, min_variation, max_variation,
                                           use_every, sleeptime, print_coords, percent)

    def natural_move_to(self, x, y, duration=0.4):
        pynput_mouse = MouseController()
        start_x, start_y = pynput_mouse.position
        
        num_steps = int(duration / 0.01)
        if num_steps < 1:
            num_steps = 1
        
        for i in range(1, num_steps + 1):
            progress = i / num_steps
            progress = 1 - (1 - progress) ** 3
            
            path_x = start_x + (x - start_x) * progress
            path_y = start_y + (y - start_y) * progress
            
            pynput_mouse.position = (int(path_x), int(path_y))
            time.sleep(0.01)

cross_mouse = CrossPlatformMouse()

def get_screen_scaling_factor():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetDpiForSystem() / 96.0
    except:
        return 1.0


def scale_coordinates(x, y):
    scaling_factor = get_screen_scaling_factor()
    return int(x * scaling_factor), int(y * scaling_factor)

def save_config(data):
    try:
        config_size = len(json.dumps(data, indent=2))
        logging.info(f"Attempting to save configuration data to '{DATA_FILE}' (size: {config_size} bytes)")
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        logging.info(f"Configuration data successfully saved to '{DATA_FILE}' with {len(data)} settings")
    except Exception as e:
        logging.error(f"[!] Configuration save operation failed for file '{DATA_FILE}': {str(e)}")

def load_config():
    if os.path.exists(DATA_FILE):
        try:
            file_size = os.path.getsize(DATA_FILE)
            logging.info(f"Loading configuration from existing file '{DATA_FILE}' (size: {file_size} bytes)")
            with open(DATA_FILE, "r") as f:
                config_data = json.load(f)
            logging.info(f"Configuration loaded successfully with {len(config_data)} settings from '{DATA_FILE}'")
            return config_data
        except Exception as e:
            logging.error(f"[!] Configuration load operation failed for file '{DATA_FILE}': {str(e)}, returning empty configuration")
    else:
        logging.info(f"[!] Configuration file '{DATA_FILE}' does not exist, returning empty configuration")
    return {}

def check_version():
    try:
        logging.info("=" * 50)
        logging.info(f"    AeroHelper v{VERSION} Application Startup    ")
        logging.info("=" * 50)
        logging.info(f"Runtime Environment Details:")
        logging.info(f"  Python Version: {sys.version}")
        logging.info(f"  Working Directory: {os.getcwd()}")
        logging.info(f"  Script Path: {os.path.abspath(sys.argv[0])}")
        logging.info(f"  Platform: {platform.system()} {platform.release()}")

        headers = {'User-Agent': f'AeroHelper v{VERSION} Application'}
        logging.info(f"Initiating version check against remote server (/version)")
        response = requests.get("https://aeronautica-helper.vercel.app/api/version", headers=headers)
        response.raise_for_status()
        latest_version = response.text.strip()
        
        logging.info(f"Version check completed - Current: v{VERSION}, Latest Available: v{latest_version}")
        
        if latest_version != VERSION:
            logging.warning(f"[!!] Version mismatch detected: Running v{VERSION} but v{latest_version} is available")
            QMessageBox.warning(None, "AeroHelper Update Required",
                f"A new version ({latest_version}) of AeroHelper is available. You are running {VERSION}.\n"
                "You will be directed to the update page. The application will now attempt to delete its data and script files.")
            webbrowser.open("https://github.com/SSkipr/AeronauticaHelper/releases/latest")
            logging.shutdown()

            files_to_delete = [DATA_FILE, LOG_FILE, "app.py", "core.py", "autopilot.py"]
            logging.info(f"Initiating cleanup of {len(files_to_delete)} application files for update")
            for file_path in files_to_delete:
                try:
                    if os.path.exists(file_path):
                        if platform.system() == "Windows":
                            subprocess.call(["del", os.path.abspath(file_path)], shell=True)
                        else:
                            subprocess.call(["rm", "-f", os.path.abspath(file_path)])
                        logging.info(f"Successfully deleted file: {file_path}")
                except Exception as e:
                    logging.warning(f"[!] Failed to delete file {file_path}: {str(e)}")
            sys.exit()
        else:
            logging.info(f"Version check passed - Application is up to date (v{VERSION})")
            
    except Exception as e:
        logging.error(f"[!] Version check operation failed: {str(e)}")
    
    try:
        headers = {'User-Agent': f'AeroHelper v{VERSION} Application'}
        logging.info(f"Sending application usage analytics to remote server (/ran)")
        response = requests.get("https://aeronautica-helper.vercel.app/api/ran", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        status = data.get("status")

        logging.info(f"Usage analytics transmission completed with status: '{status}'")
        if status != 'success':
            logging.warning(f"[!] Usage analytics reported unexpected status: '{status}'")

    except Exception as e:
        logging.error(f"[!] Usage analytics transmission failed: {str(e)}")

def click_center(bbox):
    try:
        x = int((bbox[0][0] + bbox[2][0]) / 2)
        y = int((bbox[0][1] + bbox[2][1]) / 2)
        
        if x < 0 or y < 0:
            logging.error(f"[!] Invalid click coordinates detected: x={x}, y={y} (bbox: {bbox})")
            return False
        
        logging.info(f"Executing center click at coordinates ({x}, {y}) derived from bounding box {bbox}")
        cross_mouse.left_click_xy_natural(x, y, delay=0.3, min_variation=-3, max_variation=3,
                                use_every=4, sleeptime=(0.005, 0.009), print_coords=False, percent=90)
        logging.info(f"Center click operation completed successfully at ({x}, {y})")
        return True
    except Exception as e:
        logging.error(f"[!] Center click operation failed with error: {str(e)} (bbox: {bbox})")
        return False

def capture_and_process_screenshot():
    temp_file = os.path.join(os.environ.get('TEMP', os.getcwd()), "temp_screenshot.png")
    
    logging.info(f"Capturing full screen screenshot for OCR processing")
    screenshot = pyautogui.screenshot()
    screenshot.save(temp_file)
    screenshot_size = os.path.getsize(temp_file)
    logging.info(f"Screenshot captured and saved to '{temp_file}' (size: {screenshot_size} bytes)")

    try:
        loop = asyncio.get_event_loop()
        logging.info(f"Using existing asyncio event loop for OCR processing")
    except RuntimeError:
        logging.info(f"Creating new asyncio event loop for OCR processing")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    logging.info(f"Initiating Windows OCR processing with language preference: FirstFromAvailableLanguages")
    ocr_result: OcrResult = loop.run_until_complete(_run_ocr_async(temp_file, "FirstFromAvailableLanguages"))

    lines_data = []
    full_text_lines = []
    processed_lines = 0
    
    if ocr_result and ocr_result.lines:
        logging.info(f"OCR processing completed, analyzing {len(ocr_result.lines)} detected text lines")
        for line in ocr_result.lines:
            line_words_text = [word.text for word in line.words]
            if not line_words_text:
                continue

            line_text = " ".join(line_words_text)
            full_text_lines.append(line_text)
            processed_lines += 1

            all_points = []
            for word in line.words:
                rect = word.bounding_rect
                all_points.extend([
                    (rect.x, rect.y),
                    (rect.x + rect.width, rect.y),
                    (rect.x, rect.y + rect.height),
                    (rect.x + rect.width, rect.y + rect.height)
                ])
            
            if not all_points:
                continue

            min_x = min(p[0] for p in all_points)
            min_y = min(p[1] for p in all_points)
            max_x = max(p[0] for p in all_points)
            max_y = max(p[1] for p in all_points)
            
            line_bbox = [
                [int(min_x), int(min_y)],
                [int(max_x), int(min_y)],
                [int(max_x), int(max_y)],
                [int(min_x), int(max_y)]
            ]
            lines_data.append([line_bbox, line_text])

    full_text = " ".join(full_text_lines)
    logging.info(f"OCR text extraction completed - Processed {processed_lines} lines, total text length: {len(full_text)} characters")
    
    try:
        os.remove(temp_file)
        logging.info(f"Temporary screenshot file '{temp_file}' removed successfully")
    except OSError as e:
        logging.warning(f"[!] Failed to remove temporary screenshot file '{temp_file}': {str(e)}")

    return full_text, lines_data

async def _run_ocr_async(path: str, lang_tag: str) -> OcrResult | None:
    try:
        logging.info(f"Starting asynchronous OCR processing for file: '{path}' with language setting: '{lang_tag}'")
        file = await StorageFile.get_file_from_path_async(path)
        stream_ref = RandomAccessStreamReference.create_from_file(file)
        stream = await stream_ref.open_read_async()

        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        
        logging.info(f"Image decoded successfully, bitmap dimensions: {bitmap.pixel_width}x{bitmap.pixel_height}")

        engine = None
        if lang_tag == "FirstFromAvailableLanguages":
            try:
                logging.info(f"Attempting to create OCR engine from user profile languages")
                engine = OcrEngine.try_create_from_user_profile_languages()
                if not engine:
                    logging.info("[!] User profile languages unavailable, attempting first available system language")
            except Exception as e_profile_lang:
                logging.warning(f"[!] User profile language OCR engine creation failed: {str(e_profile_lang)}, trying system languages")
            
            if not engine:
                available_langs = OcrEngine.get_available_recognizer_languages()
                if available_langs:
                    selected_lang = available_langs[0]
                    logging.info(f"Using first available system language: {selected_lang.language_tag} ({selected_lang.display_name})")
                    engine = OcrEngine.try_create_from_language(selected_lang)
                else:
                    logging.error("[!] No OCR languages available on this system")
                    return None
        else:
            language = Language(lang_tag)
            if OcrEngine.is_language_supported(language):
                logging.info(f"Creating OCR engine for specified language: {lang_tag}")
                engine = OcrEngine.try_create_from_language(language)
            else:
                logging.error(f"[!] Specified language '{lang_tag}' is not supported for OCR on this system")
                return None
        
        if not engine:
            logging.error(f"[!] Failed to create OCR engine for language configuration: '{lang_tag}'")
            try:
                all_system_languages = OcrEngine.get_available_recognizer_languages()
                if all_system_languages:
                    logging.info("Available OCR languages on this system:")
                    for lang in all_system_languages:
                        logging.info(f"  - {lang.language_tag} ({lang.display_name})")
                else:
                    logging.error("[!] No OCR languages installed or available on this system")
            except Exception as e_lang_list:
                logging.error(f"[!] Failed to query available OCR languages: {str(e_lang_list)}")
            return None

        logging.info(f"OCR engine created successfully, starting text recognition")
        result: OcrResult = await engine.recognize_async(bitmap)
        
        if result and result.lines:
            logging.info(f"OCR text recognition completed successfully - Detected {len(result.lines)} text lines")
        else:
            logging.warning(f"[!] OCR completed but no text was detected in the image")
        return result
    except Exception as e:
        logging.error(f"[!] OCR processing failed with error: {str(e)} (file: '{path}', language: '{lang_tag}')")
        return None

def show_available_languages() -> list:
    return [
        tag
        for tag in ApplicationLanguages.languages
        if OcrEngine.is_language_supported(Language(tag))
    ]

def extract_distance(ocr_text):
    ocr_text = ocr_text.lower()
    logging.info(f"Attempting to extract distance from OCR text (length: {len(ocr_text)} characters)")
    
    distance_pattern = r"distance:?\s*(\d+(?:[.,]\d+)?)\s*nm"
    match = re.search(distance_pattern, ocr_text, re.IGNORECASE)
    if match:
        try:
            distance_value = abs(float(match.group(1).replace(",", ".")))
            logging.info(f"Distance extracted successfully using primary pattern: {distance_value} nm (matched: '{match.group(0)}')")
            return distance_value
        except ValueError as e:
            logging.warning(f"[!] Distance value conversion failed for primary pattern match '{match.group(1)}': {str(e)}")
            
    pattern = r"(\d+(?:[.,]\d+)?)\s*nm"
    matches = re.findall(pattern, ocr_text, re.IGNORECASE)
    if len(matches) >= 2:
        value_str = matches[1].replace(",", ".")
        try:
            distance_value = abs(float(value_str))
            logging.info(f"Distance extracted from secondary pattern (2nd match): {distance_value} nm (all matches: {matches})")
            return distance_value
        except ValueError as e:
            logging.warning(f"[!] Distance value conversion failed for secondary pattern match '{value_str}': {str(e)}")
    elif matches:
        try:
            distance_value = abs(float(matches[0].replace(",", ".")))
            logging.info(f"Distance extracted from fallback pattern (1st match): {distance_value} nm (match: '{matches[0]}')")
            return distance_value
        except ValueError as e:
            logging.warning(f"[!] Distance value conversion failed for fallback pattern match '{matches[0]}': {str(e)}")
    
    logging.warning(f"[!] No distance value could be extracted from OCR text")
    return None

def calculate_eta(current_distance, vehicle_speed):
    try:
        if vehicle_speed <= 0:
            logging.warning(f"[!] Invalid vehicle speed for ETA calculation: {vehicle_speed} (must be > 0)")
            return None
        
        eta_hours = current_distance / vehicle_speed
        logging.info(f"ETA calculated: {eta_hours:.2f} hours (distance: {current_distance} nm, speed: {vehicle_speed} nm/h)")
        return eta_hours
    except Exception as e:
        logging.error(f"[!] ETA calculation failed: {str(e)} (distance: {current_distance}, speed: {vehicle_speed})")
        return None

def _run_doctr_ocr_on_left_screen():
    global doctr_model
    if doctr_model is None:
        logging.info("Doctr OCR model not loaded, initializing model for left screen analysis")
        doctr_model = ocr_predictor(pretrained=True)
        logging.info("Doctr OCR model initialization completed for left screen processing")

    screen_width, screen_height = pyautogui.size()
    crop_region = (0, 0, screen_width // 2, screen_height)
    img_width, img_height = crop_region[2], crop_region[3]
    
    logging.info(f"Capturing left half of screen for DocTR OCR (region: {crop_region}, dimensions: {img_width}x{img_height})")
    
    temp_filename = f"doctr_temp_{uuid.uuid4()}.png"
    temp_file = os.path.join(os.environ.get('TEMP', os.getcwd()), temp_filename)
    
    screenshot = pyautogui.screenshot(region=crop_region)
    screenshot.save(temp_file)
    file_size = os.path.getsize(temp_file)
    logging.info(f"Left screen screenshot saved to '{temp_file}' (size: {file_size} bytes)")

    lines_data = []
    full_text_lines = []
    processed_blocks = 0
    
    try:
        logging.info(f"Processing screenshot with Doctr OCR model")
        doc = DocumentFile.from_images(temp_file)
        result = doctr_model(doc)
        
        if result.pages:
            logging.info(f"Doctr processing completed, analyzing {len(result.pages)} page(s)")
            for page in result.pages:
                for block in page.blocks:
                    processed_blocks += 1
                    for line in block.lines:
                        line_text = line.render().strip()
                        if not line_text:
                            continue
                        
                        full_text_lines.append(line_text)

                        (x_min, y_min), (x_max, y_max) = line.geometry
                        abs_x_min = int(x_min * img_width)
                        abs_y_min = int(y_min * img_height)
                        abs_x_max = int(x_max * img_width)
                        abs_y_max = int(y_max * img_height)

                        line_bbox = [
                            [abs_x_min, abs_y_min], [abs_x_max, abs_y_min],
                            [abs_x_max, abs_y_max], [abs_x_min, abs_y_max]
                        ]
                        lines_data.append([line_bbox, line_text])

        logging.info(f"Doctr OCR processing completed - {processed_blocks} blocks processed, {len(full_text_lines)} text lines extracted")

    except Exception as e:
        logging.error(f"[!] Doctr OCR processing failed for left screen: {str(e)}")
    finally:
        try:
            os.remove(temp_file)
            logging.info(f"Temporary Doctr screenshot file '{temp_file}' removed successfully")
        except OSError as e:
            logging.warning(f"[!] Failed to remove temporary Doctr screenshot file '{temp_file}': {str(e)}")

    full_text = " ".join(full_text_lines)
    logging.info(f"Left screen Doctr OCR completed - Total text length: {len(full_text)} characters")
    return full_text, lines_data

def extract_target_bearing(ocr_text):
    logging.info(f"Initiating target bearing extraction using Doctr OCR on left screen")
    doctr_ocr_text, _ = _run_doctr_ocr_on_left_screen()
    logging.info(f"Doctr OCR text for bearing analysis (length: {len(doctr_ocr_text)} characters): {doctr_ocr_text}")

    ocr_text_lower = doctr_ocr_text.lower()
    dest_match = re.search(r"dest?\D+(\d{3})", ocr_text_lower)
    if dest_match:
        try:
            target_bearing = int(dest_match.group(1))
            logging.info(f"Target bearing extracted via destination pattern: {target_bearing}° (matched: '{dest_match.group(0)}')")
            return "dest", target_bearing
        except ValueError as e:
            logging.warning(f"[!] Destination bearing value conversion failed: {str(e)} (matched: '{dest_match.group(1)}')")
    
    pattern = r"(?!clear|trk|hdg)(?!\b\d{1,2}nm\b)(?!\d{3,6}(?=\s?mb\b))(\b[a-z]{4,5}\b)\s+(\d{3})"
    pattern_match = re.search(pattern, ocr_text_lower)
    if pattern_match:
        try:
            dest_name = pattern_match.group(1)
            target_bearing = int(pattern_match.group(2))
            
            if dest_name in ["knots", "games", "windy"]:
                logging.warning(f"[!] Target bearing extracted but destination name indicates OCR error: '{dest_name}' -> {target_bearing}°")
                return "OCR Error", target_bearing
            else:
                logging.info(f"Target bearing extracted successfully: destination '{dest_name}' at {target_bearing}° (matched: '{pattern_match.group(0)}')")
                return dest_name, target_bearing
        except ValueError as e:
            logging.warning(f"[!] Target bearing value conversion failed for pattern match: {str(e)} (matched: '{pattern_match.group(2)}')")

    logging.warning(f"[!] No target bearing could be extracted from Doctr OCR text")
    return None

def extract_land_clearance_altitude(ocr_text):
    logging.info(f"Initiating land clearance altitude extraction using Doctr OCR on left screen")
    doctr_ocr_text, _ = _run_doctr_ocr_on_left_screen()
    logging.info(f"Doctr OCR text for land clearance analysis (length: {len(doctr_ocr_text)} characters): {doctr_ocr_text}")

    patterns = [
        r"\((\d{1,4})\s*ft\)",
        r"altitude\s+\d+\s*ft\s*\((\d{1,4})\s*ft\)",
        r"\((\d{1,4})\)",
    ]
    
    ocr_text_lower = doctr_ocr_text.lower()
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, ocr_text_lower)
        if match:
            try:
                altitude = int(match.group(1))
                if 0 <= altitude <= 10000:
                    logging.info(f"Land clearance altitude extracted using pattern {i+1}: {altitude} ft (matched: '{match.group(0)}')")
                    return altitude
                else:
                    logging.warning(f"[!] Land clearance altitude out of valid range using pattern {i+1}: {altitude} ft (matched: '{match.group(0)}')")
            except (ValueError, IndexError) as e:
                logging.warning(f"[!] Land clearance altitude conversion failed for pattern {i+1}: {str(e)} (matched: '{match.group(0)}')")
                continue

    logging.warning(f"[!] No valid land clearance altitude could be extracted from Doctr OCR text")
    return None

def extract_sea_level_altitude(ocr_text):
    logging.info(f"Initiating sea level altitude extraction using Doctr OCR on left screen")
    doctr_ocr_text, _ = _run_doctr_ocr_on_left_screen()
    logging.info(f"Doctr OCR text for sea level altitude analysis (length: {len(doctr_ocr_text)} characters): {doctr_ocr_text}")

    patterns = [
        r"altitude\s+(\d{1,4})\s*ft",
        r"(\d{1,4})\s*ft\s*\(\d+\s*ft\)",
        r"alt\s+(\d{1,4})",
    ]
    
    ocr_text_lower = doctr_ocr_text.lower()
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, ocr_text_lower)
        if match:
            try:
                altitude = int(match.group(1))
                if 0 <= altitude <= 50000:
                    logging.info(f"Sea level altitude extracted using pattern {i+1}: {altitude} ft (matched: '{match.group(0)}')")
                    return altitude
                else:
                    logging.warning(f"[!] Sea level altitude out of valid range using pattern {i+1}: {altitude} ft (matched: '{match.group(0)}')")
            except (ValueError, IndexError) as e:
                logging.warning(f"[!] Sea level altitude conversion failed for pattern {i+1}: {str(e)} (matched: '{match.group(0)}')")
                continue

    logging.warning(f"[!] No valid sea level altitude could be extracted from Doctr OCR text")
    return None

def extract_fuel_level(ocr_text):
    logging.info(f"Initiating fuel level extraction using Doctr OCR on left screen")
    doctr_ocr_text, _ = _run_doctr_ocr_on_left_screen()
    logging.info(f"Doctr OCR text for fuel level analysis (length: {len(doctr_ocr_text)} characters): {doctr_ocr_text}")

    ocr_text_lower = doctr_ocr_text.lower()
    match = re.search(r"fuel\s+([\d.,]+)\s*%", ocr_text_lower)
    if match:
        try:
            fuel_percentage = float(match.group(1).replace(",", "."))
            logging.info(f"Fuel level extracted successfully: {fuel_percentage}% (matched: '{match.group(0)}')")
            return fuel_percentage
        except ValueError as e:
            logging.warning(f"[!] Fuel level value conversion failed: {str(e)} (matched: '{match.group(1)}')")

    logging.warning(f"[!] No fuel level could be extracted from Doctr OCR text")
    return None

def extract_current_bearing(ocr_text):
    ocr_text = ocr_text.lower()
    logging.info(f"Extracting current bearing from OCR text (length: {len(ocr_text)} characters): {ocr_text}")

    patterns = [
        (r"t\s*r\s*k\s+(\d{3})", "standard TRK pattern with space"),
        (r"t\s*r\s*k\s*(\d{3})", "TRK pattern without required space"),
        (r"t\s*r\s*k\s*\d?\s*(\d{3})", "TRK pattern with OCR error digits"),
        (r"t\s*r\s*k\s*\.\s*(\d{3})", "TRK pattern with period separator"),
        (r"t\s*r\s*k\s*[a-z]*\s*(\d{3})", "TRK pattern with OCR corruption characters")
    ]
    
    for i, (pattern, description) in enumerate(patterns):
        match = re.search(pattern, ocr_text)
        if match:
            try:
                bearing_value = int(match.group(1))
                logging.info(f"Current bearing extracted using pattern {i+1} ({description}): {bearing_value}° (matched: '{match.group(0)}')")
                return bearing_value
            except ValueError as e:
                logging.warning(f"[!] Bearing value conversion failed for pattern {i+1}: {str(e)} (matched: '{match.group(1)}')")
                continue

    logging.warning(f"[!] No current bearing could be extracted from OCR text using any of the {len(patterns)} patterns")
    return None

def alert(message, include_screenshot=False, verbose_mode=False):
    global consecutive_alerts, SHARE_DATA, QUIT_ON_ERRORS
    
    config = load_config()
    webhook_url = config.get("webhook_url", "")
    
    if message.startswith("[!]"):
        consecutive_alerts += 1
        message = "@everyone " + message
        logging.error(f"Critical alert triggered (consecutive count: {consecutive_alerts}): {message}")
        
        if SHARE_DATA:
            try:
                log_content = ""
                data_content = ""
                logging.info(f"Anonymous data sharing enabled, collecting diagnostic data for critical alert")
                
                if os.path.exists(LOG_FILE):
                    try:
                        chunk_size = 4 * 1024 * 1024
                        with open(LOG_FILE, "rb") as f:
                            file_size = os.path.getsize(LOG_FILE)
                            seek_pos = max(0, file_size - chunk_size)
                            f.seek(seek_pos)
                            last_chunk = f.read()
                        log_content = last_chunk.decode('utf-8', errors='ignore')
                        logging.info(f"Successfully read last {len(log_content)} characters from log file for data sharing")
                    except Exception as e:
                        logging.error(f"[!] Failed to read last 4MB of log file for data sharing: {str(e)}")
                        log_content = f"Error reading log file: {e}"
                else:
                    logging.warning(f"[!] Log file '{LOG_FILE}' not found for anonymous data sharing")

                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, "r") as f:
                        data_content = f.read()
                    logging.info(f"Successfully read {len(data_content)} characters from data file for sharing")
                else:
                    logging.warning(f"[!] Data file '{DATA_FILE}' not found for anonymous data sharing")

                data_payload = {
                    "Files": [
                        {
                            "filename": "log_data.txt",
                            "content": log_content
                        },
                        {
                            "filename": "data.txt",
                            "content": data_content
                        }
                    ]
                }
                
                logging.info(f"Attempting to send anonymous diagnostic data to server")
                r = requests.post("https://aeronautica-helper.vercel.app/api/data",
                                    headers={'Content-Type': 'application/json'},
                                    json=data_payload)
                r.raise_for_status()
                logging.info(f"Successfully transmitted anonymous diagnostic data to server (status: {r.status_code})")

            except Exception as e:
                logging.error(f"[!] Failed to transmit anonymous diagnostic data to server: {str(e)}")
    else:
        consecutive_alerts = 0
        if verbose_mode:
            logging.info(f"Standard notification sent via webhook: {message}")
    
    if not webhook_url:
        logging.warning(f"[*] Webhook URL not configured, skipping webhook notification: {message}")
        return False
    
    if not verbose_mode and not message.startswith("[!]"):
        logging.debug(f"Verbose mode disabled, skipping non-critical webhook notification: {message}")
        return False
    
    payload = {"content": message}
    try:
        if include_screenshot:
            logging.info(f"Capturing screenshot for webhook notification")
            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            buffer.seek(0)
            screenshot_size = len(buffer.getvalue())
            logging.info(f"Screenshot captured ({screenshot_size} bytes), sending webhook with attachment")
            files = {"file": ("screenshot.png", buffer, "image/png")}
            response = requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files=files)
        else:
            logging.info(f"Sending webhook notification without screenshot")
            response = requests.post(webhook_url, json=payload)
        
        response.raise_for_status()
        logging.info(f"Webhook notification successfully delivered (status: {response.status_code}, message: '{message}')")
    except Exception as e:
        logging.error(f"[!] Failed to deliver webhook notification: {str(e)} (webhook_url: {webhook_url})")
    
    if QUIT_ON_ERRORS and consecutive_alerts >= 5:
        logging.critical(f"[!] Critical threshold reached: {consecutive_alerts} consecutive error alerts detected, initiating application shutdown")
        os._exit(1)
        
    return True

ROBLOX_GAME_URL = "roblox://placeID=6647962258"

def close_roblox_client():
    closed_any = False
    running_processes = []
    
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if proc.info['name'] == 'RobloxPlayerBeta.exe':
                running_processes.append(proc.info['pid'])
                proc.terminate()
                closed_any = True
                logging.info(f"Successfully terminated RobloxPlayerBeta.exe process (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logging.warning(f"[!] Unable to terminate Roblox process (PID: {proc.info.get('pid', 'unknown')}): {str(e)}")
    if closed_any:
        logging.info(f"Roblox client termination completed. Processes closed: {len(running_processes)} (PIDs: {running_processes})")
    else:
        logging.info("No active RobloxPlayerBeta.exe processes found to terminate")
    
    return closed_any

def launch_roblox_client():
    try:
        logging.info(f"Attempting to launch Roblox client using os.startfile with URL: {ROBLOX_GAME_URL}")
        os.startfile(ROBLOX_GAME_URL)
        logging.info(f"Successfully initiated Roblox client launch via os.startfile")
        return True
    except Exception as e:
        logging.error(f"Primary launch method (os.startfile) failed with error: {str(e)}, attempting fallback method")
        try:
            logging.info(f"Attempting fallback launch method using webbrowser module")
            webbrowser.open(ROBLOX_GAME_URL)
            logging.info(f"Successfully initiated Roblox client launch via webbrowser fallback method")
            return True
        except Exception as e2:
            error_msg = f"All Roblox client launch methods failed. Primary error: {str(e)}, Fallback error: {str(e2)}"
            alert(f"[!] {error_msg}", include_screenshot=True)
            logging.critical(f"Complete failure to launch Roblox client: {error_msg}")
            return False

def restart_all_engines():
    global doctr_model
    logging.info("Initiating OCR engine restart and memory cleanup process")

    try:
        memory_before = psutil.virtual_memory().percent
        logging.info(f"System memory usage before cleanup: {memory_before}%")
        
        if 'torch' in sys.modules:
            logging.info("Clearing PyTorch CUDA cache")
            torch.cuda.empty_cache()
            logging.info("PyTorch CUDA cache cleared successfully")
        
        logging.info("Executing garbage collection")
        gc.collect()
        
        logging.info("Reinitializing DocTR OCR model with pretrained weights")
        doctr_model = ocr_predictor(pretrained=True)
        logging.info("Doctr OCR model reinitialization completed successfully")
        
        memory_after = psutil.virtual_memory().percent
        logging.info(f"System memory usage after cleanup: {memory_after}% (change: {memory_after - memory_before:+.1f}%)")
        
    except Exception as e:
        logging.error(f"[!] OCR engine restart failed with error: {str(e)}")

    final_gc = gc.collect()
    logging.info(f"Final garbage collection completed, collected {final_gc} objects. OCR engine cleanup process finished")


def focus_roblox_window():
    roblox_process_found = False
    process_details = []
    
    for proc in psutil.process_iter(['name', 'pid', 'memory_info']):
        if proc.info['name'] == 'RobloxPlayerBeta.exe':
            roblox_process_found = True
            process_details.append(f"PID:{proc.info['pid']} Memory:{proc.info['memory_info'].rss // 1024 // 1024}MB")
            
    if not roblox_process_found:
        logging.error("[!] Roblox process detection failed: No RobloxPlayerBeta.exe processes found in system")
        return False
    
    logging.info(f"Roblox process detection successful: Found {len(process_details)} instance(s) - {process_details}")

    try:
        roblox_windows = gw.getWindowsWithTitle('Roblox')
        if roblox_windows:
            roblox_window = roblox_windows[0]
            window_info = f"Position:({roblox_window.left},{roblox_window.top}) Size:{roblox_window.width}x{roblox_window.height}"
            logging.info(f"Roblox window detected - {window_info}, initiating focus sequence")
            
            if roblox_window.isMinimized:
                logging.info("Roblox window is minimized, restoring to normal state")
                roblox_window.restore()
                time.sleep(0.5)
                logging.info("Window restoration completed")
            
            logging.info("Activating Roblox window to bring to foreground")
            roblox_window.activate()
            time.sleep(1.0)
            
            if not roblox_window.isMinimized:
                center_x = roblox_window.left + (roblox_window.width // 2)
                center_y = roblox_window.top + (roblox_window.height // 2)
                logging.info(f"Performing focus click at window center coordinates: ({center_x}, {center_y})")
                cross_mouse.left_click_xy_natural(center_x, center_y, delay=0.1)
                time.sleep(0.3)
                logging.info("Focus click completed successfully")
            
            logging.info("Roblox window focus sequence completed successfully")
        else:
            logging.warning("[!] Roblox process is active but no window with title 'Roblox' was found, continuing with execution")
        return True
    except Exception as e:
        logging.error(f"[!] Roblox window focus operation failed with error: {str(e)}, continuing with execution anyway")
        return True

try:
    available_languages = show_available_languages()
    if not available_languages:
        logging.error("[!] Windows OCR initialization failed: No languages available for OCR processing")
    else:
        logging.info(f"Windows OCR initialized successfully with {len(available_languages)} available languages: {available_languages}")
except Exception as e:
    logging.critical(f"[!] Critical error during Windows OCR initialization: {str(e)}")
    sys.exit(1)

def _run_doctr_ocr_on_top_right_quadrant():
    global doctr_model
    if doctr_model is None:
        logging.info("Doctr OCR model not loaded, initializing model for time detection in top-right quadrant")
        doctr_model = ocr_predictor(pretrained=True)
        logging.info("Doctr OCR model initialization completed for time detection")

    screen_width, screen_height = pyautogui.size()
    crop_region = (screen_width // 2, 0, screen_width // 2, screen_height // 2)
    
    logging.info(f"Capturing top-right quadrant for time detection (region: {crop_region})")
    
    temp_filename = f"doctr_time_temp_{uuid.uuid4()}.png"
    temp_file = os.path.join(os.environ.get('TEMP', os.getcwd()), temp_filename)
    
    screenshot = pyautogui.screenshot(region=crop_region)
    screenshot.save(temp_file)
    file_size = os.path.getsize(temp_file)
    logging.info(f"Top-right quadrant screenshot saved to '{temp_file}' (size: {file_size} bytes)")

    lines_data = []
    full_text_lines = []
    processed_lines = 0
    
    try:
        logging.info(f"Processing top-right quadrant screenshot with Doctr OCR for time detection")
        doc = DocumentFile.from_images(temp_file)
        result = doctr_model(doc)
        
        if result.pages:
            logging.info(f"Doctr time detection processing completed, analyzing {len(result.pages)} page(s)")
            for page in result.pages:
                for block in page.blocks:
                    for line in block.lines:
                        try:
                            line_text = line.render()
                            full_text_lines.append(line_text)
                            processed_lines += 1
                            
                            if line.words:
                                x_coords = []
                                y_coords = []
                                
                                for word in line.words:
                                    try:
                                        if hasattr(word, 'geometry') and len(word.geometry) >= 4:
                                            x_coords.extend([word.geometry[0], word.geometry[2]])
                                            y_coords.extend([word.geometry[1], word.geometry[3]])
                                    except (IndexError, AttributeError):
                                        continue
                                
                                if x_coords and y_coords:
                                    x_min, x_max = min(x_coords), max(x_coords)
                                    y_min, y_max = min(y_coords), max(y_coords)
                                    
                                    abs_x_min = int(x_min * crop_region[2] + crop_region[0])
                                    abs_y_min = int(y_min * crop_region[3] + crop_region[1])
                                    abs_x_max = int(x_max * crop_region[2] + crop_region[0])
                                    abs_y_max = int(y_max * crop_region[3] + crop_region[1])
                                    
                                    bbox = [[abs_x_min, abs_y_min], [abs_x_max, abs_y_min], 
                                           [abs_x_max, abs_y_max], [abs_x_min, abs_y_max]]
                                    lines_data.append((bbox, line_text))
                        except Exception as e:
                            logging.debug(f"[!] Error processing line in time detection: {str(e)}")
                            continue

        logging.info(f"Top-right quadrant Doctr OCR completed - {processed_lines} lines processed for time detection")

    except Exception as e:
        logging.error(f"[!] Doctr OCR processing failed for top-right quadrant time detection: {str(e)}")
    finally:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Temporary time detection screenshot file '{temp_file}' removed successfully")
        except Exception as e:
            logging.warning(f"[!] Failed to remove temporary time detection file '{temp_file}': {str(e)}")

    full_text = " ".join(full_text_lines)
    logging.info(f"Time detection OCR completed - Total text length: {len(full_text)} characters")
    return full_text, lines_data

def _run_doctr_ocr_on_top_half():
    global doctr_model
    if doctr_model is None:
        logging.info("Doctr OCR model not loaded, initializing model for bearing detection in top half")
        doctr_model = ocr_predictor(pretrained=True)
        logging.info("Doctr OCR model initialization completed for bearing detection")

    screen_width, screen_height = pyautogui.size()
    crop_region = (0, 0, screen_width, screen_height // 2)
    
    logging.info(f"Capturing top half of screen for bearing detection (region: {crop_region})")
    
    temp_filename = f"doctr_bearing_temp_{uuid.uuid4()}.png"
    temp_file = os.path.join(os.environ.get('TEMP', os.getcwd()), temp_filename)
    
    screenshot = pyautogui.screenshot(region=crop_region)
    screenshot.save(temp_file)
    file_size = os.path.getsize(temp_file)
    logging.info(f"Top half screenshot saved to '{temp_file}' (size: {file_size} bytes)")

    lines_data = []
    full_text_lines = []
    processed_lines = 0
    
    try:
        logging.info(f"Processing top half screenshot with Doctr OCR for bearing detection")
        doc = DocumentFile.from_images(temp_file)
        result = doctr_model(doc)
        
        if result.pages:
            logging.info(f"Doctr bearing detection processing completed, analyzing {len(result.pages)} page(s)")
            for page in result.pages:
                for block in page.blocks:
                    for line in block.lines:
                        try:
                            line_text = line.render()
                            full_text_lines.append(line_text)
                            processed_lines += 1
                            
                            if line.words:
                                x_coords = []
                                y_coords = []
                                
                                for word in line.words:
                                    try:
                                        if hasattr(word, 'geometry') and len(word.geometry) >= 4:
                                            x_coords.extend([word.geometry[0], word.geometry[2]])
                                            y_coords.extend([word.geometry[1], word.geometry[3]])
                                    except (IndexError, AttributeError):
                                        continue
                                
                                if x_coords and y_coords:
                                    x_min, x_max = min(x_coords), max(x_coords)
                                    y_min, y_max = min(y_coords), max(y_coords)
                                    
                                    abs_x_min = int(x_min * crop_region[2] + crop_region[0])
                                    abs_y_min = int(y_min * crop_region[3] + crop_region[1])
                                    abs_x_max = int(x_max * crop_region[2] + crop_region[0])
                                    abs_y_max = int(y_max * crop_region[3] + crop_region[1])
                                    
                                    bbox = [[abs_x_min, abs_y_min], [abs_x_max, abs_y_min], 
                                           [abs_x_max, abs_y_max], [abs_x_min, abs_y_max]]
                                    lines_data.append((bbox, line_text))
                        except Exception as e:
                            logging.debug(f"[!] Error processing line in bearing detection: {str(e)}")
                            continue

        logging.info(f"Top half Doctr OCR completed - {processed_lines} lines processed for bearing detection")

    except Exception as e:
        logging.error(f"[!] Doctr OCR processing failed for top half bearing detection: {str(e)}")
    finally:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Temporary bearing detection screenshot file '{temp_file}' removed successfully")
        except Exception as e:
            logging.warning(f"[!] Failed to remove temporary bearing detection file '{temp_file}': {str(e)}")

    full_text = " ".join(full_text_lines)
    logging.info(f"Bearing detection OCR completed (length: {len(full_text)} characters): {full_text}")
    return full_text, lines_data

def extract_military_time(ocr_text):
    import re
    
    logging.info(f"Extracting military time from OCR text (length: {len(ocr_text)} characters)")
    time_pattern = r'\b([01]?[0-9]|2[0-3]):([0-5][0-9])\b'
    
    matches = re.findall(time_pattern, ocr_text)
    logging.info(f"Found {len(matches)} potential time matches in OCR text")
    
    for i, (hour, minute) in enumerate(matches):
        hour_int = int(hour)
        minute_int = int(minute)

        if 0 <= hour_int <= 23 and 0 <= minute_int <= 59:
            time_str = f"{hour_int:02d}:{minute_int:02d}"
            logging.info(f"Valid military time extracted (match {i+1}): {time_str} (from raw: {hour}:{minute})")
            return time_str
        else:
            logging.warning(f"[!] Invalid time values found (match {i+1}): {hour}:{minute} (hour: {hour_int}, minute: {minute_int})")
    
    logging.warning(f"[!] No valid military time could be extracted from OCR text")
    return None

def is_night_time(military_time):
    if not military_time:
        logging.warning(f"[!] ]Night time check failed: No military time provided")
        return None
    
    try:
        hour, minute = map(int, military_time.split(':'))
        time_in_minutes = hour * 60 + minute

        night_start = 16 * 60  
        night_end = 6 * 60     
        
        is_night = time_in_minutes >= night_start or time_in_minutes < night_end
        time_period = "night" if is_night else "day"
        
        logging.info(f"Time period analysis for {military_time}: {time_period} (minutes: {time_in_minutes}, night range: {night_start}-{24*60} and 0-{night_end})")
        return is_night
    except Exception as e:
        logging.error(f"[!] Night time analysis failed for time '{military_time}': {str(e)}")
        return None