⚠️ **SOON**


# <img src="https://github.com/user-attachments/assets/5dd9d0a5-c24b-4b94-9afa-a9692a72e46f" width="25" height="25" alt="AeroHelperLogo" /> AeronauticaHelper

## 🚀 Introduction

Welcome to **AeronauticaHelper** – your all-in-one AFK automation companion for [Aeronautica](https://www.roblox.com/games/6647962258/UPD-Aeronautica), the ship/aircraft simulator on Roblox. Whatever your feelings are about AeroHelper, throw them out the window! Everything is different!

This is not an exploit, nor malware. It's fully **open source**, and functions by:
- Taking a **screenshot**
- Processing it with **OCR**
- Extracting values using **regex**
- Simulating **human-like mouse and keyboard actions**
---

## 🧾 Features

### 🚢 Boat AutoPilot

Boat AutoPilot allows you to AFK full job cycles by:
- Refueling
- Performing turnaround maintenance
- Accepting the highest-paying job
- Starting the boat
- Steering the ship
- Ending the route
- Repeating

It currently supports select routes between airports that allow straight-line navigation.
<details><summary>🌍 Supported Boat Routes</summary>

**Long-Haul:**
- Leovetsk ⇄ Tikaranto
- Leovetsk ⇄ Auchenburgh
- Eisenhardt Municipal ⇄ Auchenburgh
- Nordspyd ⇄ Norman
- Nordspyd ⇄ Udyanapura
- Kapa ⇄ Hipe
- Umibutsu ⇄ Hipe
- Tenera Palm ⇄ Nordspyd

**Express:**
- Leovetsk ⇄ Kitesboro
- Rawaki ⇄ Harden
- Rawaki ⇄ Amaras

<img width="1075" height="1084" alt="v3 5Routes" src="https://github.com/user-attachments/assets/431504c0-f077-4e24-befb-7e034119d1e8" />

</details>

##

### 🛩️ Airship AutoPilot

This works similarly to the Boat AutoPilot but includes altitude control. After the airship is spawned via AutoPilot, it will first rise to 500 feet above the terrain below. Then, it will ascend to a user-defined altitude above sea level. Once the airship is 10 nautical miles from its destination, it will descend to 100 feet above the terrain.

<details><summary>↗️ Supported Airship Routes</summary>

- **Nordspyd ⇄ Valois**

</details>

##

🕧 "Start AutoPilot Mid Mission" briefly skips the vehicle spawning sequence once.
##

### 🧭 AutoSteer
Lines up your vehicle to match a target **bearing**. Uses OCR to calculate angle difference and applies smart turns via keypresses.

> Especially useful when navigating through multiple waypoints or tight paths. **Customize Aeronautica's in-game flight plan, and AeroHelper will follow the path!** (assuming this [issue](https://github.com/SSkipr/AeronauticaHelper/issues/10) is resolved)

##

### 💥AutoRejoin (\Relaunch)
Disconnected? Roblox crash? No worries – AeroHelper detects this and will:
- Quit the Roblox application
- Rejoin and continue the job at hand

##

### 📢 Webhook Alerts

Sends alerts through your webhook when:
- Disconnected
- Crashed
- Fuel low/depleted
- Collision or obstruction
- OCR issues
- ETC

Critical alerts get an `@everyone` ping. Optional debug alerts can be toggled in the app under 'Verbose Notifications'.

### 🔍 Feature Support Matrix

| Feature              | Boat 🚢 | Airship 🎈 | Aircraft ✈️ | Helicopter 🚁 |
|----------------------|--------|------------|-------------|---------------|
| AutoPilot            | ✅     | ✅         | ❌          | ❌            |
| AutoSteer            | ✅     | ✅         | ✅          | ❌            |
| AutoRejoin           | ✅     | ✅         | ✅          | ✅            |
| Webhook Alerts       | ✅     | ✅         | ✅          | ✅            |
| Anti-AFK             | ✅     | ✅         | ✅          | ✅            |

---

## 🛠️ Installation Guide (or [>> Download <<](https://github.com/SSkipr/AeronauticaHelper/releases) the compiled version)

### ✅ Supported OS:
- Windows

*MacOS Support has been dropped. I am extremely sorry for the inconvenience. If you or someone you know can make this work on Mac, reach out to me!*

### 1️⃣ Python Setup
Install **[Python 3.11.3](https://www.python.org/downloads/release/python-3113/)**

### 2️⃣ Install Required Libraries

Execute the following command in your CMD terminal:

```bash
py -m pip install PyQt5 requests pyautogui pynput psutil Pillow numpy mousekey winsdk "python-doctr[torch]" pygetwindow torch
```

### 3️⃣ Download and Setup
Grab the repo:  
[Download ZIP](https://github.com/SSkipr/AeronauticaHelper/archive/refs/heads/Standard.zip)

Your folder should look like:

```
/AeronauticaHelper
├── app.py (main)
├── core.py
├── autopilot.py
├── data.txt (after running application)
├── log_data.txt (after running application)
├── LICENSE.md
├── README.md
└── ETC...
```

### 4️⃣ Running the App
**If you have previous experience running Python files, just run ```app.py```, if not:**

Right click ```app.py``` and select 'Edit with Python IDE'

At the top of the newly opened window, click 'Run'

Then click 'Run Module'

---

## 🆕 Version 3.6 Highlights
- **Fixed:**
  - Auchenburgh AutoPilot spelling bug
  - Fuel extraction regex bug  
  - Clicking 'End Sail' on red bug
  - Different OS language issues (?)
  - Webhook notifications bug
  - Waypoint locking (targets other than DEST) bug (still waiting for Fly to [fix](https://github.com/SSkipr/AeronauticaHelper/issues/10) the in-game bug though...)
  - UI performance bug
  - Import minimal libraries

 - Removed Eisenhardt Municipal ⇄ Tikaranto Boat AutoPilot Route



### Version 3.5 Highlights
- 💥 Airship AutoPilot
  - With customizable Altitude & Fuel Percentage
- 👁️ New OCRs (hopefully this puts all the OCR errors to rest!)
  - 🌙 Because the OCR works better at night with nightvision on, AeroHelper enables nightvision from 16:00-06:00
  - Recently, I've learned that OCR Engines degrade over time without proper care... If the error rate is high, AeroHelper will take a brief break to reinitialize and clear the caches
  - Bearings are used when detected twice in a row
- 🚢 Revamped Boat AutoPilot
- 📷 Images are upscaled & greyscaled before OCR processing
- 🎯 New Boat AutoPilot Routes (thanks Yowane Haku)
- 🔨 Auto Maintenance
- 🔁 AutoRejoin now handles Roblox crashes
- 👋 AeroHelper minimizes after starting
- ⛽ Low fuel warning
- ↔️ Auscultation detection and warning
- ℹ️ New UI
- 📢 Feedback to Developer
- 🤚 Need Help button
- 📰 Issues & News
- ❌ AutoPilot incorrect lobby alert
- ⚠️ [Need Help](https://aeronautica-helper.vercel.app/help) redirect
- 🔢 Decimals now work in the UI
- ➕ And more!

### Version 3 Highlights
- 🚤 Full Boat AutoPilot
- 🎈 Airship AutoSteer support
- 🔁 AutoRejoin across all vehicle types
- 🎯 Precision Docking (AutoPilot)
- 🤫 Auto hide player list/chat
- 🧠 Smarter crash detection
- 🚫 Excludes "WINDY" and "KNOTS" from bearing calculations
- 🧮 Accepts negative distances (waypoints behind the ship)
- 📉 Sends error alerts if movement > 20 or < -20
- 🕵️ Anonymous Data Sharing

---

## 🙋 FAQ

Visit our dedicated [help page](https://aeronautica-helper.vercel.app/help) for help regarding anything AeroHelper related. 
If it is an installation issue, I recommend consulting ChatGPT as it is extremely helpful and, unlike me, responds instantly.
---

## 📡 Anonymous Data Sharing (Optional)

If enabled, this will send:
- Your `data.txt`
- `log_data.txt`
- Webhook URL

Used only for **bug reports and troubleshooting.** You may be contacted (via your webhook) with fixes or follow-up questions. Logs are not stored long-term.

---

## 📎 Useful Links

💻 [AeroHelper Website](https://aeronautica-helper.vercel.app/)

🚢 [Boat AutoPilot Map](https://github.com/user-attachments/assets/707a9f5d-f00a-4271-9bce-3adf071a4e04)


---

## ⭐ Support Us!

If you find this tool useful:
- Leave a ⭐ on the repo
- Follow the project
- Submit issues or ideas via [GitHub](https://github.com/SSkipr/AeronauticaHelper/issues) or [@sskipr](https://discord.gg/3adphMca)

**Thanks for using AeroHelper ❣️**

---

## 📈 Roadmap

- AI Plane Pathfinding (~v4)

---

# Contribution

My appreciation for all of the contributors cannot be overstated. A special thanks to the Python libraries that made this project possible! Thank you all!

<a href="https://github.com/SSkipr/AeronauticaHelper/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=SSkipr/AeronauticaHelper" />
</a>


### **SSkipr** - Lead Developer

### **Person-12** - Contributor

### **She3pd0g** - Contributor

### **muffin.** - QA Tester


## Prominent Libraries:

Doctr - OCR Engine

Winrt - OCR Engine

Mousekey - Input Control

Numpy - Data Processing

PIL - Image Processing

Psutil - System Information

Pynput - Input Control

Pyautogui - Automation

PyQt5 - User Interface

Requests - HTTP Library

Torch - ML Framework

GC - Memory Access


## Libraries:

Asyncio
Datetime
Importlib
IO
JSON
Logging
Math
OS
Pathlib
Platform
Random
RE
Subprocess
SYS
Threading
Time
UUID
Webbrowser
