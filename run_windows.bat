@echo off
cd /d "%~dp0"
title BLINK SNIPER - Hands-Free Optical Action Game
echo =========================================
echo    Starting BLINK SNIPER (Hands-Free)    
echo =========================================
if exist .venv (
    call .venv\Scripts\activate.bat
) else (
    echo Setting up Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing requirements...
    pip install -r requirements.txt
)
python main.py
if errorlevel 1 (
    echo.
    echo Game closed with an error. Press any key to exit.
    pause >nul
)
