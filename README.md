<div align="center">

  <h1>
    <img src="https://github.com/user-attachments/assets/5dd9d0a5-c24b-4b94-9afa-a9692a72e46f" width="25" height="25" alt="AeroHelperLogo" />
    AeronauticaHelper
  </h1>

  <p>
    <a href="https://github.com/SSkipr/AeronauticaHelper/releases"><img src="https://img.shields.io/badge/Version-4.1.4-blue" alt="Version"></a>
    <a href="https://github.com/SSkipr/AeronauticaHelper"><img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-0078D6" alt="Platform"></a>
    <a href="https://discord.gg/acdQ6BFrFs"><img src="https://img.shields.io/badge/Discord-Join-5865F2" alt="Discord"></a>
  </p>

  <p>
    <a href="https://github.com/SSkipr/AeronauticaHelper/releases"><strong>⭐ Download v4</strong></a>
    &nbsp;·&nbsp;
    <a href="https://aeronautica-helper.vercel.app/"><strong>🌐 Visit the Website</strong></a>
  </p>

</div>

## 🚀 Introduction

Welcome to **AeroHelper** – your all-in-one AFK automation companion for [Aeronautica](https://www.roblox.com/games/6647962258/UPD-Aeronautica), the ship/aircraft simulator on Roblox.

If you used AeroHelper before, throw your expectations out the window. Everything has been rewritten from scratch: cleaner architecture, more reliable OCR, faster cycling, and a significantly smarter AutoPilot.

This is **not** an exploit or malware. It is fully **open source**, and works by:

- Taking a **screenshot**
- Processing it with **OCR**
- Extracting values using **regex**
- Simulating **human-like mouse and keyboard actions**

## 🧾 Features

### 🚢 Boat AutoPilot

Handles complete AFK job cycles including:

- Detecting your current airport
- Performing turnaround maintenance
- Evaluating and selecting the highest-paying available route
- Starting the vessel
- Steering to destination (AutoSteer)
- Precision docking and ending the route
- Repeating indefinitely

<details><summary>🌍 Supported Boat Routes</summary>

- Leovetsk ⇄ Auchenburgh
- Leovetsk ⇄ Tierdam
- Sandris ⇄ Tenang
- Norman ⇄ Pembroke Plantation
- Norman ⇄ Hemera Sound

<img width="1075" height="1084" alt="v3 5Routes" src="https://aeronautica-helper.vercel.app/v4AutoPilotRoutes.png" />

</details>

### 🧭 AutoSteer

Lines up your vehicle to match a target **bearing** using OCR-read headings. Applies smooth, human-like turns via timed key presses.

> Works across boats, airships, and aircraft. Especially useful with [multi-waypoint](https://aeronautica-helper.vercel.app/help#custom-waypoint-mission-guide) flight plans.

### 💥 AutoRejoin

Disconnected or crashed? AeroHelper detects this and will:

- Quit the Roblox application
- Rejoin and resume the current job

### 📡 Monitoring

Keeps AeroHelper watching your vehicle without running full AutoPilot. Useful for manual flights where you just want alerts if something goes wrong.

### 📢 Webhook Alerts

Sends real-time alerts to your Discord webhook when:

- Disconnected or crashed
- Fuel low or depleted
- Collision or obstruction detected
- OCR issues arise
- Missions complete
- etc...

---

## 🛠️ Installation

### ✅ Supported OS

- **Windows**
- macOS *(may experience more bugs and feature mismatch due to the lack of support)*


# [Download](https://github.com/SSkipr/AeronauticaHelper/releases) the Compiled Version (high recomended)

or use the manual installation:

### 1️⃣ Install Python

Install **[Python 3.11](https://www.python.org/downloads/release/python-3113/)** - make sure to check **"Add Python to PATH"** during setup.

### 2️⃣ Install Dependencies

Open a terminal in the project folder and run:

```bash
py -m pip install -r requirements.txt
```

Or let AeroHelper do it for you - it will prompt you on first launch if anything is missing.

### 3️⃣ Download

[Download ZIP](https://github.com/SSkipr/AeronauticaHelper/archive/refs/heads/main.zip) and extract it, or clone the repo:

```bash
git clone https://github.com/SSkipr/AeronauticaHelper.git
```

Your folder structure should look like:

```
/AeronauticaHelper
├── AeroHelper/
│   ├── main.py          ← entry point
│   ├── config.py
│   ├── automation/
│   ├── input/
│   ├── ocr/
│   ├── ui/
│   └── utils/
├── AeroHelper.env       ← created on first run
├── AeroHelper.log       ← created on first run
├── requirements.txt
└── README.md
```

### 4️⃣ Run

```bash
py -m AeroHelper
```

Or right-click `AeroHelper/main.py` → *Edit with IDLE* → *Run → Run Module*.

On macOS, use `python3 -m pip install -r requirements.txt` and `python3 -m AeroHelper` instead of `py`.

### 🍎 macOS setup (experimental)

#### 1.1 SSL certificates

If you installed Python from [python.org](https://www.python.org/downloads/) on Mac, you *may* need to do this before `pip install` works:

1. Open **`/Applications/Python 3.x`** in Finder (`3.x` = your version, e.g. `Python 3.11`).
2. Double-click **`Install Certificates.command`**. A Terminal window opens and installs the required certificates.

    ![Install Certificates on macOS](https://github.com/user-attachments/assets/d41ea9b3-23ec-4a12-9ab6-793b75e2c779)

Not using Python from python.org? Skip this step.

#### 1.2 System permissions

Grant permissions in **System Settings → Privacy & Security**:

- **Accessibility** - enable AeroHelper (or Terminal/Python if running from source)
- **Screen Recording** - needed for screenshots and OCR

If macOS prompts you on first launch, click **Allow**, then restart AeroHelper.

#### macOS limitations

- **Human-intervention pause** is not available - use **Stop** to end automation.
- **Auto App Shutdown** is Windows-only.
- If Roblox does not come to the front after **Start**, click it after beginning automation.

More help: **[Help Page → macOS setup](https://aeronautica-helper.vercel.app/help#macos-setup)**

---

## 🆕 Version 4 Highlights

### v4.1.4

- AutoPilot: **Norman** routes replace Rawaki (Norman ⇄ Pembroke Plantation, Norman ⇄ Hemera Sound)
- AutoPilot: Turnaround **Yes** retries (up to 5) and **stops** if the confirm stays open; hover Current Vehicle without click
- AutoPilot: **Begin retry** — if spawn did not stick, restart Phase 1 (up to 2 attempts)
- Stop: **immediate halt** — Stop interrupts key holds / sleeps instead of waiting out the cycle
- Notifications: **Minimal / Urgent Only / Custom** — Custom lets you pick which categories ping @everyone
- Intelligent Steering: starts from your current **Multiplier** and **saves** what it learns
- AutoPilot always throttles up in cruise (Throttle-up checkbox is Monitoring / AutoSteer only)

### v4.1.3

- AutoPilot: smarter **Yes** confirm (ignores Vehicles / Trade / etc., prefers the dialog); retries Turnaround / Yes with instant clicks; **caches Search** so leftover search text still opens Jobs
- AutoSteer: **throttle-up at 0%** even during dock / undock (stuck engines, not the intentional 30–50%)
- Monitoring: **custom waypoint** no longer pauses on HUD codes like ZEPHR; distance-stale urgent alerts wait **2 cycles**
- OCR / Discord: distances **rounded to 2 decimals**; throttle reads without `%`; heading alerts use shortest-angle; Reconnect clicks map screenshot coords to screen
- Performance: skip EasyOCR when native HUD text is already good; faster WinRT OCR / screenshots; quieter overlay when idle
- Config: mission history stored in **AeroHelper.history.json**; Search button coords persist

### v4.1.2

- AutoSteer: **sticky turn direction** near ~180° heading error so left/right cannot thrash; steer holds **capped (~25s)** so heading is re-checked sooner; oscillation recovery locks one side and dampens holds
- AutoSteer: when distance is under the stop threshold, pause for **manual dock** with a dedicated **Destination Reached** Discord alert
- Reconnect: retries optional **Reconnect** button (up to 3×, 20s apart) before Join after bringing Roblox to front

### v4.1.1

- AutoPilot: AeroMulti-style **Play → Jobs** (hover Play → click → WinRT snap Jobs → double-click); confirms Jobs via Search field; clears bad Jobs cache on miss
- Input: **MouseKey** natural moves for hover/move so Roblox gets real cursor events (Play flyout stays open)
- OCR: heading accepts **TRK** / **H0G**; fixes `O`→`0` near HUD labels; smarter distance pick when engines disagree or a leading digit drops; uses previous distance for continuity
- UI: Known Issues cards with priority + progress; tooltips on labels (no ⓘ clutter); **Throttle up if not 100%** also shown in AutoPilot
- Webhooks: cleaner urgent-alert wording for throttle / stuck-distance

### v4.1.0

- Startup: full-screen **10s countdown** overlay before automation begins
- AutoSteer / Monitoring: optional **Throttle up if not 100%** - when enabled, hold W for 10s if throttle is below 100% (replaces the old auto hold-W-at-0%; skipped during AutoPilot docking/undocking). Urgent alerts show whether the setting is on and if W will be held
- AutoSteer: sticky ICAO lock (3-cycle confirm; keeps previous bearing if OCR briefly misses)
- OCR: prefers locked/custom waypoint; ignores runway designators (e.g. ILS 26R); accepts miles / mph / m/s HUD units
- AutoPilot: fuzzy Turnaround OCR + faster Play → Jobs so the flyout stays open; clearer Phase 1 / overlay error help
- UI: Join Discord button, status/issues panels grow with the window, main window restores on Stop; **Quit after 5 consecutive errors** marked recommended

### v4.0.3

- AutoSteer: if throttle reads 0%, hold W for 10 seconds to restore throttle (skipped during AutoPilot docking)
- Monitoring: **Unlock 5 view** option - skips pressing `5` each cycle and ignores current HDG (DEST can still be read)

### v4.0.2

- Play hover is move-only (no double-click), so the Jobs flyout can stay open
- Jobs click retries with Play re-hover if the submenu isn’t ready
- `Back` no longer matches **Welcome back** on the lobby screen
- Phase 1 error recovery retries Play → Jobs even when already on lobby (no safe Back)

### v4.0.1

- Metric HUD units (`km` / `km/h`) accepted and converted to nm / knots
- More tolerant OCR fuel/distance reads (missing `%`, doubled decimals, WinRT `843%` → `84.3`)
- Phase 1 names unsupported spawn hubs (e.g. Kashio / Clarence) instead of a generic airport-not-found fail - use a supported route airport or Start Mid-Mission

SSkipr: This is all completely new from the ground up, using your feedback. I am so serious... It has been tested on multiple different machines and took WAY too many hours because I want you to have the best experience possible. THIS BETTER WORK. I hope you enjoy.

- **Architecture & codebase**
    - Rebuilt from scratch, not a patch on v3.x
    - Modular package layout: automation, input, OCR, UI, utils, notifications
    - Dedicated controller, config, state, logger, and device client modules
    - EasyOCR pipeline (lighter deps than the old DocTR/torch stack)
    - Per-network API access via HMAC fingerprint (no local credentials)
    - Settings stored in `AeroHelper.env` instead of scattered files

- **Steering & navigation**
    - Physics-based turn model replaces v3's fixed angle buckets (7s / 5s / 3s / …)
    - Small corrections use a **quadratic ramp** (√(θ·T_ramp/ω_max)); larger turns scale **linearly** (θ/ω_max)
    - Proper 360° wrap via shortest signed angle difference (v3 used naive `abs(current - target)`)
    - Throttle-aware hold times: lower throttle = longer steer hold (100/throttle% blend)
    - Heading & distance **EWMA** smoothing for stable docking reads
    - **Blended dock approach**: entry bearing → dock bearing as distance drops inside 5 nm
    - Per-airport **exit bearings** and timed undock sequences before open-water steering
    - **Stuck-distance recovery**: Z hold + A/D alternation (up to 200s), then W boost if distance flatlines
    - Oscillation detection with Discord alert (successor to v3 "Auscultation" warnings)
    - ICAO/DEST bearings must match **3 consecutive cycles** before accepting a waypoint change

- **OCR & parsing**
    - Single full-screen EasyOCR pass (replaces separate DocTR crops for target vs current bearing)
    - WinSDK OCR on Windows where available; Apple Vision on macOS; no PyTorch/DocTR install
    - ROI fallback when ICAO/bearing reads look suspicious
    - Hardened regex parser for speed, throttle, fuel, distance, and headings
    - Fuel reads ignore DEST-adjacent false positives

- **AutoPilot flow**
    - Explicit phases: spawn & route pick → undock → cruise steer → dock alignment → final dock
    - OCR-detects current airport, compares payouts across destinations, picks best route
    - Jobs UI refresh recovery if listings fail mid-evaluation
    - Auto throttle pull-back at ≤3 nm and ≤1.5 nm (Shift+S taps)
    - Final dock: End Sail color check (white = ready), long-Z retry round, multiplier-scaled waits
    - Return-to-lobby detection resets back to Phase 1 automatically
    - Start Mid-Mission: skip spawn when already underway

- **Three automation modes**
    - 👀 **Monitoring** - watch speed, fuel, distance, and alerts without touching inputs
    - 🧭 **AutoSteer** - bearing-based steering with custom waypoint support
    - 🤖 **AutoPilot** - full AFK loop for boat and airship licenses only
    - Plain-language mode descriptions in the UI (no jargon)
    - Start AutoPilot Mid-Mission option

- **AutoPilot routes (v4)**
    - Curated route map with distance tiers (blue / red / orange / black)
    - Leovetsk ⇄ Auchenburgh
    - Leovetsk International > Tierdam Airfield
    - Sandris ⇄ Tenang
    - Norman ⇄ Pembroke Plantation · Norman ⇄ Hemera Sound
    - Routes trimmed to vehicles that can realistically complete AFK loops

- **App & UI**
    - Redesigned desktop UI with mode emojis and clearer labels
    - Live Known Issues panel (pulled from the website API)
    - In-game status overlay
    - Consent / ToS acknowledgment on first launch
    - Auto App Shutdown: block interfering processes each cycle
    - Optional share-data-with-developer + one-time override button
    - AutoRejoin on disconnect or Roblox crash
    - Human intervention detection (pauses when you take over)
    - Discord webhook alerts with optional screenshot attachments

- **Website, API, and AeroMulti**
    - Full [website](https://aeronautica-helper.vercel.app/) v4.0 refresh
    - Secured REST API: telemetry, issues, feedback, data sharing (network fingerprint auth)
    - Rate limits, input validation, and IP-hash checks on protected routes
    - [AeroMulti](https://aeronautica-helper.vercel.app/aeromulti) by AeroHelper: server multiplier scanner with API ingest (see site for Discord access)
    - Terms of Service and data-sharing policy pages
    - [Discord community server](https://discord.gg/acdQ6BFrFs) for support and API or multiplier data info
    - Help page, feedback form, and contributor credits

- **Changed from v3.x** ([GitHub Standard branch](https://github.com/SSkipr/AeronauticaHelper))
    - Curated AFK route set with distance tiers instead of v3's long express/long-haul list
    - v3 airship AutoPilot altitude loop (e.g. Nordspyd ⇄ Valois) not carried over - v4 AutoPilot targets boat AFK loops. Airship AutoPilot will come shortly (AutoSteer will work, however).
    - Removed leeway setting; arrival uses distance thresholds + dock phases instead
    - Removed automatic nightvision toggle and DocTR engine cooldown/reinit breaks
    - macOS support restored (experimental) where v3.6 dropped it

- **Also in v4**
    - Compiled `.exe` release - no Python setup required
    - Python source install via `requirements.txt`
    - Windows (primary) and experimental macOS support

---

## 🙋 FAQ

Visit the dedicated **[Help Page](https://aeronautica-helper.vercel.app/help)** for setup help, troubleshooting, and known issues.


---

## ⭐ Support the Project

If AeroHelper saves you time:

- Leave a ⭐ on the repo
- Submit issues or suggestions via [GitHub](https://github.com/SSkipr/AeronauticaHelper/issues)
- Follow for updates

**Thanks for using AeroHelper ❣️**

---

## 📈 Roadmap

- 🔜 Airship AutoPilot (v4.x)
- 🔜 Additional boat routes
- 🔭 AeroHelper x AeroMulti (for autonomously finding highest job multiplier)

---

## 🤝 Contributors

**SSkipr** - Lead Developer

**Person-12** - Contributor & QA Tester

**She3pd0g** - Contributor

**muffin.** - QA Tester

<a href="https://github.com/SSkipr/AeronauticaHelper/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=SSkipr/AeronauticaHelper" />
</a>

---

## 📦 Libraries


| Library       | Role                         |
| ------------- | ---------------------------- |
| EasyOCR       | OCR engine                   |
| PyQt5         | User interface               |
| Pillow        | Image processing             |
| NumPy         | Data processing              |
| pynput        | Input control                |
| mousekey      | Mouse acceleration (Windows) |
| psutil        | System information           |
| requests      | HTTP                         |
| python-dotenv | Config management            |
| winsdk        | Native Windows OCR fallback  |
| pywin32       | Windows API access           |
| torch         | ML backend for EasyOCR       |

*Standard library modules: asyncio, datetime, json, logging, math, os, pathlib, re, subprocess, sys, threading, time, uuid, webbrowser*

---

### [🌐 Visit the Website](https://aeronautica-helper.vercel.app/) · [📥 Download v4](https://github.com/SSkipr/AeronauticaHelper/releases) · [🙋 Help](https://aeronautica-helper.vercel.app/help)
