import os, re, sys, glob, shutil, time, ctypes, subprocess, json, base64
import winreg as wr

CF = 0x08000000
HKLM, HKCU = wr.HKEY_LOCAL_MACHINE, wr.HKEY_CURRENT_USER
SYSROOT = os.environ.get("SystemRoot", r"C:\Windows")


def run(cmd, t=120):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              creationflags=CF, timeout=t, errors="ignore").stdout or ""
    except Exception:
        return ""


def reg(root, path, name, val, kind=wr.REG_DWORD):
    k = wr.CreateKeyEx(root, path, 0, wr.KEY_SET_VALUE | wr.KEY_WOW64_64KEY)
    wr.SetValueEx(k, name, 0, kind, val)
    wr.CloseKey(k)


class _MEM(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("ml", ctypes.c_ulong), ("tp", ctypes.c_ulonglong),
                ("ap", ctypes.c_ulonglong), ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong),
                ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("ae", ctypes.c_ulonglong)]


def ram_gb():
    m = _MEM()
    m.l = ctypes.sizeof(_MEM)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.tp / 1024 ** 3


def wipe(path):
    if not path or not os.path.isdir(path):
        return
    for n in os.listdir(path):
        p = os.path.join(path, n)
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                os.remove(p)
        except Exception:
            pass


def prio(exe):
    reg(HKLM, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\%s\PerfOptions" % exe,
        "CpuPriorityClass", 3)


def L(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def is_ssd():
    out = run('powershell -NoProfile -Command "@(Get-PhysicalDisk | Where-Object MediaType -eq SSD).Count"')
    return out.strip() not in ("", "0")


def t_restore():
    run('powershell -NoProfile -Command "Enable-ComputerRestore -Drive $env:SystemDrive; '
        'Checkpoint-Computer -Description NexaTweak -RestorePointType MODIFY_SETTINGS"')


def t_power():
    out = run("powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    m = re.search(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", out, re.I)
    g = m.group(0) if m else "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    run(f"powercfg -setactive {g}")
    run(f"powercfg -setacvalueindex {g} SUB_PROCESSOR CPMINCORES 100")
    run(f"powercfg -setacvalueindex {g} 2a737441-1930-4402-8d77-b2bebba308a3 "
        f"48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0")
    run(f"powercfg -setactive {g}")
    run("powercfg -h off")


def t_pthrottle():
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling", "PowerThrottlingOff", 1)


def t_faststart():
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Power", "HiberbootEnabled", 0)


def t_netpower():
    run('powershell -NoProfile -Command "Get-NetAdapter -Physical | ForEach-Object '
        '{ Disable-NetAdapterPowerManagement -Name $_.Name -ErrorAction SilentlyContinue }"')


def t_gamemode():
    reg(HKCU, r"Software\Microsoft\GameBar", "AutoGameModeEnabled", 1)
    reg(HKCU, r"Software\Microsoft\GameBar", "AllowAutoGameMode", 1)
    reg(HKCU, r"System\GameConfigStore", "GameDVR_Enabled", 0)
    reg(HKCU, r"System\GameConfigStore", "GameDVR_FSEBehaviorMode", 2)
    reg(HKCU, r"System\GameConfigStore", "GameDVR_HonorUserFSEBehaviorMode", 1)
    reg(HKCU, r"System\GameConfigStore", "GameDVR_DXGIHonorFSEWindowsCompatible", 1)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0)
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\GameDVR", "AllowGameDVR", 0)


def t_hags():
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", 2)


def t_priority():
    p = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    reg(HKLM, p, "NetworkThrottlingIndex", 0xFFFFFFFF)
    reg(HKLM, p, "SystemResponsiveness", 0)
    g = p + r"\Tasks\Games"
    reg(HKLM, g, "GPU Priority", 8)
    reg(HKLM, g, "Priority", 6)
    reg(HKLM, g, "Scheduling Category", "High", wr.REG_SZ)
    reg(HKLM, g, "SFIO Priority", "High", wr.REG_SZ)
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", 38)


def t_mpo():
    reg(HKLM, r"SOFTWARE\Microsoft\Windows\Dwm", "OverlayTestMode", 5)


