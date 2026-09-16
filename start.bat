@echo off
cd /d "%~dp0"
title Snoop Builder

where python >nul 2>&1
if errorlevel 1 (
    echo Python introuvable. Lance install.bat d'abord.
    pause
    exit /b 1
)

python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installation des dependances...
    python -m pip install --quiet "PyQt5>=5.15.9,<6" requests selenium webdriver-manager
    if errorlevel 1 (
        echo Echec installation. Lance install.bat manuellement.
        pause
        exit /b 1
    )
)

start "" pythonw builder.py
exit /b 0