import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

import config

TIERS = ("V1", "V2", "V3", "V4")


def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    root = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(root, "Nexa")
    os.makedirs(path, exist_ok=True)
    return path


def get_hwid():
    parts = []
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                           winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        parts.append(str(winreg.QueryValueEx(k, "MachineGuid")[0]))
        winreg.CloseKey(k)
    except Exception:
        pass
    try:
        flags = 0x08000000 if os.name == "nt" else 0
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor | select -First 1).ProcessorId; "
             "(Get-CimInstance Win32_BaseBoard | select -First 1).SerialNumber"],
            capture_output=True, text=True, timeout=25, creationflags=flags, errors="ignore").stdout
        parts.extend(x.strip() for x in out.splitlines() if x.strip())
    except Exception:
        pass
    if not parts:
        parts.append(os.environ.get("COMPUTERNAME", "NEXA-UNKNOWN"))
    h = hashlib.sha256("|".join(parts).encode()).hexdigest().upper()[:20]
    return "-".join(h[i:i + 5] for i in range(0, 20, 5))


def license_path():
    return os.path.join(data_dir(), "license.dat")


def save_license(key):
    with open(license_path(), "w", encoding="utf-8") as f:
        f.write((key or "").strip())


def load_license():
    try:
        with open(license_path(), "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def clear_license():
    try:
        os.remove(license_path())
    except Exception:
        pass


def admin_mode():
    return os.path.isfile(os.path.join(base_dir(), "admin.flag"))


def post(path, body, token=None, timeout=15):
    base = (config.SERVER_URL or "").strip().strip("\"'").rstrip("/")
    if not base:
        return None, "Sunucu adresi ayarlanmamış (config.py içindeki SERVER_URL)."
    if not base.lower().startswith("http"):
        base = "https://" + base
    req = urllib.request.Request(
        base + path, data=json.dumps(body).encode(), method="POST",
        headers={"content-type": "application/json", "user-agent": "NexaTweak/1.0"})
    if token:
        req.add_header("x-admin-token", token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode()), None
        except Exception:
            return None, "Sunucu hatası (%d)." % e.code
    except Exception as e:
        reason = str(getattr(e, "reason", e))[:90]
        return None, "Sunucuya bağlanılamadı: %s | %s" % (reason, base)


def check(key, hwid):
    data, err = post("/activate", {"key": key, "hwid": hwid})
    if err:
        return "offline", err, None
    if data.get("ok"):
        return "ok", "OK", {"tier": data["tier"], "expires": data.get("expires", "Sınırsız")}
    return "denied", data.get("message", "Key geçersiz."), None


def admin_login(token):
    data, err = post("/admin/list", {}, token)
    if err:
        return False, err, []
    if not data.get("ok"):
        return False, data.get("message", "Şifre hatalı."), []
    return True, "OK", data.get("items", [])


def admin_create(token, name, tier, days):
    data, err = post("/admin/create", {"name": name, "tier": tier, "days": days}, token)
    if err:
        return None, err
    if not data.get("ok"):
        return None, data.get("message", "Oluşturulamadı.")
    return data["key"], None


def admin_list(token):
    data, err = post("/admin/list", {}, token)
    if err:
        return None, err
    if not data.get("ok"):
        return None, data.get("message", "Liste alınamadı.")
    return data.get("items", []), None


def admin_action(token, action, key):
    data, err = post("/admin/" + action, {"key": key}, token)
    if err:
        return False, err
    return bool(data.get("ok")), data.get("message", "")
