# 👉 AeronauticaHelper Setup 👈
This is an application that watches your AFK boat in Aeronautica! You will get a status update with a screenshot via the webhook every 30mins (time can be changed). There is built-in Anti-AFK.

---

## 🧾 Functionality

As previously stated, the application will recognize the following and send alerts via the designated webhook with a screenshot every 30mins (time can be changed) and stop the boat when it is within a certain distance from the destination (can be changed)

**AutoSteer** gets the current bearing and matches it to the destination. Automated keystrokes are then performed to adjust accordingly.⭐**Essentially, assuming everything works properly, you will pull out your ship to open sea and come back when you when you see it has reached the destination.**

---

## Installation:

### 1. **Python Environment**

- **Python Version:** 
  Make sure you have Python 3.7 or higher installed. You can download it from [python.org](https://www.python.org/downloads/).

### 2. **Installing Dependencies**

Use pip to install the required libraries. In your terminal or command prompt, run:

```bash
pip install pyautogui easyocr numpy requests pynupt
or
```bash
py -m pip install pyautogui easyocr numpy requests pynput
```

### 3. **Project Structure**

Your project might look like this:
```
/AeronauticaHelper
├── SimpleAeroHelperMain.py    # Contains the application code
├── log_data.txt         # Log file created by the application
└── README.md            # (Optional) Documentation for your project
```

- **SimpleAeroHelperMain.py:**  
  This file will contain the complete Python code provided. It includes:
  - Configuration constants.
  - Functions to capture screenshots, perform OCR, extract the distance, and send updates.
  - The main loop that ties everything together, running at a fixed interval (or dynamically based on elapsed time).

- **log_data.txt:**  
  This log file will be created by the application to store timestamps, OCR output, and any messages sent.


### 4. **Configuration**

  **Configure settings to your liking in the code (under configuration and logging setup)**

  - CYCLE_INTERVAL  (Cycle interval in seconds. 15-120 secs is recommended)

  - STOP_DISTANCE  (Stop distance in your units selected ingame)

  - WEBHOOK_INTERVAL  (Webhook interval in seconds, set to 10m minimum)

  - STEERING_MULTIPLIER  (Steering multiplier, keep close to 1 and don't exceed 3. Use bigger multipliers for slower-turning ships)

  - WEBHOOK_URL  (your webhook URL for updates)


### 5. **Running the Application**

**Run the Code:**  
   In your terminal or command prompt, navigate to your project directory and run:
   ```bash
   python AeroHelperMain.py
   ```

   You can also open in a code editor (such as vscode or pycharm) and run it there

  ---

## ☝️ Please Note:

- It is generally best practice to get a good multiplier in a older server, then save and go AFK in a server in which the server's age is minimal.

- Setup your webhook in a channel/server with only you, as notifications should be set to all messages, which will ping all with access to the channel!

- Some boats turn quicker than others (though it may take longer); they will all reach the target. Customize the `TURNING_MULTIPLIER` to your ship's liking; ensure it doesn't auscultate (go back and forth).

- If you enjoy our code, please ⭐ and 👁️ the repo!

---

## 🗣️ Latest Version: 1.0

Enjoy!

---

### Questions or concerns? [DM me on Discord!](https://discord.gg/3adphMca)

---

# THIS CODE HAS BEEN CLEARED WITH AERONAUTICA STAFF. THIS IS 100% SAFE TO USE.
![AeroHelperV2Approved](https://github.com/user-attachments/assets/0778f8ec-c958-479e-938d-5bea5166b56b)
