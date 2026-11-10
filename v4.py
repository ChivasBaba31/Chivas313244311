import os, re, glob, sys, ctypes, subprocess, base64, shutil
from ctypes import wintypes
import winreg as wr

import tweaks as T
from tweaks import run, reg, wipe, prio, L, ram_gb, is_ssd, HKLM, HKCU, SYSROOT, CF

SZ = wr.REG_SZ
BIN = wr.REG_BINARY
GUID = r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}"


def E(n):
    return os.environ.get(n, "")


def LA():
    return E("LOCALAPPDATA")


def RA():
    return E("APPDATA")


def PD():
    return E("ProgramData")


def win11():
    try:
        return sys.getwindowsversion().build >= 22000
    except Exception:
        return False


def ps(script, t=180):
    try:
        enc = base64.b64encode(script.encode("utf-16-le")).decode()
        return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc],
                              capture_output=True, text=True, creationflags=CF, timeout=t,
                              errors="ignore").stdout or ""
    except Exception:
        return ""


def rv(root, path, name):
    try:
        k = wr.OpenKey(root, path, 0, wr.KEY_READ | wr.KEY_WOW64_64KEY)
        v = wr.QueryValueEx(k, name)[0]
        wr.CloseKey(k)
        return v
    except Exception:
        return None


def reg_del(root, path, name):
    try:
        k = wr.OpenKey(root, path, 0, wr.KEY_SET_VALUE | wr.KEY_WOW64_64KEY)
        wr.DeleteValue(k, name)
        wr.CloseKey(k)
    except Exception:
        pass


def reg_names(root, path):
    out = []
    try:
        k = wr.OpenKey(root, path, 0, wr.KEY_READ | wr.KEY_WOW64_64KEY)
        i = 0
        while True:
            try:
                out.append(wr.EnumValue(k, i)[0])
            except OSError:
                break
            i += 1
        wr.CloseKey(k)
    except Exception:
        pass
    return out


def wipe_glob(*patterns):
    for pat in patterns:
        for p in glob.glob(pat):
            try:
                if os.path.isdir(p):
                    wipe(p)
                else:
                    os.remove(p)
            except Exception:
                pass


def free_bytes():
    try:
        return shutil.disk_usage((E("SystemDrive") or "C:") + "\\").free
    except Exception:
        return 0


def freed(before):
    d = (free_bytes() - before) / 1048576
    return "%d MB boşaltıldı" % d if d >= 1 else ""


def gpu_classes():
    base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    for i in range(20):
        sub = "%s\\%04d" % (base, i)
        d = rv(HKLM, sub, "DriverDesc")
        if d:
            yield sub, str(d).lower()


def steam_path():
    for root, path, name in ((HKCU, r"Software\Valve\Steam", "SteamPath"),
                             (HKLM, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
                             (HKLM, r"SOFTWARE\Valve\Steam", "InstallPath")):
        v = rv(root, path, name)
        if v and os.path.isdir(v):
            return os.path.normpath(v)
    return ""


def steam_libs():
    sp = steam_path()
    libs = [sp] if sp else []
    try:
        with open(os.path.join(sp, "steamapps", "libraryfolders.vdf"), encoding="utf-8", errors="ignore") as f:
            for m in re.finditer(r'"path"\s+"([^"]+)"', f.read()):
                p = os.path.normpath(m.group(1).replace("\\\\", "\\"))
                if p not in libs and os.path.isdir(p):
                    libs.append(p)
    except Exception:
        pass
    return libs


def steam_shader(appid=None):
    for lib in steam_libs():
        base = os.path.join(lib, "steamapps", "shadercache")
        if appid:
            wipe(os.path.join(base, str(appid)))
        else:
            wipe(base)


def steam_exe(rel):
    for lib in steam_libs():
        p = os.path.join(lib, "steamapps", "common", rel)
        if os.path.isfile(p):
            return p
    return None


def gpu_pref(paths):
    for p in paths:
        if p and os.path.isfile(p):
            reg(HKCU, r"Software\Microsoft\DirectX\UserGpuPreferences", p, "GpuPreference=2;", SZ)
            reg(HKCU, r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers", p,
                "~ DISABLEDXMAXIMIZEDWINDOWEDMODE", SZ)


# ---------------------------------------------------------------- güç / cpu
def v4_power():
    out = run("powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    m = re.search(GUID, out, re.I)
    g = m.group(0) if m else "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    run("powercfg -changename %s \"Nexa Ultimate\" \"Nexa Tweak V4 performans planı\"" % g)
    run("powercfg -setactive " + g)
    rows = [("SUB_PROCESSOR", "PROCTHROTTLEMIN", 100), ("SUB_PROCESSOR", "PROCTHROTTLEMAX", 100),
            ("SUB_PROCESSOR", "CPMINCORES", 100), ("SUB_PROCESSOR", "CPMAXCORES", 100),
            ("SUB_PROCESSOR", "PERFBOOSTMODE", 2), ("SUB_PROCESSOR", "SYSCOOLPOL", 1),
            ("2a737441-1930-4402-8d77-b2bebba308a3", "48e6b7a6-50f5-4782-a5d4-53bb8f07e226", 0),
            ("SUB_PCIEXPRESS", "ASPM", 0), ("SUB_DISK", "DISKIDLE", 0),
            ("SUB_SLEEP", "STANDBYIDLE", 0), ("SUB_SLEEP", "HIBERNATEIDLE", 0), ("SUB_VIDEO", "VIDEOIDLE", 0)]
    for sub, st, val in rows:
        run("powercfg -setacvalueindex %s %s %s %d" % (g, sub, st, val))
        run("powercfg -setdcvalueindex %s %s %s %d" % (g, sub, st, val))
    run("powercfg -setactive " + g)
    run("powercfg -h off")
    return "Nexa Ultimate planı aktif"


def v4_bgkill():
    procs = ["OneDrive.exe", "OneDriveStandaloneUpdater.exe", "Teams.exe", "ms-teams.exe", "Skype.exe",
             "SkypeApp.exe", "SkypeBackgroundHost.exe", "YourPhone.exe", "PhoneExperienceHost.exe",
             "GameBar.exe", "GameBarFTServer.exe", "GameBarPresenceWriter.exe", "Widgets.exe",
             "WidgetService.exe", "Cortana.exe", "HxOutlook.exe", "HxTsr.exe", "MicrosoftEdgeUpdate.exe",
             "GoogleUpdate.exe", "AdobeARM.exe", "AdobeIPCBroker.exe", "AdobeCollabSync.exe", "CCXProcess.exe",
             "CoreSync.exe", "jusched.exe", "OneNoteM.exe"]
    run("taskkill /f " + " ".join("/im " + p for p in procs))


def v4_startup():
    p = r"Software\Microsoft\Windows\CurrentVersion\Run"
    bad = ("onedrive", "teams", "skype", "edgeautolaunch", "msedge", "googleupdate", "adobe", "yourphone")
    for n in reg_names(HKCU, p):
        if any(b in n.lower() for b in bad):
            reg_del(HKCU, p, n)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize", "StartupDelayInMSec", 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize", "WaitForIdleState", 0)
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Edge", "StartupBoostEnabled", 0)
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Edge", "BackgroundModeEnabled", 0)
    reg(HKLM, r"SOFTWARE\Policies\Google\Chrome", "BackgroundModeEnabled", 0)