def t_nvidia():
    base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    for i in range(20):
        sub = f"{base}\\{i:04d}"
        try:
            k = wr.OpenKey(HKLM, sub, 0, wr.KEY_READ | wr.KEY_WOW64_64KEY)
            desc = wr.QueryValueEx(k, "DriverDesc")[0]
            wr.CloseKey(k)
        except OSError:
            continue
        if "nvidia" in desc.lower():
            reg(HKLM, sub, "PerfLevelSrc", 0x2222)
            reg(HKLM, sub, "PowerMizerEnable", 1)
            reg(HKLM, sub, "PowerMizerLevel", 1)
            reg(HKLM, sub, "PowerMizerLevelAC", 1)


def t_mouse():
    for n in ("MouseSpeed", "MouseThreshold1", "MouseThreshold2"):
        reg(HKCU, r"Control Panel\Mouse", n, "0", wr.REG_SZ)


def t_input():
    t_mouse()
    reg(HKLM, r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters", "MouseDataQueueSize", 20)
    reg(HKLM, r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters", "KeyboardDataQueueSize", 20)


def t_timer():
    run("bcdedit /set disabledynamictick yes")
    run("bcdedit /deletevalue useplatformclock")
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel", "GlobalTimerResolutionRequests", 1)


def _tcp_interfaces():
    base = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    k = wr.OpenKey(HKLM, base, 0, wr.KEY_READ | wr.KEY_WOW64_64KEY)
    i = 0
    while True:
        try:
            sub = wr.EnumKey(k, i)
        except OSError:
            break
        i += 1
        try:
            reg(HKLM, base + "\\" + sub, "TcpAckFrequency", 1)
            reg(HKLM, base + "\\" + sub, "TCPNoDelay", 1)
            reg(HKLM, base + "\\" + sub, "TcpDelAckTicks", 0)
        except Exception:
            pass


def t_network_lite():
    run("netsh int tcp set global autotuninglevel=normal")
    run("netsh int tcp set global rss=enabled")
    run("netsh int tcp set global ecncapability=disabled")
    _tcp_interfaces()
    run("ipconfig /flushdns")


def t_network():
    run("netsh int tcp set global autotuninglevel=normal")
    run("netsh int tcp set global rss=enabled")
    run("netsh int tcp set global ecncapability=disabled")
    run("netsh int tcp set global timestamps=disabled")
    _tcp_interfaces()
    run("ipconfig /flushdns")


def t_dodl():
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization", "DODownloadMode", 0)


def t_ram():
    if ram_gb() >= 15:
        reg(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
            "DisablePagingExecutive", 1)
        run('powershell -NoProfile -Command "Disable-MMAgent -MemoryCompression"')


def t_svchost():
    g = ram_gb()
    if g >= 8:
        reg(HKLM, r"SYSTEM\CurrentControlSet\Control", "SvcHostSplitThresholdInKB", int(g * 1024 * 1024))


def t_disk():
    run("fsutil behavior set disablelastaccess 1")
    run("fsutil behavior set DisableDeleteNotify 0")
    if is_ssd():
        run("sc config SysMain start= disabled")
        run("sc stop SysMain")


def t_diskopt():
    run("defrag %SystemDrive% /O", 600)


def t_diskclean():
    run("net stop wuauserv")
    run("net stop bits")
    wipe(os.path.join(SYSROOT, "SoftwareDistribution", "Download"))
    run("net start bits")
    run("net start wuauserv")
    wipe(os.path.join(SYSROOT, "Prefetch"))
    wipe(os.path.join(SYSROOT, "ServiceProfiles", "NetworkService", "AppData", "Local",
                      "Microsoft", "Windows", "DeliveryOptimization", "Cache"))
    ex = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Explorer")
    for f in glob.glob(os.path.join(ex, "thumbcache_*.db")) + glob.glob(os.path.join(ex, "iconcache_*.db")):
        try:
            os.remove(f)
        except Exception:
            pass
    run('powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"')


def _visual():
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
        "GlobalUserDisabled", 1)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 2)


def t_background_lite():
    run("sc config DiagTrack start= disabled")
    run("sc stop DiagTrack")
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0)
    _visual()


