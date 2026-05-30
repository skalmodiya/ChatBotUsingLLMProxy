@echo off
title LLM Chatbot

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

:: Create venv if missing
if not exist venv (
    echo Setting up virtual environment...
    python -m venv venv
)

:: Install / upgrade deps silently
venv\Scripts\python.exe -m pip install -q -r requirements.txt

:: Kill anything already on 8080
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8080 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)

:: Ask foreground vs background
echo.
echo  How do you want to run the server?
echo  [F] Foreground  - keep this terminal open  (press Enter for default)
echo  [B] Background  - no terminal window needed (stop via browser)
echo.
set /p MODE="Choice [F/B]: "

if /i "%MODE%"=="B" (
    echo.
    echo  Starting in background ...
    start /B venv\Scripts\pythonw.exe server.py
    echo  Server running at http://localhost:8080
    echo  Use the "Stop Server" button in the browser to shut it down.
    echo.
    start "" http://localhost:8080
) else (
    echo.
    echo  Starting LLM Chatbot at http://localhost:8080
    echo  Press Ctrl+C to stop.
    echo.
    start "" http://localhost:8080
    venv\Scripts\python.exe server.py
)