def v4_services():
    off = ["DiagTrack", "dmwappushservice", "MapsBroker", "RetailDemo", "Fax", "WerSvc", "lfsvc", "WMPNetworkSvc",
           "icssvc", "PhoneSvc", "WpcMonSvc", "wisvc", "RemoteRegistry", "TrkWnd", "NvTelemetryContainer"]
    for s in off:
        run('sc config "%s" start= disabled' % s)
        run('sc stop "%s"' % s)
    for s in ("XblAuthManager", "XblGameSave", "XboxNetApiSvc", "XboxGipSvc"):
        run('sc config "%s" start= demand' % s)


def v4_tasks():
    base = "\\Microsoft\\Windows\\"
    for t in ("Application Experience\\Microsoft Compatibility Appraiser", "Application Experience\\ProgramDataUpdater",
              "Application Experience\\StartupAppTask", "Customer Experience Improvement Program\\Consolidator",
              "Customer Experience Improvement Program\\UsbCeip", "Customer Experience Improvement Program\\KernelCeipTask",
              "DiskDiagnostic\\Microsoft-Windows-DiskDiagnosticDataCollector", "Feedback\\Siuf\\DmClient",
              "Windows Error Reporting\\QueueReporting"):
        run('schtasks /Change /TN "%s%s" /Disable' % (base, t))


def v4_privacy():
    for p in (r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection"):
        reg(HKLM, p, "AllowTelemetry", 0)
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DoNotShowFeedbackNotifications", 1)
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableWindowsConsumerFeatures", 1)
    reg(HKLM, r"SOFTWARE\Microsoft\Windows\Windows Error Reporting", "Disabled", 1)
    s = r"SOFTWARE\Policies\Microsoft\Windows\System"
    for n in ("EnableActivityFeed", "PublishUserActivities", "UploadUserActivities"):
        reg(HKLM, s, n, 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled", 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", 0)
    c = r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
    for n in ("SilentInstalledAppsEnabled", "SystemPaneSuggestionsEnabled", "SoftLandingEnabled",
              "RotatingLockScreenEnabled", "OemPreInstalledAppsEnabled", "PreInstalledAppsEnabled",
              "ContentDeliveryAllowed", "SubscribedContent-338388Enabled", "SubscribedContent-338389Enabled",
              "SubscribedContent-353694Enabled", "SubscribedContent-353696Enabled"):
        reg(HKCU, c, n, 0)


def v4_defender():
    ps("Set-MpPreference -ScanAvgCPULoadFactor 10 -EnableLowCpuPriority $true "
       "-DisableCpuThrottleOnIdleScans $false -ScanOnlyIfIdleEnabled $true -ErrorAction SilentlyContinue")
    return "Defender açık kalır, tarama CPU'su %10'a düşürüldü"


# ---------------------------------------------------------------- gecikme
XC = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0xC0, 0xCC, 0x0C, 0, 0, 0, 0, 0, 0x80, 0x99, 0x19, 0, 0, 0, 0, 0,
            0x40, 0x66, 0x26, 0, 0, 0, 0, 0, 0x00, 0x33, 0x33, 0, 0, 0, 0, 0])
