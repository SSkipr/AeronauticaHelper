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

import time
import logging
import re
import numpy
import pyautogui
from PyQt5.QtCore import QThread, pyqtSignal

from core import (
    alert, click_center, _run_doctr_ocr_on_left_screen, capture_and_process_screenshot,
    extract_distance, extract_target_bearing, extract_current_bearing,
    keyboard, cross_mouse, Key, AIRPORT_ROUTES, AIRSHIP_ROUTES
)

STEERING_HISTORY = []
OSCILLATION_ALERT_SENT = False

def clear_steering_history():
    global STEERING_HISTORY, OSCILLATION_ALERT_SENT
    STEERING_HISTORY.clear()
    OSCILLATION_ALERT_SENT = False

class AutoPilotThread(QThread):
    finished = pyqtSignal(bool)
    
    def __init__(self, is_final_phase=False, leeway=0.3, multiplier=1.9, autopilot_mode_type="boat"):
        super().__init__()
        self.is_final_phase = is_final_phase
        self.leeway = leeway
        self.multiplier = multiplier
        self.autopilot_mode_type = autopilot_mode_type
    
    def retry_action(self, action, max_attempts=3, description="action"):
        for attempt in range(max_attempts):
            logging.info(f"Attempting to execute {description} (attempt {attempt + 1}/{max_attempts})")
            if action():
                logging.info(f"Successfully completed {description} on attempt {attempt + 1}")
                return True
            time.sleep(1)
            logging.warning(f"[!] Retry required for {description} - attempt {attempt+1} failed, trying again (remaining attempts: {max_attempts - attempt - 1})")
        logging.error(f"[!] Critical failure: Unable to complete {description} after {max_attempts} attempts, manual intervention required")
        return False
    
    def final_phase(self):
        logging.info("Initiating final phase of Boat AutoPilot sequence")
        alert("Starting final phase of Boat AutoPilot", include_screenshot=False)
        
        time.sleep(15)
        
        max_attempts = 10
        docking_attempts = 0
        previous_distance = None
        
        while docking_attempts < max_attempts:
            logging.info(f"Executing docking procedure - attempt {docking_attempts + 1} of {max_attempts} maximum attempts")
            end_sail_button_coords, is_red = check_for_end_sail()
            
            if end_sail_button_coords and not is_red:
                logging.info("[*] End Sail button detected in clickable state (not red), proceeding with click sequence")
                alert("End Sail button found, attempting to click.", include_screenshot=False)
                
                time.sleep(30)

                click_center(end_sail_button_coords)
                time.sleep(1)
                click_center(end_sail_button_coords)

                logging.info("[*] End Sail button clicked successfully, transitioning to next job search phase")
                alert("End Sail clicked. Starting next job.", include_screenshot=False)
                return self.initial_phase()
            
            elif end_sail_button_coords and is_red:
                docking_attempts += 1
                logging.info(f"[*] End Sail button detected in red state (not ready), performing precision docking maneuver (attempt {docking_attempts})")
                alert("End Sail button is red. Attempting precision docking.", include_screenshot=False)

                ocr_text, _ = capture_and_process_screenshot()
                current_distance = extract_distance(ocr_text)

                if current_distance is None or current_distance == 0:
                    logging.error("[!] Critical error during docking: Unable to extract distance from OCR or distance is zero, manual intervention required")
                    alert("[!] Unexplained error during docking. Human intervention required.", include_screenshot=True)
                    return False

                logging.info(f"[*] Current distance to docking point: {current_distance} nautical miles")

                if previous_distance is None:
                    logging.info("[*] Initial docking attempt - no previous distance reference, moving forward with standard approach")
                    keyboard.press('w')
                    time.sleep(5 * self.multiplier)
                    keyboard.release('w')
                    time.sleep(15)
                    
                    logging.info("Stopping vehicle to re-evaluate position and distance")
                    keyboard.press('z')
                    time.sleep(0.5)
                    keyboard.release('z')
                    time.sleep(15)
                else:
                    if current_distance > previous_distance:
                        logging.warning(f"[*] Overshot the dock. Previous: {previous_distance}, Current: {current_distance}. Moving backward.")
                        alert("Overshot dock, moving backward.", include_screenshot=False)
                        keyboard.press('z')
                        time.sleep(15 * self.multiplier)
                        keyboard.release('z')
                        time.sleep(15)
                    else:
                        logging.info(f"[*] Getting closer. Previous: {previous_distance}, Current: {current_distance}. Moving forward.")
                        alert("Approaching dock, moving forward.", include_screenshot=False)
                        keyboard.press('w')
                        time.sleep(5 * self.multiplier)
                        keyboard.release('w')
                        time.sleep(15)

                previous_distance = current_distance
                time.sleep(3)

            else:
                docking_attempts += 1
                logging.warning(f"[*] End Sail button not found on attempt {docking_attempts}.")
                if docking_attempts > max_attempts:
                     alert("[!] Cannot find End Sail button.", include_screenshot=True)
                time.sleep(3)
                
        logging.error(f"[!] Maximum docking attempts ({max_attempts}) reached. Manual intervention required.")
        alert(f"[!] Maximum docking attempts reached. Manual intervention required.", include_screenshot=True)
        return False
    
    def initial_phase(self):
        logging.info(f"[$] Starting initial phase of {self.autopilot_mode_type.capitalize()} AutoPilot")
        alert(f"Starting initial phase of {self.autopilot_mode_type.capitalize()} AutoPilot", include_screenshot=False)
        
        if self.autopilot_mode_type == "airship":
            routes = AIRSHIP_ROUTES
            logging.info("[$] Using Airship routes.")
        else:
            routes = AIRPORT_ROUTES
            logging.info("[$] Using Boat routes.")
        
        def find_and_click_text(target_text, partial_match=False):
            ocr_text, ocr_results = capture_and_process_screenshot()
            logging.info(f"Checking for '{target_text}' with OCR: {ocr_text}")
            target_text_lower = target_text.lower()
            for res in ocr_results:
                if len(res) > 1 and isinstance(res[1], str):
                    res_text_lower = res[1].lower().strip()
                    if (partial_match and target_text_lower in res_text_lower) or (not partial_match and target_text_lower == res_text_lower):
                        logging.info(f"Found and clicked '{target_text}'. Text on screen: '{res[1]}'")
                        click_center(res[0])
                        return True
            logging.warning(f"[!] Could not find text '{target_text}' to click.")
            return False

        def check_refuel():
            ocr_text, ocr_results = _run_doctr_ocr_on_left_screen()
            logging.info(f"Checking for 'refuel' button with OCR: {ocr_text}")
            for res in ocr_results:
                if len(res) > 1 and isinstance(res[1], str):
                    if "refuel" in res[1].lower():
                        logging.info(f"Found refuel button with text: {res[1]}")
                        click_center(res[0])
                        time.sleep(0.3)
                        click_center(res[0])
                        logging.info("Clicked refuel button.")
                        return True
                else:
                    logging.warning(f"[$] Skipping malformed OCR result item in check_refuel: {res}")
            return False
        
        check_refuel()
        time.sleep(2)

        def perform_maintenance():
            logging.info("Starting new maintenance sequence using WinRT OCR.")
            
            ocr_text, ocr_results = capture_and_process_screenshot()
            logging.info(f"Checking for 'your current vehicle' line with OCR: {ocr_text}")
            vehicle_line_text = None
            vehicle_line_coords = None
            for res in ocr_results:
                if len(res) > 1 and isinstance(res[1], str) and "your current vehicle" in res[1].lower():
                    vehicle_line_coords = res[0]
                    vehicle_line_text = res[1]
                    break

            if not vehicle_line_coords:
                logging.warning("[!] Could not find 'your current vehicle' text for maintenance. Skipping.")
                return True

            logging.info(f"Found vehicle line: '{vehicle_line_text}'. Clicking it to trigger hover effect.")
            click_center(vehicle_line_coords)
            time.sleep(1.5)

            ocr_text_after_hover, ocr_results_after_hover = capture_and_process_screenshot()
            logging.info(f"Checking for '$' with OCR: {ocr_text_after_hover}")
            price_coords = None
            price_text = None
            for res in ocr_results_after_hover:
                if len(res) > 1 and isinstance(res[1], str) and "$" in res[1]:
                    price_coords = res[0]
                    price_text = res[1]
                    break
            
            if not price_coords:
                logging.warning("[!] Could not find any line with '$' after hover. Skipping maintenance.")
                return True

            logging.info(f"Found price line: '{price_text}'. Clicking it.")
            click_center(price_coords)
            time.sleep(2)

            _, ocr_results_doctr = _run_doctr_ocr_on_left_screen()
            logging.info(f"Checking for 'es' with OCR: {_}")
            yes_coords = None
            for res in ocr_results_doctr:
                if (
                    len(res) > 1
                    and isinstance(res[1], str)
                    and res[1].strip().lower().endswith("es")
                ):
                    yes_coords = res[0]
                    break
            
            if not yes_coords:
                logging.warning("[!] Could not find 'yes' confirmation button after clicking price. Skipping final step.")
                return True

            logging.info("Found 'yes' button. Clicking it.")
            click_center(yes_coords)
            time.sleep(2)

            logging.info("Maintenance sequence finished.")
            return True

        if not self.retry_action(perform_maintenance, description="performing maintenance"):
            alert("[!] Maintenance sequence failed. Continuing without maintenance.", include_screenshot=True)

        def check_menu():
            ocr_text, ocr_results = capture_and_process_screenshot()
            return "return to lobby" in ocr_text.lower()
        
        if not self.retry_action(check_menu, description="menu check"):
            logging.error("[!] Must start from lobby menu")
            alert("[!] Must start from lobby menu", include_screenshot=True)
            return False
        
        Aocr_text, Aocr_results = capture_and_process_screenshot()
        
        def click_jobs():
            _, ocr_results_doctr = _run_doctr_ocr_on_left_screen()
            logging.info(f"Checking for 'play' with OCR: {_}")
            play_coords = None
            for res in ocr_results_doctr:
                if len(res) > 1 and isinstance(res[1], str) and "play" in res[1].lower():
                    play_coords = res[0]
                    break

            if not play_coords:
                logging.error("[!] Could not find 'play' button with Doctr OCR.")
                return False

            logging.info(f"Found 'play' button. Clicking it to trigger hover effect.")
            click_center(play_coords)
            time.sleep(1.5)

            _, ocr_results_doctr_after_hover = _run_doctr_ocr_on_left_screen()
            logging.info(f"Checking for 'jobs' with OCR: {_}")
            jobs_coords = None
            for res in ocr_results_doctr_after_hover:
                if len(res) > 1 and isinstance(res[1], str) and "jobs" in res[1].lower():
                    jobs_coords = res[0]
                    break
            
            if not jobs_coords:
                logging.error("[!] Could not find 'jobs' button after hovering 'play'.")
                return False

            logging.info("Found 'jobs' button. Clicking it.")
            click_center(jobs_coords)
            return True
        
        if not self.retry_action(click_jobs, description="clicking jobs button"):
            logging.error("[!] Could not find jobs button")
            alert("[!] Could not find jobs button", include_screenshot=True)
            return False

        airport_matches = []
        
        def find_current_airport():
            nonlocal airport_matches
            airport_matches = []
            for airport in routes.keys():
                if airport in Aocr_text.lower():
                    airport_matches.append(airport)
            return len(airport_matches) == 1
        
        if not self.retry_action(find_current_airport, description="finding current airport"):
            if len(airport_matches) > 1:
                error_msg = f"[!] Multiple airports detected: {', '.join(airport_matches)}"
            else: 
                error_msg = f"[!] No valid airport detected. Ensure you are at a supported departure location for the selected mode."
            logging.error(error_msg)
            alert(error_msg, include_screenshot=True)
            return False
        
        current_airport = airport_matches[0]
        logging.info(f"Found airport: {current_airport}")
        alert(f"Found airport: {current_airport}", include_screenshot=False)

        destinations = routes.get(current_airport, [])
        if not destinations:
            error_msg = f"[!] No routes found for the current airport '{current_airport}' in the selected mode."
            logging.error(error_msg)
            alert(error_msg, include_screenshot=True)
            return False

        best_wp = 0
        best_dest = None
        search_coords = None
        destination_found = False
        
        for attempt in range(3):
            if destination_found:
                break
                
            logging.info(f"Destination finding attempt {attempt+1}/3")
            
            for dest in destinations:
                def click_search():
                    nonlocal search_coords
                    ocr_text, ocr_results = capture_and_process_screenshot()
                    for res in ocr_results:
                        if len(res) > 1 and isinstance(res[1], str):
                            if res[1].strip().lower() == "search":
                                search_coords = res[0]
                                click_center(res[0])
                                logging.info("Clicked search button.")
                                time.sleep(1)
                                keyboard.type(dest)
                                time.sleep(1)
                                return True
                        else:
                            logging.warning(f"[!] Skipping malformed OCR result item in click_search: {res}")
                    return False

                if not self.retry_action(click_search, max_attempts=5, description=f"searching for {dest}"):
                    continue
                    
                def click_transport():
                    time.sleep(3)
                    ocr_text, ocr_results = capture_and_process_screenshot()
                    for res in ocr_results:
                        if len(res) > 1 and isinstance(res[1], str):
                            res_text_no_spaces = res[1].lower().replace(" ", "")
                            search_text_no_spaces = f"transportto{dest}".lower().replace(" ", "")
                            if search_text_no_spaces in res_text_no_spaces:
                                click_center(res[0])
                                logging.info(f"Clicked transport button for {dest}.")
                                return True
                        else:
                            logging.warning(f"[!] Skipping malformed OCR result item in click_transport: {res}")

                    logging.info(f"OCR results when looking for transport to {dest}:")
                    for res in ocr_results:
                        if len(res) > 1 and isinstance(res[1], str):
                            logging.info(f"OCR text: {res[1]}")
                        else:
                            logging.info(f"[!] Malformed OCR result: {res}")
                    return False
                
                if not self.retry_action(click_transport, max_attempts=5, description=f"selecting transport to {dest}"):
                    if search_coords:
                        x = int((search_coords[0][0] + search_coords[2][0]) / 2)
                        y = int((search_coords[0][1] + search_coords[2][1]) / 2)
                        cross_mouse.left_click_xy_natural(x, y, delay=0.3, min_variation=-3, max_variation=3,
                                        use_every=4, sleeptime=(0.005, 0.009), print_coords=False, percent=90)
                        time.sleep(0.5)
                        
                        for _ in range(40):
                            keyboard.press(Key.backspace)
                            time.sleep(0.05)
                            keyboard.release(Key.backspace)
                        for _ in range(40):
                            keyboard.press(Key.delete)
                            time.sleep(0.05)
                            keyboard.release(Key.delete)
                        time.sleep(0.5)
                    continue
                
                wp_found = False
                def get_wp_value():
                    nonlocal best_wp, best_dest, wp_found
                    ocr_text, ocr_results = capture_and_process_screenshot()
                    wp_match = re.search(r"wp:\s*(\d+)", ocr_text.lower())
                    if wp_match:
                        wp = int(wp_match.group(1))
                        logging.info(f"Found WP: {wp} for destination: {dest}")
                        if wp > best_wp:
                            best_wp = wp
                            best_dest = dest
                        wp_found = True
                        return True
                    return False
                
                if self.retry_action(get_wp_value, max_attempts=3, description=f"getting WP value for {dest}"):
                    destination_found = True
                
                if search_coords:
                    x = int((search_coords[0][0] + search_coords[2][0]) / 2)
                    y = int((search_coords[0][1] + search_coords[2][1]) / 2)
                    cross_mouse.left_click_xy_natural(x, y, delay=0.3, min_variation=-3, max_variation=3,
                                    use_every=4, sleeptime=(0.005, 0.009), print_coords=False, percent=90)
                    time.sleep(0.5)
                    
                    for _ in range(40):
                        keyboard.press(Key.backspace)
                        time.sleep(0.05)
                        keyboard.release(Key.backspace)
                    for _ in range(40):
                        keyboard.press(Key.delete)
                        time.sleep(0.05)
                        keyboard.release(Key.delete)
                    time.sleep(0.5)
            
            if not destination_found and attempt < 2:
                logging.info("[!] No destinations found, refreshing the jobs page")
                if not self.retry_action(click_jobs, description="refreshing jobs page"):
                    logging.error("[!] Failed to refresh jobs page")
                time.sleep(3)
        
        if not best_dest:
            logging.error("[!] Could not find any valid destinations, refreshing the jobs page")
            alert("[!] Could not find any valid destinations, refreshing the jobs page", include_screenshot=True)
            if not self.retry_action(click_jobs, description="refreshing jobs page"):
                logging.error("[!] Failed to refresh jobs page")
            time.sleep(3)
        
        logging.info(f"Best destination: {best_dest} with WP: {best_wp}")
        alert(f"Best destination: {best_dest} with WP: {best_wp}", include_screenshot=False)

        def select_best_job():
            if not search_coords:
                logging.error("[!] Did not find search coordinates during discovery phase. Cannot select best job.")
                return False
            
            click_center(search_coords)
            logging.info("Clicked saved 'search' button location.")

            time.sleep(0.5)
            keyboard.type(best_dest)
            time.sleep(1)

            ocr_text, ocr_results = capture_and_process_screenshot()
            transport_found = False
            for res in ocr_results:
                if len(res) > 1 and isinstance(res[1], str):
                    res_text_no_spaces = res[1].lower().replace(" ", "")
                    search_text_no_spaces = f"transportto{best_dest}".lower().replace(" ", "")
                    if search_text_no_spaces in res_text_no_spaces:
                        click_center(res[0])
                        logging.info(f"Selected transport for best job: {best_dest}.")
                        transport_found = True
                        break

            x = int((search_coords[0][0] + search_coords[2][0]) / 2)
            y = int((search_coords[0][1] + search_coords[2][1]) / 2)
            cross_mouse.left_click_xy_natural(x, y, delay=0.3, min_variation=-3, max_variation=3,
                            use_every=4, sleeptime=(0.005, 0.009), print_coords=False, percent=90)
            time.sleep(0.5)
            for _ in range(40):
                keyboard.press(Key.backspace)
                time.sleep(0.05)
                keyboard.release(Key.backspace)
            for _ in range(40):
                keyboard.press(Key.delete)
                time.sleep(0.05)
                keyboard.release(Key.delete)
            time.sleep(0.5)

            if not transport_found:
                logging.error(f"[!] Could not find transport button for {best_dest} after typing in search.")
                return False

            return True
        
        if not self.retry_action(select_best_job, description="selecting best job"):
            logging.error("[!] Could not select the best job")
            alert("[!] Could not select the best job", include_screenshot=True)
            return False
        
        def click_begin():
            ocr_text, ocr_results = capture_and_process_screenshot()
            for res in ocr_results:
                if len(res) > 1 and isinstance(res[1], str):
                    if "begin" in res[1].lower():
                        click_center(res[0])
                        logging.info("Clicked begin button.")
                        return True
                else:
                    logging.warning(f"[!] Skipping malformed OCR result item in click_begin: {res}")
            return False
        
        if not self.retry_action(click_begin, description="clicking begin"):
            logging.error("[!] Could not find begin button")
            alert("[!] Could not find begin button", include_screenshot=True)
            return False
        
        time.sleep(10)
        keyboard.press('e')
        keyboard.release('e')
        logging.info("[*] Engine started")
        alert("'e' key pressed to start engine", include_screenshot=False)

        time.sleep(30)
        
        self.finished.emit(True)
        return True
    
    def run(self):
        try:
            time.sleep(5)
            logging.info(f"[$$] AutoPilot {'final' if self.is_final_phase else 'initial'} phase started")
            
            if self.is_final_phase:
                success = self.final_phase()
            else:
                success = self.initial_phase()
                
            if not success:
                self.finished.emit(False)
            
        except Exception as e:
            logging.error(f"[!] Boat AutoPilot Error: {str(e)}")
            alert(f"[!] Boat AutoPilot Error: {str(e)}", include_screenshot=True)
            self.finished.emit(False)

