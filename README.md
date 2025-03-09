# AeronauticaHelper Setup

### 1. **Python Environment**

- **Python Version:**  
  Make sure you have Python 3.7 or higher installed. You can download it from [python.org](https://www.python.org/downloads/).

---

### 2. **Required Libraries**

This project uses several Python packages:

- **PyAutoGUI:**  
  For capturing screenshots of your computer screen.
  
- **EasyOCR:**  
  For performing Optical Character Recognition (OCR) on the screenshots. Unlike Tesseract, EasyOCR doesn’t require additional external installations.
  
- **NumPy:**  
  To convert the screenshot (from a PIL image) into a NumPy array that EasyOCR can process.
  
- **Requests:**  
  To send HTTP requests, specifically to send alerts via a Discord webhook.
---

### 3. **Installing Dependencies**

Use pip to install the required libraries. In your terminal or command prompt run:

```bash
pip install pyautogui easyocr numpy requests
```
or
```bash
py -m pip install pyautogui easyocr numpy requests
```
---

### 4. **Setup**

- **Webhook URL:**  
  The code sends alerts to a Discord channel using a webhook. Replace the `WEBHOOK_URL` constant in the code with your actual Discord webhook URL:
  ```python
  WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
  ```
  Replace `SHIP_TOP_SPEED` with the corresponding speed. Customize `CYCLE_INTERVAL` and `LEEWAY` to your desire.
---

### 5. **Project Structure**

Your project might look like this:
```
/YourProjectFolder
├── AeroHelperMain.py    # Contains the application code
├── distance_log.txt     # Log file created by the application
└── README.md            # (Optional) Documentation for your project
```

- **AeroHelperMain.py:**  
  This file will contain the complete Python code provided. It includes:
  - Configuration constants.
  - Functions to capture screenshots, perform OCR, extract the distance, and send alerts (with an attached screenshot when needed).
  - The main loop that ties everything together, running at a fixed interval (or dynamically based on elapsed time).

- **distance_log.txt:**  
  This log file will be created by the application to store timestamps, OCR output, and any alerts sent.

---

### 6. **Running the Application**

**Run the Script:**  
   In your terminal or command prompt, navigate to your project directory and run:
   ```bash
   python AeroHelperMain.py
   ```

  For enhanced results, consider positioning your camera below the ship (for more OCR clarity)
  ![AeroHelperDemo](https://github.com/user-attachments/assets/9446c1ef-afa7-4377-a426-c6cf99e3c2a9)

---

### Questions or concerns? [DM me on Discord!](https://discord.gg/3adphMca)

---

# DISCLAIMER: BY USING THIS "SCRIPT", YOU ACKNOWLEDGE THE RISKS INVOLVED AND AGREE THAT I AM NOT RESPONSIBLE FOR ANY CONSEQUENCES THAT MAY ARISE FROM ITS USE. USE THIS TOOL AT YOUR OWN DISCRETION. THIS HAS NOT BEEN CLEARED WITH AERONAUTICA STAFF, *YET*