YC = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x38, 0, 0, 0, 0, 0, 0, 0, 0x70, 0, 0, 0, 0, 0,
            0, 0, 0xA8, 0, 0, 0, 0, 0, 0, 0, 0xE0, 0, 0, 0, 0, 0])


def v4_input():
    m = r"Control Panel\Mouse"
    for n, v in (("MouseSpeed", "0"), ("MouseThreshold1", "0"), ("MouseThreshold2", "0"), ("MouseSensitivity", "10")):
        reg(HKCU, m, n, v, SZ)
    reg(HKCU, m, "SmoothMouseXCurve", XC, BIN)
    reg(HKCU, m, "SmoothMouseYCurve", YC, BIN)
    k = r"Control Panel\Keyboard"
    reg(HKCU, k, "KeyboardDelay", "0", SZ)
    reg(HKCU, k, "KeyboardSpeed", "31", SZ)
    a = r"Control Panel\Accessibility"
    reg(HKCU, a + r"\StickyKeys", "Flags", "506", SZ)
    reg(HKCU, a + r"\Keyboard Response", "Flags", "122", SZ)
    reg(HKCU, a + r"\ToggleKeys", "Flags", "58", SZ)
    reg(HKLM, r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters", "MouseDataQueueSize", 20)
    reg(HKLM, r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters", "KeyboardDataQueueSize", 20)
    try:
        arr = (ctypes.c_int * 3)(0, 0, 0)
        ctypes.windll.user32.SystemParametersInfoW(0x0004, 0, arr, 2)
    except Exception:
        pass


def v4_timer():
    T.t_timer()


def v4_mmcss():
    T.t_priority()
    p = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    reg(HKLM, p, "AlwaysOn", 1)
    g = p + r"\Tasks\Games"
    reg(HKLM, g, "Affinity", 0)
    reg(HKLM, g, "Background Only", "False", SZ)
    reg(HKLM, g, "Clock Rate", 10000)


def v4_network():
    T.t_network()
    run("netsh int tcp set heuristics disabled")
    run("netsh int tcp set global initialRto=2000")
    run("netsh int tcp set global nonsackrttresiliency=disabled")
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Psched", "NonBestEffortLimit", 0)
    T.v1_dns()
    T.v1_doh()
    run("arp -d *")
    run("nbtstat -R")


def v4_nic():
    ps("$ErrorActionPreference='SilentlyContinue'\n"
       "Get-NetAdapter -Physical | ForEach-Object {\n"
       " $n=$_.Name\n Disable-NetAdapterPowerManagement -Name $n\n Disable-NetAdapterLso -Name $n\n"
       " foreach($p in 'Energy-Efficient Ethernet','Energy Efficient Ethernet','Green Ethernet','Interrupt Moderation',"
       "'Flow Control','Power Saving Mode','Ultra Low Power Mode','Advanced EEE'){\n"
       "  Set-NetAdapterAdvancedProperty -Name $n -DisplayName $p -DisplayValue 'Disabled'\n }\n}")


def v4_msi():
    ps("$ErrorActionPreference='SilentlyContinue'\n"
       "$ids=@(); $ids+=(Get-CimInstance Win32_VideoController | ForEach-Object {$_.PNPDeviceID})\n"
       "$ids+=(Get-CimInstance Win32_NetworkAdapter | Where-Object {$_.PhysicalAdapter} | ForEach-Object {$_.PNPDeviceID})\n"
       "foreach($i in $ids){ if($i -like 'PCI\\*'){\n"
       " $p='HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\'+$i+'\\Device Parameters\\Interrupt Management\\MessageSignaledInterruptProperties'\n"
       " if(-not (Test-Path $p)){New-Item -Path $p -Force | Out-Null}\n"
       " New-ItemProperty -Path $p -Name MSISupported -Value 1 -PropertyType DWord -Force | Out-Null } }")


# ---------------------------------------------------------------- grafik
def v4_gamemode():
    T.t_gamemode()
    T.v1_fso()
    reg(HKCU, r"Software\Microsoft\GameBar", "ShowStartupPanel", 0)
    reg(HKCU, r"Software\Microsoft\GameBar", "UseNexusForGameBarEnabled", 0)


def v4_vbs():
    T.t_vbs()
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control\DeviceGuard", "EnableVirtualizationBasedSecurity", 0)


def v4_gpu():
    seen = []
    for sub, d in gpu_classes():
        if "nvidia" in d:
            reg(HKLM, sub, "PerfLevelSrc", 0x2222)
            reg(HKLM, sub, "PowerMizerEnable", 1)
            reg(HKLM, sub, "PowerMizerLevel", 1)
            reg(HKLM, sub, "PowerMizerLevelAC", 1)
            reg(HKLM, sub, "DisableDynamicPstate", 1)
            seen.append("NVIDIA")
        elif "amd" in d or "radeon" in d:
            reg(HKLM, sub, "EnableUlps", 0)
            reg(HKLM, sub, "EnableUlps_NA", "0", SZ)
            seen.append("AMD")
    return (", ".join(sorted(set(seen))) + " ayarlandı") if seen else "NVIDIA/AMD kartı bulunamadı"


# ---------------------------------------------------------------- bellek / disk
def v4_ram():
    T.t_ram()
    T.t_svchost()
    run("fsutil behavior set memoryusage 2")
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "LargeSystemCache", 0)


class _LUID(ctypes.Structure):
    _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.LONG)]


