@echo off
setlocal EnableDelayedExpansion
title Snoop Builder - Installer

echo ============================================================
echo   SNOOP BUILDER - Installation
echo ============================================================
echo.

REM ---------- 1. Python ----------
echo [1/6] Verification de Python...
where python >nul 2>&1
if errorlevel 1 (
    echo     Python non detecte. Installation via winget...
    where winget >nul 2>&1
    if errorlevel 1 (
        echo     [ERREUR] winget introuvable.
        echo     Installe Python manuellement : https://www.python.org/downloads/
        echo     Coche "Add Python to PATH" pendant l'installation.
        pause
        exit /b 1
    )
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo     [ERREUR] Echec installation Python via winget.
        pause
        exit /b 1
    )
    echo     Python installe. Ferme et relance ce script pour que le PATH soit pris en compte.
    pause
    exit /b 0
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo     Python detecte : !PYVER!
echo.

REM ---------- 2. pip ----------
echo [2/6] Mise a jour de pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo     [ATTENTION] Echec mise a jour pip. On continue.
)
echo     pip a jour.
echo.

REM ---------- 3. Dependances builder ----------
echo [3/6] Installation des dependances du builder...
python -m pip install --quiet "PyQt5>=5.15.9,<6" requests selenium webdriver-manager
if errorlevel 1 (
    echo     [ERREUR] Echec installation PyQt5 / requests / selenium.
    pause
    exit /b 1
)
echo     PyQt5 + requests + selenium OK.
echo.

REM ---------- 4. Dependances payload ----------
echo [4/6] Installation des dependances du payload...
python -m pip install --quiet psutil Pillow pycryptodomex browser-history
python -m pip install --quiet pywin32
if errorlevel 1 (
    echo     [ATTENTION] Certaines dependances ont echoue. Le tool peut quand meme fonctionner.
)
echo     Dependances payload OK.
echo.

REM ---------- 5. PyInstaller ----------
echo [5/6] Installation de PyInstaller...
python -m pip install --quiet pyinstaller
if errorlevel 1 (
    echo     [ATTENTION] Echec installation PyInstaller.
) else (
    echo     PyInstaller OK.
)
echo.

REM ---------- 6. Nuitka + compilateur C ----------
echo [6/6] Installation de Nuitka + compilateur C...
python -m pip install --quiet nuitka ordered-set zstandard
if errorlevel 1 (
    echo     [ATTENTION] Echec installation Nuitka.
) else (
    echo     Nuitka OK.
)

where gcc >nul 2>&1
if errorlevel 1 (
    where clang >nul 2>&1
    if errorlevel 1 (
        echo     Aucun compilateur C detecte.
        echo     Installation de gcc via winget...
        where winget >nul 2>&1
        if errorlevel 1 (
            echo     [ATTENTION] winget introuvable. Installe MinGW-w64 manuellement.
            echo     https://www.mingw-w64.org/downloads/
        ) else (
            winget install -e --id BrechtSanders.WinLibs.POSIX.UCRT --accept-source-agreements --accept-package-agreements
            if errorlevel 1 (
                echo     [ATTENTION] Echec installation gcc via winget.
                echo     Nuitka telechargera MinGW automatiquement au premier build.
            ) else (
                echo     gcc installe.
            )
        )
    ) else (
        echo     Compilateur clang detecte.
    )
) else (
    echo     Compilateur gcc detecte.
)
echo.

REM ---------- Verification finale ----------
echo ============================================================
echo   Verification finale
echo ============================================================
python -c "import PyQt5; print('  PyQt5          OK')" 2>nul || echo   PyQt5          MANQUANT
python -c "import requests; print('  requests       OK')" 2>nul || echo   requests       MANQUANT
python -c "import psutil; print('  psutil         OK')" 2>nul || echo   psutil         MANQUANT
python -c "import PIL; print('  Pillow         OK')" 2>nul || echo   Pillow         MANQUANT
python -c "import Cryptodome; print('  pycryptodomex  OK')" 2>nul || echo   pycryptodomex  MANQUANT
python -c "import win32crypt; print('  pywin32        OK')" 2>nul || echo   pywin32        MANQUANT
python -c "import selenium; print('  selenium       OK')" 2>nul || echo   selenium       MANQUANT
python -c "import webdriver_manager; print('  wdm            OK')" 2>nul || echo   wdm            MANQUANT
python -c "import PyInstaller; print('  PyInstaller    OK')" 2>nul || echo   PyInstaller    MANQUANT
python -c "import nuitka; print('  Nuitka         OK')" 2>nul || echo   Nuitka         MANQUANT
echo.
echo ============================================================
echo   Installation terminee.
echo   Lance le builder avec :  python builder.py
echo ============================================================
echo.
pause