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
echo " Starting LLM Chatbot at http://localhost:8080"
echo " Press Ctrl+C to stop."
echo ""

# Open browser
(sleep 1 && (open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null)) &

venv/bin/python server.py