class _TP(ctypes.Structure):
    _fields_ = [("n", wintypes.DWORD), ("luid", _LUID), ("attr", wintypes.DWORD)]


def _priv(name):
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    tok = wintypes.HANDLE()
    adv.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), 0x28, ctypes.byref(tok)):
        return False
    luid = _LUID()
    adv.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(_LUID)]
    if not adv.LookupPrivilegeValueW(None, name, ctypes.byref(luid)):
        return False
    tp = _TP(1, luid, 2)
    adv.AdjustTokenPrivileges.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(_TP),
                                          wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p]
    adv.AdjustTokenPrivileges(tok, False, ctypes.byref(tp), 0, None, None)
    k32.CloseHandle(tok)
    return True


def v4_ramclean():
    _priv("SeProfileSingleProcessPrivilege")
    _priv("SeIncreaseQuotaPrivilege")
    nt = ctypes.WinDLL("ntdll")
    done = 0
    for cmd in (2, 3, 4):
        c = ctypes.c_int(cmd)
        if nt.NtSetSystemInformation(80, ctypes.byref(c), 4) == 0:
            done += 1
    if not done:
        raise RuntimeError("bellek temizlenemedi")
    return "çalışma kümeleri ve bekleme listesi boşaltıldı"


# ---------------------------------------------------------------- windows 10 / 11
def v4_win11():
    if not win11():
        return "bu bilgisayar Windows 11 değil, atlandı"
    T.v1_ctx()
    T.v1_copilot()
    T.v1_widgets()
    a = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    for n, v in (("TaskbarDa", 0), ("TaskbarMn", 0), ("ShowTaskViewButton", 0), ("Start_IrisRecommendations", 0),
                 ("ShowSyncProviderNotifications", 0)):
        reg(HKCU, a, n, v)
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Chat", "ChatIcon", 3)
    return "Windows 11 ayarları uygulandı"


def v4_win10():
    if win11():
        return "bu bilgisayar Windows 10 değil, atlandı"
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana", 0)
    s = r"Software\Microsoft\Windows\CurrentVersion\Search"
    reg(HKCU, s, "BingSearchEnabled", 0)
    reg(HKCU, s, "CortanaConsent", 0)
    reg(HKCU, s, "SearchboxTaskbarMode", 1)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Feeds", "ShellFeedsTaskbarViewMode", 2)
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Feeds", "EnableFeeds", 0)
    a = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    reg(HKCU, a + r"\People", "PeopleBand", 0)
    reg(HKCU, a, "ShowCortanaButton", 0)
    reg(HKCU, a, "ShowTaskViewButton", 0)
    return "Windows 10 ayarları uygulandı"


# ---------------------------------------------------------------- temizlik
def v4_clean_sys():
    b = free_bytes()
    run("net stop wuauserv")
    run("net stop bits")
    run("net stop FontCache")
    wipe(E("TEMP"))
    wipe(os.path.join(LA(), "Temp"))
    wipe(os.path.join(SYSROOT, "Temp"))
    wipe(os.path.join(SYSROOT, "Prefetch"))
    wipe(os.path.join(SYSROOT, "SoftwareDistribution", "Download"))
    wipe(os.path.join(SYSROOT, "Minidump"))
    wipe(os.path.join(SYSROOT, "Logs", "CBS"))
    wipe(os.path.join(SYSROOT, "ServiceProfiles", "LocalService", "AppData", "Local", "FontCache"))
    wipe(os.path.join(SYSROOT, "ServiceProfiles", "NetworkService", "AppData", "Local", "Microsoft",
                      "Windows", "DeliveryOptimization", "Cache"))
    wipe_glob(os.path.join(SYSROOT, "MEMORY.DMP"), os.path.join(LA(), "CrashDumps", "*"),
              os.path.join(PD(), "Microsoft", "Windows", "WER", "ReportQueue", "*"),
              os.path.join(PD(), "Microsoft", "Windows", "WER", "ReportArchive", "*"),
              os.path.join(PD(), "Microsoft", "Windows", "WER", "Temp", "*"),
              os.path.join(LA(), "Microsoft", "Windows", "WER", "*"),
              os.path.join(LA(), "Microsoft", "Windows", "INetCache", "*"),
              os.path.join(RA(), "Microsoft", "Windows", "Recent", "*"))
    run("net start FontCache")
    run("net start bits")
    run("net start wuauserv")
    run("ipconfig /flushdns")
    run("arp -d *")
    ps("Clear-RecycleBin -Force -ErrorAction SilentlyContinue")
    return freed(b)


def v4_clean_icons():
    ex = os.path.join(LA(), "Microsoft", "Windows", "Explorer")
    run("taskkill /f /im explorer.exe")
    wipe_glob(os.path.join(ex, "thumbcache_*.db"), os.path.join(ex, "iconcache_*.db"),
              os.path.join(LA(), "IconCache.db"))
    try:
        subprocess.Popen("explorer.exe", creationflags=CF)
    except Exception:
        pass


