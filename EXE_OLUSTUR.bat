@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Nexa Tweak - EXE Olustur

set PY=
py -3 --version >nul 2>nul && set PY=py -3
if "%PY%"=="" (
    python --version >nul 2>nul && set PY=python
)
if "%PY%"=="" (
    echo Python bulunamadi. python.org adresinden Python 3.10+ kurun.
    echo Kurulumda "Add python.exe to PATH" kutusunu isaretleyin.
    pause
    exit /b 1
)
echo Kullanilan Python: %PY%

%PY% -c "import config,sys; sys.exit(0 if config.SERVER_URL.strip() else 1)"
if errorlevel 1 (
    echo.
    echo config.py icindeki SERVER_URL bos. Once sunucu\KURULUM.md dosyasindaki adimlari yapip
    echo Cloudflare adresini config.py icindeki SERVER_URL satirina yazin.
    pause
    exit /b 1
)

echo [1/3] Paketler kuruluyor...
%PY% -m pip install --upgrade customtkinter pillow pyinstaller
if errorlevel 1 (
    echo Paket kurulumu basarisiz. Internet baglantinizi kontrol edin.
    pause
    exit /b 1
)

echo [2/3] Tek EXE derleniyor, bu birkac dakika surebilir...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin ^
    --icon assets\icon.ico --name NexaTweak ^
    --add-data "assets;assets" --collect-all customtkinter app.py
if errorlevel 1 (
    echo Derleme basarisiz.
    pause
    exit /b 1
)
if not exist dist\NexaTweak.exe (
    echo dist\NexaTweak.exe olusmadi.
    pause
    exit /b 1
)

echo [3/3] Klasorler ve kisayollar hazirlaniyor...
if exist Nexa_Admin rmdir /s /q Nexa_Admin
if exist Nexa_Musteri rmdir /s /q Nexa_Musteri
mkdir Nexa_Admin
mkdir Nexa_Musteri
copy /y dist\NexaTweak.exe Nexa_Admin\NexaTweak.exe >nul
echo admin>Nexa_Admin\admin.flag
copy /y dist\NexaTweak.exe Nexa_Musteri\NexaTweak.exe >nul
powershell -NoProfile -ExecutionPolicy Bypass -File KISAYOL_OLUSTUR.ps1 -Folder "%~dp0Nexa_Admin"

echo.
echo Bitti.
echo   Nexa_Admin   : exe + admin.flag + kisayol (KENDINIZDE kalsin, admin sifresi sunucuda belirlediginiz sifre)
echo   Nexa_Musteri : sadece exe (musteriye bunu verin, kisayolu exe ilk acilista masaustune kendisi olusturur)
echo.
pause
