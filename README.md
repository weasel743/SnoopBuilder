```markdown
<div align="center">

# 🕵️ Snoop Builder

**A modern PyQt5 GUI to build Python payloads into `.exe` / `.py`**
**Interface PyQt5 moderne pour builder des payloads Python en `.exe` / `.py`**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?logo=windows&logoColor=white)]()
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?logo=qt&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

Modules · Security · Dual Compiler · Discord Webhook

</div>

---

## ✨ Features

| | |
|---|---|
| **28 modules** | credentials, Discord tokens, wallets, WiFi, VPN, SSH, cloud, gaming, screenshot, webcam |
| **5 security options** | Anti-VM/Debug · Anti-Tamper · Persistence · Self-Delete · Wipe Logs |
| **2 compilers** | PyInstaller (fast) · Nuitka (C-compiled, stealthier) |
| **Exfiltration** | Discord webhook · cascading embeds · single structured zip (6.5 MB cap) |
| **UI** | Frameless · accent color picker · config save/load JSON |

## 📦 Install

**Windows** — install [Python 3.12+](https://python.org/downloads) (check *Add to PATH*), then:

```bat
git clone https://github.com/<user>/snoop-builder.git
cd snoop-builder
install.bat
```

macOS / Linux — brew install python or sudo apt install python3 python3-pip python3-venv, then:

```bash
git clone https://github.com/<user>/snoop-builder.git && cd snoop-builder
pip install "PyQt5>=5.15.9,<6" requests pyinstaller nuitka
```

🚀 Usage

```bash
python builder.py
```

1. Options — webhook URL, modules, security
2. Builder — name, output type, compiler, icon, path
3. Start build

🏗️ Architecture

Builder ↔ template communicate via placeholders:

Placeholder Purpose
%%WEBHOOK_URL%% Exfiltration URL
%%MODULE_FLAG_<NAME>%% Enable a module
%%SECURITY_<NAME>%% Enable a security option

Guard: build fails if any %%...%% remains.

⚠️ Disclaimer

Educational and security research purposes only. Illegal use prohibited. Authors not responsible for misuse.

📄 License

MIT

---

<div align="center">Built with 🍁 and 🖤