def v4_clean_browsers():
    b = free_bytes()
    la, ra = LA(), RA()
    bases = [os.path.join(la, "Google", "Chrome", "User Data"), os.path.join(la, "Microsoft", "Edge", "User Data"),
             os.path.join(la, "BraveSoftware", "Brave-Browser", "User Data"), os.path.join(la, "Vivaldi", "User Data"),
             os.path.join(ra, "Opera Software", "Opera Stable"), os.path.join(ra, "Opera Software", "Opera GX Stable")]
    subs = ("Cache", "Code Cache", "GPUCache", "DawnCache", os.path.join("Service Worker", "CacheStorage"),
            os.path.join("Service Worker", "ScriptCache"))
    for base in bases:
        wipe_glob(os.path.join(base, "ShaderCache"), os.path.join(base, "GrShaderCache"),
                  os.path.join(base, "GraphiteDawnCache"))
        for prof in ("Default", "Profile *", ""):
            for s in subs:
                wipe_glob(os.path.join(base, prof, s) if prof else os.path.join(base, s))
    wipe_glob(os.path.join(la, "Mozilla", "Firefox", "Profiles", "*", "cache2"),
              os.path.join(la, "Mozilla", "Firefox", "Profiles", "*", "startupCache"))
    return freed(b)


def v4_clean_shaders():
    b = free_bytes()
    la, pd = LA(), PD()
    wipe_glob(os.path.join(la, "NVIDIA", "DXCache"), os.path.join(la, "NVIDIA", "GLCache"),
              os.path.join(pd, "NVIDIA Corporation", "NV_Cache"), os.path.join(la, "NVIDIA Corporation", "NV_Cache"),
              os.path.join(la, "AMD", "DxCache"), os.path.join(la, "AMD", "DxcCache"),
              os.path.join(la, "AMD", "VkCache"), os.path.join(la, "AMD", "GLCache"),
              os.path.join(la, "D3DSCache"), os.path.join(la, "Intel", "ShaderCache"),
              os.path.join(la, "Microsoft", "DirectX Shader Cache"))
    steam_shader()
    return freed(b)


def v4_clean_apps():
    b = free_bytes()
    ra, la = RA(), LA()
    for d in ("discord", "discordptb", "discordcanary"):
        for s in ("Cache", "Code Cache", "GPUCache"):
            wipe(os.path.join(ra, d, s))
    for s in ("Cache", "Code Cache", "GPUCache", "tmp"):
        wipe(os.path.join(ra, "Microsoft", "Teams", s))
    sp = steam_path()
    if sp:
        wipe(os.path.join(sp, "appcache", "httpcache"))
        wipe(os.path.join(sp, "logs"))
        wipe(os.path.join(sp, "dumps"))
    wipe_glob(os.path.join(la, "EpicGamesLauncher", "Saved", "webcache*"),
              os.path.join(la, "EpicGamesLauncher", "Saved", "Logs", "*"),
              os.path.join(la, "EpicGamesLauncher", "Saved", "Crashes", "*"))
    return freed(b)


def v4_dism():
    run("Dism.exe /Online /Cleanup-Image /StartComponentCleanup", 1500)
    return "Windows bileşen deposu temizlendi"


# ---------------------------------------------------------------- görünüm
def _broadcast():
    try:
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, "ImmersiveColorSet", 2, 5000, None)
    except Exception:
        pass


def v4_beauty():
    p = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    reg(HKCU, p, "AppsUseLightTheme", 0)
    reg(HKCU, p, "SystemUsesLightTheme", 0)
    a = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    reg(HKCU, a, "HideFileExt", 0)
    reg(HKCU, a, "LaunchTo", 1)
    reg(HKCU, a, "ShowTaskViewButton", 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "SearchboxTaskbarMode", 1)
    h = r"Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel"
    for g in ("{20D04FE0-3AEA-1069-A2D8-08002B30309D}", "{59031a47-3f72-44a7-89c5-5595fe6b30ee}",
              "{645FF040-5081-101B-9F08-00AA002F954E}"):
        reg(HKCU, h, g, 0)
    reg(HKCU, r"Control Panel\Desktop", "FontSmoothing", "2", SZ)
    reg(HKCU, r"Control Panel\Desktop", "FontSmoothingType", 2)
    _broadcast()


def v4_visualfx():
    T.v1_visual()
    reg(HKCU, r"Software\Microsoft\Windows\DWM", "EnableAeroPeek", 0)
    reg(HKCU, r"Software\Microsoft\Windows\DWM", "AlwaysHibernateThumbnails", 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewAlphaSelect", 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewShadow", 0)


def _res(p):
    return os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), p)


