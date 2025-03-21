# This is the Next-Version branch, meaning this code is often *incomplete, obsolete, or unsafe* to use. Please head to the [main branch](https://github.com/SSkipr/AeronauticaHelper) unless you plan to contribute to this project.


# 👉 AeronauticaHelper Setup 👈
This is an application that watches your AFK boat in Aeronautica! You will get a notification via the webhook if the game crashes, if you disconnect, or if your boat suddenly stops (island collision, out of fuel, etc), accompanied by a screenshot. Though possible, errors occur minimally when the camera is positioned properly. **Version 2 introduces AutoSteer** and built-in Anti-AFK.

---

## 🧾 Functionality

As previously stated, the application will recognize the following and send alerts via the designated webhook with a screenshot to better asses the issue:
- Disconnect from game
- Boat stops (island collision, out of fuel, etc)
- Game crashes
- When you approach the destination (the ship will stop too)

Urgent alerts, such as the cases above, will include an @everyone ping, while (non-urgent) alerts will not receive a ping. You can disable regular, non-urgent alerts in the application.

**AutoSteer** gets the current bearing and matches it to the destination. Automated keystrokes are then performed to adjust accordingly.⭐**Essentially, assuming everything works properly, you will pull out your ship to the open sea and come back when you get a notification.**

---

## 🪟🍎 Installation

**This code is supported by both Windows and MacOS!**
If you are not using the [compiled version](https://github.com/SSkipr/AeronauticaHelper/releases), you must follow the instructions below (if you have previous Python experience, feel free to skip around):

### 1. **Python Environment**

- **Python Version:** 
  Make sure you have installed Python 3.7 or higher. You can download it from [python.org](https://www.python.org/downloads/).

### 2. **Installing Dependencies**

**Normally, the program will install any required libraries for you upon first launch.** However, if you want to install the libraries yourself, please follow the instructions below.

In your terminal or command prompt, run:

```bash
pip install pyautogui easyocr numpy requests pynupt PyQt5
```
or
```bash
py -m pip install pyautogui easyocr numpy requests pynput PyQt5
```

### 3. **Project Structure**

Your project might look like this:
```
/AeronauticaHelper
├── AeroHelperMain.py    # Contains the application code
├── log_data.txt         # Log file created by the application
├── LICENSE.md           # Repo's license
└── README.md            # (Optional) Documentation
```

- **AeroHelperMain.py:**  
  This file will contain the complete Python code provided. It includes:
  - Configuration constants.
  - Functions to capture screenshots, perform OCR, extract the distance, and send alerts (with an attached screenshot when needed).
  - The main loop that ties everything together, running at a fixed interval (or dynamically based on elapsed time).

- **log_data.txt:**  
  The application will create this log file to store timestamps, OCR output, and any alerts sent.


### 4. **Running the Application**

**Run the Code:**  
   In your terminal or command prompt, navigate to your project directory and run:
   ```bash
   python AeroHelperMain.py
   ```
  or
   ```
   py -m python AeroHeperMain.py
   ```

   You can also open it in a code editor (such as VS Code) and run it there.

  ---

## ☝️ Please Note

- For enhanced (OCR) results, consider doing the following:
    - If you ARE using Autosteer, you MUST use camera 5.
    - If you are NOT using AutoSteer, consider positioning your camera below the ship (for more OCR clarity).
    - Turn ROBLOX's Graphics Quality to the LOWEST option, as this makes the water's color more consistent (for whatever reason), leading to enhanced OCR clarity.
    - Set Aeronautica's in-game 'User Interface Scale' to MAX (2).

- It is generally best practice to get a good multiplier in an older server, then save and go AFK in a server in which the server's age is minimal.

- Set up your webhook in a channel/server with only you, as notifications should be set to all messages, which will ping all with access to the channel!

- Close the chat/player list so others can't mess up your mission!

- Some boats turn quicker than others (though it may take longer); they will all reach the target. Customize the `MULTIPLIER` to your ship's liking; ensure it doesn't auscultate.

- The script is set up to use the default key binds and metrics: A, D, Z, Knots, and Nautical Miles.

- If you enjoy our code, please ⭐ and 👁️ the repo!

---

## 🗣️ Latest Version: 2.4

- Installation Assistant

- [Compiled Version](https://github.com/SSkipr/AeronauticaHelper/releases)

- MacOS Support!

- UI

- QoL Improvements

Enjoy!

---

## 📈 Upcoming Features

- Full AutoPilot (v3)?

- AI Pathfinding (v4)

---

### Questions or concerns? [DM me on Discord @sskipr](https://discord.gg/3adphMca)

---

# THIS CODE HAS BEEN CLEARED WITH AERONAUTICA STAFF. THIS IS 100% SAFE TO USE.
![AeroHelperV2Approved](https://github.com/user-attachments/assets/0778f8ec-c958-479e-938d-5bea5166b56b)