def t_background():
    for s in ("DiagTrack", "dmwappushservice", "MapsBroker", "RetailDemo"):
        run(f"sc config {s} start= disabled")
        run(f"sc stop {s}")
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0)
    _visual()


def t_clean_lite():
    wipe(os.environ.get("TEMP", ""))
    wipe(os.path.join(SYSROOT, "Temp"))


def t_clean():
    wipe(os.environ.get("TEMP", ""))
    wipe(os.path.join(SYSROOT, "Temp"))
    wipe(os.path.join(SYSROOT, "Minidump"))
    wipe(os.path.join(os.environ.get("LOCALAPPDATA", ""), "CrashDumps"))


def t_vbs():
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity",
        "Enabled", 0)


def t_fivem():
    d = os.path.join(os.environ.get("LOCALAPPDATA", ""), "FiveM", "FiveM.app")
    for n in ("server-cache", "server-cache-priv"):
        wipe(os.path.join(d, "data", n))
    wipe(os.path.join(d, "data", "cache", "browser"))
    exes = ["FiveM.exe", "GTA5.exe", "FiveM_GTAProcess.exe"]
    exes += [os.path.basename(p) for p in glob.glob(os.path.join(d, "FiveM*_GTAProcess.exe"))]
    for e in set(exes):
        prio(e)


def t_cs2():
    prio("cs2.exe")


def t_val():
    d = os.path.join(os.environ.get("LOCALAPPDATA", ""), "VALORANT", "Saved")
    wipe(os.path.join(d, "Logs"))
    wipe(os.path.join(d, "Crashes"))


def v1_power():
    run("powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    run("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
    for t in ("standby-timeout-ac", "hibernate-timeout-ac", "monitor-timeout-ac", "disk-timeout-ac"):
        run(f"powercfg /change {t} 0")
    run("powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 "
        "893dee8e-2bef-41e0-89c6-b55d0929964c 100")
    run("powercfg /S SCHEME_CURRENT")


def v1_visual():
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 2)
    reg(HKCU, r"Control Panel\Desktop\WindowMetrics", "MinAnimate", "0", wr.REG_SZ)
    reg(HKCU, r"Control Panel\Desktop", "MenuShowDelay", "0", wr.REG_SZ)
    reg(HKCU, r"Control Panel\Desktop", "MouseHoverTime", "0", wr.REG_SZ)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAnimations", 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0)


def v1_temp():
    wipe(os.environ.get("TEMP", ""))
    wipe(os.path.join(SYSROOT, "Temp"))
    wipe(os.path.join(SYSROOT, "Prefetch"))
    wipe(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"))
    wipe(os.path.join(SYSROOT, "SoftwareDistribution", "Download"))


def v1_gamebar():
    reg(HKCU, r"System\GameConfigStore", "GameDVR_Enabled", 0)
    reg(HKCU, r"System\GameConfigStore", "GameDVR_FSEBehaviorMode", 2)
    reg(HKCU, r"Software\Microsoft\GameBar", "AllowAutoGameMode", 0)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0)


def v1_tcp():
    run("netsh int tcp set global autotuninglevel=normal")
    run("netsh int tcp set global rss=enabled")
    run("netsh int tcp set global chimney=disabled")
    run("netsh int tcp set global ecncapability=disabled")
    run("netsh int tcp set global timestamps=disabled")
    run("netsh int tcp set heuristics disabled")
    run("netsh int tcp set supplemental internet congestionprovider=ctcp")
    run("ipconfig /flushdns")


def v1_dns():
    run('powershell -NoProfile -Command "Get-NetAdapter -Physical | Where-Object Status -eq Up | '
        'ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex '
        '-ServerAddresses (\'1.1.1.1\',\'8.8.8.8\') }"')
    run("ipconfig /flushdns")


def v1_services():
    for svc in ("SysMain", "DiagTrack", "dmwappushservice", "Fax", "RemoteRegistry", "RetailDemo", "MapsBroker"):
        run(f'sc config "{svc}" start= disabled')
        run(f'net stop "{svc}"')


def v1_menu():
    reg(HKCU, r"Control Panel\Desktop", "MenuShowDelay", "0", wr.REG_SZ)
    reg(HKCU, r"Control Panel\Mouse", "MouseHoverTime", "0", wr.REG_SZ)
    reg(HKLM, r"SYSTEM\CurrentControlSet\Control", "WaitToKillServiceTimeout", "2000", wr.REG_SZ)


