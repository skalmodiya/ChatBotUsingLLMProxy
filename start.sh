#!/bin/bash
set -e

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.9+ first."
    exit 1
fi

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv venv
fi

# Install / upgrade deps
venv/bin/pip install -q -r requirements.txt

# Kill anything on 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

echo ""
echo " How do you want to run the server?"
echo " [F] Foreground  - keep terminal open  (press Enter for default)"
echo " [B] Background  - no terminal window  (stop via browser)"
echo ""
read -t 10 -p " Choice [F/b]: " MODE || true

if [[ "$MODE" =~ ^[Bb]$ ]]; then
    nohup venv/bin/python server.py > server.log 2>&1 &
    echo ""
    echo " Server started in background (PID $!, log: server.log)"
    echo " Use the \"Stop Server\" button in the browser to shut it down."
    echo ""
    (sleep 1 && (open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null)) &
else
    echo ""
    echo " Starting LLM Chatbot at http://localhost:8080"
    echo " Press Ctrl+C to stop."
    echo ""
    (sleep 1 && (open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null)) &
    venv/bin/python server.py
fi
