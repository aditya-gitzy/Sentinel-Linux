# 🛡️ Sentinel: Advanced Real-Time File Automation
<div align="center">

## Tech Stack

</div>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Watchdog-API-FF6F00?style=for-the-badge" alt="Watchdog API" />
  <img src="https://img.shields.io/badge/CustomTkinter-GUI-1E1E1E?style=for-the-badge&logo=windowsterminal&logoColor=white" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/JSON-Persistence-000000?style=for-the-badge&logo=json&logoColor=white" alt="JSON" />
  <img src="https://img.shields.io/badge/License-MIT-F1C40F?style=for-the-badge" alt="License: MIT" />
</div>

<br>

Digital clutter is a nightmare, and relying on standard OS tools to clean it up usually means dealing with overwrites, corrupted active downloads, or rigid workflows. 

**Sentinel** is a highly resilient, cross-platform background daemon designed to solve this. It monitors your target directories in real-time and instantly routes incoming files to their proper destinations using an intelligent, two-pass JSON configuration engine. It runs completely invisibly, meaning you never have to manually sort a downloads folder again.

---

### ✨ Key Features

* **Zero-Latency Monitoring:** Uses an event-driven observer pattern (`watchdog`) to detect files the millisecond they are created. Zero polling loops, zero wasted CPU.
* **Defensive "Settle Time" Buffer:** Actively monitors byte-stream stability. It waits for OS file-locks to release before migrating, ensuring active downloads are never corrupted.
* **Two-Pass Routing Engine:** Prioritizes strict keyword matching (e.g., routing files containing "assignment") before falling back to general extension-based sorting.
* **Atomic Collision Avoidance:** Guarantees zero data loss. If a file with the same name exists, Sentinel dynamically calculates a unique path (e.g., appending a sequence number) rather than overwriting.
* **Decoupled Headless UI:** Features a sleek, dark-mode graphical interface built with CustomTkinter to manage your sorting rules without interfering with the background daemon.

---

### 📂 Repository Structure

```text
Sentinel/
├── main.py                 # Core daemon boot script
├── ui.py                   # CustomTkinter configuration dashboard
├── config.json             # Dynamic rule registry (auto-generated)
├── requirements.txt        # Project dependencies
├── start_invisible.vbs     # Windows script for silent background execution
├── logs/                   # System operation logs
└── sorter/                 # Core logic modules
    ├── __init__.py
    ├── watcher.py          # Observer pattern implementation
    ├── rules.py            # Two-pass routing engine
    └── mover.py            # Atomic I/O and collision logic
```

---

### 🚀 Quick Start

**1. Clone the repository**
```bash
git clone [https://github.com/aditya-gitzy/Sentinel.git](https://github.com/aditya-gitzy/Sentinel.git)
cd Sentinel
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure your rules**
Launch the visual dashboard to set up your target directories, extensions, and keywords.
```bash
python ui.py
```

**4. Start the Sentinel Daemon**
You can run it directly in your terminal to see the live output:
```bash
python main.py
```
*Tip for Windows Users:* To run Sentinel completely invisibly in the background without keeping a terminal window open, simply execute the `start_invisible.vbs` script.

---

### 👥 The Team
Developed by **The Geeks** for the 2025-2026 Python Mini Project at Don Bosco Institute of Technology.

* **[Jayita Chakraborty](https://github.com/jayitamchakraborty-coder)**
* **[Bharthi Annapandi](https://github.com/bharthi12)**
* **[Aditya Lande](https://github.com/aditya-gitzy)**
* **[Ekjyot Singh](https://github.com/ekjyotsingh-2007)**

**Project Guide:** Prof. Imran Mirza
