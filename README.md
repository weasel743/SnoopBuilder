# Snoop Builder

PyQt5 interface to configure and compile a Python payload into `.exe` or `.py` — modules, security, dual compiler, Discord exfiltration.

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/fPU7DCCmnB)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

---

## 🇬🇧 English

### Features

- **PyQt5 UI** — frameless, dark theme, customizable accent color, 4 tabs
- **28 modules** — System Info, Passwords, Cookies, Credit Cards, Autofill, Extensions, History, Downloads, Discord Tokens, Discord Metadata, Roblox Cookies, Wallets, Browser Wallets, Game Launchers, Steam Extended, VPN, FTP, SSH, Cloud, Telegram, Signal, Apps, Environment, Product Key, WiFi, Screenshot, Webcam, Files
- **Firefox** — passwords (NSS), cookies, history
- **5 security options** — Anti-VM/Debug, Anti-Tamper, Startup Persistence, Self-Delete, Wipe Logs
- **2 compilers** — PyInstaller (fast) or Nuitka (C-compiled)
- **Login** — test Discord token, Roblox cookie, generic cookie + Selenium injection

### Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python builder.py
On Windows: double-click install.bat then start.bat.

Structure
text
SnoopBuilder/
├── builder.py
├── requirements.txt
├── install.bat
├── install.sh
├── start.bat
├── README.md
├── assets/
│   └── logo.png
└── templates/
    └── stealer_template.py
Usage
Options — Discord webhook, check modules, check security options

Builder — file name, output type (.py / .exe), compiler, icon, output folder

Login — test a Discord token or a Roblox / generic cookie

Settings — language EN/FR, accent color

Click Start build — the payload is generated in the chosen folder.

Dependencies
Python 3.10+

PyQt5, requests, selenium, webdriver-manager

psutil, Pillow, pycryptodomex, pywin32, browser-history

PyInstaller, Nuitka (optional, for .exe compilation)

Selenium requirement
The "Login browser" buttons need:

bash
pip install selenium webdriver-manager
Chrome must be installed on the machine.

Note
The generated payload is intended for security research and authorized testing. Only use it on systems you own or have written authorization for.

🇫🇷 Français
Fonctionnalités
Interface PyQt5 — frameless, thème sombre, couleur d'accent personnalisable, 4 onglets

28 modules — System Info, Passwords, Cookies, Credit Cards, Autofill, Extensions, History, Downloads, Discord Tokens, Discord Metadata, Roblox Cookies, Wallets, Browser Wallets, Game Launchers, Steam Extended, VPN, FTP, SSH, Cloud, Telegram, Signal, Apps, Environment, Product Key, WiFi, Screenshot, Webcam, Files

Firefox — passwords (NSS), cookies, history

5 options sécurité — Anti-VM/Debug, Anti-Tamper, Persistance, Self-Delete, Wipe Logs

2 compilateurs — PyInstaller (rapide) ou Nuitka (compilé C)

Login — test token Discord, cookie Roblox, cookie générique + injection Selenium

Lancement
bash
python -m venv .venv
# Windows : .venv\Scripts\activate
# macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
python builder.py
Sur Windows : double-clic sur install.bat puis start.bat.

Structure
text
SnoopBuilder/
├── builder.py
├── requirements.txt
├── install.bat
├── install.sh
├── start.bat
├── README.md
├── assets/
│   └── logo.png
└── templates/
    └── stealer_template.py
Utilisation
Options — webhook Discord, cocher les modules, cocher les options de sécurité

Builder — nom du fichier, type (.py / .exe), compilateur, icône, dossier de sortie

Login — tester un token Discord ou un cookie Roblox / générique

Paramètres — langue FR/EN, couleur d'accent

Clique Démarrer la construction — le payload est généré dans le dossier choisi.

Dépendances
Python 3.10+

PyQt5, requests, selenium, webdriver-manager

psutil, Pillow, pycryptodomex, pywin32, browser-history

PyInstaller, Nuitka (optionnel, pour compiler en .exe)

Prérequis pour Selenium
Les boutons « Login navigateur » ont besoin de :

bash
pip install selenium webdriver-manager
Chrome doit être installé sur la machine.

Note
Le payload généré est destiné à la recherche en sécurité et aux tests autorisés. Ne l'utilise que sur des systèmes dont tu es propriétaire ou pour lesquels tu as une autorisation écrite.

<div align="center">
https://img.shields.io/badge/Discord-discord.gg%2FfPU7DCCmnB-5865F2?style=for-the-badge&logo=discord&logoColor=white

</div> ```