def check_for_end_sail():
    ocr_text, ocr_results = capture_and_process_screenshot()
    for res in ocr_results:
        if len(res) > 1 and isinstance(res[1], str):
            if "end sail" in res[1].lower():
                bbox = res[0]
                x = int((bbox[0][0] + bbox[2][0]) / 2)
                y = int((bbox[0][1] + bbox[2][1]) / 2)
                
                button_region = pyautogui.screenshot(region=(x-20, y-10, 40, 20))
                button_rgb = numpy.array(button_region)
                
                avg_red = numpy.mean(button_rgb[:, :, 0])
                avg_green = numpy.mean(button_rgb[:, :, 1])
                avg_blue = numpy.mean(button_rgb[:, :, 2])
                
                is_red = avg_red >= 250
                logging.info(f"End Sail button RGB averages - Red: {avg_red:.1f}, Green: {avg_green:.1f}, Blue: {avg_blue:.1f}. Is red (>=250): {is_red}")
                
                if not is_red:
                    logging.info("End Sail button is NOT red - clicking it")
                    click_center(res[0])
                    time.sleep(0.5)
                    click_center(res[0])
                    logging.info("Successfully clicked 'End Sail' button")
                    return res[0], False
                else:
                    logging.info("End Sail button IS red (cannot be clicked yet) - NOT clicking")
                    return res[0], True
        else:
            logging.warning(f"[!] Skipping malformed OCR result item in check_for_end_sail: {res}")

    return None, False