def v1_prefetch():
    p = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    reg(HKLM, p, "EnablePrefetcher", 3)
    reg(HKLM, p, "EnableSuperfetch", 3)


def v1_notif():
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled", 0)


def v1_explorer():
    p = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    reg(HKCU, p, "DisableThumbnailCache", 1)
    reg(HKCU, p, "Start_TrackDocs", 0)


def v1_maint():
    reg(HKLM, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance", "MaintenanceDisabled", 1)


def v1_doh():
    run("netsh dns add global doh=yes")
    run("netsh dns add encryption server=1.1.1.1 dohtemplate=https://cloudflare-dns.com/dns-query autoupgrade=yes")
    run("netsh dns add encryption server=8.8.8.8 dohtemplate=https://dns.google/dns-query autoupgrade=yes")
    run("ipconfig /flushdns")


def v1_bgapps():
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications", "GlobalUserDisabled", 1)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "BackgroundAppGlobalToggle", 0)


def v1_fso():
    reg(HKCU, r"System\GameConfigStore", "GameDVR_FSEBehavior", 2)
    reg(HKCU, r"System\GameConfigStore", "GameDVR_HonorUserFSEBehaviorMode", 1)
    reg(HKCU, r"System\GameConfigStore", "GameDVR_DXGIHonorFSEWindowsCompatible", 1)


def v1_ctx():
    run(r'reg add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve')


def v1_copilot():
    reg(HKCU, r"Software\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", 1)
    reg(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ShowCopilotButton", 0)


def v1_telemetry():
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0)
    reg(HKLM, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection", "AllowTelemetry", 0)


def v1_widgets():
    reg(HKLM, r"SOFTWARE\Policies\Microsoft\Dsh", "AllowNewsAndInterests", 0)


def detect_gpu():
    out = run('powershell -NoProfile -Command "(Get-CimInstance Win32_VideoController).Name"')
    names = [x.strip() for x in out.splitlines() if x.strip()]
    full = " ".join(names).upper()
    if "NVIDIA" in full:
        return "NVIDIA", names
    if "AMD" in full or "RADEON" in full:
        return "AMD", names
    if "INTEL" in full:
        return "INTEL", names
    return "UNKNOWN", names


GPU_TIPS = {
    "NVIDIA": ["NVIDIA Denetim Masası > 3D Ayarları:", "Güç yönetimi: Maksimum performans",
               "Düşük gecikme modu: Açık", "Doku filtreleme: Yüksek performans", "Önceden işlenen kare: 1"],
    "AMD": ["AMD Radeon Yazılımı > Oyun:", "Radeon Anti-Lag: Açık", "Radeon Boost: Açık",
            "Görüntü Keskinleştirme: Açık", "GPU Ayarı: Rage modu"],
    "INTEL": ["Intel Grafik Komut Merkezi:", "Güç planı: Maksimum performans",
              "Doku kalitesi: Performans", "Dikey eşitleme: Kapalı"],
    "UNKNOWN": ["Ekran kartı tespit edilemedi."],
}


def gpu_tips(brand):
    return GPU_TIPS.get(brand, GPU_TIPS["UNKNOWN"])


ALL = {
    "v1_restore": ("Güvenlik", "Geri yükleme noktası", "İşlemden önce sistem yedeği alır", t_restore),
    "v1_power": ("Güç", "Yüksek performans güç planı", "Uyku ve ekran kapanma süreleri kapalı, CPU %100", v1_power),
    "v1_visual": ("Görünüm", "Görsel efektler", "Animasyon ve şeffaflık kapalı, arayüz hızlanır", v1_visual),
    "v1_temp": ("Temizlik", "Geçici dosya temizliği", "Temp, Prefetch ve Update önbelleği temizlenir", v1_temp),
    "v1_gamebar": ("Oyun", "Game Bar kapat", "Arka plan kaydı ve Game DVR kapalı", v1_gamebar),
    "v1_tcp": ("Ağ", "TCP / ağ optimizasyonu", "TCP ayarları, CTCP, DNS önbellek temizliği", v1_tcp),
    "v1_dns": ("Ağ", "Hızlı DNS", "Cloudflare 1.1.1.1 ve Google 8.8.8.8", v1_dns),
    "v1_services": ("Temizlik", "Gereksiz servisler", "Telemetri, Fax, uzak kayıt defteri vb. kapalı", v1_services),
    "v1_menu": ("Görünüm", "Menü gecikmeleri", "Menü ve kapanış gecikmeleri düşürülür", v1_menu),
    "v1_disk": ("Disk", "Disk optimizasyonu", "SSD'de ReTrim, HDD'de birleştirme", t_diskopt),
    "v1_nagle": ("Ağ", "Nagle algoritması", "Paket gecikmesi azalır, ping düşer", _tcp_interfaces),
    "v1_mouse": ("Gecikme", "Fare ivmesi", "Fare ivmesi kapalı, ham hassasiyet", t_mouse),
    "v1_throttle": ("Oyun", "Ağ kısıtlaması ve oyun önceliği", "Network throttling kapalı, oyun için yüksek öncelik", t_priority),
    "v1_prefetch": ("Bellek", "Prefetch", "Prefetch ve Superfetch en iyi seviyeye alınır", v1_prefetch),
    "v1_notif": ("Görünüm", "Bildirimler", "Bildirim balonları kapalı", v1_notif),
    "v1_explorer": ("Görünüm", "Dosya gezgini", "Küçük resim önbelleği ve son belgeler kapalı", v1_explorer),
    "v1_maint": ("Temizlik", "Otomatik bakım", "Arka plan bakım görevi kapalı", v1_maint),
    "v1_hags": ("Oyun", "GPU zamanlama (HAGS)", "Donanım hızlandırmalı GPU zamanlaması", t_hags),
    "v1_vbs": ("Gelişmiş", "Bellek bütünlüğü (VBS)", "Kapatılır, FPS kazandırır", t_vbs),
    "v1_doh": ("Ağ", "DoH DNS şifreleme", "DNS sorguları şifreli gider", v1_doh),
    "v1_bgapps": ("Temizlik", "Arka plan uygulamaları", "Arka planda çalışan uygulamalar kapalı", v1_bgapps),
    "v1_gamemode": ("Oyun", "Oyun modu", "Windows oyun modu açık", t_gamemode),
    "v1_fso": ("Oyun", "Tam ekran optimizasyonları", "Tam ekran optimizasyonları kapalı", v1_fso),
    "v1_ctx": ("Görünüm", "Klasik sağ tık menüsü", "Windows 11'de eski hızlı menü", v1_ctx),
    "v1_copilot": ("Temizlik", "Copilot", "Windows Copilot kapalı", v1_copilot),
    "v1_telemetry": ("Temizlik", "Telemetri", "Veri toplama kapalı", v1_telemetry),
    "v1_widgets": ("Temizlik", "Widgets", "Haberler ve widget paneli kapalı", v1_widgets),
    "restore": ("Güvenlik", "Geri yükleme noktası", "İşlemden önce sistem yedeği alır", t_restore),
    "power": ("Güç", "Ultimate Performance güç planı", "Çekirdek park, USB askıya alma ve hibernate kapalı", t_power),
    "pthrottle": ("Güç", "Güç kısıtlamasını kapat", "Windows'un CPU'yu arka planda kısmasını engeller", t_pthrottle),
    "faststart": ("Güç", "Hızlı başlatmayı kapat", "Zamanlayıcı ve sürücü kaynaklı takılmaları önler", t_faststart),
    "netpower": ("Güç", "Ağ kartı güç tasarrufu kapat", "Ping dalgalanması ve kopmaları azaltır", t_netpower),
    "gamemode": ("Oyun", "Oyun modu ve Game DVR", "Oyun modu açık, arka plan kaydı kapalı", t_gamemode),
    "hags": ("Oyun", "GPU zamanlama (HAGS)", "Donanım hızlandırmalı GPU zamanlaması", t_hags),
    "priority": ("Oyun", "CPU / GPU oyun önceliği", "Oyunlar için yüksek öncelik profili", t_priority),
    "mpo": ("Oyun", "MPO kapat", "Takılma ve titremeyi azaltır", t_mpo),
    "nvidia": ("Oyun", "NVIDIA maksimum performans", "Ekran kartı güç modunu sabit yüksek tutar", t_nvidia),
    "mouse": ("Gecikme", "Fare ayarları", "Fare ivmesi kapalı", t_mouse),
    "input": ("Gecikme", "Girdi gecikmesi", "Fare ivmesi kapalı, klavye/fare kuyruğu küçük", t_input),
    "timer": ("Gecikme", "Sistem zamanlayıcı", "Dynamic tick kapalı, yüksek çözünürlük", t_timer),
    "network_lite": ("Gecikme", "Ağ gecikmesi optimizasyonu", "Nagle kapalı, TCP ayarları, DNS temizliği", t_network_lite),
    "network": ("Gecikme", "Ağ gecikmesi / ping", "Nagle kapalı, gelişmiş TCP ayarları, DNS temizliği", t_network),
    "dodl": ("Gecikme", "Arka plan ağ yükünü azalt", "Windows Update teslim optimizasyonu kapalı", t_dodl),
    "ram": ("Bellek", "RAM optimizasyonu", "Bellek sıkıştırma ve paging executive (16 GB+)", t_ram),
    "svchost": ("Bellek", "Servis bellek ayarı", "Servis süreçlerini birleştirir, bellek yükünü azaltır", t_svchost),
    "disk": ("Disk", "Disk ayarları", "TRIM açık, son erişim kaydı kapalı, SSD'de SysMain kapalı", t_disk),
    "diskopt": ("Disk", "Disk optimizasyonu", "SSD'de ReTrim, HDD'de birleştirme", t_diskopt),
    "diskclean": ("Disk", "Derin disk temizliği", "Update önbelleği, Prefetch, küçük resim, çöp kutusu", t_diskclean),
    "background_lite": ("Temizlik", "Arka plan ve telemetri", "Telemetri ve şeffaflık kapalı", t_background_lite),
    "background": ("Temizlik", "Arka plan ve telemetri", "Gereksiz servisler, telemetri ve şeffaflık kapalı", t_background),
    "clean_lite": ("Temizlik", "Geçici dosya temizliği", "Temp klasörlerini temizler", t_clean_lite),
    "clean": ("Temizlik", "Geçici dosya temizliği", "Temp, crash dump ve minidump temizliği", t_clean),
    "vbs": ("Gelişmiş", "Bellek bütünlüğü (VBS) kapat", "FPS kazandırır", t_vbs),
}

TIERS = {
    "V1": ["v1_restore", "v1_temp", "v1_visual", "v1_gamebar", "v1_mouse", "v1_power",
           "v1_notif", "v1_menu"],
    "V2": ["v1_restore", "v1_temp", "v1_visual", "v1_gamebar", "v1_mouse", "v1_power",
           "v1_notif", "v1_menu", "v1_tcp", "v1_dns", "v1_services", "v1_throttle",
           "v1_disk", "v1_nagle", "v1_gamemode", "v1_hags"],
    "V3": ["v1_restore", "v1_temp", "v1_visual", "v1_gamebar", "v1_mouse", "v1_power",
           "v1_notif", "v1_menu", "v1_tcp", "v1_dns", "v1_services", "v1_throttle",
           "v1_disk", "v1_nagle", "v1_gamemode", "v1_hags", "v1_prefetch", "v1_explorer",
           "v1_bgapps", "v1_telemetry", "v1_fso", "pthrottle", "faststart", "netpower",
           "mpo", "nvidia", "timer", "ram"],
}

GAMES = {
    "fivem": ("FiveM", "Cache temizliği\nYüksek CPU önceliği", t_fivem),
    "cs2": ("CS2", "Yüksek CPU önceliği", t_cs2),
    "valorant": ("Valorant", "Log / crash temizliği\nOyuna müdahale yok", t_val),
}

TIER_GAMES = {"V1": [], "V2": ["fivem", "cs2", "valorant"], "V3": ["fivem", "cs2", "valorant"]}

TIER_TITLES = {
    "V1": "Tweak V1 • Temel",
    "V2": "Tweak V2 • Oyuncu",
    "V3": "Tweak V3 • Premium",
}

TIER_SCAN = {"V1": False, "V2": False, "V3": True}

GAMES4 = {}
VERIFY = {}
OFF_BY_DEFAULT = set()
ORDER = ["V1", "V2", "V3", "V4"]


def game_table(tier):
    return GAMES4 if tier == "V4" else GAMES


def access(tier):
    """Bir key sadece kendi paketini açar (V4 key sadece V4)."""
    return [tier]


def tier_items(tier):
    return [(i, ALL[i][0], ALL[i][1], ALL[i][2]) for i in TIERS.get(tier, [])]


def plan(tier, games, skip=None):
    skip = skip or set()
    tasks = [(i, ALL[i][1], ALL[i][3]) for i in TIERS.get(tier, []) if i not in skip]
    gt = game_table(tier)
    allowed = TIER_GAMES.get(tier, [])
    tasks += [("game:" + g, gt[g][0] + " optimizasyonu", gt[g][2]) for g in games if g in gt and g in allowed]
    return tasks


def verify(ran):
    out, seen = [], set()
    for tid in ran:
        v = VERIFY.get(tid)
        if v and v[0] not in seen:
            seen.add(v[0])
            try:
                out.append((v[0], bool(v[1]())))
            except Exception:
                out.append((v[0], False))
    return out


def _log_path():
    root = os.environ.get("APPDATA") or os.path.expanduser("~")
    p = os.path.join(root, "Nexa")
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, "last_run.log")


def run_all(tier, games, cb, skip=None):
    tasks = plan(tier, games, skip)
    v4mode = tier == "V4"
    n = max(len(tasks), 1)
    ok = bad = 0
    ran, lines = [], []
    for i, (tid, name, fn) in enumerate(tasks):
        cb(i / n * (0.96 if v4mode else 1.0), name + "...")
        try:
            msg = fn()
            ok += 1
            ran.append(tid)
            label = name + (" — " + msg if v4mode and isinstance(msg, str) and msg else "")
            lines.append("OK   " + label)
            cb((i + 1) / n * (0.96 if v4mode else 1.0), label)
        except Exception as e:
            if not v4mode:
                cb((i + 1) / n, name)
                time.sleep(0.35)
                continue
            bad += 1
            label = "%s — atlandı (%s)" % (name, type(e).__name__)
            lines.append("HATA " + label)
            cb((i + 1) / n * 0.96, "!" + label)
        time.sleep(0.2 if v4mode else 0.35)
    if not v4mode:
        cb(1.0, "Tamamlandı")
        return ok, bad
    cb(0.97, "Doğrulama...")
    res = verify(ran)
    for lab, good in res:
        t = ("Etkin: " if good else "Etkin değil (yeniden başlatınca devreye girer): ") + lab
        lines.append("DOGRULA " + t)
        cb(0.98, "#" + t)
    good_n = sum(1 for _, g in res if g)
    if res:
        cb(0.99, "#Doğrulama sonucu: %d / %d ayar etkin" % (good_n, len(res)))
    try:
        with open(_log_path(), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception:
        pass
    cb(1.0, "Tamamlandı")
    return ok, bad


def bios_restart():
    run("shutdown /r /fw /t 3")


def reboot_now():
    run("shutdown /r /t 0 /f")


def open_restore():
    subprocess.Popen("rstrui.exe", shell=True, creationflags=CF)


_PS = r'''
$ErrorActionPreference='SilentlyContinue'
$cpu=Get-CimInstance Win32_Processor | select -First 1
$gpu=@(Get-CimInstance Win32_VideoController | % {$_.Name})
$mem=@(Get-CimInstance Win32_PhysicalMemory | % {[pscustomobject]@{s=$_.Speed;c=$_.ConfiguredClockSpeed;g=[math]::Round($_.Capacity/1GB)}})
$disk=@(Get-PhysicalDisk | % {[string]$_.MediaType})
$sb=$null; try{$sb=Confirm-SecureBootUEFI}catch{}
$tpm=$null; try{$tpm=(Get-Tpm).TpmPresent}catch{}
$bios=Get-CimInstance Win32_BIOS
[pscustomobject]@{cpu=$cpu.Name.Trim();cores=$cpu.NumberOfCores;threads=$cpu.NumberOfLogicalProcessors;gpu=$gpu;mem=$mem;disk=$disk;sb=$sb;tpm=$tpm;bios=($bios.Manufacturer+' '+$bios.SMBIOSBIOSVersion)} | ConvertTo-Json -Depth 4 -Compress
'''


def scan():
    try:
        enc = base64.b64encode(_PS.encode("utf-16-le")).decode()
        out = subprocess.check_output(["powershell", "-NoProfile", "-EncodedCommand", enc],
                                      creationflags=CF, text=True, timeout=90, errors="ignore")
        return json.loads(out)
    except Exception:
        return {}


def rebar_mb():
    out = run("nvidia-smi -q -d MEMORY")
    m = re.search(r"BAR1 Memory Usage\s+Total\s+:\s+(\d+)\s+MiB", out)
    return int(m.group(1)) if m else None


def summary(d):
    mem = L(d.get("mem"))
    total = sum(int(m.get("g") or 0) for m in mem)
    cfg = max([int(m.get("c") or 0) for m in mem] or [0])
    return {
        "cpu": f'{d.get("cpu", "?")}\n{d.get("cores", "?")} çekirdek / {d.get("threads", "?")} thread',
        "gpu": "\n".join(L(d.get("gpu"))) or "?",
        "ram": f"{total} GB" + (f" • {cfg} MHz" if cfg else "") + f"\n{len(mem)} modül",
        "disk": ", ".join(sorted(set(str(x) for x in L(d.get("disk")) if x))) or "?",
    }


def bios_checks(d):
    r = []
    mem = L(d.get("mem"))
    rated = max([int(m.get("s") or 0) for m in mem] or [0])
    cfg = max([int(m.get("c") or 0) for m in mem] or [0])
    if cfg:
        if cfg <= 2400 or cfg + 100 < rated:
            r.append(("XMP / EXPO", "warn", f"RAM {cfg} MHz çalışıyor, varsayılan hızda. BIOS'ta XMP/EXPO profilini aç."))
        else:
            r.append(("XMP / EXPO", "ok", f"RAM {cfg} MHz çalışıyor."))
    else:
        r.append(("XMP / EXPO", "info", "RAM hızı okunamadı."))
    if len(mem) == 1:
        r.append(("Çift kanal", "warn", "Tek RAM modülü var. 2 modül takarak çift kanala geç."))
    elif len(mem) >= 2:
        r.append(("Çift kanal", "ok", f"{len(mem)} modül takılı."))
    else:
        r.append(("Çift kanal", "info", "RAM modülleri okunamadı."))
    rb = rebar_mb()
    if rb is None:
        r.append(("Resizable BAR", "info", "Okunamadı (NVIDIA kartı ve sürücüsü gerekir)."))
    elif rb > 256:
        r.append(("Resizable BAR", "ok", "Açık."))
    else:
        r.append(("Resizable BAR", "warn", "Kapalı görünüyor. BIOS'ta Above 4G Decoding ve Resizable BAR'ı aç."))
    sb = d.get("sb")
    if sb is True:
        r.append(("Secure Boot", "ok", "Açık (Valorant için gerekli)."))
    elif sb is False:
        r.append(("Secure Boot", "warn", "Kapalı. Valorant için BIOS'tan aç."))
    else:
        r.append(("Secure Boot", "info", "Okunamadı (Legacy BIOS olabilir)."))
    tpm = d.get("tpm")
    if tpm is True:
        r.append(("TPM 2.0", "ok", "Mevcut ve açık."))
    elif tpm is False:
        r.append(("TPM 2.0", "warn", "Kapalı. BIOS'tan fTPM / PTT aç."))
    else:
        r.append(("TPM 2.0", "info", "Okunamadı."))
    disks = [str(x).upper() for x in L(d.get("disk"))]
    if "SSD" in disks:
        r.append(("Depolama", "ok", "SSD mevcut. Oyunları SSD'ye kur."))
    elif "HDD" in disks:
        r.append(("Depolama", "warn", "Sadece HDD görünüyor. Oyunu SSD'ye taşımak takılmayı çok azaltır."))
    else:
        r.append(("Depolama", "info", "Disk tipi okunamadı."))
    r.append(("BIOS sürümü", "info", str(d.get("bios", "?"))))
    return r


import v4  # noqa: E402

v4.register()
