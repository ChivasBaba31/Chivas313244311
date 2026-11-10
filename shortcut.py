import base64
import os
import subprocess
import sys

import lic

NAME = "Nexa Tweak.lnk"
DESC = "Nexa Tweak - Developer by Chivas"


def build_script(exe):
    safe = exe.replace("'", "''")
    return (
        "$ErrorActionPreference='Stop'\n"
        "$exe = '%s'\n"
        "$d = [Environment]::GetFolderPath('Desktop')\n"
        "$p = Join-Path $d '%s'\n"
        "$ws = New-Object -ComObject WScript.Shell\n"
        "$l = $ws.CreateShortcut($p)\n"
        "$l.TargetPath = $exe\n"
        "$l.WorkingDirectory = (Split-Path $exe)\n"
        "$l.IconLocation = \"$exe,0\"\n"
        "$l.Description = '%s'\n"
        "$l.Save()\n" % (safe, NAME, DESC)
    )


def temp_location(exe):
    low = exe.lower()
    return "\\temp\\" in low or ".zip" in low


def ensure():
    if not getattr(sys, "frozen", False) or os.name != "nt":
        return
    exe = os.path.abspath(sys.executable)
    if temp_location(exe):
        return
    marker = os.path.join(lic.data_dir(), "lnk.dat")
    try:
        with open(marker, "r", encoding="utf-8") as f:
            if f.read().strip() == exe:
                return
    except Exception:
        pass
    try:
        enc = base64.b64encode(build_script(exe).encode("utf-16-le")).decode()
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc],
                           capture_output=True, timeout=40, creationflags=0x08000000)
        if r.returncode == 0:
            with open(marker, "w", encoding="utf-8") as f:
                f.write(exe)
    except Exception:
        pass
