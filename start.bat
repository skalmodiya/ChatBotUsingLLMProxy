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

:: Start server and open browser
echo.
echo  Starting LLM Chatbot at http://localhost:8080
echo  Press Ctrl+C to stop.
echo.
start "" http://localhost:8080
venv\Scripts\python.exe server.py
