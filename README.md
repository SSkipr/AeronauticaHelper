# 👉 SimpleAeronauticaHelper Setup 👈
This is an program that watches and pilots your boat in Aeronautica! You will get a status update with a screenshot via the webhook. There is also built-in Anti-AFK.

#### For more features, check out the [main branch](https://github.com/SSkipr/AeronauticaHelper). This branch has only basic autopilot and webhook functionality.
---

## 🧾 Functionality

As previously stated, the application will recognize the following and send alerts via the designated webhook with a screenshot every 30mins (time can be changed)

**AutoSteer** gets the current bearing and matches it to the destination. Automated keystrokes are then performed to adjust accordingly. 

**Essentially, assuming everything works properly, you will pull out your ship to open sea and come back when you when you see it has reached the destination.**

---

## Installation/Setup


### **This code is supported by both Windows and MacOS!**

It is currently untested on Linux.


### 1. **Python Environment**

- **Python Version:** 
  Make sure you have Python 3.7 or higher installed. You can download it from [python.org](https://www.python.org/downloads/).

### 2. **Install the program**
  Either navigate to "SimpleAeroHelperMain.py" and download the raw file, or download [here](https://downgit.github.io/#/home?url=https://github.com/SSkipr/AeronauticaHelper/raw/refs/heads/Simple/SimpleAeroHelperMain.py) and unzip.

### 3. **Configuration**
 - ####  These variables are at the top of the code. You will need a code/text editor (notepad/textedit will work fine, keep it as a .py) to edit these. There are defaults. The variables are as follows:

 - **CYLCE_INTERVAL** This determines how often the program will run it's main loop (autosteer and anti-afk) in seconds. There is a maximum of 19m as otherise you will get disconnected for being AFK

 - **WEBHOOK_INTERVAL** This determines how often a screenshot will be sent to your webhook in seconds

 - **TURNING_MULTIPLIER** This is multiplied with the base steering speeds. Increase for larger ships but ensure it doesn't auscultate (go back and forth). The boat will reach the target eventually, so this isn't very important

 - **WEBHOOK_URL** This is the webhook url for sending screenshots. See [this tutorial](https://www.youtube.com/watch?v=xIZXDdVwNaE). This is optional.

##### An example of configured variables
 ![configured variables](https://cdn.discordapp.com/attachments/1349769873282175037/1431328076498862191/image.png?ex=68fd03a6&is=68fbb226&hm=9c0c338f9b292529fcdf2e836da63a79f31d2c9b3be92ba5352b5b7804f2571c)

### 4. **Ingame Preperation**

- You will need a boat job active. Then just pull out to open seas with a straight route and point in the general direction of your destination

### 5. **Run the code** 

- On mac you may need to run  ``` bash /Applications/Python*/Install\ Certificates.command ``` in a terminal first or you will get a error

---

### **FAQ**

* Q: How does it work?

   A: SimpleAeroHelper works by taking screenshots of the TRK and HDG at the top of the screen, processing them into text then performing inputs if turning is needed. The centre of the screen will occasionally be clicked to avoid being kicked for AFK

* Q: Can I use waypoints?

   A: Theoretically, you will steer towards whatever your target is, however waypoints in boats have known to be glitchy and are solid at sea level, so you may run into problems.

## ☝️ Please Note:


- It is generally best practice to get a good multiplier in an older server, then save and go AFK in a server in which the server's age is minimal.

- The program is setup to use the deafult keybinds; A and D.

- Currently the only supported resolutions are 720p, 1080p, 1440p (2k) and 4k



## 🗣️ Latest Version: 1.1
Added full Windows support, auto-install of required packages, removed auto-stopping and more

### For additional support, DM SSkipr (sskipr) or person 12 (person_number_12) on discord.


# Aerohelper (V2 main branch at the time of this screenshot) has been cleared by Aeronautica staff.

![AeroHelperV2Approved](https://github.com/user-attachments/assets/0778f8ec-c958-479e-938d-5bea5166b56b)