def v4_wallpaper():
    from PIL import Image, ImageDraw, ImageFont
    u = ctypes.windll.user32
    w, h = u.GetSystemMetrics(0) or 1920, u.GetSystemMetrics(1) or 1080
    img = Image.new("RGB", (w, h), (11, 11, 13))
    lg = Image.open(_res("assets/logo.png")).convert("RGBA")
    th = int(h * 0.30)
    lg = lg.resize((int(th * lg.width / lg.height), th))
    img.paste(lg, ((w - lg.width) // 2, int(h * 0.30)), lg)
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(os.path.join(SYSROOT, "Fonts", "segoeuib.ttf"), int(h * 0.05))
    except Exception:
        f = ImageFont.load_default()
    t = "NEXA PACK"
    box = d.textbbox((0, 0), t, font=f)
    d.text(((w - (box[2] - box[0])) // 2, int(h * 0.64)), t, fill=(255, 255, 255), font=f)
    out = os.path.join(E("APPDATA") or os.path.expanduser("~"), "Nexa")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "wallpaper.png")
    img.save(path)
    u.SystemParametersInfoW(20, 0, path, 3)


# ---------------------------------------------------------------- oyunlar
GTA_PERF = {"Tessellation": "0", "ReflectionMSAA": "0", "MSAA": "0", "MSAAFragments": "0", "MSAAQuality": "0",
            "SSAO": "0", "ReflectionQuality": "0", "GrassQuality": "0", "WaterQuality": "0", "ParticleQuality": "1",
            "ShadowQuality": "1", "UltraShadows_Enabled": "false", "Shadow_ParticleShadows": "false",
            "Shadow_LongShadows": "false", "DoF": "false", "PostFX": "1", "HdStreamingInFlight": "false",
            "MotionBlurStrength": "0.000000", "MaxLodScale": "0.000000"}


def _patch_xml(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    bak = path + ".nexa.bak"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    n = 0
    for k, v in GTA_PERF.items():
        txt, c = re.subn(r'(<%s\s+value=")[^"]*(")' % re.escape(k), r"\g<1>%s\g<2>" % v, txt)
        n += c
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return n


def v4_fivem_settings():
    files = [os.path.join(RA(), "CitizenFX", "gta5_settings.xml"),
             os.path.join(os.path.expanduser("~"), "Documents", "Rockstar Games", "GTA V", "settings.xml")]
    done = 0
    for p in files:
        if os.path.isfile(p):
            done += _patch_xml(p)
    d = os.path.join(LA(), "FiveM")
    gpu_pref([os.path.join(d, "FiveM.exe")] + glob.glob(os.path.join(d, "FiveM.app", "FiveM*_GTAProcess.exe"))
             + glob.glob(os.path.join(d, "FiveM.app", "*GTAProcess.exe")))
    if not done and not os.path.isdir(d):
        return "FiveM bulunamadı, atlandı"
    return "%d grafik ayarı güncellendi (yedek: .nexa.bak)" % done


def g_fivem():
    d = os.path.join(LA(), "FiveM", "FiveM.app")
    for n in ("server-cache", "server-cache-priv"):
        wipe(os.path.join(d, "data", n))
    wipe(os.path.join(d, "data", "cache", "browser"))
    wipe_glob(os.path.join(d, "crashes", "*"), os.path.join(d, "logs", "*"))
    exes = ["FiveM.exe", "GTA5.exe", "FiveM_GTAProcess.exe"]
    exes += [os.path.basename(p) for p in glob.glob(os.path.join(d, "FiveM*_GTAProcess.exe"))]
    for e in set(exes):
        prio(e)


def g_gta5():
    prio("GTA5.exe")
    steam_shader(271590)
    gpu_pref([steam_exe(os.path.join("Grand Theft Auto V", "GTA5.exe")),
              os.path.join(E("ProgramFiles"), "Rockstar Games", "Grand Theft Auto V", "GTA5.exe")])
    p = os.path.join(os.path.expanduser("~"), "Documents", "Rockstar Games", "GTA V", "settings.xml")
    if os.path.isfile(p):
        _patch_xml(p)


def g_cs2():
    prio("cs2.exe")
    steam_shader(730)
    gpu_pref([steam_exe(os.path.join("Counter-Strike Global Offensive", "game", "bin", "win64", "cs2.exe"))])


def g_valorant():
    d = os.path.join(LA(), "VALORANT", "Saved")
    wipe(os.path.join(d, "Logs"))
    wipe(os.path.join(d, "Crashes"))
    wipe_glob(os.path.join(d, "webcache*"))


def g_fortnite():
    d = os.path.join(LA(), "FortniteGame", "Saved")
    wipe(os.path.join(d, "Logs"))
    wipe(os.path.join(d, "Crashes"))
    wipe_glob(os.path.join(d, "webcache*"))


def g_apex():
    steam_shader(1172470)
    wipe(os.path.join(LA(), "Electronic Arts", "EA Desktop", "Cache"))


def g_pubg():
    d = os.path.join(LA(), "TslGame", "Saved")
    wipe(os.path.join(d, "Logs"))
    wipe(os.path.join(d, "Crashes"))
    wipe_glob(os.path.join(d, "webcache*"))
    steam_shader(578080)


# ---------------------------------------------------------------- bios raporu
def v4_bios():
    d = T.scan()
    if not d:
        return "tarama yapılamadı"
    warns = [n for n, s, _ in T.bios_checks(d) if s == "warn"]
    return ("BIOS'ta düzeltilecek: " + ", ".join(warns)) if warns else "BIOS ayarları uygun görünüyor"


# ---------------------------------------------------------------- doğrulama
def _plan_ok():
    return "nexa" in run("powercfg /getactivescheme").lower()


def _svc_off(name):
    return "DISABLED" in run('sc qc "%s"' % name).upper()


CHECKS = {
    "power": ("Performans güç planı", lambda: _plan_ok() or "ultimate" in run("powercfg /getactivescheme").lower()
              or "8c5e7fda" in run("powercfg /getactivescheme").lower()),
    "faststart": ("Hızlı başlatma kapalı", lambda: rv(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Power",
                                                      "HiberbootEnabled") == 0),
    "input": ("Fare ivmesi kapalı", lambda: str(rv(HKCU, r"Control Panel\Mouse", "MouseSpeed")) == "0"),
    "gamemode": ("Game DVR kapalı", lambda: rv(HKCU, r"System\GameConfigStore", "GameDVR_Enabled") == 0),
    "mmcss": ("Oyun önceliği / ağ kısıtlaması", lambda: rv(
        HKLM, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "NetworkThrottlingIndex") == 0xFFFFFFFF),
    "hags": ("GPU zamanlama (HAGS)", lambda: rv(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
                                                "HwSchMode") == 2),
    "privacy": ("Telemetri kapalı", lambda: rv(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                                               "AllowTelemetry") == 0),
    "services": ("Telemetri servisi kapalı", lambda: _svc_off("DiagTrack")),
}

# (id, grup, ad, açıklama, fonksiyon, doğrulama anahtarı)
ITEMS = [
    ("v4_restore", "Güvenlik", "Geri yükleme noktası", "Başlamadan önce sistem yedeği alır", T.t_restore, None),
    ("v4_bios", "BIOS", "BIOS optimizasyon raporu", "XMP, ReBAR, Secure Boot, TPM, çift kanal kontrolü", v4_bios, None),
    ("v4_win10", "Windows 10", "Windows 10 optimizasyonu", "Cortana, haber paneli, web araması kapalı (Win10'da çalışır)", v4_win10, None),
    ("v4_win11", "Windows 11", "Windows 11 optimizasyonu", "Widgets, Chat, Copilot, klasik menü (Win11'de çalışır)", v4_win11, None),
    ("v4_power", "Güç", "Nexa Ultimate güç planı", "CPU %100, çekirdek park, USB/PCIe/disk tasarrufu kapalı", v4_power, "power"),
    ("v4_pthrottle", "Güç", "Güç kısıtlamasını kapat", "Windows'un CPU'yu arka planda kısmasını engeller", T.t_pthrottle, None),
    ("v4_faststart", "Güç", "Hızlı başlatmayı kapat", "Zamanlayıcı ve sürücü takılmalarını önler", T.t_faststart, "faststart"),
    ("v4_bgkill", "CPU", "Arka plan uygulamalarını kapat", "OneDrive, Teams, Skype, Widgets, güncelleyiciler kapatılır", v4_bgkill, None),
    ("v4_startup", "CPU", "Başlangıç yükünü azalt", "Gereksiz otomatik başlatmalar ve Edge/Chrome arka planı kapalı", v4_startup, None),
    ("v4_services", "CPU", "Gereksiz servisler", "Telemetri, Fax, harita, uzak kayıt vb. kapalı, Xbox servisleri isteğe bağlı", v4_services, "services"),
    ("v4_tasks", "CPU", "Telemetri görevleri", "Arka planda CPU yiyen zamanlanmış görevler kapalı", v4_tasks, None),
    ("v4_privacy", "CPU", "Veri toplama ve reklamlar", "Telemetri, öneriler, etkinlik geçmişi, reklam kimliği kapalı", v4_privacy, "privacy"),
    ("v4_defender", "CPU", "Defender CPU sınırı", "Koruma açık kalır, tarama yükü düşürülür", v4_defender, None),
    ("v4_timer", "Gecikme", "Sistem zamanlayıcı", "Dynamic tick kapalı, yüksek çözünürlüklü timer", v4_timer, None),
    ("v4_input", "Gecikme", "Fare ve klavye gecikmesi", "İvme kapalı, 1:1 fare eğrisi, klavye hızı maksimum, yapışkan tuşlar kapalı", v4_input, "input"),
    ("v4_mmcss", "Gecikme", "CPU / GPU oyun önceliği", "MMCSS oyun profili, ağ kısıtlaması kapalı", v4_mmcss, "mmcss"),
    ("v4_network", "Gecikme", "Ağ ve ping optimizasyonu", "Nagle, TCP, QoS, hızlı DNS + DoH, önbellek temizliği", v4_network, None),
    ("v4_nic", "Gecikme", "Ağ kartı gecikmesi", "Güç tasarrufu, interrupt moderation, LSO kapalı", v4_nic, None),
    ("v4_msi", "Gecikme", "MSI kesme modu", "Ekran kartı ve ağ kartı için düşük gecikmeli kesme", v4_msi, None),
    ("v4_gamemode", "Grafik", "Oyun modu ve Game DVR", "Oyun modu açık, kayıt ve tam ekran optimizasyonu kapalı", v4_gamemode, "gamemode"),
    ("v4_hags", "Grafik", "GPU zamanlama (HAGS)", "Donanım hızlandırmalı GPU zamanlaması", T.t_hags, "hags"),
    ("v4_mpo", "Grafik", "MPO kapat", "Titreme ve kare atlamasını azaltır", T.t_mpo, None),
    ("v4_vbs", "Grafik", "Bellek bütünlüğü (VBS)", "Kapatılır, FPS kazandırır", v4_vbs, None),
    ("v4_gpu", "Grafik", "Ekran kartı ayarları", "NVIDIA maksimum performans, AMD ULPS kapalı", v4_gpu, None),
    ("v4_ram", "Bellek", "RAM optimizasyonu", "Bellek sıkıştırma, paging, servis birleştirme, NTFS belleği", v4_ram, None),
    ("v4_ramclean", "Bellek", "RAM önbelleğini boşalt", "Çalışma kümeleri ve bekleme listesi temizlenir", v4_ramclean, None),
    ("v4_disk", "Disk", "Disk ayarları", "TRIM açık, son erişim kaydı kapalı, SSD'de SysMain kapalı", T.t_disk, None),
    ("v4_diskopt", "Disk", "Disk optimizasyonu", "SSD'de ReTrim, HDD'de birleştirme", T.t_diskopt, None),
    ("v4_clean_sys", "Temizlik", "Sistem önbelleği ve geçici dosyalar", "Temp, Prefetch, Update, WER, dump, font, DNS, çöp kutusu", v4_clean_sys, None),
    ("v4_clean_icons", "Temizlik", "Simge ve küçük resim önbelleği", "Explorer yeniden başlatılarak temizlenir", v4_clean_icons, None),
    ("v4_clean_browsers", "Temizlik", "Tarayıcı önbellekleri", "Chrome, Edge, Brave, Opera, Firefox (şifre ve oturumlar silinmez)", v4_clean_browsers, None),
    ("v4_clean_shaders", "Temizlik", "Ekran kartı shader önbelleği", "NVIDIA, AMD, Intel, DirectX ve Steam shader önbelleği", v4_clean_shaders, None),
    ("v4_clean_apps", "Temizlik", "Uygulama önbellekleri", "Discord, Steam, Epic, Teams önbellekleri", v4_clean_apps, None),
    ("v4_dism", "Temizlik", "Windows bileşen deposu", "Eski güncelleme kalıntıları (uzun sürer)", v4_dism, None),
    ("v4_visualfx", "Görünüm", "Performans görsel ayarları", "Animasyon, şeffaflık ve gölgeler kapalı", v4_visualfx, None),
    ("v4_beauty", "Görünüm", "Masaüstü güzelleştirme", "Koyu tema, dosya uzantıları, Bu Bilgisayar simgesi, ClearType", v4_beauty, None),
    ("v4_wallpaper", "Görünüm", "Nexa duvar kağıdı", "Siyah zemin üzerinde Nexa logosu", v4_wallpaper, None),
    ("v4_fivem_settings", "FiveM", "FiveM oyun ayarları", "Yarışmacı grafik profili, yüksek GPU tercihi (yedek alınır)", v4_fivem_settings, None),
]

GAMES4 = {
    "fivem": ("FiveM", "Cache temizliği\nYüksek CPU önceliği", g_fivem),
    "gta5": ("GTA V", "Shader temizliği\nYüksek CPU önceliği", g_gta5),
    "cs2": ("CS2", "Shader temizliği\nYüksek CPU önceliği", g_cs2),
    "valorant": ("Valorant", "Log / crash temizliği\nOyuna müdahale yok", g_valorant),
    "fortnite": ("Fortnite", "Log / webcache temizliği\nOyuna müdahale yok", g_fortnite),
    "apex": ("Apex Legends", "Shader / EA önbelleği\nOyuna müdahale yok", g_apex),
    "pubg": ("PUBG", "Log / shader temizliği\nOyuna müdahale yok", g_pubg),
}


def register():
    for i, grp, name, desc, fn, chk in ITEMS:
        T.ALL[i] = (grp, name, desc, fn)
        if chk:
            T.VERIFY[i] = CHECKS[chk]
    T.TIERS["V4"] = [x[0] for x in ITEMS]
    T.GAMES4.update(GAMES4)
    T.TIER_GAMES["V4"] = list(GAMES4)
    T.TIER_TITLES["V4"] = "Tweak V4 • Ultimate"
    T.TIER_SCAN["V4"] = True
    for old, chk in (("v1_power", "power"), ("power", "power"), ("v1_mouse", "input"), ("mouse", "input"),
                     ("input", "input"), ("v1_gamemode", "gamemode"), ("gamemode", "gamemode"),
                     ("v1_throttle", "mmcss"), ("priority", "mmcss"), ("v1_hags", "hags"), ("hags", "hags"),
                     ("faststart", "faststart"), ("v1_telemetry", "privacy"), ("v1_services", "services"),
                     ("background", "services")):
        T.VERIFY.setdefault(old, CHECKS[chk])


def clean_games():
    for _, _, f in GAMES4.values():
        try:
            f()
        except Exception:
            pass


def quick_clean(cb):
    steps = [("Arka plan uygulamaları kapatılıyor", v4_bgkill), ("Sistem önbelleği temizleniyor", v4_clean_sys),
             ("Tarayıcı önbellekleri temizleniyor", v4_clean_browsers),
             ("Shader önbelleği temizleniyor", v4_clean_shaders),
             ("Uygulama önbellekleri temizleniyor", v4_clean_apps),
             ("Oyun önbellekleri temizleniyor", clean_games),
             ("RAM önbelleği boşaltılıyor", v4_ramclean)]
    n = len(steps)
    for i, (name, fn) in enumerate(steps):
        cb(i / n, name + "...")
        try:
            msg = fn()
            cb((i + 1) / n, name + (" — " + msg if msg else ""))
        except Exception as e:
            cb((i + 1) / n, "!" + name + " — atlandı (%s)" % type(e).__name__)
    cb(1.0, "Tamamlandı")
